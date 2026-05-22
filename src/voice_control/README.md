# Voice Control Package

使用 Vosk 語音識別模型（vosk-model-small-en-us-0.15）實現語音控制小車運動的 ROS2 包。

## 功能

- 使用 Vosk 進行實時語音識別
- 將語音命令轉換為小車運動控制指令
- 支持前進、後退、左轉、右轉、停止等命令

## 安裝依賴

```bash
# 安裝 Python 依賴
pip3 install vosk pyaudio

# 下載 Vosk 模型
mkdir -p ~/vosk_models
cd ~/vosk_models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

## 編譯

```bash
cd /home/boris/ros_final
colcon build --packages-select voice_control
source install/setup.bash
```

## 使用方法

### 基本使用

```bash
ros2 launch voice_control voice_control.launch.py
```

### 指定模型路徑

如果模型不在默認位置，可以指定路徑：

```bash
ros2 launch voice_control voice_control.launch.py model_path:=/path/to/vosk-model-small-en-us-0.15
```

### 指定音頻設備

如果有多個音頻輸入設備，可以指定設備索引：

```bash
# 先查看可用設備（運行節點時會顯示）
ros2 launch voice_control voice_control.launch.py input_device_index:=0
```

### 調整速度參數

```bash
ros2 launch voice_control voice_control.launch.py linear_speed:=0.5 angular_speed:=0.8
```

### 指定控制話題

```bash
ros2 launch voice_control voice_control.launch.py cmd_vel_topic:=/cmd_vel
```

## 語音命令

支持以下語音命令（英文）：

- **前進**: "forward", "go forward", "move forward", "ahead", "go ahead"
- **後退**: "back", "backward", "go back", "move back", "backwards"
- **左轉**: "left", "turn left", "go left"
- **右轉**: "right", "turn right", "go right"
- **停止**: "stop", "halt", "stop moving"

## 節點說明

### speech_to_text

語音識別節點，將語音轉換為文本。

**發布話題:**
- `voice_text` (std_msgs/String): 識別到的語音文本

**參數:**
- `model_path` (string): Vosk 模型路徑
- `input_device_index` (int): 音頻輸入設備索引（-1 表示自動檢測）

### voice_cmd

語音命令處理節點，將文本命令轉換為運動控制指令。

**訂閱話題:**
- `voice_text` (std_msgs/String): 語音識別結果

**發布話題:**
- `/cmd_vel_nav` (geometry_msgs/Twist): 小車運動控制指令

**參數:**
- `cmd_vel_topic` (string): 控制話題名稱（默認: `/cmd_vel_nav`）
- `linear_speed` (double): 線速度（m/s，默認: 0.3）
- `angular_speed` (double): 角速度（rad/s，默認: 0.5）

## 故障排除

### 找不到音頻設備

確保系統有可用的音頻輸入設備：

```bash
# 列出音頻設備
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]"
```

### 模型路徑錯誤

確保模型已正確下載並解壓，路徑應包含 `model.json` 文件。

### 權限問題

如果無法訪問音頻設備，可能需要將用戶添加到音頻組：

```bash
sudo usermod -a -G audio $USER
```

然後重新登錄。


