from arduino.app_utils import *
import time

import cv2

# Default camera
# TODO: when to release capture?
cap = cv2.VideoCapture(0)

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

def call_model(frame):
    # TODO: outsource to model rather than dummy data
    # NOTE: dummy data is based on a left hand
    example_res = {
        'thumb_tip': [31, 90, 0],
        'index_finger_tip': [72, 57, 0],
        'middle_finger_tip': [108, 56, 0],
        'ring_finger_tip': [138, 83, 0],
        'pinky_tip': [155, 142, 0]
        'index_finger_mcp': [64, 90, 20],
    }
    return example_res

def find_keys_pressed(frame):
    # Model returns x, y, z of each tip 0 to 192
    # TODO: use the Edge Impulse ML
    locations = call_model(frame)
    # Figure out whether finger is down based on the highest finger
    pressed_finger_coordinates = []
    for v in locations.values():
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

def press_key(to_press):
    # TODO: press new key in hardware
    Bridge.call('press_key', to_press)

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

def dummy_loop():
    press_key(0)
    time.sleep(1)
    press_key(1)
    time.sleep(1)
    press_key(2)
    time.sleep(1)
    press_key(3)
    time.sleep(1)

# Start the application
App.run(user_loop=dummy_loop)
