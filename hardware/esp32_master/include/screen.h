#ifndef SCREEN_H
#define SCREEN_H

#include <PubSubClient.h>

void setupScreen();
void updateScreen(PubSubClient& client);
void updateScreenFromMQTT(const char* message);
void requestSensorData();

#endif
