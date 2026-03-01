# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

# EXAMPLE_NAME = "Basic usage of the Video Image Classification Brick"
from arduino.app_utils import *
import time
from arduino.app_bricks.video_imageclassification import VideoImageClassification

# Create a classification stream with default confidence threshold (0.3)
classification_stream = VideoImageClassification()


def press_key(to_press):
    Bridge.call('press_key', to_press)

# Example: callback when "sunglasses" are detected
def sunglass_detected():
    press_key(3)
    time.sleep(0.430)
    press_key(3)
    time.sleep(0.430)
    press_key(4)
    time.sleep(0.430)
    press_key(5)
    time.sleep(0.430)
    press_key(5)
    time.sleep(0.430)
    press_key(4)
    time.sleep(0.430)
    press_key(3)
    time.sleep(0.430)
    press_key(2)
    time.sleep(0.430)
    press_key(1)
    time.sleep(0.430)
    press_key(1)
    time.sleep(0.430)
    press_key(2)
    time.sleep(0.430)
    press_key(3)
    time.sleep(0.430)
    press_key(3)
    time.sleep(645)
    press_key(1)
    time.sleep(215)
    press_key(1)
    time.sleep(1)



classification_stream.on_detect("banana", sunglass_detected)


# Example: callback for all classifications
def all_detected(results):
    print("Classifications:", results)


classification_stream.on_detect_all(all_detected)

App.run()
