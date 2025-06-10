#include <Arduino.h>
#include "config.h"
#include "uart_utils.h"
#include "uart.h"
#include "main_door.h"

void setup() {
  Serial.begin(115200); // Serial Monitor
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  setupUART();
  setupDoor();
}

void loop() {
  handleUART();
  handleDoor();
}