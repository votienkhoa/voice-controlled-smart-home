#include "uart_utils.h"
#include <Arduino.h>
#include "config.h"

#define UART_TX_PIN 17
#define UART_RX_PIN 16
#define UART_BAUD 115200

void setupUART() {
  Serial2.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
}

void sendUART(const char* message) {
  Serial2.println(message);
}

String receiveUART() {
  unsigned long start = millis();
  while (millis() - start < 1000) {
    if (Serial2.available()) {
      return Serial2.readStringUntil('\n');
    }
  }
  return "";
}