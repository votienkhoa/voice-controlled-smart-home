#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"
#include "uart_utils.h"
#include "wifi_handler.h"
#include "mqtt.h"
#include "uart.h"
#include "screen.h"


WiFiClient espClient;
PubSubClient mqttClient(espClient);

void setup() {
  Serial.begin(115200);
  setupWiFi();
  setupMQTT(mqttClient);
  setupUART();
  setupScreen();
  Serial.println("Setup complete.");
}

void loop() {
  maintainWiFi();
  maintainMQTT(mqttClient);
  mqttClient.loop();
  receive(mqttClient);
  updateScreen(mqttClient);

  delay(100); 
}