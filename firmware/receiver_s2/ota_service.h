#pragma once
#include <HTTPUpdateServer.h>
#if __has_include("ota.private.h")
#include "ota.private.h"
#else
#include "ota_config.h"
#endif

bool otaPowerOkay();

// Thin car-specific wrapper. Espressif HTTPUpdateServer owns the upload page,
// authentication, transfer and reboot; its Update library owns flash storage.
class CarUpdater {
 public:
  void begin() {
    const size_t length = strlen(OTA_PASSWORD);
    if (length < 12 || length > 63) {
      Serial.println("OTA disabled: set a private 12–63 character password.");
      return;
    }
    for (size_t i = 0; i < length; ++i) {
      if (OTA_PASSWORD[i] < 33 || OTA_PASSWORD[i] > 126) return;
    }
    if (!otaPowerOkay()) {
      Serial.println("OTA unavailable: charge/check the battery, then restart.");
      return;
    }
    WiFi.mode(WIFI_AP);
    if (!WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0)) ||
        !WiFi.softAP(OTA_SSID, OTA_PASSWORD, 1, false, 1)) return;
    httpUpdater_.setup(&server_, "/update", "admin", OTA_PASSWORD);
    server_.begin();
    started_ = millis();
    online_ = true;
    Serial.printf("Parked: join %s, open http://192.168.4.1/update, user admin.\n", OTA_SSID);
  }

  void tick() {
    if (!online_) return;
    // The standard server handles an upload synchronously. Let an active
    // transfer finish; close the network on the next serviced timeout check.
    if (millis() - started_ >= OTA_NETWORK_TIMEOUT_MS) {
      server_.stop();
      WiFi.softAPdisconnect(true);
      online_ = false;
      Serial.println("Update network closed. Driving stays locked; unplug battery after use.");
      return;
    }
    server_.handleClient();
  }

 private:
  WebServer server_{80};
  HTTPUpdateServer httpUpdater_;
  bool online_ = false;
  uint32_t started_ = 0;
};
