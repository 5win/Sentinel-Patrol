import math
import os
from typing import Optional

import yaml

from ament_index_python import get_package_share_directory
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.task import Future
from rclpy.time import Time
from rclpy.duration import Duration
from rclpy.qos import QoSProfile, DurabilityPolicy

from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose, Spin
from geometry_msgs.msg import Twist, PoseStamped, PoseArray
from patrol_msgs.msg import FrontScan
from std_msgs.msg import String, Int32

from enum import Enum, auto

from patrol_manager.constants import (
    TIMER_PERIOD_SEC,
    EMERGENCY_TIMEOUT_SEC,
    SAFE_CONFIRM_SEC,
    ACTION_SERVER_TIMEOUT_SEC,
    SPIN_TIME_ALLOWANCE_SEC,
)



class PatrolState(Enum):
    IDLE        = auto()
    PATROLLING  = auto()
    WAIT        = auto()
    EMERGENCY   = auto()
    AVOIDING    = auto()
    RETURNING   = auto()


def make_pose(x, y, yaw) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'

    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0

    # yaw → quaternion (z축 회전만)
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)

    return pose


class PatrolManager(Node):

    def __init__(self):
        super().__init__('patrol_manager')

        self.state: PatrolState = PatrolState.IDLE
        self.current_wp_index: int = 0   # 현재 웨이포인트 인덱스

        # navigate_to_pose action 관련
        self._goal_handle: Optional[ClientGoalHandle] = None
        self.send_goal_future: Optional[Future] = None
        self.emergency_start_time: Time = None

        # spin action 관련
        self.turn_direction: float = 1.0
        self._spin_goal_handle: Optional[ClientGoalHandle] = None
        self._spin_goal_sent: bool = False
        self._spin_completed: bool = False
        self.safe_start_time: Time = None


        # subscriber
        self.create_subscription(
            FrontScan,
            '/front_scan',
            self.front_scan_callback,
            10
        )

        # publisher
        self.cmd_vel_manager_publisher = self.create_publisher(
            Twist,
            '/cmd_vel_manager',
            10
        )

        self.patrol_state_publisher = self.create_publisher(
            String,
            '/patrol/state',
            10
        )

        # 웨이포인트 목록은 한 번 publish 후 새 구독자가 붙을 때 자동 재전송되도록
        # TRANSIENT_LOCAL QoS 사용 (latched)
        latching_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.waypoints_publisher = self.create_publisher(
            PoseArray,
            '/patrol/waypoints',
            latching_qos,
        )
        self.current_wp_publisher = self.create_publisher(
            Int32,
            '/patrol/current_waypoint',
            10,
        )

        # action client
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.spin_client = ActionClient(self, Spin, 'spin')

        # set timer
        self.timer = self.create_timer(TIMER_PERIOD_SEC, self.timer_callback)

        # waypoint YAML 경로
        self.declare_parameter('waypoints_file', '')
        waypoints_file = (
            self.get_parameter('waypoints_file')
            .get_parameter_value()
            .string_value
        )
        if not waypoints_file:
            waypoints_file = os.path.join(
                get_package_share_directory('patrol_manager'),
                'config',
                'waypoints.yaml',
            )
        self.waypoints_file: str = os.path.expanduser(waypoints_file)
        self.waypoints: list[tuple[float, float, float]] = self._load_waypoints(self.waypoints_file)
            

        # start
        self.get_logger().info(f'Patrol manager started in {self.state} state')

        # 웨이포인트 목록 1회 publish (latched QoS이므로 이후 구독자는 자동 수신)
        self.publish_waypoints()

        self.start_patrol()
    
    def _load_waypoints(self, path: str) -> list[tuple[float, float, float]]:
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        result: list[tuple[float, float, float]] = []
        for wp in data.get('waypoints', []):
            result.append((float(wp['x']), float(wp['y']), float(wp['yaw'])))
        self.get_logger().info(f'Loaded {len(result)} waypoints from {path}')
        return result

    def publish_waypoints(self):
        msg = PoseArray()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.poses = [make_pose(x, y, yaw).pose for x, y, yaw in self.waypoints]

        self.waypoints_publisher.publish(msg)
        self.get_logger().info(f'Published {len(self.waypoints)} waypoints')

    def publish_current_wp(self):
        self.current_wp_publisher.publish(Int32(data=self.current_wp_index))

    # 경과 시간 계산
    def _seconds_since(self, start_time: Time) -> float:
        return (self.get_clock().now() - start_time).nanoseconds / 1e9

    # 상태 전이
    def transition_to(self, new_state: PatrolState):
        self.get_logger().info(f'Transitioning from {self.state} to {new_state}')
        self.state = new_state

    # front_scan callback
    def front_scan_callback(self, msg: FrontScan):
        self.turn_direction = msg.turn_direction

        if msg.status == 'danger' and self.state not in (
            PatrolState.EMERGENCY, PatrolState.AVOIDING, PatrolState.RETURNING
        ):
            self.get_logger().warn(f'Obstacle detected min_range={msg.min_range:.2f} -> EMERGENCY')
            self.cancel_goal()
            self.transition_to(PatrolState.EMERGENCY)
            self.emergency_start_time = self.get_clock().now()
        
        elif msg.status in ('safe', 'caution') and self.state == PatrolState.AVOIDING:
            # Spin 완료 후 safe 타이머 시작
            if self._spin_completed and self.safe_start_time is None:
                self.safe_start_time = self.get_clock().now()

        elif msg.status == 'danger' and self.state == PatrolState.AVOIDING:
            # AVOIDING 중 다시 danger가 오면 safe 타이머 리셋
            self.safe_start_time = None
            
    
    def start_patrol(self):
        self.current_wp_index = 0
        self.publish_current_wp()
        self.transition_to(PatrolState.PATROLLING)
        self.send_next_waypoint()


    # send next waypoint
    def send_next_waypoint(self):

        # 다음 waypoint goal 메시지 생성
        x, y, yaw = self.waypoints[self.current_wp_index]
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = make_pose(x, y, yaw)
        
        # action server가 준비될 때까지 대기
        self.nav_to_pose_client.wait_for_server(timeout_sec=ACTION_SERVER_TIMEOUT_SEC) 

        # send asyn goal (feedback X)
        self.send_goal_future = self.nav_to_pose_client.send_goal_async(goal_msg)
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
        
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Arrived at waypoint [{self.current_wp_index}]')
            self.current_wp_index = (self.current_wp_index + 1) % len(self.waypoints)    # waypoint 순환
            self.publish_current_wp()
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

    def execute_emergency_behavior(self):
        # emergency이면 일단 정지
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.cmd_vel_manager_publisher.publish(msg)

        # 5초 동안 장애물이 사라지지 않으면 회피로 상태 전이
        if self._seconds_since(self.emergency_start_time) > EMERGENCY_TIMEOUT_SEC:
            self.get_logger().info(f'{EMERGENCY_TIMEOUT_SEC} seconds passed -> AVOIDING', throttle_duration_sec=1.5)
            self.transition_to(PatrolState.AVOIDING)

    def execute_avoiding_behavior(self):
        # Spin action으로 90도 회전하여 장애물 회피
        goal = Spin.Goal()
        goal.target_yaw = math.pi / 2.0 * self.turn_direction  # ±90도
        goal.time_allowance.sec = SPIN_TIME_ALLOWANCE_SEC

        self.spin_client.wait_for_server(timeout_sec=ACTION_SERVER_TIMEOUT_SEC)

        send_goal_future = self.spin_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.spin_goal_response_callback)
        self._spin_goal_sent = True
        self.get_logger().info(f'Spin goal sent: {math.degrees(goal.target_yaw):.1f} degrees')

    # spin goal response callback
    def spin_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Spin goal rejected')
            self._spin_goal_sent = False
            return

        self.get_logger().info('Spin goal accepted')
        self._spin_goal_handle = goal_handle

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.spin_goal_result_callback)

    # spin goal result callback
    def spin_goal_result_callback(self, future):
        self._spin_goal_handle = None
        self._spin_goal_sent = False

        if self.state != PatrolState.AVOIDING:
            self.get_logger().info(f'Spin finished but state is {self.state}, ignoring')
            return


        result = future.result()

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Spin completed -> waiting for safe (3s)')
            self._spin_completed = True
            self.safe_start_time = None  # front_scan에서 safe 올 때 시작
        else:
            self.get_logger().warn('Spin failed -> retrying')
            self._spin_goal_sent = False  # 재시도 허용

    # cancel spin
    def cancel_spin(self):
        if self._spin_goal_handle is not None:
            self._spin_goal_handle.cancel_goal_async()
            self._spin_goal_handle = None
            self.get_logger().info('Spin goal cancelled')
        self._spin_goal_sent = False


    def timer_callback(self):
        self.get_logger().info(f'Current state: {self.state} | WP: {self.current_wp_index}/{len(self.waypoints)}', throttle_duration_sec=1.5)

        # 상태 publish
        self.patrol_state_publisher.publish(String(data=self.state.name))

        # state별 behavior
        if self.state == PatrolState.EMERGENCY:
            self.execute_emergency_behavior()

        elif self.state == PatrolState.AVOIDING:
            if not self._spin_goal_sent and not self._spin_completed:
                self.execute_avoiding_behavior()
            elif self._spin_completed and self.safe_start_time is not None:
                if self._seconds_since(self.safe_start_time) > SAFE_CONFIRM_SEC:
                    self.get_logger().info(f'Safe for {SAFE_CONFIRM_SEC} seconds -> PATROLLING')
                    self._spin_completed = False
                    self.safe_start_time = None
                    self.transition_to(PatrolState.PATROLLING)
                    self.send_next_waypoint()

        


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
