# Validation and remaining physical checks

Revision 0.1 is an unbuilt design. No physical replica comparison, print fit, load test, battery runtime, camera reception or driving result is claimed.

## Digital checks

- Blender 5.2.1 LTS generated both reference and assembly `.blend` files, eight binary millimetre STLs and three renderings.
- `cad/mesh-report.json` records dimensions, closed manifold edges and positive volume for each exported part.
- `scripts/verify_artifacts.py` independently parses STL bytes, checks edge incidence, connected shells and Z=0 print placement; also checks BOM shape and relative Markdown links. Its output is `cad/artifact-report.json`.
- `scripts/validate_blender.py` checks Boolean intersections of printed parts with the modeled nominal hardware and other printed parts. Its output is `cad/clearance-report.json`. This excludes illustrative wires/details and does not certify real hardware tolerances or dynamic wheel screw clearance.
- Host C++ tests exercise the radio drive state gate: inhibition, arming, deadman, stale packets, timeout, session changes and sequence wrap. Board compilation results are recorded below after the target checks run.
- No slicing or extrusion simulation was performed. Import each STL into your own slicer and inspect layers/scale/orientation before printing.

## Before finalizing the mechanical design

1. Record the owned servo bodies, ears, output-axis positions, original horn shapes and screws in [measurement-checklist.md](measurement-checklist.md).
2. Confirm which S2 mini revision is owned and the actual header/connector heights.
3. Obtain the actual IDC-681H dimensions and permitted supply voltage. Replace the provisional camera envelope; adjust its padded cradle.
4. Check the selected fuse, connectors and completed sense board fit the reserved volumes with insulation and lead bend space.
5. Print the coupon and a single wheel. Establish the chosen screw fit and verify the horn lies flat against its wheel.
6. Check all four contact points, the full wheel/screw sweep and access to the battery disconnect. Nominal dimensions are not tolerance-stack validation.

## Before driving

Follow the staged steps in [wiring.md](../electronics/wiring.md) and [power.md](power.md). Measure 5 V regulation, backup cutoff and restart, battery ADC scale, and each cell separately. Verify the gated ADC input is not held high when board power disappears. Confirm servo neutral and direction with raised wheels and start with a current-limited supply.

Verify release-to-stop, transmitter power loss, receiver restart, stale packet behavior and battery stop. Measure straight and turning current with the full payload. Abort a stalled or overheating turn; diagonal steering requires wheel scrub and cannot be assumed to work on carpet. Check camera image/noise while driving and confirm regulator temperature with the assembled layout.

Keep the 2S pack removable for balance charging. Pack-level sensing does not detect a weak individual cell and is not a BMS. A later unsupervised or enclosed revision needs a deliberate protection design and validated thermals; none is certified by these files.

## Board compilation

Verified on macOS with Arduino CLI **1.5.2-rc.1** and Espressif Arduino-ESP32 **3.3.11**. All three checked-in sketches compiled and linked successfully with their default, disabled commissioning configuration:

| Sketch | Target FQBN | Flash bytes | Static RAM bytes |
|---|---|---:|---:|
| `receiver_s2` | `esp32:esp32:lolin_s2_mini` | 867374 | 72936 |
| `transmitter_esp32` | `esp32:esp32:esp32` | 889140 | 45536 |
| `servo_neutral_s2` | `esp32:esp32:lolin_s2_mini` | 301995 | 49096 |

The final receiver was rebuilt after review fixes. Host state-gate tests passed, including the exact 249/250 ms timeout boundary. No firmware was flashed to physical hardware. `TMPDIR=/private/tmp` was used for the macOS sandbox compilation environment; normal installations can follow the portable commands in [firmware/README.md](../firmware/README.md).
