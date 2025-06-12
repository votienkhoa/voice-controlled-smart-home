#include "screen.h"
#include "uart.h"
#include "uart_utils.h"
#include "config.h"
#include <SPI.h>
#include <TFT_eSPI.h>

#define BUTTON_W 160
#define BUTTON_H 60

TFT_eSPI tft = TFT_eSPI();

typedef struct {
  int x, y;
  const char* label;
} Button;

// Danh sách nút
Button buttons[4] = {
  {0,  60,  "Child room light"},
  {160, 60, "Main Door"},
  {0,  120, "Parent room light"},
  {160, 120, "Living room light"}
};

bool buttonStates[4] = {false, false, false, false};

// Lệnh UART cho từng nút
const char* onCommands[]  = { "device:led1,state:ON", "device:maindoor,state:ON", "device:led2,state:ON", "device:led3,state:ON" };
const char* offCommands[] = { "device:led1,state:OFF", "device:maindoor,state:OFF", "device:led2,state:OFF", "device:led3,state:OFF" };

float latestTemp = -1, latestHum = -1, latestMQ2 = -1;

// Vẽ tiêu đề
void drawTitle() {
  tft.setTextSize(1);
  tft.setTextColor(TFT_BLACK, TFT_LIGHTGREY);
  tft.fillRect(0, 0, 320, 60, TFT_LIGHTGREY);
  tft.setCursor(75, 35);
  tft.print("kdth-smarthome");
}

// Vẽ nút
void drawButton(int i) {
  uint16_t fillColor = buttonStates[i] ? TFT_GREEN : TFT_RED;
  uint16_t textColor = TFT_WHITE;

  tft.fillRect(buttons[i].x, buttons[i].y, BUTTON_W, BUTTON_H, fillColor);
  tft.drawRect(buttons[i].x, buttons[i].y, BUTTON_W, BUTTON_H, TFT_BLACK);
  tft.setTextColor(textColor, fillColor);
  tft.setCursor(buttons[i].x + 30, buttons[i].y + 40);
  tft.print(buttons[i].label);
}

void drawButtons() {
  for (int i = 0; i < 4; i++) {
    drawButton(i);
  }
}
void displaySensorData() {
  tft.fillRect(0, 180, 320, 60, TFT_BLACK);
  tft.setTextSize(1);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setCursor(0, 185);
  tft.print("Temp: ");
  tft.print(latestTemp >= 0 ? String(latestTemp, 2) : "N/A");
  tft.println(" C");
  tft.setCursor(0, 205);
  tft.print("Hum: ");
  tft.print(latestHum >= 0 ? String(latestHum, 2) : "N/A");
  tft.println(" %");
  tft.setCursor(0, 225);
  tft.print("Gas: ");
  tft.print(latestMQ2 >= 0 ? String(latestMQ2, 2) : "N/A");
  tft.println(" %");
}

// Gọi trong setup()
void setupScreen() {
  tft.init();
  tft.invertDisplay(false);
  tft.setRotation(1);

  // Calibration (sửa lại nếu cần)
  uint16_t calData[5] = { 366, 3380, 209, 3468, 1 };
  tft.setTouch(calData);

  tft.fillScreen(TFT_BLACK);
  tft.setTextSize(5);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);

  drawTitle();
  drawButtons();
}

// Gọi trong loop()
void updateScreen(PubSubClient& client) {
  uint16_t x = 0, y = 0;
  bool pressed = tft.getTouch(&x, &y);
  if (pressed) {
    for (int i = 0; i < 4; i++) {
      if (x > buttons[i].x && x < (buttons[i].x + BUTTON_W) &&
          y > buttons[i].y && y < (buttons[i].y + BUTTON_H)) {

        buttonStates[i] = !buttonStates[i];
        drawButton(i);


        const char* command = buttonStates[i] ? onCommands[i] : offCommands[i];
        send(command);
        client.publish(MQTT_TOPIC_PUB, command);

        delay(300);  
      }
    }
  }
}
void updateScreenFromMQTT(const char* message) {
  String msg = String(message);
  msg.trim();
  Serial.println("MQTT Received: [" + msg + "]");
  for (int i = 0; i < 4; i++) {
    if (msg == onCommands[i]) {
      buttonStates[i] = true;
      drawButton(i);
      Serial.println("Updated button " + String(i) + ": ON");
      return;
    } else if (msg == offCommands[i]) {
      buttonStates[i] = false;
      drawButton(i);
      Serial.println("Updated button " + String(i) + ": OFF");
      return;
    }
  }
}
void requestSensorData() {
  // Gửi lệnh UART yêu cầu cảm biến
  sendUART("device:dht11,action:read_temp");
  sendUART("device:dht11,action:read_hum");
  sendUART("device:mq2,action:read");

  // Nhận và xử lý phản hồi
  unsigned long start = millis();
  while (millis() - start < 1000) { // Chờ tối đa 1 giây
    String message = receiveUART();
    message.trim();
    if (message != "") {
      Serial.println("UART Received: [" + message + "]");
      if (message.startsWith("dht11_temp:")) {
        latestTemp = message.substring(11).toFloat();
      } else if (message.startsWith("dht11_hum:")) {
        latestHum = message.substring(10).toFloat();
      } else if (message.startsWith("mq2:")) {
        latestMQ2 = message.substring(4).toFloat();
      }
    }
  }
  displaySensorData(); // Cập nhật màn hình
}
