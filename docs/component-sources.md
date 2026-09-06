# Component geometry and evidence

Research date: 2026-09-05 (America/Los_Angeles). Dimensions are millimetres. A manufacturer outline is not an exact replica of a particular clone or purchased revision. Measure the owned parts before a final fit print.

## LOLIN S2 mini

[WEMOS official board documentation](https://docs.wemos.cc/en/latest/s2/s2_mini.html) specifies a **34.3 × 25.4 mm** board, 2.4 g, ESP32-S2FN4R2, 4 MB flash and 2 MB PSRAM. The [official V1.0.0 mechanical PDF](https://docs.wemos.cc/en/latest/_static/files/dim_s2_mini_v1.0.0.pdf) dimensionally confirms that outline; it also shows two 2 mm holes at 20.4 mm transverse spacing, with the left hole 2.5 mm from the edge. It does not dimension the holes' longitudinal position, PCB thickness, USB shell or component heights. Do not infer exact mounting geometry from a different “ESP32 mini” board name. Board-edge retention avoids relying on incompletely dimensioned holes.

The [official V1.0.0 schematic](https://docs.wemos.cc/en/latest/_static/files/sch_s2_mini_v1.0.0.pdf) shows ME6211C33 onboard 3.3 V regulation and direct VBUS connection to the 5 V header. It does not contain a LiPo charger, boost converter or servo power stage. GPIO runs at 3.3 V. Supply regulated 5 V at the board's 5 V/VBUS pin and common ground; disconnect external 5 V before plugging in ordinary USB power unless an explicit power-isolation arrangement has been installed.

**Geometry status:** board outline is manufacturer specified. Decorative packages, solder pads, connector dimensions and clearance volumes are modeling assumptions unless separately measured. Do not label the complete board model “exact.”

## IDC-681H camera from the video

Identification comes from the [creator's video description](https://www.youtube.com/watch?v=aJbycyJAl0k) and its [resolved camera listing](https://robu.in/product/idc-681h-25mw-40ch-vtx-600tvl-m7-fpv-camera/). The linked listing identifies the IDC-681H 25 mW 40-channel 600TVL M7 unit. The original retailer currently serves incomplete product content to research tools. No authoritative dimensional drawing or manufacturer electrical datasheet was located.

**Geometry status:** reserve an adjustable camera bay and use an explicitly provisional envelope. The CAD camera is not an exact replica. Confirm total lens-to-PCB depth, board width/height, mounting features, rear connector/wire bend space, antenna exit and button access after sourcing the unit. Do not print a tight friction socket from the provisional model.

**Electrical status:** the design budget provision of 0.25 A working / 0.35 A peak at regulated 5 V is a planning assumption. Verify the delivered module's permitted supply and measure actual current before connection. Never connect this provisioned camera directly to the 2S pack. Do not interpret the 25 mW radio output rating as electrical input consumption.

A manufacturer-documented fallback is the [Eachine TX06](https://www.eachine.com/Eachine-TX06-700TVL-FOV-130-Degree-5_8Ghz-40CH-Smart-Audio-Mini-FPV-Camera-AIO-Transmitter-For-RC-Dr-p-1418.html): 25 mW, 700TVL, 3.3–5.5 V input. Its official page lists both 280 mA working current and 40 mA at 3.7 V, so use the higher figure as the preliminary budget and verify the delivered unit. This fallback is a different camera and requires its own fit check; it is not evidence for IDC-681H geometry.

## MG90S-style continuous servos

The two owned units are the controlling mechanical reference. “MG90S” alone does not establish a continuous-rotation variant, spline count, body/ear dimensions, neutral pulse, stall current or clone manufacturer. Confirm continuous rotation on the bench; obtain dimensions from calipers and retain the supplied horn/center screw interface. Treat the visual servo model as a dimensional proxy until the recorded dimensions match the physical units. Exact manufacturer claims for a positional MG90S must not be applied to an unidentified 360-degree version.
