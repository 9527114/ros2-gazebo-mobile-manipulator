#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist


class VoiceCmd(Node):
    def __init__(self):
        super().__init__('voice_cmd')

        self.sub = self.create_subscription(
            String,
            'voice_text',
            self.voice_callback,
            10
        )

        # 獲取控制話題參數
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_nav')
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value

        self.pub = self.create_publisher(
            Twist,
            cmd_vel_topic,
            10
        )

        # 獲取速度參數
        self.declare_parameter('linear_speed', 0.3)
        self.declare_parameter('angular_speed', 30.0)
        self.linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        self.angular_speed = self.get_parameter('angular_speed').get_parameter_value().double_value

        self.get_logger().info(f"🎙 語音控制節點已就緒")
        self.get_logger().info(f"   控制話題: {cmd_vel_topic}")
        self.get_logger().info(f"   線速度: {self.linear_speed} m/s")
        self.get_logger().info(f"   角速度: {self.angular_speed} rad/s")

    def voice_callback(self, msg):
        text = msg.data.lower().strip()
        cmd = Twist()

        # 語音命令映射
        # 支持多種表達方式
        if any(word in text for word in ["forward", "go forward", "move forward", "ahead", "go ahead"]):
            cmd.linear.x = self.linear_speed
            cmd.angular.z = 0.0
            self.get_logger().info(f"🚗 執行命令: 前進 ({text})")
            
        elif any(word in text for word in ["back", "backward", "go back", "move back", "backwards"]):
            cmd.linear.x = -self.linear_speed
            cmd.angular.z = 0.0
            self.get_logger().info(f"🚗 執行命令: 後退 ({text})")
            
        elif any(word in text for word in ["left", "turn left", "go left"]):
            cmd.linear.x = 0.0
            cmd.angular.z = self.angular_speed
            self.get_logger().info(f"🚗 執行命令: 左轉 ({text})")
            
        elif any(word in text for word in ["right", "turn right", "go right"]):
            cmd.linear.x = 0.0
            cmd.angular.z = -self.angular_speed
            self.get_logger().info(f"🚗 執行命令: 右轉 ({text})")
            
        elif any(word in text for word in ["stop", "halt", "stop moving"]):
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.get_logger().info(f"🚗 執行命令: 停止 ({text})")
            
        else:
            self.get_logger().debug(f"未識別的命令: {text}")
            return

        self.pub.publish(cmd)


def main():
    rclpy.init()
    node = VoiceCmd()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


