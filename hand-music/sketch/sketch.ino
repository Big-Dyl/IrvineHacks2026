#include <Arduino_RouterBridge.h>

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Bridge.begin();
    Bridge.provide("set_led_state", set_led_state);
    Bridge.provide("press_key", press_key);
}

void loop() {}

void set_led_state(bool state) {
    // LOW = on, HIGH = off
    digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}

void press_key(int to_unpress, int to_press) {
    // TODO: release the key at to_unpress and press the key at to_press
}
