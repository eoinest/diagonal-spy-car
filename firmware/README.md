# Firmware: ESP-NOW drive control

Original MIT-licensed prototype firmware for an ESP32-S2 mini car and a separate original ESP32 DevKit handheld controller. The current car has no camera. Driving uses ESP-NOW; a separate parked Wi-Fi mode provides browser firmware updates. Arduino-ESP32 **3.x** is required; the LEDC API differs from 2.x. No code from the inspiration repository was copied.

The checked-in configuration cannot arm. Pairing keys, actual MAC addresses, joystick calibration, servo neutral, and battery ADC calibration must be configured first. Firmware compilation and host tests do not validate wiring, servo behavior, RF performance, or battery protection on real hardware.

## Hardware

| Board | Pin | Connection |
| --- | --- | --- |
| S2 mini | GPIO16 | Left continuous-rotation servo signal |
| S2 mini | GPIO18 | Right continuous-rotation servo signal |
| S2 mini | GPIO3 | Battery divider midpoint, with 100 nF to GND |
| S2 mini | GPIO7 | Enable for the BS250P/2N3904 battery-sense gate |
| Original ESP32 DevKit | GPIO32 | Joystick throttle wiper |
| Original ESP32 DevKit | GPIO33 | Joystick steering wiper |
| Original ESP32 DevKit | GPIO27 | Normally-open deadman button to GND; internal pull-up |

Power the joystick from **3.3 V**, connect grounds, and keep all analog input voltages in range. Servo power comes from the regulated servo rail, never from an ESP GPIO or its 3.3 V pin. See [wiring](../electronics/wiring.md) for the gated battery divider and the complete power path. An ungated pack divider can backpower the MCU when its regulator turns off; do not omit that circuit.

## Build

Install Arduino CLI and the Espressif board package using its [official instructions](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html). These commands are run from the repository root. The commands below pin core 3.3.11 for reproducibility; a different 3.x version must be rebuilt and tested.

```sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.11 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli compile --fqbn esp32:esp32:lolin_s2_mini:PartitionScheme=default --libraries firmware/libraries --output-dir firmware/build/receiver_s2 firmware/receiver_s2
arduino-cli compile --fqbn esp32:esp32:esp32 --libraries firmware/libraries firmware/transmitter_esp32
arduino-cli compile --fqbn esp32:esp32:lolin_s2_mini firmware/servo_neutral_s2
```

For Arduino IDE, copy `firmware/libraries/SpyCarProtocol` into the sketchbook `libraries` directory, open the desired `.ino`, select **LOLIN S2 MINI** for the receiver/calibration tool or **ESP32 Dev Module** for the transmitter, and build. If USB serial is used on the S2, enable USB CDC on boot in the board menu. See [WEMOS's S2 Arduino guide](https://www.wemos.cc/en/latest/tutorials/s2/get_started_with_arduino_s2.html) for the boot/reset sequence if upload does not connect.

List attached ports with `arduino-cli board list`; upload each sketch to its own actual port:

```sh
arduino-cli upload --fqbn esp32:esp32:lolin_s2_mini --port YOUR_S2_PORT firmware/receiver_s2
arduino-cli upload --fqbn esp32:esp32:esp32 --port YOUR_ESP32_PORT firmware/transmitter_esp32
arduino-cli monitor --port YOUR_PORT --config baudrate=115200
```

Do not connect computer USB power and the vehicle's external 5 V rail simultaneously without the isolation described in the wiring document. Do not use a placeholder port literally.

## Wireless receiver updates

This uses **Espressif's bundled `HTTPUpdateServer` and `Update` libraries**, pinned with Arduino-ESP32 3.3.11. They supply the browser page, authentication, upload handling, flash writing and reboot. There is no custom upload protocol, storage implementation or web UI. Our wrapper starts the password-protected AP only in latched maintenance mode. `ArduinoOTA`, also bundled, is an alternative for IDE/command-line network uploads; it is not enabled here.

No new switch, programmer, router, or custom PCB is needed. USB remains necessary for initial installation and recovery. The handheld transmitter is unchanged and still uses USB programming.

### One-time setup

1. Copy `firmware/receiver_s2/ota_config.h` to `ota.private.h` alongside it. Set `OTA_PASSWORD` to a unique random **12–63 character printable ASCII password without spaces**. This ignored file must never be published. The password protects both the Wi-Fi network and browser login; browser username: `admin`. The empty checked-in password disables the network.
2. Keep your existing `config.private.h` containing pairing keys and calibration. Both private files must accompany **every future build**. Settings are currently compiled into the application, not saved separately in NVS.
3. Build with the command above and upload over isolated USB using the existing wiring procedure. Keep **Default 4 MB with SPIFFS** (`PartitionScheme=default`): it contains two 1,310,720-byte application slots. Huge APP and No OTA schemes cannot support this workflow. Changing the partition layout later requires USB.

### Each wireless update

1. Build the receiver with those same private files and partition scheme. The upload file is **`firmware/build/receiver_s2/receiver_s2.ino.bin`**. Do not select a merged image, bootloader, partition table, transmitter, or servo calibration sketch.
2. Leave USB unplugged and power the car normally from its LiPo and buck. Raise the wheels and release the transmitter deadman. Check **both cells** with the meter and start with a charged, balanced pack. During initial setup, servos with unknown neutral must have their power disconnected.
3. Boot normally with **BOOT/0 released**, then hold that existing button for **three seconds**. Do not hold it while switching on or pressing RESET: that enters the ROM bootloader. A short press already disarms; the long press locks maintenance mode until restart.
4. Join **`SpyCar-Update`** on your laptop with your private password. Stay connected when warned there is no internet. Open **http://192.168.4.1/update**, log in as `admin`, choose `receiver_s2.ino.bin` in the **Firmware** section, and select **Update Firmware**. Leave the library page's **FileSystem** section alone; the car does not use filesystem updates.
5. Keep power connected until success and restart. The update network disappears; driving starts disarmed and requires the normal fresh deadman sequence. Failed uploads stay parked and can be retried while the network remains available.

The network has a five-minute window from entry. The library handles uploads synchronously, so an active or stalled request can extend that window. Timeout leaves driving locked and **does not disconnect battery power**. Restart to reopen the network; unplug the battery after use.

### Behavior and verification limits

Maintenance blocks incoming commands, stops ESP-NOW, and sets hardware PWM to calibrated neutral before starting the server. The bundled HTTPUpdateServer checks credentials and browser Origin before accepting an upload; Update writes to an inactive application slot and selects it on successful completion. We rely on these standard library behaviors and do not duplicate their parser or storage logic. Their checks cannot determine whether the selected application is the correct car program or free of bugs. Automatic rollback and signed firmware are not configured. Keep USB physically accessible for recovery.

With confirmed ADC calibration, opening update mode requires a valid reading of at least **7.4 V total pack voltage**. This is an entry check only: voltage is not monitored during the library's blocking upload. **Without confirmed ADC calibration there is no automatic update voltage check**; use the meter. Neither path monitors individual cells or disconnects power. Normal drive firmware still requires the existing calibrated sensing circuit; OTA does not remove it.

Calibrated servos can remain connected for routine OTA, but neutral is a command, not electrical isolation. PWM is interrupted during reboot. Verify the owned servos' behavior with wheels raised. The page uses HTTP within the password-protected local AP, not HTTPS; anyone given the password can replace the firmware.

Bench acceptance: verify button entry, neutral during uploading and reboot, wrong-password rejection, two successive successful updates, interrupted/wrong-file uploads, timeout remaining parked, and fresh arming after restart. Host tests and compilation do not establish these physical outcomes.

References: [Espressif HTTPUpdateServer](https://github.com/espressif/arduino-esp32/tree/3.3.11/libraries/HTTPUpdateServer), [Update](https://github.com/espressif/arduino-esp32/tree/3.3.11/libraries/Update), [ArduinoOTA alternative](https://github.com/espressif/arduino-esp32/tree/3.3.11/libraries/ArduinoOTA), [WEMOS schematic](https://docs.wemos.cc/en/latest/_static/files/sch_s2_mini_v1.0.0.pdf).

## Commissioning

1. **Start with servo power disconnected.** Upload the receiver and transmitter in their checked-in state. Their serial status reports the station MAC repeatedly. Keep the car's wheels off the floor during all remaining setup.
2. Copy each sketch's `config.h` to `config.private.h` in the same folder. The private file overrides the example and is ignored by Git. Put the transmitter station MAC in the receiver config and the receiver station MAC in the transmitter config. Keep the channel identical. Generate two independent random 16-byte values for PMK and LMK, put the same pair in both private files, and set `PAIRING_CONFIGURED=true`. Never upload the private files to GitHub.
3. Measure joystick center and both endpoints using the transmitter's raw serial readings. Update minima, centers, maxima, and directions. Power must remain 3.3 V. Adjust deadzone so the untouched stick consistently reads zero. Then set `JOYSTICK_CALIBRATION_CONFIRMED=true`.
4. Find the true neutral of each servo using a servo tester or the supplied `servo_neutral_s2` sketch. The bench sketch accepts serial lines such as `L1500` or `R1500`, emits that pulse for at most five seconds, then removes PWM. Only one output is active. Begin at 1500 µs and adjust in 1–2 µs steps within 1400–1600 until the shaft stops. Record the midpoint of its stopped band. This is an intentional powered bench test: removing PWM is not a guaranteed physical stop for every clone, so keep the switch reachable and turn off power after each test. Do not leave the bench sketch installed for driving.
5. Enter `LEFT_NEUTRAL_US` and `RIGHT_NEUTRAL_US` in the receiver private config. Confirm the units really are continuous-rotation servos. Restore the receiver sketch. Set `SERVO_CALIBRATION_CONFIRMED=true` only after the neutral measurements. Start with the limited ±180 µs range; verify direction with wheels lifted before trying the floor. Reverse a `*_DIRECTION` constant if necessary.
6. Assemble and verify the gated divider before connecting ADC3. With the receiver still unable to drive, compare displayed battery voltage with a multimeter and set `BATTERY_SCALE = meter_voltage / displayed_voltage`. If a known offset is measured, use `BATTERY_OFFSET_V`. Validate across the intended range, including around 7.0 V, then set `BATTERY_CALIBRATION_CONFIRMED=true`. A single point is an initial adjustment, not proof of accuracy across the range.
7. Rebuild and upload private configurations. With the stick centered, release the deadman, then press it while still centered. Move the stick only after that sequence. Release the deadman to stop. Confirm radio loss, transmitter reboot, and low-battery behavior while the wheels are lifted, then make a slow floor test.

Generate local keys, for example, with Python; the resulting values belong only in private config files:

```sh
python3 -c 'import secrets; print(", ".join("0x%02x" % b for b in secrets.token_bytes(16)))'
```

Run twice for independent PMK and LMK values. These are local pairing secrets, not credentials for any online service.

## Behavior and limits

The transmitter sends encrypted unicast commands every 20 ms. Both peers use an explicit MAC, fixed channel, PMK, and LMK. The receiver checks source MAC, packet size, magic, version, flags, bounds, session ID, and increasing sequence number. Radio reception only queues packets; control runs in the main loop, with at most eight packets handled per iteration. A queue overflow immediately requests neutral, discards the backlog, and disarms. A random session is generated at each transmitter boot. New sessions start disarmed.

Releasing the deadman immediately commands the calibrated neutral. A 250 ms command timeout disarms and requires a fresh release-and-centered, then press-and-centered sequence. A held deadman after reconnect cannot restart motion. A moved stick during an arming attempt cancels readiness. The transmitter has no return telemetry or armed indicator, so verify behavior during commissioning. Radio loss detection includes the main-loop scheduling interval; physical stopping distance depends on the servos and surface.

Normal PWM changes slew by at most 8 µs per 20 ms. Deadman, radio-loss, invalid-battery, and fault stops bypass that ramp and command neutral. Neutral PWM is a stop request; it does not disconnect servo power. Unplug XT30 for a definitive power stop; the optional EN switch is only standby. Missing PWM while unconfigured is also not a guarantee that every servo variant will remain still when powered.

Battery measurement enables GPIO7, waits at least 20 ms without blocking the drive loop, averages eight calibrated millivolt readings at ADC3, then disables the gate. It samples approximately every 100 ms. A reading below 7.0 V or above 8.6 V immediately disarms; one second continuously outside that range latches drive off until reset. The voltage is based on the 100 kΩ/33 kΩ divider and the user's calibration. This is a **2S pack early-stop aid**, not individual-cell monitoring, charger logic, current protection, or guaranteed undervoltage cutoff. The selected hardware protection remains necessary, and leaving the car powered after it stops still consumes battery energy.

The diagonal wheel geometry remains mechanically prone to scrub; electronic mixing does not remove that resistance. See [mechanics](../docs/mechanics.md).

## Host checks

```sh
TMPDIR=/private/tmp c++ -std=c++14 -Wall -Wextra -Werror -Ifirmware/libraries/SpyCarProtocol/src firmware/tests/drive_gate_test.cpp -o /private/tmp/spy-car-gate-test
/private/tmp/spy-car-gate-test
TMPDIR=/private/tmp c++ -std=c++14 -Wall -Wextra -Werror firmware/tests/maintenance_gate_test.cpp -o /private/tmp/spy-car-maintenance-test
/private/tmp/spy-car-maintenance-test
```

On Linux use `/tmp` instead of `/private/tmp`. Tests cover default inhibition, neutral arming, deadman release, timeout, duplicate/stale packets, new sessions, rearming, counter/timer wrap, packet validation, maintenance button timing and maintenance staying latched. These test our gates directly; they do not simulate the standard HTTPUpdateServer, RF, ADC accuracy, PWM timing, motors, or the power circuit.

API provenance: [Espressif ESP-NOW](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/network/esp_now.html), [Arduino-ESP32 LEDC](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html), [Arduino-ESP32 ADC](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/adc.html). The implementation is original code built against these documented interfaces.
