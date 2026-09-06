# Battery and power design

Design proposal; **not electrically bench-validated**. Sources checked 2026-09-05 (Pacific time). Prices exclude shipping/tax and are snapshots. The actual continuous-rotation MG90S variants and camera must be measured before the power design is released as a tested build.

## Recommendation

Use a removable **Tattu 450 mAh 2S 75C long battery**, part **TA-75C-450-2S1P-L-XT30** / SKU **TAA4502S75X3L**, and a **Pololu D30V30MALCMA, item 4872**, adjusted to **5.00 V**. Charge the removed pack with a **SkyRC B6neo SK-100198** balance charger. The servo already contains its motor driver: no external H-bridge or ESC is needed for a continuous-rotation servo. A voltage regulator is needed; a custom PCB is not needed for this prototype.

The battery manufacturer lists **61 × 16 × 15 mm**, **28.4 g**, **7.4 V nominal**, an XT30 discharge connector and a three-contact JST-XH balance connector. Its page showed **$7.22** and stock **>100**. The pack is rated well above the few amperes expected here; the connector/wiring/regulator remain separate limits. This is an ordinary 4.2 V/cell LiPo, not LiHV. [Tattu product page](https://www.genstattu.com/tattu-450mah-7-4v-75c-2s1p-lipo-battery-pack-with-xt30-plug-long-size-for-h-frame.html)

The regulator measures **15.2 × 25.4 × 9.0 mm**, has adjustable output and adjustable undervoltage cutoff, and includes reverse-input, overcurrent and thermal protections. It was listed **$39.95**, rationed/backorders allowed; immediate dispatch is not confirmed. Its 3.4 A headline rating is not a universal limit. The manufacturer's 5 V curve is approximately **3.7–3.9 A at 6–8.4 V input**, in open still air at room temperature. Enclosure performance requires testing. [Pololu 4872](https://www.pololu.com/product/4872), [current curve](https://a.pololu-files.com/picture/0J12632.600.png), [dimension drawing](https://www.pololu.com/file/0J2035/d30v30max-fine-adjust-step-down-voltage-regulator-dimensions.pdf)

CAD battery cavity target: **66 × 20 × 19 mm**, plus a distinct cable/connector pocket; this clearance is a design allowance, not a manufacturer tolerance guarantee. Use a strap and soft padding, never screws or a tight interference fit against a pouch cell. Reserve **18 × 28 × 12 mm** for the regulator with underside clearance and airflow. The board has components on both faces. These are nominal component/envelope models, not verified replicas of purchased specimens.

## What the power controller does

| Function | Prototype implementation |
|---|---|
| Motor direction/speed | Electronics inside each continuous-rotation servo; ESP32 sends its control pulse |
| Battery voltage conversion | Pololu 4872 converts 2S voltage to a shared 5 V supply |
| Hard OFF | Unplug the accessible XT30 connector |
| Optional standby | Small switch between regulator EN and GND; this does not physically disconnect the battery |
| Charging/balancing | External SkyRC balance charger, battery removed from car |
| Hardware low-pack cutoff | Pololu cutoff adjusted and verified at 6.2 V, as a last-resort backup |
| Normal low-battery operation | Stop at about 7.0 V pack / 3.5 V per cell; monitor during prototype use |
| Per-cell protection | Not built into the selected RC pack or regulator; see limitations below |

Avoid an ordinary tiny slide switch in the main current path unless its **DC** current rating supports the measured load. An optional EN switch handles only a signal. Always unplug after use, including after a low-voltage shutdown.

## Wiring

```text
2S battery XT30 + --> inline fuse --> regulator VIN
2S battery XT30 - ------------------> regulator GND
                                      |
                  regulator VOUT = 5.00 V
                      +---------------+---------------+
                      |               |               |
                left servo +    right servo +   ESP32-S2 Mini 5V/VBUS
                      |               |               |
                      +--- separate camera/VTX branch--+

All return wires meet at regulator GND / a soldered distribution point.
ESP32 signal pins --> servo signal wires, with shared ground.
Battery balance connector --> charger ONLY during charging / cell measurement.
```

Do not route servo supply current through the ESP32 board, USB connector, GPIO pins, 3.3 V regulator, or a solderless breadboard. Use a short soldered star harness, **22 AWG or thicker** stranded supply/return wires, insulated joints, and strain relief. Use a fuse close to the battery connector; **4 A nominal** is a starting design choice to validate against inrush and the actual wire/fuse time-current ratings, not servo overload protection. Choose a DC-rated fuse with interrupt rating suitable for a LiPo source. Do not alter the battery's original leads.

Add **1000 µF / 10 V** across 5 V/GND near the servo power split, and **100 µF / 10 V plus 100 nF** at the controller/camera branch. These are starting values to validate, not a cure for an undersized converter. A concrete bulk capacitor is Panasonic **EEUFR1A102**, **10 mm diameter × 16 mm body**, 5 mm lead pitch; allow lead bend/insulation clearance. [Panasonic component page](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1A102)

Give the camera its own supply/ground pair back to the star point. Add a suitably rated LC filter only if the powered video test shows motor noise; an arbitrary filter can create voltage drop or resonance. Keep camera RF antenna and ESP32 antenna away from motor leads and the switching regulator.

The genuine LOLIN S2 Mini schematic connects its USB VBUS and board power circuitry without a complete battery charger or a dual-source power mux. **Disconnect the car's 5 V feed to the S2 Mini before connecting powered USB for flashing**, and leave servo power off during that work. Verify clone boards separately. A battery attached to VIN must never touch the S2 Mini's 5 V or 3.3 V pins directly. [LOLIN schematic](https://www.wemos.cc/en/latest/_static/files/sch_s2_mini_v1.0.0.pdf)

## Current budget and runtime

These are engineering allowances, **not measured MG90S specifications**. Continuous-rotation servos sold under this name differ substantially. Do not borrow an unrelated positional MG90S stall-current number as a guarantee.

| 5 V load | Running assumption | Short peak allowance |
|---|---:|---:|
| Two servos | 2 × 0.25 A = 0.50 A | 2 × 1.20 A = 2.40 A |
| S2 Mini, Wi-Fi active | 0.15 A | 0.40 A |
| Tiny 25 mW camera + VTX | 0.25 A | 0.35 A |
| **Total** | **0.90 A** | **3.15 A** |

At 3.15 A output, 5 V output, 6.2 V input and assumed 90% conversion efficiency, battery current is approximately **2.82 A**. A pack's high C rating does not make this test unnecessary. If the actual camera uses more power, update this table. Never substitute RF transmission power (25 mW) for its electrical input power.

Battery energy is 7.4 V × 0.45 Ah = **3.33 Wh**. With an assumed usable fraction of 80% and 90% conversion efficiency, load energy is about **2.40 Wh**. That predicts **32 minutes at 0.90 A average** or **19 minutes at 1.50 A average**, both on the 5 V rail. Early cutoff, friction, carpet, turning scrub, pack condition, radio duty cycle and camera power can shorten this. Treat **roughly 15–30 minutes** as a planning range, not a tested promise.

## Low-voltage setup and its limits

The cutoff is **pack-level**, not a 2S battery-management system. An unbalanced pack can have one low cell even when its total looks acceptable. Balance charge every time, measure both cells before use, stop if cells diverge, and remove the battery when finished. Normal operating target is **at least 3.5 V/cell under load**. The manufacturer advises 3.5 V/cell for Tattu UAV operation and specifies never going below 3.0 V/cell under load. [Tattu battery guidance](https://www.genstattu.com/bw/)

The regulator cutoff has unusually large restart hysteresis: its EN threshold is typically 0.85 V with approximately 0.20 V hysteresis. Restart voltage is therefore approximately `cutoff × (1 + 0.20 / EN_threshold)`. A 6.2 V cutoff typically restarts around 7.66 V, while threshold variation can put it near 8.11 V. **A 7.0 V hardware cutoff can prevent startup even on a fully charged 8.4 V pack.** This is why 6.2 V is only the backup, with earlier normal stopping. Actual thresholds must be measured. [Pololu cutoff procedure](https://www.pololu.com/product/4872)

With loads disconnected, use an adjustable supply and a multimeter to set VOUT to 5.00 V, set/verify falling cutoff at 6.2 V, and verify restart at no more than the fully charged pack voltage. Pololu also gives a multimeter-only threshold calibration method when a variable supply is unavailable; use its measured EN threshold rather than assuming 0.85 V. The original B6neo's digital-power mode can serve as the variable supply for this low-load calibration when used with the proper output cable. Recheck VOUT after adjustment and before connecting any electronics.

The design now includes a GPIO7-controlled **BS250P / 2N3904 high-side sensing switch**, a 100 kΩ / 33 kΩ divider, and a 100 nF filter into GPIO3. See the exact net table and commissioning sequence in [wiring.md](../electronics/wiring.md). The pull-up/pull-down network defaults sensing OFF when MCU power disappears, avoiding a sustained battery-fed ADC path; verify actual power-off behavior. Firmware enables sensing, waits at least 20 ms, reads/calibrates pack voltage and disables sensing again. The normal stop is 7.0 V; it still cannot identify an individual weak cell. Measure both cells during supervised prototype operation and stop if cells diverge. For unattended discharge protection, add a properly rated per-cell protector or a purpose-designed power board.

## Charging

Choose the **original SkyRC B6neo SK-100198** or an already-owned equivalent that explicitly supports 2S LiPo balance charging at **0.4 A or less**. B6neo supports 1–6S lithium packs, balance/storage modes, USB-C PD power and 0.2–10 A charge current. It is an external bench tool, **70 × 50 × 31 mm**, not part of the car. Connect its main output through a polarity-checked XT60-to-XT30 charging adapter and also connect the three-pin balance lead using the charger's documented 2S alignment. Supply it with a compatible USB-C PD adapter/cable; a plain 5 V USB supply is not sufficient for the original model's PD input specification. [SkyRC specifications](https://www.skyrc.com/b6neo-series), [original B6neo manual](https://www.skyrc.com/download/100198%20B6neo%20Instruction%20Manual%20V1.0_231206.pdf)

Set **LiPo / 2S / balance charge / 4.20 V per cell / 0.4 A**. 0.4 A is below 1C for a 450 mAh pack. Remove the pack from the printed car and supervise charging on a nonflammable surface. Use the charger's storage mode for storage; do not charge a swollen, damaged or unbalanced pack. No onboard charger, TP4056 board or charge-and-drive feature is needed. A TP4056 is a 1S charger and cannot charge this 2S battery.

## Why not a 1S build?

| Choice | Assessment |
|---|---|
| 1S directly into servo + board | 3.0–4.2 V is below the intended 5 V rail; inconsistent servo behavior and regulator dropout are likely. Not the baseline. |
| 1S high-discharge pack + proper boost | Feasible, potentially flatter, but at 5 V/3.15 A, 3.3 V battery and 85% efficiency it needs **5.6 A battery current**. Requires a converter rated at low input voltage plus appropriate connector, cell protection and charger. |
| 1S generic protected 1200 mAh hobby cell + small USB boost | Not an acceptable automatic substitution. The Adafruit 1200 mAh example has 2 A-rated cables, below this design's possible boost input demand. [Example battery](https://www.adafruit.com/product/258) |
| **2S high-discharge pack + 5 V buck** | **Selected**: less input current, narrow battery shape, hardware cutoff available, straightforward external balance charging. |

A cheaper fixed 5 V buck may work electrically but does not automatically provide appropriate low-battery cutoff. The compact Pololu S9V11 cutoff boards have only up to 1.5 A output in buck operation and a 700 mA startup limit, so they are not a substitute for the selected power stage. [Pololu S9V11 example](https://www.pololu.com/product/2870)

## Bench acceptance before printing the final chassis

1. Confirm both servos rotate continuously and identify neutral pulses with wheels lifted; reject a positional or multi-turn positional substitute.
2. Verify polarity, 5.00 V output, hardware cutoff and restart before connecting the electronics.
3. Measure no-load, driving and brief startup/reversal currents; do not hold tiny servos stalled. Test full battery and a 6.5–7.0 V supply. Use a current-limited supply first.
4. Exercise both servos and the camera while transmitting Wi-Fi. Check for ESP32 resets, video breakup and voltage dips at the servo and MCU connectors. A scope is preferable for short dips that a multimeter can miss.
5. Run a thermal test in the proposed enclosure at realistic worst continuous load. Keep air around the regulator. If the rail droops, resets or overheats, change the power design before road use.
6. Record per-cell battery voltage and measured runtime; revise the estimated table using those measurements.

A soldered harness and off-the-shelf modules suit a basic soldering kit. A custom PCB becomes worthwhile only after fit/current testing, or if integrated per-cell cutoff, gated sensing, a real power button, USB power-source isolation or compact onboard balancing is required. It is not needed to get this first car rolling.
