#include <Arduino.h>
#include <Adafruit_NeoPixel.h> 

#define RGB_PIN 38  // RGB LED is connected to GPIO38
#define NUM_PIXELS 1

Adafruit_NeoPixel rgb(NUM_PIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

const int inputPin1 = 9;   // PIR sensor 1 (left)
const int inputPin2 = 10;  // PIR sensor 2 (right)

void setup() {
  rgb.begin();
  rgb.setBrightness(50);
  rgb.setPixelColor(0, rgb.Color(0, 0, 255));  // Blue on start
  rgb.show();

  pinMode(inputPin1, INPUT);
  pinMode(inputPin2, INPUT);

  Serial.begin(115200);
  Serial.println("Started!");
}

void loop() {
  int val1 = digitalRead(inputPin1); // Left sensor
  int val2 = digitalRead(inputPin2); // Right sensor

  bool triggered = false;

  if (val1 == HIGH) {
    Serial.println("left");
    rgb.setPixelColor(0, rgb.Color(0, 255, 0));  // Green for left
    triggered = true;
  }

  else if (val2 == HIGH) {
    Serial.println("right");
    rgb.setPixelColor(0, rgb.Color(255, 255, 0));  // Yellow for right
    triggered = true;
  }

  if (!triggered) {
    rgb.setPixelColor(0, rgb.Color(0, 0, 255));  // Blue idle
  }

  rgb.show();
  delay(200); // Minimal debounce
}
