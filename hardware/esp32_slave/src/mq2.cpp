#include "mq2.h"
#include <Arduino.h>
#include "config.h"

void initMQ2() {
  pinMode(MQ2_PIN, INPUT);
}

int readMQ2() {
  int analogValue = analogRead(MQ2_PIN);
  return (analogValue / 4095.0) * 100;
}