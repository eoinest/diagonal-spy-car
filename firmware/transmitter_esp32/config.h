#pragma once
#include <stdint.h>

constexpr bool PAIRING_CONFIGURED = false;
constexpr uint8_t RECEIVER_MAC[6] = {0, 0, 0, 0, 0, 0};
constexpr uint8_t WIFI_CHANNEL = 1;
constexpr uint8_t ESPNOW_PMK[16] = {};
constexpr uint8_t ESPNOW_LMK[16] = {};

// Original ESP32 DevKit, not S2. Joystick must be powered from 3.3V.
constexpr uint8_t THROTTLE_PIN = 32;
constexpr uint8_t STEERING_PIN = 33;
constexpr uint8_t DEADMAN_PIN = 27; // Normally-open momentary switch to GND.
constexpr bool JOYSTICK_CALIBRATION_CONFIRMED = false;
constexpr int THROTTLE_MIN = 0;
constexpr int THROTTLE_CENTER = 2048;
constexpr int THROTTLE_MAX = 4095;
constexpr int STEERING_MIN = 0;
constexpr int STEERING_CENTER = 2048;
constexpr int STEERING_MAX = 4095;
constexpr int THROTTLE_DIRECTION = 1;
constexpr int STEERING_DIRECTION = 1;
constexpr int JOYSTICK_DEADZONE = 120;
