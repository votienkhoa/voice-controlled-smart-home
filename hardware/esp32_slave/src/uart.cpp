#include "uart.h"
#include <Arduino.h>
#include "uart_utils.h"
#include "config.h"
#include "main_door.h"
#include "led.h"
#include "servo_handler.h"
#include "dht11.h"
#include "mq2.h"

String lock = "MAIN_DOOR_OFF";
String unlock = "MAIN_DOOR_ON";

void handleUART() {
  String message = receiveUART();
  message.trim();
  if (message != "") {
    Serial.println("UART Received: [" + message + "]");
    if (message == unlock) {
      Serial.println("Unlocking door...");
      unlockDoor();
      sendUART("door:UNLOCKED");
    } else if (message == lock) {
      Serial.println("Locking door...");
      lockDoor();
      sendUART("door:LOCKED");
    } 
    else if (message == "device:led1,state:ON") {
      controlLED(1, true);
    } 
    else if (message == "device:led1,state:OFF") {
      controlLED(1, false);
    } 
    else if (message == "device:led2,state:ON") {
      controlLED(2, true);
    } 
    else if (message == "device:led2,state:OFF") {
      controlLED(2, false);
    } 
    else if (message == "device:led3,state:ON") {
      controlLED(3, true);
    } 
    else if (message == "device:led3,state:OFF") {
      controlLED(3, false);
    } 
    else if (message.startsWith("device:servo1,angle:")) {
      int angle = message.substring(20).toInt();
      Serial.print(angle);
      controlServo(1, angle);
      sendUART(("servo1:" + String(angle)).c_str());
    } 
    else if (message.startsWith("device:servo2,angle:")) {
      int angle = message.substring(20).toInt();
      controlServo(2, angle);
      sendUART(("servo2:" + String(angle)).c_str());
    } 
    else if (message == "device:dht11,action:read_temp") {
      float temp = readTemperature();
      sendUART(("dht11_temp:" + String(temp, 2)).c_str());
    } 
    else if (message == "device:dht11,action:read_hum") {
      float hum = readHumidity();
      sendUART(("dht11_hum:" + String(hum, 2)).c_str());
    } 
    else if (message == "device:mq2,action:read") {
      float value = readMQ2();
      sendUART(("mq2:" + String(value, 2)).c_str());
    }
  }
}