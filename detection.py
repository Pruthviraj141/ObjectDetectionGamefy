import cv2
import torch
from ultralytics import YOLO
import numpy as np

# Configuration
MODEL_NAME = 'yolov10m.pt'
CONFIDENCE = 0.40
PROCESSING_WIDTH = 320

# Global variables
model = None
device = None
class_names = {}
colors = {}

def load_model():
    global model, device, class_names, colors
    print(f"🧠 Loading HIGH-ACCURACY YOLOv10 model ({MODEL_NAME})...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    try:
        model = YOLO(MODEL_NAME)
        model.to(device)
        if device == 'cuda':
            model.model.half()  # Enable FP16 for GPU
        print(f"✅ Model '{MODEL_NAME}' loaded successfully on device: {device.upper()}")
        class_names.clear()
        class_names.update(model.names)
        np.random.seed(42)
        colors = {name: tuple(np.random.randint(100, 256, 3).tolist()) for name in class_names.values()}
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        model = None

def draw_detections(frame, boxes):
    """Draws detection boxes and labels on the original frame."""
    for box in boxes:
        x1, y1, x2, y2 = map(int, box[:4])
        conf, cls_id = float(box[4]), int(box[5])
        label = class_names.get(cls_id, 'Unknown')
        color = colors.get(label, (0, 255, 0))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{label} {conf:.2f}"
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        y = y1 - 10 if y1 - 10 > h else y1 + h + 10
        cv2.rectangle(frame, (x1, y - h - 5), (x1 + w, y), color, -1)
        cv2.putText(frame, text, (x1, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    return frame

def process_frame(image_data):
    if not model:
        return None
    original_frame = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    original_height, original_width, _ = original_frame.shape
    scale = PROCESSING_WIDTH / original_width
    resized_frame = cv2.resize(original_frame, (int(original_width * scale), int(original_height * scale)))

    with torch.no_grad():
        results = model(resized_frame, conf=CONFIDENCE, verbose=False, device=device)[0]

    scaled_boxes = [torch.cat((box.xyxy[0] / scale, box.conf, box.cls)) for box in results.boxes] if results.boxes is not None else []
    processed_frame = draw_detections(original_frame, scaled_boxes)
    return processed_frame

def get_detections(image_data):
    if not model:
        return None
    original_frame = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    original_height, original_width, _ = original_frame.shape
    scale = PROCESSING_WIDTH / original_width
    resized_frame = cv2.resize(original_frame, (int(original_width * scale), int(original_height * scale)))

    with torch.no_grad():
        results = model(resized_frame, conf=CONFIDENCE, verbose=False, device=device)[0]

    detections = []
    if results.boxes is not None:
        for box in results.boxes:
            scaled_box = box.xyxy[0] / scale
            detection = [
                float(scaled_box[0]),  # x1
                float(scaled_box[1]),  # y1
                float(scaled_box[2]),  # x2
                float(scaled_box[3]),  # y2
                float(box.conf),       # confidence
                int(box.cls)           # class_id
            ]
            detections.append(detection)

    return detections