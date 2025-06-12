#include <Arduino.h>
#include "config.h"
#include "uart_utils.h"
#include "uart.h"
#include "main_door.h"
#include "led.h"
#include "servo_handler.h"
#include "dht11.h"
#include "mq2.h"

void setup() {
  Serial.begin(115200);
  setupUART();
  // setupDoor();
  initLED();
  initServo();
  initDHT11();
  initMQ2();
}

void loop() {
  handleUART();
  // handleDoor();

  delay(100); // Adjust delay as needed
}