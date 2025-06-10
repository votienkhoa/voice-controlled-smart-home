#include "dht11.h"
#include <DHT.h>
#include "config.h"

DHT dht(DHT11_PIN, DHT11);

void initDHT11() {
  dht.begin();
}

float readTemperature() {
  float temp = dht.readTemperature();
  return isnan(temp) ? -1 : temp;
}

float readHumidity() {
  float hum = dht.readHumidity();
  return isnan(hum) ? -1 : hum;
}