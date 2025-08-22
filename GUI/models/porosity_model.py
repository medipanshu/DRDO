import cv2
import numpy as np
from ultralytics import YOLO
import os
import tempfile

# Base directory for assets, e.g., for best.pt weights
base_dir = "/home/vulture/Desktop/DRDO/GUI/Assets/"

class DefectDetector:
    def __init__(self):
        self.class_names = ['crack', 'lof', 'lop', 'overlap', 'porosity', 'slag', 'spattering', 'undercut']
        self.class_colors = {
            'crack': (255, 0, 0),       # Red
            'lof': (0, 255, 0),         # Green
            'lop': (0, 0, 255),         # Blue
            'overlap': (255, 255, 0),   # Cyan
            'porosity': (255, 0, 255),  # Magenta
            'slag': (0, 255, 255),      # Yellow
            'spattering': (128, 0, 128),# Purple
            'undercut': (0, 128, 128)   # Teal
        }

    def load_image(self, image_path):
        image = cv2.imread(image_path)
        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def detect_defect_boundary(self, image):
        if len(image.shape) == 2:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            image_rgb = image.copy()

        weight_path = os.path.join(base_dir, "porosity_model.pt")
        model = YOLO(weight_path)
        results = model.predict(image_rgb, conf=0.25)

        image_detected = image_rgb.copy()
        # boxes_detected = [4 if int(i)==1 for i in result.boxes.cls.tolist()]

        for result in results:
            boxes = result.boxes.xyxy  # Bounding boxes
            scores = result.boxes.conf   # Confidence scores
            class_ids = result.boxes.cls # Class indices
            boxes_detected_cls = [4 if int(i)==0 else int(i) for i in class_ids.tolist()]

            for box, score, cls in zip(boxes, scores, boxes_detected_cls):
                x1, y1, x2, y2 = map(int, box.tolist())
                class_name = self.class_names[int(cls)]
                color = self.class_colors[class_name]
                cv2.rectangle(image_detected, (x1, y1), (x2, y2), color, 1)
                label = f"Class: {class_name}, Score: {score:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                label_y = y1 - 10 if y1 - 10 > 10 else y1 + 10 + label_size[1]
                cv2.putText(image_detected, label, (x1, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        print(results)
        return image_rgb, image_detected, result.boxes.xyxy.tolist(), result.boxes.conf.tolist(), boxes_detected_cls

    def run(self, image_path):
        image = self.load_image(image_path)
        if image is not None:
            original, detected, bbox ,confidence, classs = self.detect_defect_boundary(image)
            # Save images to temporary files
            orig_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            det_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            # Convert RGB back to BGR for cv2.imwrite
            cv2.imwrite(orig_file.name, cv2.cvtColor(original, cv2.COLOR_RGB2BGR))
            cv2.imwrite(det_file.name, cv2.cvtColor(detected, cv2.COLOR_RGB2BGR))
            # Print the file paths so the main process can capture them
            print(orig_file.name, det_file.name, bbox, confidence, classs)
            return orig_file.name, det_file.name, bbox, confidence, classs 
        else:
            print("Failed to load image.")
            return None, None, None, None, None

if __name__ == "__main__":
    import sys
    # image_path = sys.argv[1]
    detector = DefectDetector()
    image_path = '/home/vulture/Desktop/DRDO/Images/air-hole1-27_jpg.rf.f0322b78909d41514503ab5520f46f06.jpg'
    orig_path, det_path, bboxes, confidences, class_labels = detector.run(image_path)
    print(orig_path, det_path)
    print(bboxes)
    print(confidences)
    print(class_labels)
