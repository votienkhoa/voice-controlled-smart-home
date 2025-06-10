#include "wifi.h"
#include <Arduino.h>
#include "config.h"

void setupWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void maintainWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
    }
  }
}