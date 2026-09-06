// Original MIT-licensed prototype. Requires Arduino-ESP32 3.x.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <atomic>
#include <SpyCarProtocol.h>
#if __has_include("config.private.h")
#include "config.private.h"
#else
#include "config.h"
#endif

#if !CONFIG_IDF_TARGET_ESP32S2
#error "Select LOLIN S2 MINI for this receiver."
#endif

struct Received {
  spycar::Packet packet;
  uint32_t time;
};
QueueHandle_t receiveQueue;
std::atomic<bool> receiveOverflow{false};
spycar::DriveGate drive;
bool radioReady = false;
bool pwmReady = false;
bool outputFault = false;
bool batteryLatched = false;
bool batteryValid = false;
bool lowPending = false;
uint32_t lowSince = 0;
float batteryVoltage = 0;
int leftPulse = LEFT_NEUTRAL_US;
int rightPulse = RIGHT_NEUTRAL_US;

bool keyPresent(const uint8_t *key) {
  uint8_t combined = 0;
  for (int i = 0; i < 16; ++i) combined |= key[i];
  return combined != 0;
}

void onReceive(const esp_now_recv_info_t *info, const uint8_t *data, int length) {
  if (!info || length != sizeof(spycar::Packet) ||
      memcmp(info->src_addr, TRANSMITTER_MAC, 6) != 0) return;
  Received received;
  memcpy(&received.packet, data, sizeof(received.packet));
  if (!spycar::valid(received.packet)) return;
  received.time = millis();
  // ESP-NOW invokes this from its Wi-Fi task; leave work to the main loop.
  if (xQueueSend(receiveQueue, &received, 0) != pdTRUE) receiveOverflow = true;
}

void writePulse(uint8_t pin, int microseconds) {
  const uint32_t duty = ((uint32_t)microseconds * 16384UL + 10000UL) / 20000UL;
  if (!ledcWrite(pin, duty)) {
    drive.stop();
    pwmReady = false;
    outputFault = true;
    digitalWrite(BATTERY_SENSE_ENABLE_PIN, LOW);
    ledcDetach(LEFT_SERVO_PIN);
    ledcDetach(RIGHT_SERVO_PIN);
    pinMode(LEFT_SERVO_PIN, OUTPUT);
    pinMode(RIGHT_SERVO_PIN, OUTPUT);
    digitalWrite(LEFT_SERVO_PIN, LOW);
    digitalWrite(RIGHT_SERVO_PIN, LOW);
  }
}

void stopNow() {
  leftPulse = LEFT_NEUTRAL_US;
  rightPulse = RIGHT_NEUTRAL_US;
  if (pwmReady) writePulse(LEFT_SERVO_PIN, leftPulse);
  if (pwmReady) writePulse(RIGHT_SERVO_PIN, rightPulse);
}

int approach(int current, int target) {
  return current + constrain(target - current, -SLEW_US_PER_20MS, SLEW_US_PER_20MS);
}

void updateBattery(uint32_t now) {
  uint32_t totalMv = 0;
  for (int i = 0; i < 8; ++i) totalMv += analogReadMilliVolts(BATTERY_ADC_PIN);
  batteryVoltage = (totalMv / 8000.0f) * BATTERY_DIVIDER_RATIO * BATTERY_SCALE +
                   BATTERY_OFFSET_V;
  batteryValid = batteryVoltage >= BATTERY_STOP_V &&
                 batteryVoltage <= BATTERY_MAX_VALID_V;
  if (!batteryValid) {
    if (!lowPending) { lowPending = true; lowSince = now; }
    if (now - lowSince >= BATTERY_LOW_HOLD_MS) batteryLatched = true;
  } else {
    lowPending = false;
  }
}

void setup() {
  pinMode(BATTERY_SENSE_ENABLE_PIN, OUTPUT);
  digitalWrite(BATTERY_SENSE_ENABLE_PIN, LOW);
  pinMode(LEFT_SERVO_PIN, OUTPUT);
  pinMode(RIGHT_SERVO_PIN, OUTPUT);
  digitalWrite(LEFT_SERVO_PIN, LOW);
  digitalWrite(RIGHT_SERVO_PIN, LOW);
  Serial.begin(115200); // No indefinite USB-serial wait: failsafe loop must run.
#if ARDUINO_USB_CDC_ON_BOOT
  Serial.setTxTimeoutMs(0); // A full USB monitor buffer must not delay stopping.
#endif
  analogReadResolution(12);
  analogSetPinAttenuation(BATTERY_ADC_PIN, ADC_11db);
  receiveQueue = xQueueCreate(8, sizeof(Received));
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  Serial.printf("Receiver station MAC: %s\n", WiFi.macAddress().c_str());
  if (!receiveQueue || !PAIRING_CONFIGURED || !keyPresent(ESPNOW_PMK) ||
      !keyPresent(ESPNOW_LMK)) {
    Serial.println("Drive disabled: configure both MAC addresses and private keys.");
    return;
  }
  if (esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE) != ESP_OK ||
      esp_now_init() != ESP_OK || esp_now_set_pmk(ESPNOW_PMK) != ESP_OK) return;
  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, TRANSMITTER_MAC, 6);
  memcpy(peer.lmk, ESPNOW_LMK, 16);
  peer.channel = WIFI_CHANNEL;
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = true;
  if (esp_now_add_peer(&peer) != ESP_OK ||
      esp_now_register_recv_cb(onReceive) != ESP_OK) return;
  radioReady = true;
  if (SERVO_CALIBRATION_CONFIRMED && BATTERY_CALIBRATION_CONFIRMED) {
    const bool leftOk = ledcAttach(LEFT_SERVO_PIN, 50, 14);
    const bool rightOk = ledcAttach(RIGHT_SERVO_PIN, 50, 14);
    pwmReady = leftOk && rightOk;
    if (!pwmReady) {
      outputFault = true;
      ledcDetach(LEFT_SERVO_PIN);
      ledcDetach(RIGHT_SERVO_PIN);
      pinMode(LEFT_SERVO_PIN, OUTPUT);
      pinMode(RIGHT_SERVO_PIN, OUTPUT);
      digitalWrite(LEFT_SERVO_PIN, LOW);
      digitalWrite(RIGHT_SERVO_PIN, LOW);
    }
    stopNow();
  }
}

void loop() {
  const uint32_t now = millis();
  static uint32_t lastBattery = 0, lastServo = 0, lastStatus = 0;
  static bool batterySampling = false;
  static uint32_t batteryEnabledAt = 0;
  if (outputFault) {
    digitalWrite(BATTERY_SENSE_ENABLE_PIN, LOW);
    batterySampling = false;
  }
  if (!batterySampling && !batteryLatched && !outputFault && now - lastBattery >= 100) {
    lastBattery = now;
    digitalWrite(BATTERY_SENSE_ENABLE_PIN, HIGH);
    batteryEnabledAt = now;
    batterySampling = true;
  }
  if (batterySampling && now - batteryEnabledAt >= 20) {
    updateBattery(now);
    digitalWrite(BATTERY_SENSE_ENABLE_PIN, LOW);
    batterySampling = false;
  }
  // A low reading immediately disarms; 1s continuous low latches until reboot.
  drive.inhibit(!radioReady || !pwmReady || !batteryValid || batteryLatched);
  drive.tick(now);
  const bool queueFault = receiveOverflow.exchange(false);
  if (queueFault) {
    drive.stop();
    stopNow();
    xQueueReset(receiveQueue);
  }
  Received received;
  // Bound callback work so a busy sender cannot starve sensing or failsafes.
  // After overflow, accept no command in this iteration, including a rearm.
  for (int processed = 0; !queueFault && receiveQueue && processed < 8 &&
       xQueueReceive(receiveQueue, &received, 0) == pdTRUE; ++processed) {
    drive.accept(received.packet, received.time, millis());
    // Process every release packet, even if a press follows in the same batch.
    if (!drive.armed) stopNow();
  }
  drive.tick(millis()); // Recheck the boundary immediately before any PWM write.
  if (!drive.armed) {
    stopNow();
  } else if (now - lastServo >= 20) {
    lastServo = now;
    int left = drive.throttle - drive.steering;
    int right = drive.throttle + drive.steering;
    const int maximum = max(1000, max(abs(left), abs(right)));
    left = left * 1000 / maximum;
    right = right * 1000 / maximum;
    leftPulse = approach(leftPulse, LEFT_NEUTRAL_US + LEFT_DIRECTION * left * MAX_DEVIATION_US / 1000);
    rightPulse = approach(rightPulse, RIGHT_NEUTRAL_US + RIGHT_DIRECTION * right * MAX_DEVIATION_US / 1000);
    if (pwmReady) writePulse(LEFT_SERVO_PIN, leftPulse);
    if (pwmReady) writePulse(RIGHT_SERVO_PIN, rightPulse);
  }
  if (now - lastStatus >= 1000) {
    lastStatus = now;
    Serial.printf("VBAT=%.3fV armed=%d low_latched=%d radio=%d PWM=%d MAC=%s\n",
                  batteryVoltage, drive.armed, batteryLatched, radioReady, pwmReady,
                  WiFi.macAddress().c_str());
  }
  delay(1);
}
