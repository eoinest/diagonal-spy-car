# Measurements needed to turn the reference CAD into an exact fit

The component models are nominal reference models. Fill this sheet from the actual parts before locking mounting holes and printing the complete car. A cheap digital caliper, ruler, and multimeter are useful additions to the printer and soldering kit. Record millimetres unless stated otherwise.

## MG90S units (measure both separately)

| Measurement | Left servo | Right servo | Why it matters |
| --- | --- | --- | --- |
| Vendor / label / purchase link | | | Distinguishes continuous variants and clones |
| Body length excluding ears | | | Cradle fit |
| Body width | | | Cradle fit |
| Rectangular body height | | | Do not confuse with total shaft height |
| Total height to shaft top, no horn | | | Wheel axle and hub clearance |
| Mounting-ear overall length | | | Bracket envelope |
| Mounting-ear thickness and vertical offset | | | Bracket seating |
| Ear hole diameter and center spacing | | | Fastener locations |
| Shaft center to near end of body | | | Wheel position |
| Shaft center to side face | | | Wheel position |
| Boss diameter and height | | | Wheel/horn clearance |
| Horn shape, diameter or arm length | | | Printed wheel pocket |
| Horn thickness and center boss depth | | | Wheel offset and retaining-screw access |
| Useful horn hole diameters / radial positions | | | Wheel fasteners |
| Original center-screw length and head diameter | | | Engagement and tool access |
| Cable exit position, plug size, cable length | | | Routing and strain relief |
| Weight with usable cable and horn (g) | | | Balance and battery estimate |

Place a ruler in photographs of the top, bottom, and side if recording visual detail. Photographs help model features; calipers establish fit-critical dimensions. Do not infer precise millimetres from a perspective photograph.

## S2 mini

| Measurement | Actual value |
| --- | --- |
| Exact manufacturer and PCB revision | |
| PCB length, width, thickness | |
| Corner shape / radius | |
| Header installation: bare, pins, sockets | |
| Header pitch and row offsets | |
| Tallest part above and below PCB | |
| USB-C overhang, width, height | |
| Cable plug envelope and usable insertion direction | |
| Reset and boot button clearance | |
| Antenna end and nearby keep-clear region | |

Use the [official v1.0.0 dimension drawing](https://www.wemos.cc/en/latest/_static/files/dim_s2_mini_v1.0.0.pdf) only after confirming the board matches it. The official board size is a good reference; clone connectors, buttons, and header heights may differ.

## Battery, power parts, and FPV module

| Measurement or check | Actual value |
| --- | --- |
| Battery model and cell count | |
| Battery maximum stated dimensions including wrap | |
| Actual dimensions without squeezing the pouch | |
| Lead exit, connector type, polarity, cable length | |
| Balance connector access if a 2S pack is used | |
| Charger model and supported chemistry / cell count | |
| Regulator model, board dimensions, underside protrusions | |
| Switch and fuse-holder body / panel dimensions | |
| Camera model and voltage range printed on product | |
| Camera PCB, lens barrel and connector envelopes | |
| VTX board and antenna envelope | |
| Camera view unobstructed by body or wheels | |

Do not substitute a battery because its nominal voltage and connector look similar. Chemistry, cell count, discharge rating, charge method, and connector polarity must match the power design.

## Fit and function log

| Test | Result / change needed |
| --- | --- |
| Printer, material, nozzle, layer height | |
| Clearance coupon chosen | |
| Servo-to-bracket fit and positive restraint | |
| Horn and printed wheel concentricity | |
| Screw engagement and wheel case clearance | |
| All four ground contact heights | |
| Full assembled mass (g) | |
| Neutral pulse width for each servo (µs) | |
| Verified continuous rotation and direction | |
| Neutral, free-running, and loaded-turn current | |
| Radio-loss and deadman stop time | |
| Low-battery behavior | |
| Straight / left / right floor test | |

Leave unknown fields blank. Do not convert an unmeasured assumption into a claimed exact replica.
