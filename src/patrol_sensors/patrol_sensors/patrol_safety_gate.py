import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from patrol_msgs.msg import FrontScan

class PatrolSafetyGate(Node):
    def __init__(self):
        super().__init__('patrol_safety_gate')

        self.safety_status = 'unknown'

        # subscriber
        self.create_subscription(
            Twist,
            '/cmd_vel_raw',
            self.cmd_vel_raw_callback,
            10
        )
        self.create_subscription(
            FrontScan,
            '/front_scan',
            self.front_scan_callback,
            10
        )

        # publisher
        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

    def cmd_vel_raw_callback(self, msg: Twist):
        # danger 상태이면 정지
        if self.safety_status == 'danger':
            self.get_logger().fatal(f'safety_status: {self.safety_status}')
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        elif self.safety_status == 'caution':
            self.get_logger().warn(f'safety_status: {self.safety_status}')
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        
        self.cmd_vel_publisher.publish(msg)
        

    def front_scan_callback(self, msg: FrontScan):
        self.safety_status = msg.status


def main():
    rclpy.init()
    node = PatrolSafetyGate()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
