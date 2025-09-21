from ultralytics import YOLO
import os
import cv2  # pip install opencv-python

# Define a pixel-to-mm ratio (example: 1 pixel = 0.2 mm)
PIXEL_TO_MM_RATIO = 0.2

def detect_stones_report(image_path, model_path, output_dir, patient_id, conf_threshold=0.25, stone_class_id=0):
    model = YOLO(model_path)
    results = model.predict(source=image_path, imgsz=640, conf=conf_threshold)
    result = results[0]
    boxes = result.boxes

    stones = []
    stone_count = 0
    locations = []

    # Loop through the detected boxes and extract relevant data
    for i in range(len(boxes)):
        cls = int(boxes.cls[i])
        conf = float(boxes.conf[i])

        # If stone is detected and confidence is above threshold
        if cls == stone_class_id and conf >= conf_threshold:
            xyxy = boxes.xyxy[i].tolist()
            x_min, y_min, x_max, y_max = xyxy
            width_px = x_max - x_min
            height_px = y_max - y_min

            # Convert from pixels to millimeters using the ratio
            width_mm = width_px * PIXEL_TO_MM_RATIO
            height_mm = height_px * PIXEL_TO_MM_RATIO

            # Determine the location (Left or Right)
            if x_min < 640:  # Assuming the left part of the image is less than half the width (640px)
                location = "Left Kidney"
            else:
                location = "Right Kidney"

            stone_count += 1

            # Append stone details to the list
            stones.append({
                "location": location,
                "stone_size": {
                    "width": width_mm,
                    "height": height_mm
                }
            })

    # If no stones detected, create a report
    if not stones:
        report = {"message": "No kidney stones detected."}
    else:
        # Create the final report with the required structure
        report = {
            "no_of_stones": stone_count,
            "stones": stones
        }

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save the detected image using patient_id as filename
    detected_image_path = os.path.join(output_dir, f"{patient_id}_detected.jpg")

    # Get annotated image as a numpy array (BGR format)
    annotated_img = result.plot()

    # Save annotated image with OpenCV
    cv2.imwrite(detected_image_path, annotated_img)

    return report, detected_image_path
