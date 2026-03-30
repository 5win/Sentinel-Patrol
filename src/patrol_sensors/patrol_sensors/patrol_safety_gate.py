import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

class PatrolSafetyGate(Node):
    def __init__(self):
        super().__init__('patrol_safety_gate')

        self.cmd_vel_raw: Twist = None
        self.cmd_vel_manager: Twist = None
        self.patrol_state: str = 'idle'

        # subscriber
        self.create_subscription(
            Twist,
            '/cmd_vel_raw',
            self.cmd_vel_raw_callback,
            10
        )

        self.create_subscription(
            Twist,
            '/cmd_vel_manager',
            self.cmd_vel_manager_callback,
            10
        )

        self.create_subscription(
            String,
            '/patrol/state',
            self.patrol_state_callback,
            10
        )

        # publisher
        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # timer
        self.timer = self.create_timer(0.1, self.timer_callback)


    def cmd_vel_raw_callback(self, msg: Twist):
        self.cmd_vel_raw = msg
    
    def cmd_vel_manager_callback(self, msg: Twist):
        self.cmd_vel_manager = msg
    
    def patrol_state_callback(self, msg: String):
        self.patrol_state = msg.data.lower()    # 소문자로 변환

    def timer_callback(self):
        self.get_logger().info(f'patrol/state: {self.patrol_state}', throttle_duration_sec=1.0)

        if self.cmd_vel_raw is None:
            return

        if self.patrol_state == 'patrolling':
            self.cmd_vel_publisher.publish(self.cmd_vel_raw)

        elif self.patrol_state in ('emergency', 'avoiding'):
            self.cmd_vel_publisher.publish(self.cmd_vel_manager)


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
