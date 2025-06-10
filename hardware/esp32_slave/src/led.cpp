#include "led.h"
#include <Arduino.h>
#include "config.h"

void initLED() {
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  digitalWrite(LED3_PIN, LOW);
}

void controlLED(int ledNumber, bool state) {
  int pin;
  switch (ledNumber) {
    case 1: pin = LED1_PIN; break;
    case 2: pin = LED2_PIN; break;
    case 3: pin = LED3_PIN; break;
    default: return;
  }
  digitalWrite(pin, state ? HIGH : LOW);
}