import airlib

import cv2
from PIL import Image
import numpy as np

show = False

cap = cv2.VideoCapture(4)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    img = Image.fromarray(frame).resize((224, 224))
    landmarks, hand_presence, handedness, world_landmarks = airlib.landmark(img)
    landmarks = airlib.parse_landmarks(landmarks)
    if show:
        vis = airlib.draw_landmarks(np.array(img, dtype=np.uint8), landmarks)
        cv2.imshow('', vis)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()