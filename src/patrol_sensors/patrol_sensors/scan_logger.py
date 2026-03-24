import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from patrol_msgs.msg import FrontScan

class ScanLogger(Node):
    def __init__(self):
        super().__init__('scan_logger')

        self.min_range = None
        self.status = 'safe'
        self.prev_status = 'safe'
        self.current_velocity = 0.0

        # subscriber
        self.scan_subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10,
        )

        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            1, 
        )

        # publisher
        self.front_scan_publisher = self.create_publisher(
            FrontScan,
            '/front_scan',
            3,
        )

        self.timer = self.create_timer(0.5, self.timer_callback)


    def scan_callback(self, msg: LaserScan):

        # 전방 범위의 라이다 값 추출
        center_index: int = int((0.0 - msg.angle_min) / msg.angle_increment)

        angle_range: float = math.radians(10)
        half_window: int = int(angle_range / msg.angle_increment)

        start_index: int = center_index - half_window 
        end_index: int = center_index + half_window

        if start_index < 0:
            front_ranges = msg.ranges[start_index:] + msg.ranges[:end_index]
        elif end_index > len(msg.ranges):
            front_ranges = msg.ranges[start_index:] + msg.ranges[:end_index - len(msg.ranges)]
        else:
            front_ranges = msg.ranges[start_index:end_index]

        # 이상치 제거
        valid_ranges = [r for r in front_ranges if msg.range_min < r < msg.range_max]

        if not valid_ranges:
            self.get_logger().warn('No valid ranges detected')
            return

        # 전방 최소 거리
        self.min_range = min(valid_ranges)

        # 위험 상태 분류(safe, caution, danger)
        base_caution_dist = 0.4     # 0.1m/s x 4s = 0.4m
        base_danger_dist = 0.2      # 0.1m/s x 2s = 0.2m
        # if self.min_range > base_caution_dist + self.current_velocity * 4:
        #     self.status = 'safe'
        # elif self.min_range > base_danger_dist + self.current_velocity * 2:
        #     self.status = 'caution'
        # else:
        #     self.status = 'danger'
        

        target_vel = 0.1
        caution_th = base_caution_dist + target_vel * 4
        danger_th = base_danger_dist + target_vel * 2
        
        # 센서 노이즈 및 로봇의 급정거 반동으로 인한 경계값 진동을 막기 위한 히스테리시스(마진) 적용
        margin = 0.1 # 10cm 마진 (여유 반경)
        
        if self.status == 'danger':
            if self.min_range > caution_th + margin:
                self.status = 'safe'
            elif self.min_range > danger_th + margin:
                self.status = 'caution'
            else:
                self.status = 'danger'
        elif self.status == 'caution':
            if self.min_range > caution_th + margin:
                self.status = 'safe'
            elif self.min_range <= danger_th:
                self.status = 'danger'
            else:
                self.status = 'caution'
        else: # 'safe'
            if self.min_range <= danger_th:
                self.status = 'danger'
            elif self.min_range <= caution_th:
                self.status = 'caution'
            else:
                self.status = 'safe'
        

    def odom_callback(self, msg: Odometry):
        # 현재 속도 갱신
        self.current_velocity = msg.twist.twist.linear.x

    def timer_callback(self):

        log_msg = (
            f'min_range={self.min_range:.3f} m |'
            f'status={self.status} | '
            f'vel={self.current_velocity:.3f} m/s'
        )

        # custom message 생성
        front_scan_msg = FrontScan()
        front_scan_msg.status = self.status
        front_scan_msg.min_range = self.min_range
        front_scan_msg.current_velocity = self.current_velocity
        

        if self.status != self.prev_status:
            self.front_scan_publisher.publish(front_scan_msg)
            self.get_logger().warn(f'[STATE CHANGE] {log_msg}') 
            self.prev_status = self.status
        else:
            self.front_scan_publisher.publish(front_scan_msg)
            self.get_logger().info(log_msg)


def main():
    rclpy.init()
    node = ScanLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()