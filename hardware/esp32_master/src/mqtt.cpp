#include "mqtt.h"
#include <Arduino.h>
#include "config.h"
#include "uart.h"

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("MQTT Received: [" + message + "]");
  send(message.c_str());
}

void setupMQTT(PubSubClient& client) {
  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(mqttCallback);
  maintainMQTT(client);
}

void maintainMQTT(PubSubClient& client) {
  while (!client.connected()) {
    if (client.connect(MQTT_CLIENT_ID)) {
      client.subscribe(MQTT_TOPIC_SUB);
    } else {
      delay(5000);
    }
  }
}

void sendMQTT(PubSubClient& client, const char* topic, const char* message) {
  if (client.connected()) {
    client.publish(topic, message);
  }
}