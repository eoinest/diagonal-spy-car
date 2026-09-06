# Mechanical design and its limits

This is a dimensioned first prototype for two continuous-rotation micro servos driving the front-left and rear-right wheels. The other two corners need low-friction supports. The supplied CAD is an editable design and fit-check model; it is not an exact scan of the owner's components or a physically validated production chassis.

## What was found locally

A filename inventory searched `~/Documents/dev/playground`, then the wider `~/Documents/dev`, including hidden and ignored files while excluding dependency, build, and Git internals. No MG90S or S2 mini component CAD was found. Unrelated enclosure `.blend`, `.stl`, and `.scad` files existed outside playground. No existing component model was copied into this project. Files hidden inside archives or named without a recognizable CAD extension could still exist.

## Reference dimensions and fidelity

| Part | Published nominal dimensions | CAD confidence |
| --- | --- | --- |
| TowerPro MG90S reference | 22.8 × 12.2 × 28.5 mm; manufacturer's second table uses width 12.4 and height 28.4 mm | Reference envelope only; continuous-rotation clones can differ |
| LOLIN S2 mini v1.0.0 | PCB outline 34.3 × 25.4 mm | Manufacturer outline; verify actual board revision and installed headers |
| Servo horn, spline, screw | Use the horn and center screw supplied with each actual servo | Must measure; no assumed spline compatibility |
| Battery, regulator, camera | See BOM and power documentation | Mounts must match the ordered variant including wiring and connectors |

Sources: [TowerPro MG90S](https://towerpro.com.tw/product/mg90s-3/), [WEMOS S2 mini](https://www.wemos.cc/en/latest/s2/s2_mini.html), and [official S2 mini dimension drawing](https://www.wemos.cc/en/latest/_static/files/dim_s2_mini_v1.0.0.pdf).

The MG90S product name alone does not establish that a servo rotates continuously. Confirm that the owner's units have speed/direction control around a stopped neutral. The reference dimensions do not establish the body-only height, shaft offset, mounting-ear hole spacing, or spline geometry of those units. Any such CAD detail is an explicit modeling assumption until measured. A realistic render does not increase dimensional confidence.

## Diagonal drive means tire scrub during turns

The proposed front-left/rear-right arrangement preserves the requested layout. With conventional wheels pointing forward, it must skid sideways while turning. Adding casters at the other corners removes their steering resistance but does not remove the sideways scrub of the powered wheels.

This follows directly from planar rigid-body kinematics. Define forward as `x`, left as `y`, and yaw rate as `ω`. At each conventional wheel contact, the no-side-slip condition is:

```text
v_y + ω x_front = 0
v_y + ω x_rear  = 0
therefore ω (x_front - x_rear) = 0
```

When the powered wheels are separated front-to-back, both conditions can hold only for zero yaw. Any actual turn therefore needs lateral slip, compliance, or steering. For a turn around the midpoint, each wheel's lateral scrub speed is `|ω| × half the front/back separation`. Its commanded forward rolling speed depends on the left/right spacing. A long wheelbase and narrow track make scrub particularly severe. This is an engineering derivation, not a tested performance claim.

Build the diagonal arrangement as a smooth-floor experiment. Begin with narrow, modest-grip tire contact patches and slow acceleration. Check both turning directions because diagonal load transfer and servo mismatch can produce different behavior. A tire grippier than necessary increases turning load. Do not assume it will turn on carpet merely because it drives straight there.

Two conventional powered wheels on a shared transverse axle give normal differential drive and are the straightforward fallback if the diagonal prototype scrubs or stalls excessively. Another geometric solution keeps opposite-corner contacts but rotates both wheel planes so their common axle direction lies along the diagonal joining those contacts; the vehicle's rolling direction then changes relative to its rectangular body. Neither alternative is implemented automatically: choose a revised layout explicitly before modifying the chassis.

## Supports, weight, and height

Two diagonal contact points alone cannot form a stable support polygon. Use the two opposite corner supports shown in the prototype and keep the battery low, approximately central. All four contacts should meet a flat surface without unloading a drive wheel. Rigid four-point support can rock; adjust shims or use slightly compliant mounting to keep both powered wheels loaded. Avoid pushing on a LiPo pouch to obtain compliance.

A purchased ball caster is an optional upgrade from printed sliding feet. For example, the [Pololu 3/8-inch plastic ball caster](https://www.pololu.com/product/950) is approximately 10.2 mm tall without spacers, with approximately 13.5 mm hole spacing and included spacers for height adjustment. Its manufacturer supports #2 or M2 mounting hardware. Check the actual drawing and stock before adapting a mount. This part is not a drop-in promise for a generic printed foot, and a printed captured sphere should not be assumed to roll like a manufactured ball caster.

Match support contact height to the assembled wheel radius, hub offset, chassis thickness, and servo axis height. A nominal wheel diameter is not sufficient: tire compression and printer shrinkage change the final ride height. Leave clearance around rotating wheels and their horn screws, including small wheel wobble.

## Wheel attachment

Retain the original servo horn as the spline interface. Attach a printed wheel to that horn with two small through-fasteners or appropriately sized screws through measured horn holes. Keep a central access hole large enough to fit a screwdriver onto the original horn retaining screw. The small center screw retains the horn axially; the spline transmits motor torque. It must not be the only friction clamp driving an unsplined printed wheel.

Do not force a generic micro-servo wheel onto an MG90S shaft. For example, [Pololu's micro-servo wheel](https://www.pololu.com/product/4914) specifies a particular 21-tooth, 4.8 mm spline for compatible servos; that does not establish compatibility with these MG90S units. A purchased horn supplied with the servo avoids relying on a printer to reproduce tiny spline teeth.

Use two opposing horn holes when practical to reduce eccentricity. Print and test one wheel/horn coupon first. Adjust hole positions to the measured horn. Retain the original center screw and check engagement by hand; do not substitute an unverified screw length or pitch. Leave the wheel close to the case while maintaining clearance to reduce shaft bending load. Do not use glue as the only wheel retention.

## Assembly and print strategy

1. Measure the components using the [measurement checklist](measurement-checklist.md), then update the CAD parameters. Print small fit coupons before the full chassis.
2. Print the chassis and rigid brackets in PLA for the first fit check or PETG if desired. A 0.4 mm nozzle, 0.2 mm layers, four perimeters, and approximately 25% infill are initial slicing choices, not validated strength specifications. Orient broad flat faces on the bed; inspect the slicer's support and bridge preview.
3. Use the actual servo body as a fit gauge without forcing it into a tight pocket. Aim initially for approximately 0.25–0.40 mm clearance per mating side, adjusted for the printer and material. Strap mounts accommodate clone variation; positively restrain rotation and cable strain.
4. Secure the electronics using the designated retainers or removable straps, with an insulating layer under solder joints. Keep USB, reset/boot buttons, switch, charge disconnect, and horn screws reachable. Leave space at the S2 antenna end and around the camera/VTX for heat and wiring.
5. Mount the battery in a padded tray with a soft strap. Do not drive screws toward the pouch or clamp it rigidly. Keep the removable battery connector accessible.
6. Attach wheels, adjust support height, then test with wheels lifted. Confirm neutral, direction, failsafe, and supply behavior before a slow floor test.
7. After a short drive, inspect wheel screw retention, bracket movement, cable abrasion, servo temperature, turn behavior, and brownouts. Stop and revise the mount or geometry if a powered wheel binds, lifts, or stalls.

## Acceptance before calling the car build-ready

- Actual parts fit without stressing the battery, PCB, connectors, or servo case.
- Both powered wheels can rotate fully without chassis or wire contact.
- The chassis rests stably and both powered wheels retain traction.
- Forward, reverse, and both turns work on the intended floor at low speed.
- Lost radio contact and a released deadman stop motion promptly.
- Loaded turn current and battery/regulator temperature are measured within the selected electrical limits.

The last four items require real hardware. They cannot be certified by a Blender render or mesh validation.
