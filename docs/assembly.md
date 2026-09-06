# Prototype printing and assembly

This is an **unbuilt fit prototype**. The meshes have been generated in Blender; neither a slicer preview nor a physical print/drive test has been completed. Hardware dimensions and the exact continuous-servo variant still require the [measurement checklist](measurement-checklist.md). Read [mechanics.md](mechanics.md), [power.md](power.md), and [wiring.md](../electronics/wiring.md) before assembly.

## Print files and orientation

STLs are in millimetres and already placed at Z=0 in the intended orientation. Import at 100% scale. Do not apply the assembly model's world coordinates to the individual STLs.

| Order | File in `stl/` | Quantity | Build-plate face |
| --- | --- | --- | --- |
| First | `08_fit_coupon.stl` | 1 | Broad flat underside |
| 1 | `01_chassis.stl` | 1 | Flat chassis underside; posts upward |
| 2 | `04_skid_foot.stl`, `05_skid_foot.stl` | 1 each | Flat mounting flange down; dome upward |
| 3 | `06_drive_wheel.stl`, `07_drive_wheel.stl` | 1 each | Flat outer wheel face down; horn recess upward |
| 4 | `02_electronics_deck.stl` | 1 | Flat deck underside; support rails upward |
| 5 | `03_camera_cradle.stl` | 1 | Flat cradle underside; open side upward |

Start with PLA for a fit prototype or PETG for the assembled chassis, a 0.4 mm nozzle, 0.2 mm layers, four walls, five top/bottom layers, and approximately 25% infill. Use the same material and slicer profile for the coupon and mating parts. These are starting settings, not demonstrated strength or printability results. Inspect every part in the slicer: the posts need continuous perimeter walls, the wheel slots must remain open, and the cradle's small horizontal strap openings may need bridging or localized support. The convex skid surface will show layer steps; smooth it before fitting optional PTFE wear tape. Do not sand parts while installed near the battery or electronics.

The coupon provides a 13.4 × 24 mm nominal rectangular opening and five holes of 1.6, 1.8, 2.0, 2.2 and 2.4 mm diameter in order along its row. Identify that order in Blender before testing. It checks printer fit and screw pilot behavior; it is not a complete servo pocket or horn mating test. Print one wheel separately to validate the actual horn fit.

## Nominal fasteners and retention

Lengths below are measured under the screw head. Printed pilot holes are not modeled threads. Use small pan-head plastic-tapping screws, or properly tap a coupon and use matching machine screws. Do not treat an M2 machine screw and an arbitrary 2 mm tapping screw as interchangeable. Calibrate the chosen fastener on the coupon; enlarge a pilot carefully only when necessary.

| Joint | Quantity | Initial hardware choice | Nominal engagement and limitation |
| --- | --- | --- | --- |
| Upper deck to chassis posts | 4 | 2 mm diameter × 6 mm plastic-tapping screws | Through 2.5 mm deck into about 3.5 mm of post; modeled pilot diameter 1.7 mm |
| Skid feet to chassis | 2 | 2 mm diameter × 6 mm plastic-tapping screws | Insert from inside chassis, through 3 mm floor into about 3 mm of foot; modeled pilot diameter 1.6 mm; longer screws risk breaking through the dome |
| Camera cradle to deck nose | 2 | 2 mm diameter × 5 mm plastic-tapping screws | Insert upward from beneath the deck, through 2.5 mm deck into 2.5 mm cradle floor; pilot diameter 1.7 mm; tips must not protrude into camera space |
| Printed wheel to purchased horn | At least 2 per wheel | Small through-bolts, washers and locknuts matched to the actual horn; M1.6 × 8 mm is only a starting candidate | Nominal web 4.4 mm + representative horn 1.2 mm = 5.6 mm before washer/nut; verify horn hole clearance, engagement, shaft/case clearance and weight balance |
| Purchased horn to servo shaft | 1 per servo | Original supplied center screw | Retain the original pitch and length; do not substitute a generic M2 screw |

The modeled horn holes are illustrative. Do not force an M1.6 bolt through a smaller supplied hole. Choose compatible hardware after measurement; modify the printed wheel rather than assuming the horn is safe to drill. Use opposite horn holes and place any protruding hardware where a full rotation clears the case. The 5 mm wheel center access hole is for the screwdriver, not a printed spline.

Allow at least four approximately 2.5 mm-wide nylon ties for the two servos, soft approximately 5 mm-wide straps for the battery slots, and narrow ties/straps for the boards and auxiliary parts. Use thin insulating foam or other suitable electrical insulation beneath boards and a soft approximately 1 mm pad below the pouch. Select strap thickness to fit the slots. Keep buckles away from the pouch, components and moving wheels. Do not tighten a rigid tie directly against an unpadded LiPo pouch.

## Assembly sequence

1. **Print and check the coupon.** Check the selected screws by hand and measure printed openings. Update core envelopes in `cad/parameters.json` and the corresponding mating geometry in `cad/build.py` as needed; layout coordinates and detailed mounts are not all automatic. Regenerate and recheck before printing the chassis.
2. **Dry-fit the bare parts.** Remove sharp edges and debris. Check that the flat deck rests on all four posts and that neither servo touches a post. Confirm ear clearance at the notches in the servo stop walls. Do not install the battery during drilling, tapping or trimming.
3. **Install both skid feet.** Place each flat flange against the chassis underside and insert its screw from above. Tighten lightly. The dome tips and nominal 34 mm drive wheels should contact the same level plane; final adjustment depends on printer error and grip bands.
4. **Restrain the servos.** Set the front-left and rear-right servos on the chassis in the orientations shown in `cad/diagonal-spy-car.blend`. Thread two independent ties per servo through the paired floor slots and over its body. Keep ties clear of the mounting flange and harness exit. They should prevent case movement without crushing the housing.
5. **Fit the horns and wheels.** With the pack disconnected, bolt each printed wheel flat against its supplied horn. Seat the horn on the servo spline and install the original retaining screw through the center access hole. Rotate each wheel fully by hand without forcing the servo gears. Check screw ends, case clearance and wobble. Add modest-grip bands only after the basic fit works.
6. **Install the lower auxiliary hardware.** Secure and insulate the voltage-sense perfboard, capacitors, fuse and connectors in the reserved volumes. The rendered auxiliary shapes are packaging allowances, not fabricated circuit boards. Keep capacitor bodies from resting on unsupported leads and cover all exposed supply joints. Route the fuse and connector leads without entering either wheel's sweep. The balance connector must remain insulated and accessible for external balance charging.
7. **Wire and calibrate off the battery.** Follow `electronics/wiring.md` and `docs/power.md` using the specified commissioning process. Program the S2 before securing its strap. The packed layout does not reserve a straight USB cable insertion corridor: release and lift the S2 for USB programming, with external battery power disconnected. Do not pry a connector against the regulator.
8. **Assemble the upper deck while accessible.** Attach the camera cradle using the two upward-facing screws from below; then place insulated boards on their support rails and strap them without touching switches, USB or antenna traces. Fit the camera with soft padding and its retention strap. Verify camera power requirements before plugging it in. Keep its antenna and ventilation clear.
9. **Install the padded, removable battery.** Route the soft straps before closing the deck. Hold the pack firmly enough to prevent sliding, with no sharp object or screw tip pointing at the pouch. Leave the XT30 disconnect reachable and enough slack to remove the pack without pulling solder joints.
10. **Close and inspect.** Fit the four deck screws. Confirm no trapped wires, trapped balance lead, loose metal, wheel contact or battery compression. Check the four contact points on a flat surface; shim supports gently if needed without unloading either powered wheel.
11. **Commission with the wheels raised.** Perform polarity, regulation, low-voltage behavior, neutral, direction and radio failsafe checks from the electrical documentation. Only then attempt a slow smooth-floor test. Measure turn current and inspect heat, screw retention and body movement. This diagonal layout must scrub sideways to turn, so successful straight driving does not validate turning.

Keep the pack removable and use the specified external balance charger. This assembly does not add onboard charging. Record measured dimensions, chosen fastener details, print settings and test results before describing a later revision as build-tested.
