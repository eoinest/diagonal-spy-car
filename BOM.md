# Historical bill of materials

> **Historical BOM — do not order this list for the current build.** This table records the original camera-equipped Tattu/Pololu proposal and is retained for design history. The current camera-free build uses the owned LM2596-style buck and a Lumenier 300 mAh 2S XT30 pack. Use the [current camera-free BOM](electronics/camera-free-bom.csv), [current wiring](electronics/wiring.md), and [picture wiring guide](output/pdf/spy-car-wiring-guide.pdf). The old camera, Pololu cutoff/enable switch, capacitor choices and subtotal below are not the current selection.

Research snapshot: 2026-09-05. Quantities cover one car plus one radio controller. Owned parts are marked. Prices exclude shipping/tax and are not a complete project total. Generic hardware dimensions must be checked before buying.

| Ref | Qty | Item / part | Status | Price USD | Source |
|---|---:|---|---|---:|---|
| BAT1 | 1 | Tattu 450mAh 2S 75C long LiPo — TA-75C-450-2S1P-L-XT30 | yes | 7.22 | [source](https://www.genstattu.com/tattu-450mah-7-4v-75c-2s1p-lipo-battery-pack-with-xt30-plug-long-size-for-h-frame.html) |
| U_PWR | 1 | Adjustable buck regulator with low-voltage cutoff — Pololu D30V30MALCMA item4872 | yes | 39.95 | [source](https://www.pololu.com/product/4872) |
| C_BULK | 1 | 1000uF 10V low-ESR radial electrolytic — Panasonic EEUFR1A102 | yes | — | [source](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1A102) |
| C_LOGIC | 1 | 100uF 10V radial electrolytic — Select stocked equivalent | yes | — | Select locally |
| C_BYPASS | 1 | 100nF ceramic 16V or higher — Select stocked through-hole equivalent | yes | — | Select locally |
| J_BAT | 1 | XT30 mating connector with 22AWG or thicker pigtail — AMASS-compatible keyed XT30 mate | yes | — | Select locally |
| F_IN | 1 | Inline DC fuse nominal4A plus insulated holder or leaded assembly — Select DC-rated part after inrush test | yes | — | Select locally |
| HARNESS | 1 | Stranded22AWG supply wire and soldered distribution harness — Hookup wire / heatshrink / strain relief | yes | — | Select locally |
| SW_EN | 1 | Small SPST switch across regulator EN-GND — Generic low-current signal switch | optional | — | Select locally |
| CHG1 | 1 | 2S-capable balance charger with low-current setting — SkyRC B6neo SK-100198 | yes_unless_owned | — | [source](https://www.skyrc.com/b6neo-series) |
| CHG_ADAPTER | 1 | XT60 charger-output to XT30 battery adapter — Polarity-checked mating lead | yes_unless_owned | — | Select locally |
| CHG_SUPPLY | 1 | Compatible USB-C PD supply and cable — 12-20V PD support for original B6neo | yes_unless_owned | — | [source](https://www.skyrc.com/b6neo-series) |
| DMM | 1 | Digital multimeter with DC voltage and current measurement — User-owned or suitable meter | yes_unless_owned | — | Select locally |
| LIPO_BAG | 1 | LiPo charging and storage bag — Select reputable bag | recommended | — | Select locally |
| QP_SENSE | 1 | Through-hole P-channel MOSFET battery-sense switch — Diodes BS250P | yes | 1.75 | [source](https://www.diodes.com/datasheet/download/BS250P.pdf) |
| QN_SENSE | 1 | Through-hole NPN battery-sense gate driver — onsemi 2N3904BU | yes | — | [source](https://www.onsemi.com/download/data-sheet/pdf/2n3904-d.pdf) |
| R_SENSE_100K | 3 | 100k ohm1percent axial resistor — Stocked metal-film equivalent | yes | — | Select locally |
| R_SENSE_33K | 1 | 33k ohm1percent axial resistor — Stocked metal-film equivalent | yes | — | Select locally |
| R_SENSE_10K | 2 | 10k ohm axial resistor — Stocked metal-film equivalent | yes | — | Select locally |
| C_SENSE | 1 | 100nF ceramic16V or higher — Stocked through-hole equivalent | yes | — | Select locally |
| PROTO_SENSE | 1 | Insulated perfboard for switched sensing and divider — Small cuttable perfboard | yes | — | Select locally |
| M_FL_RR | 2 | Owned MG90S-style 360 degree continuous servos — Exact owned variant TBD | owned | — | [source](https://towerpro.com.tw/product/mg90s-3/) |
| MCU_RX | 1 | LOLIN WEMOS S2 mini — ESP32-S2FN4R2 S2 mini V1.0.0 | owned | — | [source](https://www.wemos.cc/en/latest/s2/s2_mini.html) |
| CAM1 | 1 | Creator-linked analog FPV AIO camera — IDC-681H 25 mW 40CH 600TVL M7 | yes_for_FPV | — | [source](https://robu.in/product/idc-681h-25mw-40ch-vtx-600tvl-m7-fpv-camera/) |
| V_RX | 1 | Analog 5.8 GHz video receiver — EWRF 5.8 GHz UVC OTG Android AV receiver | yes_for_FPV | — | [source](https://robu.in/product/ewrf-5-8g-uvc-otg-android-av-phone-receiver/) |
| MCU_TX | 1 | Second ESP32 development board — Classic ESP32 DevKit assumed | owned_if_available | — | [source](https://docs.espressif.com/projects/arduino-esp32/en/latest/) |
| JOY1 | 1 | Two-axis spring-centered analog joystick — 3.3 V potentiometer joystick; exact module TBD | yes | — | Select locally |
| DEADMAN | 1 | Normally open momentary pushbutton — SPST button to GND | yes | — | Select locally |
| TX_POWER | 1 | USB power bank and board-compatible cable — User-owned USB source | yes_unless_owned | — | Select locally |
| SERVO_HORNS | 2 | Factory servo horns and original shaft screws — Supplied with owned servos | owned | — | Select locally |
| HORN_FIX | 4 | Wheel-to-horn fasteners — Choose matching factory horn screws or M1.6/M2 bolts + nuts | yes | — | Select locally |
| M2_DECK | 4 | Deck mount screws — 2 mm x 6 pan head plastic-tapping screws or coupon-verified M2 | yes | — | Select locally |
| M2_SKID | 2 | Skid mount screws — 2 mm x 6 pan head plastic-tapping screws or coupon-verified M2 | yes | — | Select locally |
| M2_CAM | 2 | Camera cradle screws — 2 mm x 5 pan head plastic-tapping screws or coupon-verified M2 | yes | — | Select locally |
| TIES | 12 | Nylon cable ties — Approximately 2.5 mm wide; 100 mm long | yes | — | Select locally |
| FOAM | 1 | Thin nonconductive foam and insulation — 0.5–1 mm foam plus polyester/Kapton insulation | yes | — | Select locally |
| VELCRO | 1 | Camera retention strap — Thin strap through 2.5 mm side windows | yes | — | Select locally |
| PTFE | 1 | Low-friction skid contact tape — Thin PTFE tape | recommended | — | Select locally |
| PRINT | 1 | Eight supplied STLs — PETG or PLA; 0.4 mm nozzle | yes | — | Select locally |
| CALIPER | 1 | Digital caliper — 0.1 mm or better useful resolution | yes_unless_owned | — | Select locally |

The verified-price subtotal for the battery, buck regulator and BS250P is **$48.92**. Camera, charger, viewing hardware, connectors and consumables are additional. Check current stock: the Pololu regulator was rationed/backordered at research time.

See [BOM.csv](BOM.csv) for dimensions and per-row notes, [power design](docs/power.md), [wiring](electronics/wiring.md), and [assembly](docs/assembly.md).
