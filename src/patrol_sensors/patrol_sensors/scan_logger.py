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
        self.turn_direction = 1.0


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

        self.timer = self.create_timer(0.1, self.timer_callback)


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

        # 좌우 공간 비교하여 회피 방향 결정 (10도 ~ 50도 기준)
        def get_sector_avg(center_deg, window_deg):
            c_rad = math.radians(center_deg)
            # Normalize to [msg.angle_min, msg.angle_max]
            while c_rad < msg.angle_min: c_rad += 2 * math.pi
            while c_rad > msg.angle_max: c_rad -= 2 * math.pi
                
            idx = int((c_rad - msg.angle_min) / msg.angle_increment)
            half_w = int(math.radians(window_deg) / msg.angle_increment / 2)
            
            s_idx = idx - half_w
            e_idx = idx + half_w
            
            if s_idx < 0:
                ranges = msg.ranges[s_idx:] + msg.ranges[:e_idx]
            elif e_idx > len(msg.ranges):
                ranges = msg.ranges[s_idx:] + msg.ranges[:e_idx - len(msg.ranges)]
            else:
                ranges = msg.ranges[s_idx:e_idx]
                
            valid = [r for r in ranges if msg.range_min < r < msg.range_max and not math.isinf(r) and not math.isnan(r)]
            return sum(valid) / len(valid) if valid else 0.0

        left_avg = get_sector_avg(30.0, 40.0)    # +10 ~ +50
        right_avg = get_sector_avg(-30.0, 40.0)  # -10 ~ -50
        
        # 거리가 더 먼(빈 공간이 많은) 방향으로 설정
        self.turn_direction = 1.0 if left_avg >= right_avg else -1.0

        

    def odom_callback(self, msg: Odometry):
        # 현재 속도 갱신
        self.current_velocity = msg.twist.twist.linear.x

    def timer_callback(self):
        if self.min_range is None:
            return

        log_msg = (
            f'min_range={self.min_range:.3f} m |'
            f'status={self.status} | '
            f'vel={self.current_velocity:.3f} m/s | '
            f'dir={self.turn_direction}'
        )

        # custom message 생성
        front_scan_msg = FrontScan()
        front_scan_msg.status = self.status
        front_scan_msg.min_range = self.min_range
        front_scan_msg.current_velocity = self.current_velocity
        front_scan_msg.turn_direction = self.turn_direction
        

        if self.status != self.prev_status:
            self.front_scan_publisher.publish(front_scan_msg)
            self.get_logger().warn(f'[STATE CHANGE] {log_msg}', throttle_duration_sec=1.5) 
            self.prev_status = self.status
        else:
            self.front_scan_publisher.publish(front_scan_msg)
            self.get_logger().info(log_msg, throttle_duration_sec=1.5)


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