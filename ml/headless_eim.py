import airlib

import cv2
from PIL import Image
import numpy as np
from edge_impulse_linux.image import ImageImpulseRunner

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("camera_no", default=0, type=int)
parser.add_argument("-s", "--show", action="store_true")

args = parser.parse_args()

show = args.show

print(args)
cap = cv2.VideoCapture(args.camera_no)
mdl = ImageImpulseRunner("/home/dante/coding/irvinehacks26/repo/ml/hand_landmark_detector.eim")
# mdl._allow_shm = False
mdl.init()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    img = Image.fromarray(frame).resize((224, 224))
    feats, crop = mdl.get_features_from_image(np.array(img))
    got_back = mdl.classify(feats)
    landmarks, hand_presence, handedness, world_landmarks = got_back["result"]["freeform"]

    landmarks = airlib.parse_landmarks(np.array(landmarks))

    print(landmarks[0])
    if show:
        vis = airlib.draw_landmarks(np.array(img, dtype=np.uint8), landmarks)
        cv2.imshow('', vis)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
