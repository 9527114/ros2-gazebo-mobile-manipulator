#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import cv2
import mediapipe as mp

# =================================================================
# 🛠️ 关键修复区域：显式导入 MediaPipe 模块
# 这能避开 "module has no attribute 'solutions'" 的报错
# =================================================================
try:
    from mediapipe.python.solutions import hands as mp_hands_module
    from mediapipe.python.solutions import drawing_utils as mp_drawing_module
except ImportError:
    # 如果显式导入失败，尝试回退到普通导入（兼容性处理）
    import mediapipe.python.solutions.hands as mp_hands_module
    import mediapipe.python.solutions.drawing_utils as mp_drawing_module
# =================================================================

class GestureControlNode(Node):
    def __init__(self):
        super().__init__('gesture_control_node')
        
        # 👇👇👇 修改点：话题名称适配您的 URDF 配置 👇👇👇
        # 您的 URDF 将 cmd_vel 重映射为了 /cmd_vel_nav
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel_nav', 10)
        
        # 设置定时器，每0.1秒处理一次图像 (10Hz)
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        # 打开摄像头 (默认索引0)
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            self.get_logger().error("无法打开摄像头！")
            exit()

        # 配置 MediaPipe
        self.mp_hands = mp_hands_module
        self.mp_drawing = mp_drawing_module
        
        # 初始化手部检测模型
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
            max_num_hands=1  # 只检测一只手
        )
        
        self.get_logger().info("手势控制节点已启动！发布话题: /cmd_vel_nav")
        self.get_logger().info("操作说明: 1指=前, 2指=后, 3指=左, 4指=右, 拳头/5指=停")

    def count_fingers(self, hand_landmarks):
        """简单粗暴的数手指算法"""
        finger_tips = [8, 12, 16, 20]  # 食指、中指、无名指、小指的指尖索引
        finger_pips = [6, 10, 14, 18]  # 指关节索引
        
        count = 0
        
        # 1. 拇指判断 (根据手是左还是右，判断x坐标)
        # 这里简化处理，假设右手，且手掌朝向摄像头
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            count += 1
            
        # 2. 其他四指判断 (指尖是否高于指关节 - 注意y轴向下为正)
        for i in range(4):
            if hand_landmarks.landmark[finger_tips[i]].y < hand_landmarks.landmark[finger_pips[i]].y:
                count += 1
                
        return count

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # 镜像翻转，让画面更符合直觉
        frame = cv2.flip(frame, 1)
        
        # MediaPipe 需要 RGB 格式
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 进行处理
        results = self.hands.process(image_rgb)
        
        # 创建速度消息
        msg = Twist()
        gesture_name = "STOP"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 绘制骨架
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # 数手指
                fingers = self.count_fingers(hand_landmarks)
                
                # === 控制逻辑 ===
                # 线速度 (m/s) 和 角速度 (rad/s) 可以根据您的仿真环境微调
                if fingers == 1:  # 食指 -> 前进
                    msg.linear.x = 0.5   # 加快一点速度
                    gesture_name = "FORWARD"
                elif fingers == 2: # 剪刀手 -> 后退
                    msg.linear.x = -0.5
                    gesture_name = "BACKWARD"
                elif fingers == 3: # 三根手指 -> 左转
                    msg.angular.z = 3.0  # 加大转向速度
                    gesture_name = "LEFT"
                elif fingers == 4: # 四根手指 -> 右转
                    msg.angular.z = -3.0
                    gesture_name = "RIGHT"
                else:              # 拳头(0) 或 手掌(5) -> 停止
                    msg.linear.x = 0.0
                    msg.angular.z = 0.0
                    gesture_name = "STOP"

        # 发布速度指令
        self.publisher_.publish(msg)

        # 在画面上显示当前状态
        cv2.putText(frame, f"Gesture: {gesture_name}", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Topic: /cmd_vel_nav", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        cv2.imshow('Gesture Control', frame)
        cv2.waitKey(1)

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = GestureControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
