#include "main_door.h"
#include <Arduino.h>
#include <ezButton.h>
#include "config.h"
#include "uart_utils.h"

ezButton limitOpen(LIMIT_OPEN);
ezButton limitClose(LIMIT_CLOSE);

bool isLocked = false;

void setupDoor() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(PIR1, INPUT);
  pinMode(PIR2, INPUT);

  limitOpen.setDebounceTime(50);
  limitClose.setDebounceTime(50);
}

void handleDoor() {
  limitOpen.loop();
  limitClose.loop();

  int PIR1_value = digitalRead(PIR1);
  int PIR2_value = digitalRead(PIR2);

  Serial.print("PIR1: ");
  Serial.println(PIR1_value);
  Serial.print("PIR2: ");
  Serial.println(PIR2_value);

  if (!isLocked) {
    if (!PIR1_value && !PIR2_value) {
      closeDoor();
    } else {
      openDoor();
    }
  }
}

void openDoor() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  while (limitOpen.getState() == HIGH) {
    Serial.println("Opening..");
    limitOpen.loop();
  }

  stopMotor();
  Serial.println("Fully Opened");
  sendUART("DOOR:OPENED");
}

void closeDoor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  while (limitClose.getState() == HIGH) {
    Serial.println("Closing..");
    limitClose.loop();
  }

  stopMotor();
  Serial.println("Fully Closed");
  sendUART("DOOR:CLOSED");
}

void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void lockDoor() {
  closeDoor();        
  isLocked = true;
  Serial.println("Door is now locked.");
}
void unlockDoor() {
  isLocked = false;   
  Serial.println("Door is now unlocked.");
}
