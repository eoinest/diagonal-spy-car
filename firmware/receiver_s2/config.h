#pragma once
#include <stdint.h>

// Commission with wheels lifted. Never publish your private pairing keys.
constexpr bool PAIRING_CONFIGURED = false;
constexpr uint8_t TRANSMITTER_MAC[6] = {0, 0, 0, 0, 0, 0};
constexpr uint8_t WIFI_CHANNEL = 1;
constexpr uint8_t ESPNOW_PMK[16] = {};
constexpr uint8_t ESPNOW_LMK[16] = {};

// False leaves PWM pins LOW and does not attach LEDC. Verify your servo's
// missing-signal behavior; the XT30 disconnect is the definitive stop.
constexpr bool SERVO_CALIBRATION_CONFIRMED = false;
constexpr uint8_t LEFT_SERVO_PIN = 16;
constexpr uint8_t RIGHT_SERVO_PIN = 18;
constexpr int LEFT_NEUTRAL_US = 1500;
constexpr int RIGHT_NEUTRAL_US = 1500;
constexpr int LEFT_DIRECTION = 1;
constexpr int RIGHT_DIRECTION = -1;
constexpr int MAX_DEVIATION_US = 180;  // Conservative initial speed range.
constexpr int SLEW_US_PER_20MS = 8;    // Emergency stops bypass this ramp.

// This POC has no battery sensing hardware. GPIO3 and GPIO7 are unconnected.
// Check both LiPo cells with a multimeter before/between short attended runs;
// firmware cannot warn about low voltage or disconnect the battery.
