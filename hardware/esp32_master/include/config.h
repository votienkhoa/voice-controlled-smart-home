#ifndef CONFIG_H
#define CONFIG_H

// UART
#define UART_TX_PIN 17
#define UART_RX_PIN 16
#define UART_BAUD 115200    

// WiFi
#define WIFI_SSID "ALPHA"
#define WIFI_PASS "27082021"

// MQTT
#define MQTT_BROKER "192.168.2.39" 
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "ESP32_Master"
#define MQTT_TOPIC_SUB "home/command"  
#define MQTT_TOPIC_PUB "home/status"

#endif