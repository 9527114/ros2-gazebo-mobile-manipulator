# 基于 Gazebo 的 ROS2 仿真小车巡航与夹取系统

本项目是一个基于 ROS2、Gazebo、Nav2 与 MoveIt 的移动机器人仿真系统。项目完成了四轮差速小车、机械臂、夹爪和多传感器的 URDF 建模，并在 Gazebo 中接入差速驱动、激光雷达、IMU、深度相机、机械臂控制器和夹爪控制器，实现仿真环境下的小车自主巡航、语音控制与夹取执行能力。

## 功能特性

- 基于 URDF 搭建四轮差速小车、机械臂、夹爪及传感器模型
- 支持 Gazebo 仿真加载、RViz 可视化和 `robot_state_publisher` 状态发布
- 集成 `ros2_control` 与 Gazebo 控制插件，支持底盘、机械臂和夹爪控制
- 基于 Nav2 实现地图加载、AMCL 定位、路径规划、局部避障与巡航
- 基于 MoveIt 配置机械臂运动规划与夹爪控制
- 基于 Vosk + PyAudio 实现电脑麦克风语音识别控制小车运动
- 支持语音命令控制小车前进、后退、左转、右转和停止

## 技术栈

- ROS2
- Gazebo
- RViz
- URDF / Xacro
- Nav2
- MoveIt
- ros2_control / ros2_controllers
- Python / C++
- Vosk / PyAudio
- AMCL / DWB Local Planner / Pure Pursuit Controller

## 项目结构

```text
ros_final/
└── src/
    ├── car_bot_urdf/                 # 小车、机械臂、夹爪、传感器 URDF 与 Gazebo 仿真配置
    │   ├── config/                   # Nav2、控制器、EKF、SLAM 参数
    │   ├── launch/                   # Gazebo、导航、总启动文件
    │   ├── map/                      # 室内地图
    │   ├── meshes/                   # 机器人 STL 模型文件
    │   ├── rviz/                     # RViz 配置
    │   ├── urdf/                     # 机器人 URDF 文件
    │   └── world/                    # Gazebo 世界文件
    ├── car_moveit_config/            # MoveIt 运动规划配置
    ├── nav2_pure_pursuit_controller/ # Nav2 Pure Pursuit 控制器插件
    ├── nav2_sms_behavior/            # Nav2 自定义行为插件示例
    └── voice_control/                # 语音识别与语音控制模块

```

## 环境依赖

建议环境：

- Ubuntu 22.04
- ROS2 Humble
- Gazebo Classic
- Python 3.10

ROS2 相关依赖：

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-moveit \
  ros-humble-robot-localization \
  ros-humble-xacro
```

语音识别依赖：

```bash
pip3 install vosk pyaudio
```

下载 Vosk 语音识别模型：

```bash
mkdir -p ~/vosk_models
cd ~/vosk_models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

## 构建项目

进入工作空间根目录：

```bash
cd ~/ros_final
```

安装依赖：

```bash
rosdep install --from-paths src --ignore-src -r -y
```

构建：

```bash
colcon build
```

加载环境：

```bash
source install/setup.bash
```

## 运行方式

### 1. 启动完整系统

完整启动 Gazebo、机器人模型、控制器、Nav2、MoveIt、RViz 和语音控制节点：

```bash
ros2 launch car_bot_urdf alltogether.launch.py
```

### 2. 仅启动导航仿真

启动 Gazebo、机器人模型、Nav2 导航和 RViz：

```bash
ros2 launch car_bot_urdf navigation.launch.py
```

### 3. 单独启动语音控制

```bash
ros2 launch voice_control voice_control.launch.py
```

指定 Vosk 模型路径：

```bash
ros2 launch voice_control voice_control.launch.py \
  model_path:=~/vosk_models/vosk-model-small-en-us-0.15
```

指定麦克风输入设备和速度参数：

```bash
ros2 launch voice_control voice_control.launch.py \
  input_device_index:=0 \
  linear_speed:=0.3 \
  angular_speed:=0.5 \
  cmd_vel_topic:=/cmd_vel_nav
```

## 语音控制命令

语音控制模块会从电脑麦克风采集音频，使用 Vosk 将语音识别为文本，再将文本映射为 `geometry_msgs/Twist` 消息并发布到 `/cmd_vel_nav`。

| 语音命令 | 小车动作 |
| --- | --- |
| `forward` / `go forward` / `move forward` / `ahead` | 前进 |
| `back` / `backward` / `go back` / `move back` | 后退 |
| `left` / `turn left` / `go left` | 左转 |
| `right` / `turn right` / `go right` | 右转 |
| `stop` / `halt` / `stop moving` | 停止 |

也可以使用测试脚本启动语音控制：

```bash
./test_voice_control.sh
```

## 主要模块说明

### car_bot_urdf

机器人描述与仿真核心包，包含小车底盘、机械臂、夹爪、IMU、激光雷达、深度相机等模型配置。URDF 中集成了 Gazebo 差速驱动插件、雷达传感器插件、IMU 插件、深度相机插件以及 `gazebo_ros2_control` 控制接口。

### voice_control

语音控制包，包含两个主要节点：

- `speech_to_text`：通过 PyAudio 采集麦克风音频，使用 Vosk 离线模型识别语音文本，并发布到 `voice_text` 话题
- `voice_cmd`：订阅 `voice_text`，将识别文本映射为速度控制指令，并发布到 `/cmd_vel_nav`

### car_moveit_config

MoveIt 配置包，包含机械臂和夹爪的 SRDF、运动学配置、规划配置、控制器配置和 RViz 配置，用于机械臂运动规划和执行。

### nav2_pure_pursuit_controller

Nav2 控制器插件，实现 Pure Pursuit 路径跟踪算法。算法根据机器人当前位置裁剪全局路径，在前视距离内选择目标点，并计算线速度和角速度用于路径跟踪。

## 常用话题

| 话题 | 类型 | 说明 |
| --- | --- | --- |
| `/cmd_vel_nav` | `geometry_msgs/Twist` | 小车速度控制话题 |
| `/odom` | `nav_msgs/Odometry` | 里程计话题 |
| `/scan` | `sensor_msgs/LaserScan` | 激光雷达话题 |
| `voice_text` | `std_msgs/String` | 语音识别文本结果 |
| `/joint_states` | `sensor_msgs/JointState` | 机器人关节状态 |

## 注意事项

- 运行前请确认已经执行 `source install/setup.bash`
- 如果 Gazebo 中模型无法加载，请检查 STL 模型文件路径和 `car_bot_urdf` 包是否成功安装
- 如果 Nav2 无法启动，请检查地图文件路径、`nav2_params.yaml` 中的话题配置以及 `/scan`、`/odom` 是否正常发布
- 如果语音识别无法启动，请确认 Vosk 模型已下载，并检查麦克风权限和 PyAudio 是否安装成功
- 如果存在多个音频输入设备，可以通过 `input_device_index` 指定设备编号

## 项目效果

本项目实现了一个完整的 ROS2 仿真机器人工作流：从机器人建模、Gazebo 仿真、控制器接入、导航巡航，到语音交互控制与机械臂夹爪仿真，为移动机器人导航和操作任务提供了可复现的仿真实验平台。
<img width="355" height="270" alt="image" src="https://github.com/user-attachments/assets/80439550-ccea-433b-849e-45567d3a8c71" />
<img width="609" height="382" alt="image" src="https://github.com/user-attachments/assets/fe408f31-2569-46b2-9b24-3693744c5bd2" />
<img width="626" height="392" alt="image" src="https://github.com/user-attachments/assets/44d288cc-9354-4bd1-9746-62668409f4e5" />

