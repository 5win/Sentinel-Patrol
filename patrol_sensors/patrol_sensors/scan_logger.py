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
        valid_ranges = [r for r in msg.ranges if msg.range_min < r < msg.range_max]

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