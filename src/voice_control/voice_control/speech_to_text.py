#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import os


class SpeechToText(Node):
    def __init__(self):
        super().__init__('speech_to_text')

        self.pub = self.create_publisher(String, 'voice_text', 10)

        # 獲取模型路徑參數，如果沒有設置則使用默認路徑
        self.declare_parameter('model_path', '')
        model_path_param = self.get_parameter('model_path').get_parameter_value().string_value
        
        # 如果參數為空，嘗試常見的模型路徑
        if not model_path_param:
            # 嘗試多個可能的路徑
            possible_paths = [
                os.path.expanduser('~/vosk_models/vosk-model-small-en-us-0.15'),
                '/usr/local/share/vosk-model-small-en-us-0.15',
                os.path.join(os.path.dirname(__file__), '../../models/vosk-model-small-en-us-0.15'),
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                # 如果都找不到，使用當前用戶目錄下的路徑
                model_path = os.path.expanduser('~/vosk_models/vosk-model-small-en-us-0.15')
                self.get_logger().warn(f"⚠️  模型路徑未找到，將使用: {model_path}")
                self.get_logger().warn("⚠️  請確保已下載並解壓 vosk-model-small-en-us-0.15 到該路徑")
        else:
            model_path = model_path_param

        self.get_logger().info(f"📦 載入 Vosk 模型: {model_path}")
        
        if not os.path.exists(model_path):
            self.get_logger().error(f"❌ 模型路徑不存在: {model_path}")
            self.get_logger().error("請下載模型: https://alphacephei.com/vosk/models")
            raise FileNotFoundError(f"Vosk model not found at {model_path}")
        
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.rec.SetWords(True)

        # 音頻設備配置
        self.audio = pyaudio.PyAudio()
        
        # 自動檢測輸入設備
        self.declare_parameter('input_device_index', -1)
        input_device_index = self.get_parameter('input_device_index').get_parameter_value().integer_value
        
        if input_device_index < 0:
            # 自動檢測默認輸入設備
            try:
                default_input = self.audio.get_default_input_device_info()
                input_device_index = default_input['index']
                self.get_logger().info(f"🎤 使用默認輸入設備: {default_input['name']} (索引: {input_device_index})")
            except Exception as e:
                self.get_logger().warn(f"⚠️  無法獲取默認輸入設備，將使用索引 0: {e}")
                input_device_index = 0
        else:
            device_info = self.audio.get_device_info_by_index(input_device_index)
            self.get_logger().info(f"🎤 使用指定輸入設備: {device_info['name']} (索引: {input_device_index})")
        
        # 列出所有可用的輸入設備（用於調試）
        self.get_logger().info("📋 可用的音頻輸入設備:")
        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    marker = " ← 當前使用" if i == input_device_index else ""
                    self.get_logger().info(f"  [{i}] {info['name']}{marker}")
            except:
                pass

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=4000
        )

        self.stream.start_stream()
        self.get_logger().info("🎤 開始監聽語音...")

        self.timer = self.create_timer(0.1, self.listen)

    def listen(self):
        try:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.rec.AcceptWaveform(data):
                result = json.loads(self.rec.Result())
                text = result.get("text", "").strip()
                if text:
                    msg = String()
                    msg.data = text
                    self.pub.publish(msg)
                    self.get_logger().info(f"✅ 識別到: {text}")
            else:
                # 獲取部分結果（用於實時反饋）
                partial = json.loads(self.rec.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text:
                    self.get_logger().debug(f"部分識別: {partial_text}")
        except Exception as e:
            self.get_logger().error(f"❌ 音頻處理錯誤: {e}")

    def destroy_node(self):
        self.get_logger().info("🛑 停止語音識別...")
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        super().destroy_node()


def main():
    rclpy.init()
    node = SpeechToText()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


