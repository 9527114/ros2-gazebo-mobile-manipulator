import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue

def generate_launch_description():
    # --- 0. 环境配置 ---
    os.environ['GAZEBO_MODEL_DATABASE_URI'] = '' 

    # --- 1. 路径定义 ---
    pkg_name = 'car_bot_urdf'
    try:
        pkg_share = get_package_share_directory(pkg_name)
    except Exception:
        print(f"Error: Package '{pkg_name}' not found.")
        return LaunchDescription([])

    default_model_path = os.path.join(pkg_share, 'urdf', 'car_bot_urdf.urdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz', 'config.rviz') 
    world_path = os.path.join(pkg_share, 'world', 'my_world.sdf')
    ekf_params_path = os.path.join(pkg_share, 'config', 'ekf.yaml')
    default_map_path = os.path.join(pkg_share, 'map', 'indoor_map.yaml')
    default_params_path = os.path.join(pkg_share, 'config', 'nav2_params.yaml')  
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    nav2_launch_dir = os.path.join(nav2_bringup_dir, 'launch')

    # --- 2. 参数声明 ---
    declare_model_arg = DeclareLaunchArgument('model', default_value=default_model_path, description='Robot model file')
    declare_rviz_arg = DeclareLaunchArgument('rvizconfig', default_value=default_rviz_config_path, description='RViz config file')
    declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='True', description='Enable use_sim_time')
    declare_map_yaml_cmd = DeclareLaunchArgument('map', default_value=default_map_path, description='Full path to map file to load')
    declare_params_file_cmd = DeclareLaunchArgument('params_file', default_value=default_params_path, description='Nav2 params')

    # --- 3. 启动 Gazebo (无头模式) ---
    gazebo_process = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            world_path,
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
        ],
        output='screen'
    )

    # --- 4. 生成机器人 ---

    # --- 5. 机器人状态发布 (关键修改：重映射 joint_states) ---


    robot_state_publisher_node = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': ParameterValue(
                    Command(['xacro ', LaunchConfiguration('model')]), value_type=str
                ),
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }]
        )
    
    spawn_entity = Node(
        package='gazebo_ros', executable='spawn_entity.py',
        arguments=['-entity', 'car_bot', '-topic', 'robot_description', '-x', '0', '-y', '0', '-z', '0.05'],
        output='screen'
    )

#     control_node = Node(
#     package='controller_manager',
#     executable='ros2_control_node',
#     parameters=[{
#         # 把 robot_description 通过 xacro/URDF 传进去（与你 robot_state_publisher 保持一致）
#         'robot_description': ParameterValue(
#             Command(['xacro ', LaunchConfiguration('model')]), value_type=str
#         ),
#         'use_sim_time': LaunchConfiguration('use_sim_time')
#     },
#     # 也可以加入 controllers YAML 路径，例如 controllers.yaml（如果有）
#     # os.path.join(pkg_share, 'config', 'controllers.yaml')
#     ],
#     output='screen'
# )

    # --- 6. 定位 (EKF) ---
    robot_localization_node = Node(
        package='robot_localization', executable='ekf_node', name='ekf_filter_node', output='screen',
        parameters=[ekf_params_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

# --- 7. 导航 (Nav2) - 【核心修正】 ---
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_launch_dir, 'bringup_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            # 【关键】必须设置为 True，否则 Map Server 永远不会激活
            'autostart': 'True',
            'use_composition': 'True'
        }.items()
    )
    # 这里的 hack 是因为 IncludeLaunchDescription 很难直接加 remappings，
    # 我们通常依赖 nav2_params.yaml 里的 topic 设置，或者依赖 Gazebo 端的插件配合。
    # 鉴于你的 diff_drive 插件在 /demo/cmd_vel，我们需要一个简单的 relay 或者在 Nav2 参数里改。
    # 最简单的方法：启动一个 relay 节点把 /cmd_vel 转发给 /demo/cmd_vel
    # cmd_vel_relay = Node(
    #     package='topic_tools',
    #     executable='relay',
    #     name='cmd_vel_relay',
    #     arguments=['/cmd_vel', '/demo/cmd_vel'],
    #     output='screen'
    # )

    # --- 8. RViz ---
    rviz_node = Node(
        package='rviz2', executable='rviz2', name='rviz2', output='screen',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # ... 前面的代码 ...

    # 加载控制器 1: joint_state_broadcaster
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
        parameters=[{'use_sim_time': True}],
    )

    # 加载控制器 2: arm_controller
    load_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller"],
        output="screen",
        parameters=[{'use_sim_time': True}],
    )

    from launch.actions import RegisterEventHandler
    from launch.event_handlers import OnProcessExit

    load_controllers_event = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                # 【核心修改】不要直接启动，而是套一个 10秒 的倒计时
                TimerAction(
                    period=10.0,
                    actions=[load_joint_state_broadcaster, load_arm_controller]
                )
            ],
        )
    )

    # ... return LaunchDescription([ ..., load_joint_state_broadcaster, load_arm_controller])

    ld = LaunchDescription([
        # 参数
        declare_model_arg,
        declare_rviz_arg,
        declare_use_sim_time,
        declare_map_yaml_cmd,
        declare_params_file_cmd,

        # 核心节点
        gazebo_process,
        robot_state_publisher_node, # 先发状态
        spawn_entity,               # 再生模型
        
        # 依赖关系的节点
        load_controllers_event,     # 模型生完 -> 启动控制器
        
        robot_localization_node,
        nav2_bringup_launch,
        
        # 延迟启动 RViz 防止卡顿
        TimerAction(period=5.0, actions=[rviz_node]),
    ])

    return ld