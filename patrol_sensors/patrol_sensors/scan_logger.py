import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry

class ScanLogger(Node):
    def __init__(self):
        super().__init__('scan_logger')

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

        self.current_velocity = 0.0


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
        min_range = min(valid_ranges)
        self.get_logger().info(f'Min range: {min_range:.3f} m')

        # 위험 상태 분류(safe, caution, danger)
        base_caution_dist = 0.4     # 0.1m/s x 4s = 0.4m
        base_danger_dist = 0.2      # 0.1m/s x 2s = 0.2m
        if min_range > base_caution_dist + self.current_velocity * 4:
            status = 'safe'
        elif min_range > base_danger_dist + self.current_velocity * 2:
            status = 'caution'
        else:
            status = 'danger'
        
        self.get_logger().info(f'status: {status}')
    

    def odom_callback(self, msg: Odometry):
        # 현재 속도 갱신
        self.current_velocity = msg.twist.twist.linear.x
        # self.get_logger().info(f'Current velocity: {self.current_velocity:.3f} m/s')




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