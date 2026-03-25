import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from patrol_msgs.msg import FrontScan

from enum import Enum, auto


class PatrolState(Enum):
    IDLE        = auto()
    PATROLLING  = auto()
    WAIT        = auto()
    EMERGENCY   = auto()
    AVOIDING    = auto()
    RETURNING   = auto()


class PatrolManager(Node):

    def __init__(self):
        super().__init__('patrol_manager')

        self.state = PatrolState.IDLE

        # subscriber
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

        # set timer
        self.timer = self.create_timer(1.0, self.timer_callback)

        self.get_logger().info(f'Patrol manager started in {self.state} state')

    def transition_to(self, new_state: PatrolState):
        self.get_logger().info(f'Transitioning from {self.state} to {new_state}')
        self.state = new_state

    def front_scan_callback(self, msg: FrontScan):
        if msg.status == 'danger' and self.state not in (
            PatrolState.EMERGENCY, PatrolState.AVOIDING, PatrolState.RETURNING
        ):
            self.transition_to(PatrolState.EMERGENCY)

    def timer_callback(self):
        self.get_logger().info(f'Current state: {self.state}')


def main():
    rclpy.init()
    node = PatrolManager()
    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
