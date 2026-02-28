#include <Arduino_RouterBridge.h>

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Bridge.begin();
    Bridge.provide("set_led_state", set_led_state);
}

void loop() {}

void set_led_state(bool state) {
    // LOW = on, HIGH = off
    digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}
