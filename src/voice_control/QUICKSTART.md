# 快速開始指南

## 1. 下載 Vosk 模型

```bash
mkdir -p ~/vosk_models
cd ~/vosk_models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

模型應該解壓到：`~/vosk_models/vosk-model-small-en-us-0.15/`

## 2. 安裝 Python 依賴

```bash
pip3 install vosk pyaudio
```

## 3. 編譯包

```bash
cd /home/boris/ros_final
colcon build --packages-select voice_control
source install/setup.bash
```

## 4. 運行語音控制

### 方式 1: 使用 launch 文件（推薦）

```bash
ros2 launch voice_control voice_control.launch.py
```

### 方式 2: 單獨運行節點

終端 1 - 語音識別：
```bash
ros2 run voice_control speech_to_text
```

終端 2 - 命令處理：
```bash
ros2 run voice_control voice_cmd
```

## 5. 測試語音命令

對著麥克風說以下英文命令：
- "forward" 或 "go forward" - 小車前進
- "back" 或 "go back" - 小車後退
- "left" 或 "turn left" - 小車左轉
- "right" 或 "turn right" - 小車右轉
- "stop" - 小車停止

## 6. 檢查音頻設備

如果無法識別語音，檢查音頻設備：

```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'[{i}] {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]"
```

然後使用正確的設備索引：
```bash
ros2 launch voice_control voice_control.launch.py input_device_index:=0
```

## 故障排除

1. **模型路徑錯誤**: 確保模型已正確下載到 `~/vosk_models/vosk-model-small-en-us-0.15/`
2. **音頻權限**: 如果無法訪問麥克風，運行 `sudo usermod -a -G audio $USER` 並重新登錄
3. **找不到設備**: 檢查系統音頻設置，確保麥克風已啟用


