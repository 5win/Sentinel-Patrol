from ultralytics import YOLO
from datetime import datetime
from pathlib import Path

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from patrol_msgs.msg import DetectedPerson, DetectedPersons

from cv_bridge import CvBridge

PERSON_CLASS_ID = 0
CAMERA_FOV_DEG = 60.0

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

    def image_callback(self, msg: Image) -> None:
        # Image msg -> OpenCV image
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        img_h, img_w = frame.shape[:2]  # shape -> (height, width, channels)

        # YOLO inference
        results = self.model.predict(frame, verbose=False)

        detected_person_list = []
        
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls)   # class
                conf = float(box.conf)  # confidence

                # person 클래스가 아닌 경우 무시
                if cls_id != PERSON_CLASS_ID:
                    continue
                
                # edge case 발견 시 저장
                if conf < 0.7:
                    self.save_edge_case(frame, result.plot(), cls_id, conf)
                    continue

                # confidence가 너무 낮으면 무시
                if conf < 0.5:
                    continue


                # bbox 중심 x좌표
                bbox_cx = float((box.xyxy[0][0] + box.xyxy[0][2]) / 2.0)

                # bbox_cx -> 각도 변환
                angle_deg = (bbox_cx - img_w / 2.0) / (img_w / 2.0) * (CAMERA_FOV_DEG / 2.0)

                self.get_logger().info(f'Person detected | angle: {angle_deg:.2f} | conf: {conf:.2f}°')

                detected_person = self.create_detected_person(box, cls_id, conf, bbox_cx, angle_deg)
                detected_person_list.append(detected_person)

        detected_persons = DetectedPersons()
        detected_persons.header = msg.header
        detected_persons.persons = detected_person_list
        detected_persons.person_detected = len(detected_person_list) > 0

        # Todo: publish detected_persons topic

    def create_detected_person(self, box, cls_id: int, conf: float, bbox_cx: float, angle_deg: float) -> DetectedPerson:
        detected_person = DetectedPerson()
        detected_person.class_id = cls_id
        detected_person.class_name = self.model.names[cls_id]
        detected_person.confidence = conf
        detected_person.x_min = float(box.xyxy[0][0])
        detected_person.y_min = float(box.xyxy[0][1])
        detected_person.x_max = float(box.xyxy[0][2])
        detected_person.y_max = float(box.xyxy[0][3])
        detected_person.center_x = bbox_cx
        detected_person.center_y = float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
        detected_person.angle_deg = angle_deg
        return detected_person

    def save_edge_case(self, frame, plotted_frame, cls_id, conf) -> None:
        edge_case_dir = Path('edge_cases')
        raw_dir = edge_case_dir / 'raw'
        plot_dir = edge_case_dir / 'plot'
        raw_dir.mkdir(parents=True, exist_ok=True)
        plot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_name = f'{timestamp}_cls{cls_id}_conf{conf:.2f}.jpg'
        raw_path = raw_dir / file_name
        plot_path = plot_dir / file_name

        raw_saved = cv2.imwrite(str(raw_path), frame)
        plot_saved = cv2.imwrite(str(plot_path), plotted_frame)

        if raw_saved and plot_saved:
            self.get_logger().info(f'Saved edge case images: {raw_path}, {plot_path}')
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
