#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#define RGB_PIN 38
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
  while (!Serial);  // Ensure serial is ready
  delay(1000);
  Serial.println("Started!");
}

void loop() {
  int val1 = digitalRead(inputPin1); // Left
  int val2 = digitalRead(inputPin2); // Right

  if (val1 == HIGH && val2 == HIGH) {
    rgb.setPixelColor(0, rgb.Color(0, 0, 255));  // Blue = Idle
    Serial.println(2);  // Center
  } 
  else if (val1 == HIGH) {
    Serial.println(1);  // Move left
    rgb.setPixelColor(0, rgb.Color(0, 255, 0));  // Green
  } 
  else if (val2 == HIGH) {
    Serial.println(3);  // Move right
    rgb.setPixelColor(0, rgb.Color(255, 255, 0));  // Yellow
  } else {
    rgb.setPixelColor(0, rgb.Color(0, 0, 255));  // Default blue
  }

  rgb.show();
  delay(100);  // Reduce serial spam
}