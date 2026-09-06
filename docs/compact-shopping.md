# Camera-free compact build: shopping shortlist

Researched 2026-09-06. These are candidates for the next smaller design; the existing CAD, BOM and firmware have not been revised to implement this layout. Dimensions below are supplier envelopes, not measured replicas. Prices exclude tax and shipping.

## Preferred battery

[Lumenier 300mAh 2S 75C LiPo, XT30, SKU 10188](https://www.racedayquads.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30) — $13.49; retailer product data showed available at research time. **48 × 17 × 12 mm, 18 g**, nominal 7.4 V, fully charged 8.4 V. Allow extra room for cables, connector bends, padding and pack tolerances.

[Manufacturer specifications](https://www.lumenier.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30).

![Lumenier 300mAh 2S XT30 battery; retailer photo](https://cdn.shopify.com/s/files/1/1285/4651/files/lumenier-lumenier-300mah-2s-75c-lipo-battery-xt-30-battery-32426879811697.webp?v=1736984212)

This is 13 mm shorter than the original 61 mm pack, with two thirds of its nominal capacity. Real runtime depends on servo load and must be measured. Retain an external 2S balance charger; select a charge current permitted by the pack instructions (0.3 A corresponds to 1C). This RC pack does not supply a complete battery-management system.

## Preferred regulator candidate

[Pololu S13V30F5, item 4082](https://www.pololu.com/product/4082) — $17.95; backorders allowed, dispatch availability not confirmed. **22.9 × 22.9 × 9.7 mm**, fixed 5 V, buck-boost topology, 2.8–22 V input. Solder wires directly to avoid the height of the included terminal blocks.

![Pololu S13V30F5 regulator; manufacturer photo](https://a.pololu-files.com/picture/0J11251.600x480.jpg?92eb61fc7dbbb0f99153fc24a20f40b0)

The manufacturer's 3 A class rating varies with input voltage and cooling. Our provisional 2.8 A peak allowance for two servos plus the ESP32 is not a measurement: test simultaneous startup, reversal, brief stall and enclosure temperatures before approving this board for the build.

The default undervoltage lockout is not an appropriate 2S LiPo discharge cutoff. Its EN input supports an external resistor divider for a higher cutoff, accounting for the onboard 475 kΩ pullup. A proposed calibrated 7.0 V falling threshold requires physical validation: the documented maximum hysteresis could require about 8.33 V to restart. This leaves little margin below an 8.4 V full pack. Verify both thresholds, startup under load and battery rebound behavior before relying on it. This is pack-level cutoff, not individual-cell protection; unplug the battery after use.

## Smaller alternative, currently unavailable

[BETAFPV 300mAh 2S 45C XT30, two pack](https://betafpv.com/products/300mah-2s-lipo-battery-2pcs) — $12.99/two listed, **sold out** at research time. **45 × 17 × 12 mm, 18.4 g** per pack. Only 3 mm shorter than the available Lumenier option.

## Build implications

Battery plus regulator total: **$31.44**, excluding small parts and charging equipment. Reuse the owned S2 Mini and two continuous-rotation servos. No motor driver or custom PCB is inherently required: the servos contain their own drivers. Still budget for a mating XT30 pigtail, switch, cutoff resistors, decoupling capacitor, wire and insulation. The exact cutoff circuit and compact mechanical placement remain to be validated.

Suggested placement: two staggered servos below, battery beside the S2 Mini and regulator on an upper deck. The discussed roughly 50 × 70 mm vehicle footprint remains an estimate pending CAD fit checks. Product photos above are externally hosted, credited references and are not covered by this repository's MIT license.
