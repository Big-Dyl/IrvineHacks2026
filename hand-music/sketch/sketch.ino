#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define NUM_SERVOS 16
#define SERVOMIN  0   // Min pulse length (0 degrees)
#define SERVOMAX  600   // Max pulse length (180 degrees)
#define SERVO_FREQ 50   // 50 Hz for analog servos

void press_key(int key){
    for(uint8_t k = 0; k < NUM_SERVOS; ++k){
        setServoAngle(k, 0);
    }
    setServoAngle(key, 90);
}

void setup() {
  Serial.begin(9600);
  Serial.println("HELLO!!");
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ);
  Bridge.provide("press_key", press_key);
}

void setServoAngle(uint8_t channel, float angle) {
  channel *= 2;
  angle = constrain(angle, 0, 180);
  uint16_t pwm_val = SERVOMIN + 
                     (angle / 180.0) * (SERVOMAX - SERVOMIN);
  pwm.setPWM(channel, 0, pwm_val);
}

void loop() {}
