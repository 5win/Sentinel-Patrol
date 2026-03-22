import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class ScanLogger(Node):
    def __init__(self):
        super().__init__('scan_logger')

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10,
        )
    
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

        min_range = min(valid_ranges)
        self.get_logger().info(f'Min range: {min_range:.3f} m')


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