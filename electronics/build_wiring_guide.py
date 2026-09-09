"""Rebuild the illustrated prototype wiring guide; requires reportlab and Pillow."""
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'electronics/guide-assets'
OUT = ROOT / 'output/pdf/spy-car-wiring-guide.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
W,H = 1200,850
c = canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('Diagonal Spy Car | Illustrated wiring guide')
c.setAuthor('Diagonal Spy Car project')
INK='#183047'; MUTED='#536779'; RED='#CE3946'; GND='#354354'; ORANGE='#C77700'; BLUE='#007EAD'; GREEN='#13806A'
def text(x,y,s,size=14,color=INK,bold=False):
    c.setFillColor(HexColor(color)); c.setFont('Helvetica-Bold' if bold else 'Helvetica',size); c.drawString(x,H-y-size,s)
def para(x,y,s,width,size=14,color=INK):
    st=ParagraphStyle('p',fontName='Helvetica',fontSize=size,leading=size*1.4,textColor=HexColor(color))
    p=Paragraph(s,st); _,h=p.wrap(width,700); p.drawOn(c,x,H-y-h); return h
def box(x,y,w,h,fill='#FFFFFF',stroke='#DCE4E9'):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke)); c.setLineWidth(1); c.roundRect(x,H-y-h,w,h,10,fill=1,stroke=1)
def line(points,color=INK,width=2,dash=None):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(width); c.setDash(dash or [])
    p=c.beginPath();p.moveTo(points[0][0],H-points[0][1])
    for x,y in points[1:]:p.lineTo(x,H-y)
    c.drawPath(p);c.setDash([])
def dot(x,y,color=INK,r=4):
    c.setFillColor(HexColor(color));c.circle(x,H-y,r,fill=1,stroke=0)
def img(name,x,y,w,h):
    im=Image.open(A/name); iw,ih=im.size; s=min(w/iw,h/ih); ww,hh=iw*s,ih*s
    c.drawImage(ImageReader(im),x+(w-ww)/2,H-y-hh,width=ww,height=hh,mask='auto')
def header(n,title,sub):
    c.setFillColor(HexColor('#F4F7FA'));c.rect(0,0,W,H,fill=1,stroke=0)
    text(40,25,'DIAGONAL SPY CAR  /  CAMERA-FREE PROTOTYPE',12,GREEN,True)
    text(40,52,title,30,INK,True); text(40,96,sub,14,MUTED)
    text(40,817,'08 SEP 2026  |  Unbuilt electrical prototype - verify the delivered hardware before connecting',10,MUTED)
    text(1100,817,f'{n} / 7',10,MUTED)
def end():c.showPage()
def link(x,y,label,url,size=12):
    text(x,y,label,size,BLUE);c.linkURL(url,(x,H-y-size*1.4,x+c.stringWidth(label,'Helvetica',size),H-y),relative=0)

# Page 1: electrical topology, picture cards and named terminals.
header(1,'Connect the car','Read the named terminals here; page 2 locates the actual solder pads. All grounds connect together. Crossings connect only where marked with a dot.')
box(40,150,210,285);text(55,164,'1  BATTERY',16,bold=True);img('battery.webp',50,195,190,185)
text(55,387,'2S / 7.4 V / 300 mAh',13);text(55,410,'8.4 V when fully charged',11,MUTED)
box(390,150,220,285);text(405,164,'2  YOUR LARGE BUCK',16,bold=True);img('owned-buck.jpg',450,199,100,187)
text(405,399,'OUT+ to OUT- = 5.00 V',13,RED,True)
box(930,150,230,230);text(945,163,'3  FRONT-LEFT SERVO',15,bold=True);img('servo.jpg',970,195,140,140)
text(945,348,'Owned continuous-rotation unit',11,MUTED)
box(930,450,230,230);text(945,463,'4  REAR-RIGHT SERVO',15,bold=True);img('servo.jpg',970,495,140,140)
text(945,648,'Same supply; separate signal',11,MUTED)
box(570,510,215,248);text(585,524,'5  LOLIN S2 MINI',16,bold=True);img('s2-mini-top.jpg',588,555,175,175)
text(585,736,'5 V enters VBUS, never 3V3',11,MUTED)
# Battery input / disconnect / fuse
line([(250,230),(295,230),(295,250),(390,250)],RED,3);text(262,188,'XT30',12,bold=True);text(262,205,'unplug = OFF',10)
box(305,240,55,20);text(311,242,'FUSE',10);text(307,268,'4 A*',10,MUTED)
line([(250,300),(280,300),(280,330),(390,330)],GND,3)
text(353,230,'IN+',11,RED,True);text(353,310,'IN-',11,GND,True)
text(247,247,'+',12,RED,True);text(247,306,'-',12,GND,True)
img('fuse-pico-251.jpg',290,352,90,90)
text(283,444,'Fuse family photo',9,MUTED)
text(283,456,'Details: page 6',9,BLUE)
line([(610,250),(840,250),(840,700)],RED,3);text(624,227,'OUT+  /  5 V BUS',12,RED,True)
line([(610,330),(870,330),(870,725)],GND,3);line([(870,307),(870,330)],GND,3);text(624,308,'OUT-  /  GND BUS',12,GND,True)
for y in [275,575]:
    line([(840,y),(930,y)],RED,3);dot(840,y,RED);text(892,y-20,'RED +',10,RED,True)
    line([(870,y+32),(930,y+32)],GND,3);dot(870,y+32,GND);text(884,y+36,'BROWN -',9,GND)
line([(840,700),(785,700)],RED,3);dot(840,700,RED)
box(792,690,36,20);text(796,694,'LINK',7,RED,True);text(788,667,'J_PWR',9,RED,True)
line([(870,725),(785,725)],GND,3);dot(870,725,GND)
text(734,680,'VBUS',10,RED,True);text(744,723,'GND',10,GND,True)
line([(715,510),(715,400),(905,400),(905,338),(930,338)],ORANGE,2);text(720,382,'GPIO16 > LEFT SIGNAL',11,ORANGE,True)
line([(750,510),(750,428),(910,428),(910,638),(930,638)],BLUE,2);text(760,430,'GPIO18 > RIGHT',10,BLUE,True)
text(918,343,'S',10,ORANGE,True);text(918,641,'S',10,BLUE,True)
box(40,470,470,130);text(56,484,'At the 5 V / GND split',16,bold=True)
para(56,512,'At the split: <b>220 uF / 10 V electrolytic</b> (+ to 5 V; striped negative to GND). At the S2, <b>after J_PWR:</b> add <b>100 nF ceramic across VBUS and GND</b> with short leads. Preserve the buck\'s onboard capacitor.',435,13)
box(40,615,470,143);text(56,629,'Manual battery checks: page 4',16,bold=True)
para(56,659,'No sensing perfboard or GPIO3/GPIO7 wires. The car has <b>no battery reading, alarm or low-voltage stop</b>. Check each cell with a meter between short runs and unplug when parked.',433,13)
text(40,778,'* Fuse rating is provisional. Photos show reference servos; wire functions, not plug orientation, define the connections.',11,MUTED)
end()

# Page 2: photo landing points.
header(2,'Exactly where each wire lands','Component side facing you. S2 antenna at the top; USB-C at the bottom. Photos are not mirrored.')
box(40,140,655,490);img('s2-mini-top.jpg',125,190,400,400)
text(60,157,'LOLIN S2 MINI v1.0.0 REFERENCE',16,bold=True)
coords={'18':(1239,833),'16':(1238,930),'GND':(1238,1027),'VBUS':(1238,1126)}
labels={'18':('GPIO18 > right signal',BLUE),'16':('GPIO16 > left signal',ORANGE),'GND':('GND > ground bus',GND),'VBUS':('VBUS > buck 5 V via join',RED)}
for k,(px,py) in coords.items():
    x,y=125+px/4,190+py/4; lab,col=labels[k];dot(x,y,col,5);line([(x,y),(480,y)],col);text(488,y-7,lab,12,col,True)
text(62,568,'Only four S2 connections: VBUS, GND, GPIO16 and GPIO18.',12,GREEN)
text(62,594,'Use GPIO labels. Inner-row GPIO17 is NOT the right servo pin.',12,INK,True)
box(715,140,445,490);text(735,157,'YOUR LARGE BUCK: SAME ORIENTATION',15,bold=True)
img('owned-buck.jpg',860,204,159,300)
# Photo coordinates refer to 265x500 crop from supplied portrait.
for px,py,label,lx,ly,col in [(32,48,'OUT+  5 V',730,208,RED),(220,38,'OUT-  GND',1027,208,GND),(49,470,'IN+  BATTERY +',728,514,RED),(240,456,'IN-  BATTERY -',1005,538,GND)]:
    x,y=860+px*.6,204+py*.6;dot(x,y,col,5);line([(x,y),(lx+15,ly-6)],col);text(lx,ly,label,10,col,True)
para(735,570,'Blue trimmer sets output. Measure OUT+ to OUT- and set <b>5.00 V with all loads disconnected</b>. IC marking is not readable: confirm the board type.',403,12)
box(40,650,1120,135,fill='#E8F3F0')
text(58,666,'Soldered wiring + removable connectors',17,bold=True)
para(58,697,'Bare S2 holes and converter pads need soldered wires or soldered headers. Use 22 AWG or thicker for the battery and main 5 V / GND paths. Servo red normally means supply; brown/black ground; orange/yellow signal. Verify your servo wires before fitting a 3-pin extension. Split its three wires to the correct nets - do not plug the whole servo lead onto random adjacent S2 pins.',1077,14)
end()

header(3,'Battery, plug and converter choice','Reuse the larger buck for this prototype. A custom power PCB is not required.')
box(40,145,540,310);img('battery.webp',55,180,240,230);text(310,166,'BUY: LUMENIER 300',19,bold=True)
para(310,210,'<b>2S 75C LiPo, XT30</b><br/>48 x 17 x 12 mm<br/>18 g; 7.4 V nominal<br/>8.4 V fully charged<br/><br/>$13.49; listed available<br/>at the research snapshot.',245,15)
link(60,425,'RaceDayQuads product / purchase page','https://www.racedayquads.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30')
box(605,145,555,310);img('owned-connectors.jpg',622,179,112,240);text(755,166,'YOUR YELLOW CONNECTORS',18,bold=True)
para(755,205,'The photo establishes the XT family, but does not distinguish <b>XT30 from XT60</b>. Read the molded marking.<br/><br/><b>XT30:</b> use the mating harness half.<br/><b>XT60:</b> buy an XT30 mating pigtail; a bulky adapter also works but increases footprint.<br/><br/>Check + / - with a meter. Housing shape or wire color alone is not proof of polarity.',385,13)
box(40,475,540,185);text(57,491,'Why the large buck wins here',18,bold=True)
para(57,526,'A 2S pack feeds a step-down converter naturally. Allowing 1.2 A per servo plus 0.4 A for the S2 gives a <b>provisional 2.8 A at 5 V</b>. Actual servo peaks are unknown. The LM2596 IC is rated 3 A with suitable parts and cooling; this particular board must still pass load and temperature checks at 8.4 V and 7.0 V.',505,14)
box(605,475,555,185);img('owned-buckboost.jpg',624,512,70,117);text(712,491,'Why not the small XL63070 board?',17,bold=True)
para(712,528,'It appears to be a TPS63070-style buck-boost module; the IC is unconfirmed. TI specifies 2 A output at 4 V in / 5 V out. That is below our provisional load. A 1S design at 14 W could also need about 5 A near 3.3 V. Smaller hardware needs current measurements first.',425,13)
box(40,680,1120,105,fill='#FFF3DF');text(57,692,'Battery handling and fit',16,bold=True)
para(57,721,'12 mm is the published nominal pack height, not measured installed height: leave room for padding and lead bends. This hobby pack has no verified protection PCB. Neither owned converter provides charging, balancing or a suitable LiPo cutoff. Use a 2S balance charger and unplug the pack after each run.',1085,14)
end()

header(4,'Manual battery checks','The perfboard is removed. GPIO3 and GPIO7 stay unwired. The car cannot detect a low battery.')
box(40,145,1120,120,fill='#FFF3DF')
text(58,161,'No automatic low-voltage protection',21,bold=True)
para(58,201,'The fuse opens on sufficiently large overcurrent, <b>not</b> low voltage. Firmware has no pack reading, low-battery alarm or voltage-triggered motion stop. A joystick stop leaves the electronics powered. <b>Unplug XT30 whenever parked.</b>',1080,14)
box(40,285,550,300)
text(58,302,'Measure the two cells separately',20,bold=True)
para(58,343,'Unplug XT30 from the car. Set the multimeter to <b>DC volts</b>, leads in <b>COM and V</b>, never the current socket/range. Prefer an insulated mating balance breakout.<br/><br/>The three balance taps are pack negative, cell midpoint and pack positive. Each adjacent pair measures one cell; the two end taps measure the whole pack.<br/><br/><b>Verify tap order and polarity on your pack.</b> Do not assume left/right orientation or colors. Never bridge adjacent contacts with metal probe tips.',510,14)
box(610,285,550,300)
text(628,302,'Short, attended trials',20,bold=True)
para(628,343,'Start with a correctly balance-charged pack. Check both cells before and between very short runs while establishing runtime.<br/><br/><b>End the session at or below 3.7 V per cell at rest</b>, or earlier if the pack instructions require. This is an early project stopping point, not a battery minimum or a guarantee against dips during use. At 3.5 V or lower, do not do another run.<br/><br/>Unplug promptly for abnormal heat, puffing, slowing or resets. Do not use those symptoms as the normal battery gauge.',510,14)
box(40,605,1120,180,fill='#E8F3F0')
text(58,622,'What a multimeter cannot do',20,bold=True)
para(58,662,'Periodic checks cannot catch a weak cell or rapid voltage drop between measurements. Total pack voltage can hide an individually depleted cell. No safe fixed runtime has been measured for this car.<br/><br/><b>Before Wi-Fi updates:</b> use a freshly balance-charged pack and lift the wheels. Firmware does not check voltage before or during upload. Longer unattended operation needs a different protection plan.',1080,14)
end()

header(5,'Build, check and use','No custom PCB. This is a soldered prototype harness, not a tested plug-and-play electrical assembly.')
box(40,145,550,392);text(58,162,'Wire and check in this order',19,bold=True)
steps=[
'1. Battery unplugged: solder the mating XT30 lead through a provisional 4 A inline fuse to IN+; negative to IN-. Insulate every joint.',
'2. Leave all loads disconnected. Power the buck, read OUT+ to OUT- with a multimeter and adjust to 5.00 V. Unplug before adding wires.',
'3. Split OUT+ and OUT- into separate servo and S2 branches. Add the capacitors. Fit J_PWR as a removable insulated connector in the S2 VBUS feed.',
'4. Leave GPIO3 and GPIO7 unwired. There is no sensing circuit. Check both cells with a meter as shown on page 4.',
'5. With wheels lifted, test each servo, then both together. Check 5 V stability, resets and board temperature at 8.4 V and 7.0 V input. Do not hold a servo stalled.',
'6. Verify calibrated neutral on joystick release and signal loss. Firmware cannot detect a low battery. Establish short run intervals with manual cell checks.'
]
y=200
for s in steps:y+=para(58,y,s,513,12.5)+10
box(610,145,550,198,fill='#FFF3DF');text(628,162,'Before connecting USB to the S2',18,bold=True)
para(628,199,'<b>Unplug the battery, remove J_PWR, and disconnect both servo signal wires.</b> Ground may remain connected. The S2 VBUS header is connected to USB power: battery disconnection alone can still let USB feed the servos or buck backward through the 5 V wire. Restore J_PWR and signals only after USB is removed.',510,14)
box(610,363,550,174);text(628,380,'Charge outside the car',18,bold=True)
para(628,417,'Use a <b>2S LiPo balance charger</b> set for 4.20 V/cell (8.40 V pack). A conservative 1C setting for 300 mAh is <b>0.30 A</b>, subject to pack instructions. Connect its XT30 main lead and 3-pin balance lead as the charger requires. A 1S USB/TP4056 charger is not compatible. Charge attended on a nonflammable surface.',510,13)
box(40,556,1120,88,fill='#E8F3F0');para(58,572,'<b>POC battery checks:</b> check both cells with your multimeter before and between short, attended test runs. Do not bridge adjacent balance contacts with probe tips. End the session when either cell reaches 3.7 V at rest. Unplug when parked. Firmware has no battery sensing, alarm or low-voltage stop; periodic checks cannot guarantee protection between measurements.',1080,13)
text(40,660,'Sources, image credits and build files',17,bold=True)
sources=[('WEMOS: S2 Mini photo, board pinout and schematic','https://docs.wemos.cc/en/latest/s2/s2_mini.html'),('TI: LM2596 buck datasheet','https://www.ti.com/lit/ds/symlink/lm2596.pdf'),('TI: TPS63070 buck-boost datasheet','https://www.ti.com/lit/ds/symlink/tps63070.pdf'),('TowerPro: MG90S reference image (not proof of continuous rotation)','https://towerpro.com.tw/product/mg90s-3/')]
for i,(lab,url) in enumerate(sources):link(40+(i//3)*565,694+(i%3)*24,lab,url,11)
text(40,774,'Battery photo: Lumenier / RaceDayQuads (page 3). Converter and connector photos: user. Third-party images are not MIT-licensed.',10,MUTED)
end()

header(6,'What is underneath the deck?','The sensing perfboard is removed. The fuse and power capacitors remain; none is a charger.')
box(40,145,545,395)
text(58,162,'F_IN: a compact fuse candidate',20,bold=True)
img('fuse-pico-251.jpg',68,219,180,180)
text(68,411,'251-series reference photo',11,MUTED)
text(68,429,'Appearance / markings may vary',10,MUTED)
para(277,211,'<b>Littelfuse 0251004.MXL</b><br/>PICO II 251 series<br/><b>4 A, very fast acting</b><br/>125 V DC rated<br/>300 A DC interrupt rating<br/><br/>Body: 7.11 mm long,<br/>2.80 mm maximum diameter.<br/>Leads and insulation add space.',280,14)
link(58,471,'DigiKey: 0251004.MXL / purchase page','https://www.digikey.com/en/products/detail/littelfuse-inc/0251004-MXL/700745',11)
link(58,495,'Littelfuse: specifications and mechanical drawing','https://www.littelfuse.com/assetdocs/littelfuse_fuse_251_253_datasheet.pdf?assetguid=f47a0bb7-8ede-4679-9646-7114c3787688',11)
box(610,145,550,395)
text(628,162,'Why these extra parts are here',20,bold=True)
para(628,207,'<b>Fuse:</b> opens the battery-positive feed during a sufficiently large overcurrent, such as a wiring short. It is one-time use; replace after finding the fault. It is not low-battery protection or a precise 4 A current limiter.',510,14)
para(628,316,'<b>No perfboard:</b> the voltage divider, transistors, sensing resistors and ADC filter are removed. There are no GPIO3 or GPIO7 wires. Battery checks are manual; no electronic low-voltage protection remains.',510,14)
para(628,438,'<b>Capacitors:</b> the nearby 220 uF and 100 nF parts help smooth the 5 V supply. They do not replace an adequately sized converter.',510,14)
box(40,560,1120,115,fill='#E8F3F0')
text(58,574,'Where the fuse connects',17,bold=True)
text(62,619,'XT30 harness +',15,RED,True)
line([(228,630),(370,630)],RED,3)
box(370,612,135,34);text(395,617,'F_IN fuse',15,bold=True)
line([(505,630),(670,630)],RED,3)
text(682,619,'VBAT_SW: fused battery positive to buck IN+',14,RED,True)
para(58,690,'<b>Assembly:</b> put the fuse close to the battery connector in the positive harness lead. This axial candidate is soldered inline and insulated with strain relief; it does not require a bulky cartridge holder. Either fuse lead can face the battery. Keep motor current in the insulated power harness, away from S2 GPIOs.',1080,13)
para(58,751,'<b>Still provisional:</b> validate 4 A against measured startup current, wire size and fault current. The updated Blender body follows the axial candidate; lead bends, insulation and loose cradle retention still need a fit check. Photo: Littelfuse / DigiKey, reference image supplied with this product listing.',1080,11,MUTED)
end()

header(7,'Buck 5 V goes straight to ESP32 VBUS.','J_PWR is our label for a removable join in that wire. It is not a board, regulator, or ESP32 pin.')
box(40,145,1120,325)
text(60,163,'NORMAL POWER PATH',15,GREEN,True)
img('owned-buck.jpg',75,205,100,170)
text(65,394,'Owned step-down buck',11,MUTED)
text(65,412,'Measure 5.00 V first',12,RED,True)
img('s2-mini-top.jpg',890,190,210,210)
text(900,414,'S2 Mini: VBUS / 5V',13,bold=True)
line([(180,250),(320,250),(430,250)],RED,3)
dot(320,250,RED)
line([(320,250),(320,199),(645,199)],RED,3)
text(420,173,'Separate +5 V branches to both servos',13,RED,True)
box(430,232,85,36,fill='#F4F7FA');box(520,232,85,36,fill='#F4F7FA')
text(445,241,'WIRE',11,RED,True);text(534,241,'WIRE',11,RED,True)
line([(605,250),(890,250)],RED,3)
text(431,285,'J_PWR = removable join in the 5 V wire',13,bold=True)
text(431,310,'Joined = direct electrical connection.',13,GREEN)
text(431,332,'Leave joined for driving and Wi-Fi updates.',12,MUTED)
text(655,266,'To VBUS, NOT 3V3',12,RED,True)
line([(180,367),(890,367)],GND,3)
text(253,380,'OUT- to shared GND: continuous, no switch in ground',13,GND,True)
box(40,490,545,150,fill='#E8F3F0');text(58,507,'Driving on your home Wi-Fi',18,bold=True)
para(58,542,'Set your network in <b>web.private.h</b>. Open <b>http://spy-car.local/</b> on a computer or phone on the same network. Your computer keeps internet access. Battery, buck, J_PWR and servos stay connected; no USB cable.',505,13)
box(610,490,550,150);text(628,507,'Wireless update mode: current firmware',18,bold=True)
para(628,542,'Lift the wheels. Boot normally, then hold <b>BOOT/0 for 3 seconds</b>. Driving locks off. Join <b>SpyCar-Update</b>; open <b>http://192.168.4.1/update</b>. Login: <b>admin</b>. Use your configured password for both Wi-Fi and login. Keep USB unplugged.',510,13)
box(40,660,1120,125,fill='#FFF3DF')
text(58,676,'USB recovery and the next software step',17,bold=True)
para(58,710,'<b>USB initial setup / recovery:</b> unplug XT30, separate J_PWR and unplug both servo signals first. Ground may remain connected. <b>Planned, not yet implemented:</b> updates over home Wi-Fi at spy-car.local/update, with SpyCar-Update as fallback. The wiring already supports both approaches; no extra switch is needed.',1080,13)
end();c.save();print(OUT)
