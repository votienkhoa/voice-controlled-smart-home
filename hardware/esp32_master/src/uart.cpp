#include "uart.h"
#include <Arduino.h>        // Cho String
#include "uart_utils.h"
#include "mqtt.h"
#include "config.h"

void send(const char* command) {
  sendUART(command);
}

void receive(PubSubClient& client) {
  String message = receiveUART();
  if (message != "") {
    Serial.println("UART Received: [" + message + "]");
    client.publish(MQTT_TOPIC_PUB, message.c_str());
  }
}