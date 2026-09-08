#pragma once

// Copy to ota.private.h and set a unique 12–63 character ASCII password.
// Never publish that file. Empty passwords disable the update network.
constexpr char OTA_PASSWORD[] = "";
constexpr char OTA_SSID[] = "SpyCar-Update";
constexpr uint8_t OTA_BUTTON_PIN = 0; // Existing BOOT/0 button, after normal boot.
constexpr uint32_t OTA_NETWORK_TIMEOUT_MS = 5UL * 60UL * 1000UL;
