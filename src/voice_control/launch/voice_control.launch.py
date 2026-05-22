from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # 聲明啟動參數
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='',
        description='Vosk 模型路徑（留空則自動檢測）'
    )
    
    input_device_arg = DeclareLaunchArgument(
        'input_device_index',
        default_value='-1',
        description='音頻輸入設備索引（-1 表示自動檢測）'
    )
    
    cmd_vel_topic_arg = DeclareLaunchArgument(
        'cmd_vel_topic',
        default_value='/cmd_vel_nav',
        description='控制小車運動的話題名稱'
    )
    
    linear_speed_arg = DeclareLaunchArgument(
        'linear_speed',
        default_value='0.3',
        description='線速度（m/s）'
    )
    
    angular_speed_arg = DeclareLaunchArgument(
        'angular_speed',
        default_value='0.5',
        description='角速度（rad/s）'
    )

    # 語音識別節點
    speech_node = Node(
        package='voice_control',
        executable='speech_to_text',
        name='speech_to_text',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'input_device_index': LaunchConfiguration('input_device_index'),
        }]
    )

    # 語音命令處理節點
    voice_cmd_node = Node(
        package='voice_control',
        executable='voice_cmd',
        name='voice_cmd',
        output='screen',
        parameters=[{
            'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic'),
            'linear_speed': LaunchConfiguration('linear_speed'),
            'angular_speed': LaunchConfiguration('angular_speed'),
        }]
    )

    return LaunchDescription([
        model_path_arg,
        input_device_arg,
        cmd_vel_topic_arg,
        linear_speed_arg,
        angular_speed_arg,
        speech_node,
        voice_cmd_node,
    ])


