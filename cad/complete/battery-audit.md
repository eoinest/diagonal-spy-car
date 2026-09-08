# Independent battery dimension audit

Checked **2026-09-08**, against the saved `complete-spy-car.blend` at revision `49a3692`. This audit measured the saved geometry independently; it did not change or resave the Blender file. The separately modified `cad/rolling/rolling-chassis.blend` was not touched.

## Saved geometry

Both scenes were activated and their dependency graphs updated before reading world transforms. Measurements include all 13 `Battery •` objects (wrap, illustrative cells, folds and label), and exclude foam, wires and connectors.

| Scene | World X × Y × Z extent | World minimum | World maximum |
| --- | --- | --- | --- |
| `01 ASSEMBLED` | 48.000000 × 17.000004 × 12.000000 mm | −24, −11.000002, 28 | 24, 6.000002, 40 |
| `02 EXPLODED` | 48.000000 × 17.000004 × 12.000008 mm | −54, −11.000002, 79.999992 | −6, 6.000002, 92 |

The small deviations are floating-point precision. The wrap has unit object scale, no parent, local dimensions **17 × 48 × 11.96 mm**, and a −90° rotation about Z. Its world dimensions are **48 × 17 × 11.96 mm**; the label brings the finished pack to 12 mm. Exploding the assembly translates the battery without stretching it. No hidden scaling or width/height interchange was found.

## Live Blender check

The parent agent separately queried the user's currently open `01 ASSEMBLED` scene through Blender's Python console: the wrap reports local dimensions **17 × 48 × 11.96 mm**, scale **1, 1, 1**, and transformed world dimensions **48 × 17 × 11.96 mm**. The file already includes `03 BATTERY DIMENSIONS`, so this was the updated model rather than an older open copy. No geometry was changed or saved; the existing unsaved state was preserved and the 3D view restored.

## Manufacturer sources conflict

| Source for the selected 300 mAh 2S 75C XT30, SKU 10188 | Dimensions | Weight |
| --- | --- | --- |
| [Lumenier product listing](https://www.lumenier.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30) | Explicitly **length 48, width 17, height 12 mm** | 18 g |
| [MSDS linked from that listing, page 2](https://cdn.shopify.com/s/files/1/0698/9525/8342/files/66_10188_Lumenier_300mAh_2s_75c_Lipo_Battery_XT-30.pdf?v=1756837387) | **13 × 16 × 45 mm**, with no axis labels | About 25 g |

The MSDS names the exact 2S 300 mAh XT30 product and specifies 7.4 V / 2.22 Wh. It was issued December 25, 2024, effective January 1, 2025. The discrepancy was checked in the rendered table, not inferred from text extraction. Neither source explains whether the difference reflects a sample revision, measurement convention or documentation error.

The listing's [generic dimension icon](https://cdn-v2.getfpv.com/media/wysiwyg/product-detail-images/height-length-width.png) uses height vertically and width horizontally. It provides no evidence that 17 and 12 should be exchanged. The [manufacturer photograph](https://cdn.shopify.com/s/files/1/0698/9525/8342/files/lumenier-300mah-2s-xt30-main_1.jpg?v=1734560763&width=1000) visibly shows a 2 CELL 7.4 V label and XT30 connector; no different-SKU mismatch was established.

## What the visual mismatch means

The model matches one published envelope; that does **not** establish an exact physical replica. The photograph shows tapered, folded shrink-wrap, while the model remains a mostly constant-height rounded cuboid. Correct maximum bounds alone cannot verify that silhouette. Camera angle, foreshortening and partially obscured lower edges also affect apparent thickness, but are not proof that the user's concern is mistaken.

The assembly also places the XT30 pair and balance connector above the pack; the product photo places its loose connectors beside it. Those are additional objects, not extra battery thickness, but they make the installed package look taller. The observed user viewport looks toward a short end and foreshortens the long dimension. Neither observation resolves the physical silhouette uncertainty.

No source found justifies flattening the model to a different thickness. The MSDS does not establish a thinner pack either. Keep 48 × 17 × 12 mm explicitly provisional until the actual selected pack is measured: maximum length/width/height including wrap, thickness through the central body versus folded ends, and lead exits. Those measurements should control the final battery model and retention fit.
