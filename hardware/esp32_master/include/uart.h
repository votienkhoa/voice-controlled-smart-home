#ifndef UART_H
#define UART_H

#include <PubSubClient.h>

void send(const char* command);
void receive(PubSubClient& client);

#endif