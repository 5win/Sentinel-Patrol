from ultralytics import YOLO
from datetime import datetime
from pathlib import Path

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from patrol_msgs.msg import Detection, Detections

from cv_bridge import CvBridge

CAMERA_FOV_DEG = 60.0
TARGET_CLASSES = {'person'}


class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')

        self.model = YOLO('yolo11n.pt')
        self.bridge = CvBridge()

        # subscriber
        self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # publisher
        self.detections_publisher = self.create_publisher(
            Detections,
            '/detections',
            10
        )

    def image_callback(self, msg: Image) -> None:
        # Image msg -> OpenCV image
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        img_h, img_w = frame.shape[:2]  # shape -> (height, width, channels)

        # YOLO inference
        results = self.model.predict(frame, verbose=False)

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls)
                cls_name = self.model.names[cls_id]
                conf = float(box.conf)

                if cls_name not in TARGET_CLASSES:
                    continue

                if conf < 0.5:
                    self.save_edge_case(frame, box, cls_name, conf, reason='low_conf')
                    continue

                if conf < 0.7:
                    self.save_edge_case(frame, box, cls_name, conf, reason='uncertain')
                    continue

                # bbox 중심 x좌표
                bbox_cx = float((box.xyxy[0][0] + box.xyxy[0][2]) / 2.0)

                # bbox_cx -> 각도 변환
                angle_deg = (bbox_cx - img_w / 2.0) / (img_w / 2.0) * (CAMERA_FOV_DEG / 2.0)

                self.get_logger().info(f'{cls_name} detected | angle: {angle_deg:.2f} | conf: {conf:.2f}')

                detection = self.create_detection(box, cls_id, cls_name, conf, bbox_cx, angle_deg)
                detections.append(detection)

        detections_msg = Detections()
        detections_msg.header = msg.header
        detections_msg.detections = detections
        detections_msg.has_detections = len(detections) > 0

        self.detections_publisher.publish(detections_msg)

    def create_detection(self, box, cls_id: int, cls_name: str, conf: float, bbox_cx: float, angle_deg: float) -> Detection:
        detection = Detection()
        detection.class_id = cls_id
        detection.class_name = cls_name
        detection.confidence = conf
        detection.x_min = float(box.xyxy[0][0])
        detection.y_min = float(box.xyxy[0][1])
        detection.x_max = float(box.xyxy[0][2])
        detection.y_max = float(box.xyxy[0][3])
        detection.center_x = bbox_cx
        detection.center_y = float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
        detection.angle_deg = angle_deg
        return detection

    def save_edge_case(self, frame, box, cls_name: str, conf: float, reason: str) -> None:
        edge_case_dir = Path('edge_cases')
        raw_dir = edge_case_dir / 'raw'
        plot_dir = edge_case_dir / 'plot'
        raw_dir.mkdir(parents=True, exist_ok=True)
        plot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_name = f'{timestamp}_{reason}_{cls_name}_conf{conf:.2f}.jpg'
        raw_path = raw_dir / file_name
        plot_path = plot_dir / file_name

        plotted_frame = frame.copy()
        x_min = int(float(box.xyxy[0][0]))
        y_min = int(float(box.xyxy[0][1]))
        x_max = int(float(box.xyxy[0][2]))
        y_max = int(float(box.xyxy[0][3]))

        cv2.rectangle(plotted_frame, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)

        label = f'{cls_name} {conf:.2f} [{reason}]'
        (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        label_top = max(y_min - label_height - baseline - 6, 0)
        label_bottom = label_top + label_height + baseline + 6
        label_right = min(x_min + label_width + 8, plotted_frame.shape[1] - 1)

        cv2.rectangle(plotted_frame, (x_min, label_top), (label_right, label_bottom), (0, 255, 255), -1)
        cv2.putText(plotted_frame, label, (x_min + 4, label_bottom - baseline - 3), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 1, cv2.LINE_AA)

        raw_saved = cv2.imwrite(str(raw_path), frame)
        plot_saved = cv2.imwrite(str(plot_path), plotted_frame)

        if raw_saved and plot_saved:
            self.get_logger().info(f'Saved edge case [{reason}] for {cls_name}: {raw_path}, {plot_path}')
        else:
            self.get_logger().warning(f'Failed to save edge case images: raw={raw_path}, plot={plot_path}')



def main() -> None:
    rclpy.init()
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
