from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.task import Future
from rclpy.time import Time
from rclpy.duration import Duration

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Twist, PoseStamped
from patrol_msgs.msg import FrontScan

from enum import Enum, auto


class PatrolState(Enum):
    IDLE        = auto()
    PATROLLING  = auto()
    WAIT        = auto()
    EMERGENCY   = auto()
    AVOIDING    = auto()
    RETURNING   = auto()

# waypoints (x, y, yaw)
WAYPOINTS = [
    (1.0, 0.0, 0.0),
    (1.0, 2.0, 0.0),
    (0.0, 2.0, 0.0),
]

def make_pose(x, y, yaw) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'

    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0

    # yaw → quaternion (z축 회전만)
    import math
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)

    return pose


class PatrolManager(Node):

    def __init__(self):
        super().__init__('patrol_manager')

        self.state: PatrolState = PatrolState.IDLE
        self.current_wp_index: int = 0   # 현재 웨이포인트 인덱스
        self._goal_handle: Optional[ClientGoalHandle] = None
        self.send_goal_future: Optional[Future] = None
        self.emergency_start_time: Time = None

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

        # action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # set timer
        self.timer = self.create_timer(1.0, self.timer_callback)

        self.get_logger().info(f'Patrol manager started in {self.state} state')

        self.start_patrol()

    # 상태 전이
    def transition_to(self, new_state: PatrolState):
        self.get_logger().info(f'Transitioning from {self.state} to {new_state}')
        self.state = new_state

    # front_scan callback
    def front_scan_callback(self, msg: FrontScan):
        if msg.status == 'danger' and self.state not in (
            PatrolState.EMERGENCY, PatrolState.AVOIDING, PatrolState.RETURNING
        ):
            self.get_logger().warn(f'Obstacle detected min_range={msg.min_range:.2f} -> EMERGENCY')
            self.cancel_goal()
            self.transition_to(PatrolState.EMERGENCY)
            self.emergency_start_time = self.get_clock().now()

        elif msg.status == 'safe' and self.state == PatrolState.EMERGENCY:
            self.get_logger().info('Obstacle cleared -> PATROLLING')
            self.transition_to(PatrolState.PATROLLING)
            self.send_next_waypoint()   # 장애물이 없어졌으니, 계속 진행
            
            
    
    def start_patrol(self):
        self.current_wp_index = 0
        self.transition_to(PatrolState.PATROLLING)
        self.send_next_waypoint()


    # send next waypoint
    def send_next_waypoint(self):

        # 다음 waypoint goal 메시지 생성
        x, y, yaw = WAYPOINTS[self.current_wp_index]
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose = make_pose(x, y, yaw)
        
        # action server가 준비될 때까지 대기
        self.nav_client.wait_for_server() 

        # send asyn goal (feedback X)
        self.send_goal_future = self.nav_client.send_goal_async(goal_msg)
        self.send_goal_future.add_done_callback(self.goal_response_callback)
        

    # goal response callback
    # goal이 수락/거절되었을 때 호출되는 콜백 함수
    def goal_response_callback(self, future):
        goal_handle = future.result()        
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        
        self.get_logger().info("Goal accepted -> Moving")

        self._goal_handle = goal_handle # cancel 시 필요

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)
            

    # goal result callback
    # goal이 완료되었을 때 호출되는 콜백 함수
    def goal_result_callback(self, future):
        result = future.result()

        # emergency, avoiding이면 무시
        if self.state not in (PatrolState.PATROLLING, PatrolState.WAIT):
            self.get_logger().info(f'Goal cancelled or preempted[state: {self.state}]')
            return

        from action_msgs.msg import GoalStatus
        
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Arrived at waypoint [{self.current_wp_index}]')
            self.current_wp_index = (self.current_wp_index + 1) % len(WAYPOINTS)    # waypoint 순환
            self.send_next_waypoint()
        else: 
            self.get_logger().info(f'Failed to arrive at waypoint [{self.current_wp_index}]')
            self.send_next_waypoint()   # 실패 재시도


    # cancel goal
    def cancel_goal(self):
        if hasattr(self, '_goal_handle') and self._goal_handle is not None:
            self._goal_handle.cancel_goal_async()
            self._goal_handle = None    # 중복 취소 호출을 방지
            self.get_logger().info('Goal cancelled')

    def execute_avoiding_behavior(self):
        pass    # Todo


    def timer_callback(self):
        self.get_logger().info(f'Current state: {self.state} | WP: {self.current_wp_index}/{len(WAYPOINTS)}')

        if self.state == PatrolState.EMERGENCY:
            elapsed_time: Duration = self.get_clock().now() - self.emergency_start_time
            if (elapsed_time.nanoseconds / 1e9) > 5.0:
                self.get_logger().info('5 seconds passed -> AVOIDING')
                self.transition_to(PatrolState.AVOIDING)
            pass
        elif self.state == PatrolState.AVOIDING:
            self.execute_avoiding_behavior()
        


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
