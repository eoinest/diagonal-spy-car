// Original MIT-licensed bench-only tool. Wheels OFF the floor; switch reachable.
// No output until a serial command. Missing PWM is not a hardware power cut.
#include <Arduino.h>

#if !CONFIG_IDF_TARGET_ESP32S2
#error "Select LOLIN S2 MINI."
#endif

constexpr uint8_t LEFT_PIN = 16;
constexpr uint8_t RIGHT_PIN = 18;
constexpr uint8_t SENSE_ENABLE_PIN = 7;
int activePin = -1;
uint32_t started = 0;
char line[16] = {};
size_t used = 0;

void disconnectSignal() {
  if (activePin >= 0) ledcDetach(activePin);
  activePin = -1;
  pinMode(LEFT_PIN, OUTPUT);
  pinMode(RIGHT_PIN, OUTPUT);
  digitalWrite(LEFT_PIN, LOW);
  digitalWrite(RIGHT_PIN, LOW);
}

void handleCommand() {
  line[used] = 0;
  if (used == 1 && line[0] == 'X') {
    disconnectSignal();
    Serial.println("PWM removed. Use XT30 disconnect if servo keeps moving.");
  } else if (used == 5 && (line[0] == 'L' || line[0] == 'R')) {
    bool digits = true;
    for (size_t i = 1; i < used; ++i) digits &= line[i] >= '0' && line[i] <= '9';
    const int pulse = atoi(line + 1);
    if (digits && pulse >= 1400 && pulse <= 1600) {
      disconnectSignal();
      activePin = line[0] == 'L' ? LEFT_PIN : RIGHT_PIN;
      if (ledcAttach(activePin, 50, 14) &&
          ledcWrite(activePin, (uint32_t(pulse) * 16384UL + 10000UL) / 20000UL)) {
        started = millis();
        Serial.printf("%c: %d us for up to 5 seconds.\n", line[0], pulse);
      } else {
        disconnectSignal();
        Serial.println("PWM initialization failed.");
      }
    } else {
      Serial.println("Use L1400..L1600 or R1400..R1600; one servo at a time.");
    }
  } else {
    Serial.println("Commands: L1500, R1500, or X. 1400..1600 us only.");
  }
  used = 0;
}

void setup() {
  pinMode(SENSE_ENABLE_PIN, OUTPUT);
  digitalWrite(SENSE_ENABLE_PIN, LOW);
  disconnectSignal();
  Serial.begin(115200);
#if ARDUINO_USB_CDC_ON_BOOT
  Serial.setTxTimeoutMs(0); // Preserve the five-second limit if USB stops draining.
#endif
}

void loop() {
  // A continuous stream of input must not starve the five-second deadline.
  for (int processed = 0; processed < 32 && Serial.available() > 0; ++processed) {
    const char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') handleCommand();
    else if (used < sizeof(line) - 1) line[used++] = c;
    else { used = 0; disconnectSignal(); }
  }
  if (activePin >= 0 && millis() - started >= 5000) {
    disconnectSignal();
    Serial.println("5-second test ended; PWM removed. Turn off servo power.");
  }
  delay(1);
}
