#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVOMIN 150   // Adjust if needed
#define SERVOMAX 600   // Adjust if needed
#define SERVO_FREQ 50  // 50Hz for analog servos

void setup() {
  Serial.begin(9600);
  Serial.println("Servo sanity test");

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ);

  delay(1000);
}

void setServoAngle(uint8_t channel, float angle) {
  channel *= 2;
  angle = constrain(angle, 0, 180);
  uint16_t pwm_val = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  pwm.setPWM(channel, 0, pwm_val);
}

void loop() {
  setServoAngle(0, 30);
  delay(1000);
  setServoAngle(0, 90);
  delay(1000);
  setServoAngle(0, 180);
}