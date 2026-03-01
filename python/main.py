from arduino.app_utils import *
import time

import cv2
from PIL import Image
import numpy as np
from edge_impulse_linux.image import ImageImpulseRunner

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("camera_no", default=0, type=int)
parser.add_argument("-s", "--show", action="store_true")

cap = cv2.VideoCapture(args.camera_no)
mdl = ImageImpulseRunner("/home/arduino/hand_landmark_detector.eim")
# mdl._allow_shm = False
mdl.init()

if not cap.isOpened():
    print("ERROR: failed to open camera 0")

led_is_on = False

keyboard_state = {
    'keys_down': [],
    'active_key': -1
}

# For demo/visibility purposes
def led_blink():
    global led_is_on
    led_is_on = not led_is_on
    Bridge.call('set_led_state', led_is_on)


LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
]


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


def call_model(frame):
    global mdl

    img = Image.fromarray(frame).resize((224, 224))
    feats, crop = mdl.get_features_from_image(np.array(img))
    got_back = mdl.classify(feats)
    landmarks, hand_presence, handedness, world_landmarks = got_back["result"]["freeform"]

    landmarks = parse_landmarks(np.array(landmarks))
    # see airlib.LANDMARK_NAMES
    return landmarks

def find_keys_pressed(frame):
    # Model returns x, y, z of each tip 0 to 192
    locations = call_model(frame)
    locations_zipped = {l: loc for l, loc in zip(locations, LANDMARK_NAMES)}
    # Figure out whether finger is down based on the highest finger
    pressed_finger_coordinates = []
    for k, v in locations_zipped:
        if k.endswith("_TIP"):
            z_pos = v[2]
            if z_pos > 10:
                pressed_finger_coordinates.append(v)

    # Imagine there are several white keys on screen; we partition them
    # OR, determine the key width based on the average distance from the finger tips?
    key_width = 192 / 8

    # Depending on the pressed finger coordinates, press the corresponding keys
    pressed = [False] * 8

    for coord in pressed_finger_coordinates:
        key_number = max(0, min(7, coord[0] // key_width))
        pressed[key_number] = True

    return pressed

def activated_key(prev_frame, this_frame):
    for i in range(0, 8):
        if i < len(this_frame) and i < len(prev_frame) and this_frame[i] and not prev_frame[i]:
            return i
    return -1

def loop():
    global keyboard_state
    global cap

    time.sleep(0.50)
    led_blink()

    # Read from camera
    if not cap:
        # Cannot proceed
        return
    ret, frame = cap.read()
    if not ret:
        return

    this_frame = find_keys_pressed(frame)
    new_active_key = activated_key(keyboard_state['keys_down'], this_frame)
    if new_active_key != keyboard_state['active_key']:
        press_key(new_active_key)

    keyboard_state['keys_down'] = this_frame
    keyboard_state['active_key'] = new_active_key

def press_key(to_press):
    Bridge.call('press_key', to_press)

def dummy_loop():
    press_key(2)
    time.sleep(0.430)
    press_key(2)
    time.sleep(0.430)
    press_key(3)
    time.sleep(0.430)
    press_key(4)
    time.sleep(0.430)
    press_key(4)
    time.sleep(0.430)
    press_key(3)
    time.sleep(0.430)
    press_key(2)
    time.sleep(0.430)
    press_key(1)
    time.sleep(0.430)
    press_key(0)
    time.sleep(0.430)
    press_key(0)
    time.sleep(0.430)
    press_key(1)
    time.sleep(0.430)
    press_key(2)
    time.sleep(0.430)
    press_key(2)
    time.sleep(0.645)
    press_key(0)
    time.sleep(0.215)
    press_key(0)
    time.sleep(1)

try:
    # Start the application
    App.run(user_loop=dummy_loop)
finally:
    cap.release()
    cv2.destroyAllWindows()

