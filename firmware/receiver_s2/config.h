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

// Pack divider requires the GPIO7-controlled BS250P/2N3904 high-side gate
// described in electronics/wiring.md; prevents backpower after regulator shutdown.
// Gated battery+ -> 100k -> ADC3 -> 33k -> GND, 100nF ADC3 to GND.
constexpr uint8_t BATTERY_ADC_PIN = 3;
constexpr uint8_t BATTERY_SENSE_ENABLE_PIN = 7;
constexpr bool BATTERY_CALIBRATION_CONFIRMED = false;
constexpr float BATTERY_DIVIDER_RATIO = 133.0f / 33.0f;
constexpr float BATTERY_SCALE = 1.0f;  // DMM voltage / displayed voltage.
constexpr float BATTERY_OFFSET_V = 0.0f;
constexpr float BATTERY_STOP_V = 7.0f; // Early stop for 2S; not cell protection.
constexpr float BATTERY_MAX_VALID_V = 8.6f;
constexpr uint32_t BATTERY_LOW_HOLD_MS = 1000;
