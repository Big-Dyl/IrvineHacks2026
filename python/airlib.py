from ai_edge_litert.interpreter import Interpreter
import numpy as np
from PIL import Image

import anchorlib

interpreter_detect = Interpreter(model_path="../palm_detection_full.tflite")
interpreter_detect.allocate_tensors()

input_details_detect = interpreter_detect.get_input_details()
output_details_detect = interpreter_detect.get_output_details()

interpreter_landmark = Interpreter(model_path="../hand_landmark_full.tflite")
interpreter_landmark.allocate_tensors()

input_details_landmark = interpreter_landmark.get_input_details()
output_details_landmark = interpreter_landmark.get_output_details()


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))

def decode_best_palm_detection(raw_boxes, raw_scores):
    """
    raw_boxes:  (1, 2016, 18) - raw regression output from palm detector
    raw_scores: (1, 2016, 1)  - raw logit scores from palm detector

    Returns the decoded box and keypoints (in pixels) for the highest-confidence anchor.
    """
    input_size = 192.0

    # --- Strip batch dimension ---
    boxes  = raw_boxes[0]   # (2016, 18)
    scores = raw_scores[0]  # (2016, 1)

    # --- Find highest confidence anchor ---
    confidences = sigmoid(scores[:, 0])   # (2016,) - convert logits to probabilities
    best_idx = np.argmax(confidences)
    best_conf = confidences[best_idx]

    print(f"Best anchor index: {best_idx}")
    print(f"Confidence: {best_conf:.4f}")

    # --- Retrieve the corresponding anchor and raw prediction ---
    anchors = anchorlib.generate_anchors(anchorlib.PALM_DETECTION_OPTIONS)
    anchor  = anchors[best_idx]           # [x_center, y_center, w, h] normalized
    raw     = boxes[best_idx]             # (18,)

    # Anchor center in pixels
    ax = anchor.x_center * input_size
    ay = anchor.y_center * input_size

    # --- Decode box (dy, dx, h, w) ---
    dy, dx, h, w = raw[0], raw[1], raw[2], raw[3]
    box = {
        'x_center': ax + dx,
        'y_center': ay + dy,
        'width':    w,
        'height':   h,
        # Convenience: corners
        'x_min':    ax + dx - w / 2,
        'y_min':    ay + dy - h / 2,
        'x_max':    ax + dx + w / 2,
        'y_max':    ay + dy + h / 2,
    }

    # --- Decode 7 keypoints ---
    # Each is a (dx, dy) offset from the same anchor center
    keypoint_names = [
        'wrist',
        'pinky_mcp',
        'index_mcp',
        'middle_tip',
        'index_tip',
        'thumb_tip',
        'thumb_mcp',
    ]
    keypoints = {}
    for i, name in enumerate(keypoint_names):
        kp_dx = raw[4 + 2*i]
        kp_dy = raw[4 + 2*i + 1]
        keypoints[name] = (ax + kp_dx, ay + kp_dy)

    return best_conf, box, keypoints


def detect(image):
    image = image.copy().resize((192, 192)).convert("RGB")
    image_np = np.array(image, dtype=np.uint8)
    input_data = image_np.astype(np.float32) / 255.0
                      
    input_data = np.expand_dims(input_data, axis=0)
    interpreter_detect.set_tensor(input_details_detect[0]['index'], input_data)
    interpreter_detect.invoke()

    output_0 = interpreter_detect.get_tensor(output_details_detect[0]['index'])
    output_1 = interpreter_detect.get_tensor(output_details_detect[1]['index'])

    best_conf, box, keypoints = decode_best_palm_detection(output_0, output_1)
    return best_conf, box, keypoints

def parse_landmarks(output_63: np.ndarray):
    """
    Convert flat [63] array of interleaved x,y,z values into
    a list of 21 (px, py, z) tuples.
    x and y are normalized [0,1] -> scaled to image pixels.
    z is depth relative to wrist (not scaled).
    """
    coords = output_63.reshape(21, 3)  # shape (21, 3)
    landmarks = []
    for x, y, z in coords:
        landmarks.append((x, y, float(z)))
    return landmarks

def landmark(image):
    image = image.copy().resize((224, 224)).convert("RGB")
    image_np = np.array(image, dtype=np.uint8)
    input_data = image_np.astype(np.float32) / 255.0
                      
    input_data = np.expand_dims(input_data, axis=0)
    interpreter_landmark.set_tensor(input_details_landmark[0]['index'], input_data)
    interpreter_landmark.invoke()

    landmarks = interpreter_landmark.get_tensor(output_details_landmark[0]['index'])[0]
    hand_presence = interpreter_landmark.get_tensor(output_details_landmark[1]['index'])[0][0]
    handedness = interpreter_landmark.get_tensor(output_details_landmark[2]['index'])[0][0]
    world_landmarks = interpreter_landmark.get_tensor(output_details_landmark[3]['index'])[0]

    return landmarks, hand_presence, handedness, world_landmarks

import numpy as np
import cv2

# ── Landmark connections (finger skeletons) ──────────────────────────────────
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle
    (0, 9), (9, 10), (10, 11), (11, 12),
    # Ring
    (0, 13), (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm
    (5, 9), (9, 13), (13, 17),
]

LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
]


def draw_landmarks(image: np.ndarray, landmarks: list, draw_labels: bool = True):
    """
    Draw hand skeleton and landmark points over image (in-place).
    """
    img = image.copy()
    h, w = img.shape[:2]

    # Draw connections
    for (a, b) in HAND_CONNECTIONS:
        x1, y1, _ = landmarks[a]
        x1 = int(x1)
        y1 = int(y1)
        x2, y2, _ = landmarks[b]
        x2 = int(x2)
        y2 = int(y2)
        cv2.line(img, (x1, y1), (x2, y2), color=(0, 200, 0), thickness=2)

    # Draw landmark dots and labels
    for i, (px, py, z) in enumerate(landmarks):
        px = int(px)
        py = int(py)
        # Fingertips (indices 4,8,12,16,20) get a larger dot
        is_tip = i in (4, 8, 12, 16, 20)
        radius = 6 if is_tip else 4
        color = (0, 0, 255) if is_tip else (255, 0, 0)
        cv2.circle(img, (px, py), radius, color, -1)
        cv2.circle(img, (px, py), radius, (255, 255, 255), 1)  # white outline

        if draw_labels:
            label = f"{i}"  # just the index; swap for LANDMARK_NAMES[i] if you want full names
            cv2.putText(img, label, (px + 6, py - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    return img