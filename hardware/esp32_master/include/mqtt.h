#ifndef MQTT_H
#define MQTT_H

#include <PubSubClient.h>

void setupMQTT(PubSubClient& client);
void maintainMQTT(PubSubClient& client);
void sendMQTT(PubSubClient& client, const char* topic, const char* message);

#endif