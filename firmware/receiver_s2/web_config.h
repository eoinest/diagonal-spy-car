#pragma once

// Copy to web.private.h to override network options. Standalone AP mode uses
// OTA_PASSWORD from ota.private.h; existing-network mode uses credentials below.
constexpr bool WEB_CONTROL_ENABLED = true;
constexpr char WEB_SSID[] = "SpyCar";
constexpr char WEB_HOSTNAME[] = "spy-car"; // http://spy-car.local
// Set these in web.private.h to follow auto-switch: join your existing Wi-Fi.
// Empty SSID selects the standalone SpyCar AP using OTA_PASSWORD instead.
constexpr char WEB_WIFI_SSID[] = "";
constexpr char WEB_WIFI_PASSWORD[] = "";
