# bringup_with_slam_fixed.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from launch.actions import ExecuteProcess
from launch.conditions import IfCondition
import os

def generate_launch_description():
    pkg_share = FindPackageShare(package='car_bot_urdf').find('car_bot_urdf')
    default_model_path = os.path.join(pkg_share, 'urdf', 'car_bot_urdf.urdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz', 'config.rviz')
    world_path = os.path.join(pkg_share, 'world', 'my_world.sdf')
    slam_params_path = os.path.join(pkg_share, 'config', 'slam_toolbox.yaml')
    ekf_params_path = os.path.join(pkg_share, 'config', 'ekf.yaml')
    default_map_filename = os.path.join(pkg_share, 'maps', 'indoor_map')

    # launch args: joint_states topic is made configurable because Gazebo may use a namespace (e.g. /demo/joint_states)
    declare_model_arg = DeclareLaunchArgument('model', default_value=default_model_path, description='Robot model file')
    declare_rviz_arg = DeclareLaunchArgument('rvizconfig', default_value=default_rviz_config_path, description='RViz config file')
    declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='True', description='Enable use_sim_time')
    # If your Gazebo publishes joint_states under a namespace, set this to that topic (e.g. /demo/joint_states)
    declare_joint_states_topic = DeclareLaunchArgument('joint_states_topic', default_value='/demo/joint_states',
                                                      description='Topic where Gazebo publishes joint_states (set to /joint_states or /<ns>/joint_states)')
    declare_enable_slam = DeclareLaunchArgument('enable_slam', default_value='True', description='Enable SLAM (slam_toolbox)')
    declare_save_map = DeclareLaunchArgument('save_map', default_value='False', description='Automatically save map after delay')
    declare_map_filename = DeclareLaunchArgument('map_filename', default_value=default_map_filename, description='Filename prefix for saved map')

    # Start Gazebo
    gazebo_process = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            world_path,
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so'
        ],
        output='screen'
    )

    # Spawn entity (delay a bit to let Gazebo init)
    spawn_entity = TimerAction(
        period=3.0,
        actions=[Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'car_bot', '-topic', 'robot_description', '-x', '0', '-y', '0', '-z', '0.05'],
            output='screen'
        )]
    )

    # robot_state_publisher: REMAP joint_states to the actual topic (Launch arg 'joint_states_topic')
    # Also delayed so that joint_states exist in the bus.
    robot_state_publisher_node = TimerAction(
        period=4.0,  # spawn_entity (3s) -> give one more second for Gazebo plugins to start publishing joint_states
        actions=[Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': ParameterValue(
                    Command(['xacro ', LaunchConfiguration('model')]), value_type=str
                ),
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }],
            # remap the joint_states topic to the actual topic produced by Gazebo (default set to /demo/joint_states above)
            # ...
            # remappings=[
            #     ('/joint_states', LaunchConfiguration('joint_states_topic')) # <--- 使用参数变量
            # ]
# ...
        )]
    )
    # robot_localization EKF (no change)
    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # SLAM node delayed a bit to wait for robot_state_publisher/odom
    slam_node = TimerAction(
        period=6.0,
        actions=[Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_path, {'use_sim_time': LaunchConfiguration('use_sim_time')}],
            remappings=[('scan', '/scan')]  # change if your lidar topic differs
        )]
    )

    # RViz: start after SLAM so that map/tf exist (avoids tf buffer errors)
    rviz_node_delayed = TimerAction(
        period=9.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', LaunchConfiguration('rvizconfig')],
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
        )]
    )

    # Optional map saving (conditional)
    map_saver_delayed = TimerAction(
        period=60.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'run', 'nav2_map_server', 'map_saver_cli', '-f', LaunchConfiguration('map_filename')],
            output='screen',
            condition=IfCondition(LaunchConfiguration('save_map'))
        )]
    )

    ld = LaunchDescription([
        declare_model_arg,
        declare_rviz_arg,
        declare_use_sim_time,
        declare_joint_states_topic,
        declare_enable_slam,
        declare_save_map,
        declare_map_filename,

        gazebo_process,
        spawn_entity,
        robot_state_publisher_node,
        robot_localization_node,
        slam_node,
        rviz_node_delayed,
        map_saver_delayed
    ])

    return ld
