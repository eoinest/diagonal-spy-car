// Original MIT-licensed prototype. Requires Arduino-ESP32 3.x.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <esp_system.h>
#include <SpyCarProtocol.h>
#if __has_include("config.private.h")
#include "config.private.h"
#else
#include "config.h"
#endif

#if !CONFIG_IDF_TARGET_ESP32
#error "This joystick pinout targets an original ESP32 DevKit."
#endif

bool radioReady = false;
uint32_t session = 0;
uint32_t sequence = 0;

bool keyPresent(const uint8_t *key) {
  uint8_t combined = 0;
  for (int i = 0; i < 16; ++i) combined |= key[i];
  return combined != 0;
}

int readAxis(int raw, int minimum, int center, int maximum) {
  if (raw > center + JOYSTICK_DEADZONE)
    return constrain((raw - center - JOYSTICK_DEADZONE) * 1000 /
                     max(1, maximum - center - JOYSTICK_DEADZONE), 0, 1000);
  if (raw < center - JOYSTICK_DEADZONE)
    return constrain((raw - center + JOYSTICK_DEADZONE) * 1000 /
                     max(1, center - JOYSTICK_DEADZONE - minimum), -1000, 0);
  return 0;
}

void setup() {
  Serial.begin(115200);
  pinMode(DEADMAN_PIN, INPUT_PULLUP);
  analogReadResolution(12);
  analogSetPinAttenuation(THROTTLE_PIN, ADC_11db);
  analogSetPinAttenuation(STEERING_PIN, ADC_11db);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  Serial.printf("Transmitter station MAC: %s\n", WiFi.macAddress().c_str());
  if (!PAIRING_CONFIGURED || !keyPresent(ESPNOW_PMK) || !keyPresent(ESPNOW_LMK)) return;
  if (esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE) != ESP_OK ||
      esp_now_init() != ESP_OK || esp_now_set_pmk(ESPNOW_PMK) != ESP_OK) return;
  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, RECEIVER_MAC, 6);
  memcpy(peer.lmk, ESPNOW_LMK, 16);
  peer.channel = WIFI_CHANNEL;
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = true;
  if (esp_now_add_peer(&peer) != ESP_OK) return;
  do { session = esp_random(); } while (session == 0);
  radioReady = true;
}

void loop() {
  const uint32_t now = millis();
  static uint32_t lastSend = 0, lastStatus = 0;
  const int throttleRaw = analogRead(THROTTLE_PIN);
  const int steeringRaw = analogRead(STEERING_PIN);
  const bool held = digitalRead(DEADMAN_PIN) == LOW;
  if (radioReady && now - lastSend >= 20) {
    lastSend = now;
    spycar::Packet packet = {};
    packet.magic = spycar::kMagic;
    packet.version = spycar::kVersion;
    packet.session = session;
    packet.sequence = ++sequence;
    if (JOYSTICK_CALIBRATION_CONFIRMED) {
      packet.flags = held ? spycar::kDeadman : 0;
      packet.throttle = THROTTLE_DIRECTION * readAxis(throttleRaw, THROTTLE_MIN, THROTTLE_CENTER, THROTTLE_MAX);
      packet.steering = STEERING_DIRECTION * readAxis(steeringRaw, STEERING_MIN, STEERING_CENTER, STEERING_MAX);
    }
    // Sending means queued, not confirmed delivered; receiver enforces timeout.
    esp_now_send(RECEIVER_MAC, reinterpret_cast<const uint8_t *>(&packet), sizeof(packet));
  }
  if (now - lastStatus >= 1000) {
    lastStatus = now;
    Serial.printf("joystick=%d,%d deadman=%d configured=%d radio=%d MAC=%s\n",
                  throttleRaw, steeringRaw, held, JOYSTICK_CALIBRATION_CONFIRMED,
                  radioReady, WiFi.macAddress().c_str());
  }
  delay(1);
}
