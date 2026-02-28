from arduino.app_utils import *
import time

led_is_on = False

keyboard_state = {
    'keys_down': [],
    'active_key': -1
}

#def get_led_status():
#    """Get current LED status for API."""
#    return {
#        "led_is_on": led_is_on,
#        "status_text": "LED IS ON" if led_is_on else "LED IS OFF"
#    }

#def toggle_led_state(client, data):
#    """Toggle the LED state when receiving socket message."""
#    global led_is_on
#    led_is_on = not led_is_on

    # Call a function in the sketch, using the Bridge helper library, to control the state of the LED connected to the microcontroller.
    # This performs a RPC call and allows the Python code and the Sketch code to communicate.
#    Bridge.call("set_led_state", led_is_on)

    # Send updated status to all connected clients
    #ui.send_message('led_status_update', get_led_status())

#def on_get_initial_state(client, data):
#    """Handle client request for initial LED state."""
#    #ui.send_message('led_status_update', get_led_status(), client)
#    pass

# Handle socket messages (like in Code Scanner example)
#ui.on_message('toggle_led', toggle_led_state)
#ui.on_message('get_initial_state', on_get_initial_state)

def led_blink():
    global led_is_on
    time.sleep(1)
    led_is_on = not led_is_on
    Bridge.call('set_led_state', led_is_on)
    print("led blinking")

def find_keys_pressed():
    # TODO: use the Edge Impulse ML
    return [False, True, False, False, True, True, False, True, False, True, False, False, False, False]

def activated_key(prev_frame, this_frame):
    for i in range(0, 14):
        if i < len(this_frame) and i < len(prev_frame) and this_frame[i] and not prev_frame[i]:
            return i
    return -1

def press_key(to_unpress, to_press):
    # TODO: unpress prev frame in hardware
    # TODO: is to_unpress necessary from hardware?
    # TODO: press this frame in hardware
    Bridge.call('press_key', to_press)

def loop():
    global keyboard_state
    led_blink()

    this_frame = find_keys_pressed()
    new_active_key = activated_key(keyboard_state['keys_down'], this_frame)
    if new_active_key != keyboard_state['active_key']:
        press_key(keyboard_state['active_key'], new_active_key)

    keyboard_state['keys_down'] = this_frame
    keyboard_state['active_key'] = new_active_key

# Start the application
App.run(user_loop=loop)
