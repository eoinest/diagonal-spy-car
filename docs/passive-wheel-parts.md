# Passive wheel bearings and axles

Shopping and fit notes checked **2026-09-07**. This version uses **one conventional steel bearing in each of the two passive wheels**. The bearing outer ring turns with the wheel; its inner ring sits on a stationary smooth shoulder screw.

| Part | Quantity | Price / availability | Purchase and image |
|---|---:|---|---|
| Avid MR83ZZ, metal shields, steel/chrome bearing, **3 mm ID × 8 mm OD × 3 mm wide** | 2 | **$1.00 each**; listing showed **73 in stock** | [Avid product](https://www.avidrc.com/product/p/227/3x8x3-Metal) · [product photograph](https://www.avidrc.com/shop/images/products/large_227_5602db2f85619.jpg) |
| STR601M3X8 stainless shoulder screw, **3 mm shoulder × 8 mm long**, **M2 × 0.4 thread × 3.8 mm long** | 2 | **$6.79 each** at Zoro; current stock/dispatch date **not exposed and not verified** | [Zoro product](https://www.zoro.com/zoro-select-shoulder-screw-m2-040-thr-sz-38-mm-thr-lg-8-mm-shoulder-lg-18-8-stainless-steel-str601m3x8/i/G4578621/) · [catalog product image](https://www.zoro.com/static/cms/product/large/Z-tAp0qcpEx_.JPG) |
| M2 × 0.4 metal hex nut, captured in chassis axle mount | 2 | Unpriced; measure purchased nut before finalizing its pocket | Standard hardware; source not selected |
| M2 × 6 mm screws for removable bearing-retaining caps | 6 | **Provisional length**, unpriced; three per wheel | Confirm cap thickness and usable thread engagement before buying |
| Inner-ring spacers, **4 mm OD × 3.2 mm ID**, printed prototype | 4 | Print **two 2.8 mm long** and **two 1.0 mm long** | One of each length per wheel; fit checks below |

**Bearing + shoulder-screw subtotal: $15.58 USD.** Nuts, cap screws, spacers, printing, shipping and taxes are excluded. Servo mounting and other chassis hardware are outside this list. Prices and stock can change.

## Wheel and axle fit

The printed wheel has a nominal **8.1 mm bearing pocket** and removable retaining caps that capture the **outer ring**. This pocket dimension is a prototype starting point, not a guaranteed fit across printers. Print a fit coupon first: the bearing should seat without damage, remain concentric, and avoid spinning loosely in the wheel. Caps must clear the inner ring, shields and stationary spacers.

The stationary axle uses the screw's smooth **3 mm × 8 mm shoulder**, seated **1 mm into the chassis mount**, with its M2 thread secured by a captured metal nut. Keep the threaded section out of the bearing bore. The screw head is **5 mm diameter × 2 mm high**; do not put that full head face directly against the bearing shield. Place the narrow spacers against the **inner ring only**.

The nominal axial allocation is **1.00 mm mount engagement + 2.80 mm spacer + 3.00 mm bearing + 1.00 mm spacer = 7.80 mm**, leaving approximately **0.20 mm** relative to an 8.00 mm shoulder. These spacer heights align with 0.2 mm print layers. This is a fit target, not guaranteed endplay: Zoro specifies shoulder length **8.00–8.25 mm** and diameter **2.96–3.00 mm**. Measure the actual screws, bearings, printed mount and spacers; adjust spacer lengths so the axle is securely retained while the wheel turns freely with minimal axial play. Do not tighten away excessive clearance by loading the shield or distorting the printed mount. Do not force an oversized shoulder through the bearing.

## Spacer material and contact limits

The printed **4 mm OD / 3.2 mm ID** spacers are prototypes with just **0.4 mm radial wall thickness**. Inspect the slicer to confirm a continuous wall is produced, and measure the printed lengths. A more durable alternative is **brass tube with nominal 3 mm ID / 4 mm OD**, cut to the measured required lengths, with square ends and all burrs removed. No purchase source has been selected for this tube. Verify that its actual bore slides over the delivered shoulder; nominal tube dimensions alone do not guarantee clearance. Replace any spacer that rubs a shield or sheds material.

The [KMT manufacturer catalog](https://www.e-kmt.com/wp-content/themes/dc_e-kmt/img/download/dl03.pdf), miniature-bearing table on printed pages 5–6, lists **4.0 mm maximum shaft-abutment diameter for MR83ZZ**. This supports the provisional 4 mm spacer OD, but **it is not an Avid-specific abutment drawing**. Avid publishes the bearing's overall dimensions, not the exact exposed inner-ring contact land. Inspect the purchased bearings and confirm both spacer faces touch only that land before final assembly. Supplier differences, printing tolerances and screw-head fillets all require physical fit verification.

With the axle secured and caps installed, turn each wheel by hand and check for shield rubbing, binding, bearing movement in the wheel, and excessive tilt or axial play. Repeat after a short low-speed floor test before committing to final printed parts.
