# What the reference project actually contains

Inspected 2026-09-05 (local time). Upstream commit: `067cbcc8ea202b5367174b04307b865cb0d397f4`.

The [Pro Know repository](https://github.com/proknowdiy/micro_rc_fpv_car_esp-now) inspired this project. Its README links [Making a Micro FPV RC Car - ESP NOW](https://www.youtube.com/watch?v=aJbycyJAl0k). Upstream has an MIT license. This repository independently models and documents a different chassis and electronics; no upstream CAD or firmware has been copied.

## Camera identified from the creator's links

The video's own description names DFRobot 2.5 g continuous servos and a 3.7 V, 200 mAh LiPo. Its camera link, `https://bit.ly/3z0JrOv`, resolves to [IDC-681H 25 mW 40CH VTX 600TVL M7 FPV camera](https://robu.in/product/idc-681h-25mw-40ch-vtx-600tvl-m7-fpv-camera/). Its receiver link, `https://bit.ly/3yJWRyk`, resolves to [EWRF 5.8 GHz UVC OTG Android AV phone receiver](https://robu.in/product/ewrf-5-8g-uvc-otg-android-av-phone-receiver/). These are evidence of the creator's product choices, not proof that every currently sold revision is identical.

This is an analog camera with an integrated 5.8 GHz video transmitter. Its video path is separate from the ESP32 control link. A compatible analog receiver/display is required; a phone needs compatible UVC/OTG hardware and software. It does not stream video through ESP-NOW.

## Important disagreement between the uploaded files

The [receiver sketch](https://github.com/proknowdiy/micro_rc_fpv_car_esp-now/blob/067cbcc8ea202b5367174b04307b865cb0d397f4/Code/Receiver_with_elevon_mix/Receiver_with_elevon_mix.ino) controls two servos on GPIO27/26 with 1000–2000 microsecond pulses and a one-second loss-of-signal timeout. Those pin assignments are not portable to the S2 mini.

However, the [receiver BOM](https://github.com/proknowdiy/micro_rc_fpv_car_esp-now/blob/067cbcc8ea202b5367174b04307b865cb0d397f4/PCB%20Files/Receiver/BOM_ESP-WROOM-32-ESP-NOW-RECEIVER_2025-07-04.csv) specifies an MX1508 motor driver, ESP32-WROOM module, AMS1117-3.3 regulator, capacitors, resistors and a BZV55C5V6 zener. The [receiver schematic](https://github.com/proknowdiy/micro_rc_fpv_car_esp-now/blob/067cbcc8ea202b5367174b04307b865cb0d397f4/Diagram/Schematic_ESP-WROOM-32-ESP-NOW-RECEIVER_PCB.pdf) has bare motor outputs, a misleading “L293D” section title, and a TC1508A alternative note. Its power circuit contains an AMS1117 and a resistor/zener branch, not a boost converter. The resistor/zener branch labeled +5V cannot supply the proposed servos.

The published schematic/BOM show no charger, battery protection, or undervoltage cutoff. They are not a validated, directly reusable power design for this car. The continuous servos contain their own motor drive electronics; an external MX1508 is unnecessary. Use the independent power design in [power.md](power.md).
