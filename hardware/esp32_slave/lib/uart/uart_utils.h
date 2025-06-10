#ifndef UART_UTILS_H
#define UART_UTILS_H

#include <Arduino.h>  

void setupUART();
void sendUART(const char* message);
String receiveUART();

#endif