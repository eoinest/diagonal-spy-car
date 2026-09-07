# Passive wheel parts — v0.4

This **mechanical stage** uses the two owned continuous-rotation MG90S servos and two purchased bearings. Electronics are outside this list. The chassis is one printed part with integrated stationary axles, inner-ring abutments and servo-ear clips. Wheels are separate printed moving parts. The interface to the servos’ original supplied horns remains future work.

| Part | Quantity | Price / availability | Source |
|---|---:|---|---|
| Owned continuous-rotation MG90S servos | 2 | Already owned | Measure the actual cases, mounting ears and supplied horns |
| Avid MR83ZZ, steel/chrome bearing with metal shields, **3 mm ID × 8 mm OD × 3 mm wide** | 2 | **$1.00 each**, last checked **2026-09-07**; listing then showed **73 in stock** | [Buy from Avid](https://www.avidrc.com/product/p/227/3x8x3-Metal) · [product photograph](https://www.avidrc.com/shop/images/products/large_227_5602db2f85619.jpg) |

**Additional purchased mechanical parts: two bearings, $2.00 total**, excluding shipping, taxes and printing material. There are no purchased axles, caps, spacers, nuts or screws in v0.4. Prices and availability can change.

## Bearing and wheel fit

Each passive wheel carries one bearing. Its **outer ring fits into the wheel’s nominal 8.0 mm pocket** and rotates with the wheel. Its **inner ring fits over the chassis’s nominal 3.0 mm stationary printed journal**. These are intended friction fits; equal nominal CAD dimensions do **not** establish a reliable press fit on an FDM printer.

A **4.0 mm OD abutment**, integrated into the chassis, contacts the inner ring only. The wheel and bearing shield must clear this stationary feature. The [KMT manufacturer catalog](https://www.e-kmt.com/wp-content/themes/dc_e-kmt/img/download/dl03.pdf), miniature-bearing table on printed pages 5–6, gives **4.0 mm maximum shaft-abutment diameter for MR83ZZ**. This is supporting reference geometry, **not an Avid-specific abutment drawing**: inspect the purchased bearing’s exposed inner-ring contact land and confirm the printed abutment clears its shield.

There is **no end clip**. Axial retention depends entirely on friction at both the bearing-to-wheel and bearing-to-journal interfaces. Pull-off resistance, PETG creep, journal durability and the physical fits have not been validated. The nominal model must not be treated as a proven retained wheel assembly.

## Fit coupon and physical checks

Before printing the full chassis, print a coupon with **7.9 / 8.0 / 8.1 mm bearing holes** and **2.9 / 3.0 / 3.1 mm journal pegs**. Reproduce the final parts’ **horizontal bore/journal orientation, supports, material and slicer settings**; a vertical coupon does not characterize the horizontal features. Remove support material carefully and measure the resulting features. If none fits, adjust the coupon sizes before changing the complete model.

Choose fits that retain both rings without cracking the wheel, damaging the printed journal or causing bearing drag. When seating a bearing in the wheel, apply force to its outer ring; when seating it on the journal, support its inner ring. Do not force assembly loads through the balls or shields.

With the wheel installed, verify free rotation, shield clearance, low wobble and secure axial retention. Pull the wheel outward by hand to test both friction interfaces and check again after repeated rotation, a short low-speed floor test and time under load. Any loosening, creep, binding or easy pull-off means the fit needs revision before use. Check the integrated servo-ear clips against the actual servos as well; their retention is also unverified until physically tested.
