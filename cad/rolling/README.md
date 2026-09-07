# Integral printed axles and press-fit wheels — revision 0.4

The axles are now **part of the chassis itself**. One continuous printed solid includes the base, two axle supports, two solid bearing journals, their inner-ring shoulders, and four clips that retain the servo tabs. The earlier metal axle screws, nuts, bearing caps, cap screws and separate spacers have been removed.

The only purchased mechanical components for this stage are **the two owned servos and two MR83ZZ bearings**. The moving wheels are separate printed parts. Electronics are outside this mechanical-stage parts list; the powered-wheel horn interfaces remain a later step.

![One printed chassis, including both axles and all four servo clips](chassis-only.png)

## How the wheels fit

Each passive wheel has an **8.0 mm nominal bearing pocket**, 3.2 mm deep. The bearing outer ring is friction-fit into that pocket, against a ledge that touches only its outer rim. There is no retaining cap. The bearing inner ring is friction-fit onto the chassis's **3.0 mm nominal solid journal**. A tapered tip guides it on, and an integral 4 mm diameter shoulder locates its inner ring.

The bearing provides the rotation. The chassis, axle and bearing inner ring stay stationary; the wheel and outer ring turn together. Both friction fits must retain the assembly axially. There is **no separate end lock**: a loose fit can let the wheel or bearing slide off. Nominal CAD contact is not proof of a working press fit.

![The revised four-wheel arrangement](assembly.png)

The front-right free wheel shares Y = +20 mm and Z = 8.5 mm with the front-left servo shaft. The rear-left free wheel shares Y = -20 mm and Z = 8.5 mm with the rear-right servo shaft. Both front and rear pairs therefore lie on common X-axis lines, without an axle physically passing through a servo.

Wheel diameter is 30 mm, with 44 mm between tread centers and a 40 mm wheelbase. The nominal illustrated envelope is approximately **50.2 × 70 × 30 mm**. The chassis including its integral pegs is **50.2 × 66 × 16.7 mm**. All dimensions inherit the unmeasured servo assumptions from the [original compact model](../compact/README.md).

![Exploded view: only wheel and bearing separate from the integral chassis axle](exploded.png)

## Servo retention

Four integral cantilever clips replace the four servo mounting screws. Each hook overlaps its assumed mounting tab by 1 mm, with a 0.3 mm vertical gap above the tab. The stems have outward root reinforcement, insertion ramps and small outward release tabs. Existing low locating rails and the clip positions constrain the cases.

These clips are an **unbuilt fit prototype**. Their static clearances have been checked, but insertion force, flex, layer strength, retention and repeated removal have not been tested. Gently flex the clips outward to install or release the tabs; do not force an incorrectly sized case past them. Adjust the parameters to measured servo tabs if needed.

## Files and print quantities

Open [rolling-chassis.blend](rolling-chassis.blend) to edit the full assembly. Geometry settings are in [parameters.json](parameters.json), with source in [build.py](build.py).

| File | Quantity | Purpose |
|---|---:|---|
| [rolling-chassis.stl](rolling-chassis.stl) | 1 | One-piece chassis, integral axles and servo clips |
| [passive-wheel.stl](passive-wheel.stl) | 2 | Identical moving wheels, bearing pockets open upward in the STL |
| [bearing-fit-coupon.stl](bearing-fit-coupon.stl) | 1 initially | Pockets 7.9 / 8.0 / 8.1 mm, starting at the notched end |
| [axle-fit-coupon.stl](axle-fit-coupon.stl) | 1 initially | Horizontal journals 2.9 / 3.0 / 3.1 mm, starting at the notched end |

Only the chassis and wheels are installed prints; the two coupons are test pieces. Purchase **two MR83ZZ bearings, 3 × 8 × 3 mm**. See the [current mechanical parts list and bearing source](../../docs/passive-wheel-parts.md). Old cap/spacer STLs have been removed from this directory; the earlier screw-based revision is retained in Git history.

## Print and fit before assembly

Use the same material, layer settings, orientation and support strategy for the coupons and final parts. PETG is the first prototype material proposed for the flexible clips; this is not a validated material/process specification. A 0.2 mm layer height and four perimeters are starting settings for the larger parts.

**The horizontal axles and hook undersides need removable slicer supports.** Inspect the preview and ensure the 3 mm journals are actually supported. Remove supports carefully without levering against the small pegs, and clean their bearing surfaces. The integral axles cannot be replaced individually if broken. Printing a vertical test peg would not reproduce the supported horizontal surface of these axles; use the supplied coupon.

1. Test the bearing outer ring in the wheel-pocket coupon, pressing only on the outer ring. Choose a snug fit that holds it without deforming the bearing or letting the outer ring rotate loosely in the pocket. Change `wheel.bearing_seat_diameter` and rebuild if necessary.
2. Test the bearing inner ring on the horizontal peg coupon, pressing on the inner ring. Choose a fit that seats gently but resists slipping off and spinning on the axle. Do not force a fit that bends or cracks the peg. Change `axle.journal_diameter` and rebuild if needed.
3. Verify the actual bearing's inner-ring contact land clears the 4 mm printed shoulder. The 7 mm opening through the wheel clears that stationary shoulder and the rotating bearing's center region.
4. Print and check the chassis clips against both actual servos before engaging them fully. Release the tabs outward during fitting; avoid repeated flex cycles until fit is established.
5. Fit each bearing into its wheel using outer-ring pressure. When seating the wheel/bearing assembly on a chassis peg, apply installation force to the inner ring, not through the wheel and bearing balls. Do not hammer the assembly onto the printed axle.
6. Spin both wheels and check for shield rubbing, binding, tilt and axial looseness. Gently pull on the wheel to confirm that neither friction fit releases. Repeat after sitting assembled and after a short low-speed test, since a printed fit can relax over time.

The dark powered wheels and short horn-interface shapes are **size envelopes only**, with no powered-wheel STL or finalized horn attachment. Their tread diameter must match the free wheels so all four touch the same ground plane. Four fixed-direction wheels still rely on sideways tire scrub to turn.

## Verification and rebuilding

[validation.json](validation.json) reports four closed, connected STL solids with correct winding and no unintended nominal intersections. It distinguishes any deliberate bearing press-fit overlap from unrelated collisions. This checks geometry, not friction force, clip deflection, creep, support removal or loaded strength. The servo dimensions and bearing internal face details remain nominal/assumed.

```sh
blender --background --python-exit-code 1 --python cad/rolling/build.py
python3 cad/rolling/mesh_checks.py
```

Run from the repository root; on macOS use `/Applications/Blender.app/Contents/MacOS/Blender` if needed. Add `-- --skip-renders` to regenerate geometry and checks only. The compact Blender file supplies the nominal servo geometry; its old screw posts are removed by this generator and are absent from the current STL.
