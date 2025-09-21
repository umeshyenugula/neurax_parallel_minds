from ultralytics import YOLO
import cv2
import os
import json
from datetime import datetime

def detect_kidney_stones(image_path, model_path, save_path, image_dpi=96, conf_threshold=0.25, stone_class_id=0):

    model = YOLO(model_path)

    # Run detection
    results = model.predict(source=image_path, imgsz=640, conf=conf_threshold)
    result = results[0]
    boxes = result.boxes

    # Read original image using OpenCV
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # List for storing detection info
    stones = []

    for i in range(len(boxes)):
        cls = int(boxes.cls[i])
        conf = float(boxes.conf[i])
        if cls == stone_class_id and conf >= conf_threshold:
            x_min, y_min, x_max, y_max = boxes.xyxy[i].tolist()

            # Draw rectangle only
            cv2.rectangle(
                image,
                (int(x_min), int(y_min)),
                (int(x_max), int(y_max)),
                color=(0, 255, 0),
                thickness=2
            )

            # Calculate stone size in pixels
            width_px = x_max - x_min
            height_px = y_max - y_min

            # Convert to millimeters (assuming image DPI; 1 inch = 25.4 mm)
            mm_per_pixel = 25.4 / image_dpi
            width_mm = round(width_px * mm_per_pixel, 2)
            height_mm = round(height_px * mm_per_pixel, 2)

            # Determine location (left or right side)
            center_x = (x_min + x_max) / 2
            side = "Left Kidney" if center_x < width / 2 else "Right Kidney"

            stones.append({
                "confidence": round(conf, 3),
                "location": side,
                "box": {
                    "x_min": int(x_min),
                    "y_min": int(y_min),
                    "x_max": int(x_max),
                    "y_max": int(y_max)
                },
                "size_mm": {
                    "width": width_mm,
                    "height": height_mm
                }
            })

    # Save image with rectangles only
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, image)

    # Build result JSON
    result_json = {
        "timestamp": datetime.now().isoformat(),
        "detected": len(stones) > 0,
        "num_stones": len(stones),
        "stones": stones,
        "image_saved_to": save_path
    }
    print(json.dumps(result_json, indent=4))
    return result_json
if __name__ == "__main__":
    IMAGE_PATH = r"C:\Users\potha\OneDrive\Desktop\retest.png"
    MODEL_PATH = r"C:\kaggle\working\kidney_stone_ssl\simclr_yolo11n\weights\best.pt"
    OUTPUT_IMAGE_PATH = r"C:\Users\potha\OneDrive\Desktop\test_boxes_only.png"

    detect_kidney_stones(
        image_path=IMAGE_PATH,
        model_path=MODEL_PATH,
        save_path=OUTPUT_IMAGE_PATH,
        image_dpi=200 
    )
