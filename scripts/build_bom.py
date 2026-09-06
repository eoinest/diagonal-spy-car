"""Merge researched power BOM with mechanical/control items, emit CSV + Markdown."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
with (R/'docs/power-bom.csv').open() as f:
    reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
def add(ref,quantity,category,item,part,dimensions,required,url='',notes=''):
    rows.append(dict(zip(fields,[ref,quantity,category,item,part,dimensions,'','Not priced; verify selected seller',required,url,notes])))
# The baseline removable MCU supply disconnect is included with the harness.
for row in rows:
    if row['ref']=='HARNESS': row['notes'] += '; includes removable insulated 2-pin J_PWR disconnect for S2 supply, plus servo connectors'
add('M_FL_RR',2,'on_car','Owned MG90S-style 360 degree continuous servos','Exact owned variant TBD','Nominal 22.8 x 12.2 x 28.5; measure ears/shaft','owned','https://towerpro.com.tw/product/mg90s-3/','Official page describes nominal MG90S; does not verify owned 360-degree variant. Retain supplied horns and shaft screws; verify 5 V suitability, current and neutral.')
add('MCU_RX',1,'on_car','LOLIN WEMOS S2 mini','ESP32-S2FN4R2 S2 mini V1.0.0','34.3x25.4; decorative height assumed','owned','https://www.wemos.cc/en/latest/s2/s2_mini.html','Headerless soldered leads recommended; fitted headers require taller packaging. Not C3/S3 mini.')
add('CAM1',1,'on_car','Creator-linked analog FPV AIO camera','IDC-681H 25 mW 40CH 600TVL M7','Provisional 20 x 20 x 24 total envelope','yes_for_FPV','https://robu.in/product/idc-681h-25mw-40ch-vtx-600tvl-m7-fpv-camera/','Confirm actual dimensions, permitted supply voltage and current; no camera data connection to ESP32 needed; antenna remains attached.')
add('V_RX',1,'off_car','Analog 5.8 GHz video receiver','EWRF 5.8 GHz UVC OTG Android AV receiver','Off car','yes_for_FPV','https://robu.in/product/ewrf-5-8g-uvc-otg-android-av-phone-receiver/','Creator-linked receiver. Check phone OTG/UVC/software compatibility; alternatively use compatible analog 5.8 GHz monitor/goggles. Wi-Fi alone cannot display analog FPV.')
add('MCU_TX',1,'controller','Second ESP32 development board','Classic ESP32 DevKit assumed','Off car','owned_if_available','https://docs.espressif.com/projects/arduino-esp32/en/latest/','Transmitter sketch targets classic ESP32 pins 32/33 ADC, 27 deadman; use USB power bank.')
add('JOY1',1,'controller','Two-axis spring-centered analog joystick','3.3 V potentiometer joystick; exact module TBD','Off car','yes','','Power at 3.3 V; calibrate endpoints and neutral; do not use 5 V analog signals.')
add('DEADMAN',1,'controller','Normally open momentary pushbutton','SPST button to GND','Off car','yes','','Hold to enable motion; release stops. GPIO27 INPUT_PULLUP.')
add('TX_POWER',1,'controller','USB power bank and board-compatible cable','User-owned USB source','Off car','yes_unless_owned','','Controller power separate from car; no onboard controller pack charger designed.')
add('SERVO_HORNS',2,'on_car','Factory servo horns and original shaft screws','Supplied with owned servos','Measure actual horn; model 20 mm disc assumed','owned','','Never print a servo spline. Wheel radial slots have radius 5 to 11 mm; use at least two opposed attachment points.')
add('HORN_FIX',4,'on_car','Wheel-to-horn fasteners','Choose matching factory horn screws or M1.6/M2 bolts + nuts','Measure horn first','yes','','Nominal wheel web 4.4 mm plus actual horn; choose engagement without case contact. Do not force M2 screws into unverified horn holes.')
add('M2_DECK',4,'on_car','Deck mount screws','2 mm x 6 pan head plastic-tapping screws or coupon-verified M2','4 pieces','yes','','2.5 mm deck leaves 3.5 mm thread; 1.7 mm pilots in posts; print coupon and adjust pilot.')
add('M2_SKID',2,'on_car','Skid mount screws','2 mm x 6 pan head plastic-tapping screws or coupon-verified M2','2 pieces','yes','','3 mm base leaves 3 mm thread in 4 mm deep, 1.6 mm pilot.')
add('M2_CAM',2,'on_car','Camera cradle screws','2 mm x 5 pan head plastic-tapping screws or coupon-verified M2','2 pieces','yes','','From below 2.5 mm deck nose into 2.5 mm cradle floor. Verify tip does not puncture camera foam.')
add('TIES',12,'on_car','Nylon cable ties','Approximately 2.5 mm wide; 100 mm long','Trim after fit','yes','','Two per servo, two for battery, auxiliary hardware as needed; avoid crushing battery pouch or exposed PCB components.')
add('FOAM',1,'on_car','Thin nonconductive foam and insulation','0.5–1 mm foam plus polyester/Kapton insulation','Trim to fit','yes','','Under battery, servos, boards and camera; leave buck cooling and antenna area open.')
add('VELCRO',1,'on_car','Camera retention strap','Thin strap through 2.5 mm side windows','Measure chosen strap','yes','','Use foam to adapt camera envelope. Fit is provisional.')
add('PTFE',1,'on_car','Low-friction skid contact tape','Thin PTFE tape','Two 12 mm pads','recommended','','Smooth-floor prototype; optional rubber wheel bands increase grip but can increase diagonal turning load.')
add('PRINT',1,'printed','Eight supplied STLs','PETG or PLA; 0.4 mm nozzle','Base 81 x 100 x 27 mm; see mesh report','yes','','Includes fit coupon. Print settings and fastener fit in docs/assembly.md. Not physically print-tested.')
add('CALIPER',1,'bench','Digital caliper','0.1 mm or better useful resolution','Off car','yes_unless_owned','','Needed for actual servo, camera, connector and board height measurements.')
# Improve word separation in generated human fields; identifiers remain literal.
with (R/'BOM.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
lines=['# Bill of materials','', 'Research snapshot: 2026-09-05. Quantities cover one car plus one radio controller. Owned parts are marked. Prices exclude shipping/tax and are not a complete project total. Generic hardware dimensions must be checked before buying.','', '| Ref | Qty | Item / part | Status | Price USD | Source |','|---|---:|---|---|---:|---|']
for r in rows:
    link=f"[source]({r['url']})" if r['url'] else 'Select locally'
    lines.append(f"| {r['ref']} | {r['quantity']} | {r['item']} — {r['manufacturer_part']} | {r['required']} | {r['unit_price_usd'] or '—'} | {link} |")
lines+=['','The verified-price subtotal for the battery, buck regulator and BS250P is **$48.92**. Camera, charger, viewing hardware, connectors and consumables are additional. Check current stock: the Pololu regulator was rationed/backordered at research time.','', 'See [BOM.csv](BOM.csv) for dimensions and per-row notes, [power design](docs/power.md), [wiring](electronics/wiring.md), and [assembly](docs/assembly.md).']
(R/'BOM.md').write_text('\n'.join(lines)+'\n')
print(f'BOM: {len(rows)} line items')
