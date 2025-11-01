import os
import cv2
import time
from datetime import datetime

TRAINING_DATA_DIR = 'training_data'
IMAGES_DIR = os.path.join(TRAINING_DATA_DIR, 'images')
LABELS_DIR = os.path.join(TRAINING_DATA_DIR, 'labels')

def ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(LABELS_DIR, exist_ok=True)

def save_frame_for_training(image_data, label_data):
    ensure_dirs()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    image_path = os.path.join(IMAGES_DIR, f'{timestamp}.jpg')
    label_path = os.path.join(LABELS_DIR, f'{timestamp}.txt')

    # Decode and save image
    frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    cv2.imwrite(image_path, frame)

    # Save label in YOLO format
    with open(label_path, 'w') as f:
        for label in label_data:
            class_id, x_center, y_center, width, height = label
            f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

    return image_path, label_path

def get_training_data():
    ensure_dirs()
    images = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
    labels = [f for f in os.listdir(LABELS_DIR) if f.endswith('.txt')]
    data = []
    for img in images:
        base = img.replace('.jpg', '')
        label_file = f'{base}.txt'
        if label_file in labels:
            data.append({
                'image': img,
                'label': label_file,
                'timestamp': base
            })
    return sorted(data, key=lambda x: x['timestamp'], reverse=True)

def delete_sample(timestamp):
    image_path = os.path.join(IMAGES_DIR, f'{timestamp}.jpg')
    label_path = os.path.join(LABELS_DIR, f'{timestamp}.txt')
    if os.path.exists(image_path):
        os.remove(image_path)
    if os.path.exists(label_path):
        os.remove(label_path)