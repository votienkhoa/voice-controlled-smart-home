#include "servo_handler.h"
#include <ESP32Servo.h>
#include "config.h"

Servo servo1;
Servo servo2;

void initServo() {
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  servo1.write(0);
  servo2.write(0);
}

void controlServo(int servoNumber, int angle) {
  if (angle < 0 || angle > 180) return;
  Servo& servo = (servoNumber == 1) ? servo1 : servo2;
  servo.write(angle);
}