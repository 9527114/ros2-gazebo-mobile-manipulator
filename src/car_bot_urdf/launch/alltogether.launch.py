import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch.event_handlers import OnProcessExit

# --- 辅助函数：加载 YAML 文件 ---
def load_yaml(package_name, file_path):
    try:
        package_path = get_package_share_directory(package_name)
    except Exception as e:
        print(f"\033[91m[ERROR] Package '{package_name}' not found in install! Did you source setup.bash?\033[0m")
        return None

    absolute_file_path = os.path.join(package_path, file_path)
    
    try:
        with open(absolute_file_path, 'r') as file:
            print(f"\033[92m[SUCCESS] Loaded: {absolute_file_path}\033[0m") # 绿色成功提示
            return yaml.safe_load(file)
    except EnvironmentError: 
        # 红色报错提示，告诉你具体缺了哪个文件
        print(f"\033[91m[ERROR] YAML file missing: {absolute_file_path}\033[0m")
        return None

def generate_launch_description():
    # --- 0. 环境配置 ---
    os.environ['GAZEBO_MODEL_DATABASE_URI'] = '' 

    # --- 1. 基础路径定义 ---
    pkg_name = 'car_bot_urdf'
    moveit_config_pkg = 'car_moveit_config' # MoveIt 配置包的名字
    
    pkg_share = get_package_share_directory(pkg_name)
    moveit_config_share = get_package_share_directory(moveit_config_pkg)
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # 资源路径
    default_model_path = os.path.join(pkg_share, 'urdf', 'car_bot_urdf.urdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz', 'config.rviz') 
    world_path = os.path.join(pkg_share, 'world', 'my_world.sdf')
    ekf_params_path = os.path.join(pkg_share, 'config', 'ekf.yaml')
    default_map_path = os.path.join(pkg_share, 'map', 'indoor_map.yaml')
    default_params_path = os.path.join(pkg_share, 'config', 'nav2_params.yaml')  
    nav2_launch_dir = os.path.join(nav2_bringup_dir, 'launch')

    # --- 2. 准备 MoveIt 配置 ---
    # 2.1 加载 SRDF (语义描述)
    # ⚠️ 请确认这里的文件名与 car_moveit_config/config/ 下的文件名一致
    srdf_file_name = 'car_bot_urdf.srdf' 
    srdf_path = os.path.join(moveit_config_share, 'config', srdf_file_name)
    with open(srdf_path, 'r') as f:
        robot_description_semantic_content = f.read()

    # 2.2 加载各种 YAML 配置
    kinematics_yaml = load_yaml(moveit_config_pkg, 'config/kinematics.yaml')
    joint_limits_yaml = load_yaml(moveit_config_pkg, 'config/joint_limits.yaml')
    ompl_planning_yaml = load_yaml(moveit_config_pkg, 'config/ompl_planning.yaml')
    moveit_controllers_yaml = load_yaml(moveit_config_pkg, 'config/moveit_controllers.yaml')

    # 2.3 规划场景与执行配置
    trajectory_execution = {
        'moveit_manage_controllers': True,
        'trajectory_execution.allowed_execution_duration_scaling': 1.2,
        'trajectory_execution.allowed_goal_duration_margin': 0.5,
        'trajectory_execution.allowed_start_tolerance': 0.01,
    }
    planning_scene_monitor_parameters = {
        'publish_planning_scene': True,
        'publish_geometry_updates': True,
        'publish_state_updates': True,
        'publish_transforms_updates': True,
    }

    # 2.4 构建 Move Group 核心参数字典
    # 注意：robot_description 会在 Node 中动态生成，这里先准备好逻辑
    move_group_params = {
        'robot_description_semantic': robot_description_semantic_content,
        'robot_description_kinematics': kinematics_yaml,
        'planning_pipelines': ['ompl'],
        'ompl': ompl_planning_yaml,
        'use_sim_time': LaunchConfiguration('use_sim_time'),
    }
    
    # 合并关节限制配置
    if joint_limits_yaml:
        move_group_params['robot_description_planning'] = joint_limits_yaml
    
    move_group_params.update(trajectory_execution)
    move_group_params.update(planning_scene_monitor_parameters)

    # --- 3. 参数声明 (Launch Arguments) ---
    declare_model_arg = DeclareLaunchArgument('model', default_value=default_model_path, description='Robot model file')
    declare_rviz_arg = DeclareLaunchArgument('rvizconfig', default_value=default_rviz_config_path, description='RViz config file')
    declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='True', description='Enable use_sim_time')
    declare_map_yaml_cmd = DeclareLaunchArgument('map', default_value=default_map_path, description='Full path to map file to load')
    declare_params_file_cmd = DeclareLaunchArgument('params_file', default_value=default_params_path, description='Nav2 params')

    # --- 4. 节点定义 ---

    # 4.1 Gazebo
    gazebo_process = ExecuteProcess(
        cmd=[
            'gazebo', '--verbose', world_path,
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
        ],
        output='screen'
    )

    # 4.2 Robot State Publisher (生成 robot_description)
    robot_description_content = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]), value_type=str
    )
    
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )
    
    # 把 robot_description 也加到 move_group 参数里
    move_group_params['robot_description'] = robot_description_content

    # 4.3 Spawn Entity (生成模型)
    spawn_entity = Node(
        package='gazebo_ros', executable='spawn_entity.py',
        arguments=['-entity', 'car_bot', '-topic', 'robot_description', '-x', '0', '-y', '0', '-z', '0.05'],
        output='screen'
    )

    # 4.4 Controllers (控制器加载)
    load_joint_state_broadcaster = Node(
        package="controller_manager", executable="spawner",
        arguments=["joint_state_broadcaster"], output="screen",
        parameters=[{'use_sim_time': True}],
    )

    load_arm_controller = Node(
        package="controller_manager", executable="spawner",
        arguments=["arm_controller"], output="screen",
        parameters=[{'use_sim_time': True}],
    )

    load_gripper_controller = Node(
    package="controller_manager",
    executable="spawner",
    arguments=["gripper_controller"],
    output="screen",
    parameters=[{'use_sim_time': True}],
    )

    # 事件处理：模型生成后再启动控制器 (延迟启动)
    load_controllers_event = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                TimerAction(
                    period=10.0, # 等待 Gazebo 彻底稳定
                    actions=[load_joint_state_broadcaster, load_arm_controller, load_gripper_controller]
                )
            ],
        )
    )

    # 4.5 MoveIt Node (运动规划核心)
    run_move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            move_group_params,
            moveit_controllers_yaml, # 传入控制器配置，让 MoveIt 知道如何与 ros2_control 交互
        ],
    )

    # 4.6 Robot Localization (EKF)
    robot_localization_node = Node(
        package='robot_localization', executable='ekf_node', name='ekf_filter_node', output='screen',
        parameters=[ekf_params_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # 4.7 Nav2 Bringup (导航)
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_launch_dir, 'bringup_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            'autostart': 'True',
            'use_composition': 'True'
        }.items()
    )

    # 4.8 RViz
    rviz_node = Node(
        package='rviz2', executable='rviz2', name='rviz2', output='screen',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
        parameters=[
            # 1. 传递时间同步参数
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            # 2. 传递 URDF (机器人模型)
            {'robot_description': robot_description_content},
            # 3. 传递 SRDF (语义描述) - 这一步能修复 XML_ERROR_EMPTY_DOCUMENT
            {'robot_description_semantic': robot_description_semantic_content},
            # 4. 传递运动学配置
            kinematics_yaml,
        ]
    )

    # --- 4.9 语音控制节点 (新增) ---
    speech_to_text_node = Node(
        package='voice_control',
        executable='speech_to_text',
        name='speech_to_text',
        output='screen'
    )

    voice_cmd_node = Node(
        package='voice_control',
        executable='voice_cmd',
        name='voice_cmd',
        output='screen'
    )

    # --- 5. 组合 Launch Description ---
    ld = LaunchDescription([
        # 参数声明
        declare_model_arg,
        declare_rviz_arg,
        declare_use_sim_time,
        declare_map_yaml_cmd,
        declare_params_file_cmd,

        # 基础设施
        gazebo_process,
        robot_state_publisher_node,
        spawn_entity,

        # 依赖链：模型生成 -> 控制器 -> MoveIt
        load_controllers_event,
        
        # 导航与定位
        robot_localization_node,
        nav2_bringup_launch,

        # 语音控制模块
        speech_to_text_node,
        voice_cmd_node,

        # MoveIt (延迟启动以确保控制器已就绪)
        TimerAction(period=15.0, actions=[run_move_group_node]),

        # RViz
        TimerAction(period=5.0, actions=[rviz_node]),
    ])

    return ld
