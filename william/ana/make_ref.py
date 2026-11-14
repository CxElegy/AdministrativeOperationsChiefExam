# アナちゃんのベース絵：お手本の設定画の「正面で立つ猫」を そのまま使い、毛の色だけ アナちゃんの色（白＋こい あたたかい灰色）に変える
# 使い方: python3 william/ana/make_ref.py [プレビューを書くフォルダ]
#   入力: william/ana/ref_front_cut.png（設定画から切り出して 4 倍に拡大し、背景を消したもの。820×1640）
#   出力: william/assets/ana_ref.webp
# 変えるのは 毛の色だけ：オレンジと黒の ぶち → 灰色。顔の見え方・顔のパーツの位置・体型・毛の質感は お手本のまま。首輪は 消して 白い毛でうめる
import sys, os, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
im = cv2.imread(os.path.join(HERE, 'ref_front_cut.png'), cv2.IMREAD_UNCHANGED); H, W = im.shape[:2]
bgr = im[..., :3].copy(); a = im[..., 3].copy()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# 背景の うすい残り（となりの猫の影など）を落とす
a = np.where(a > 150, 255, 0).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(a); a = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
a[:, :40][yy[:, :40] > 1100] = 0; a = cv2.GaussianBlur(a, (0, 0), 1.5)
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32); Hh, Ss, Vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
# 首輪（紫）と かざり（金）を消して、まわりの白い毛でうめる
band = np.clip(1 - np.abs(yy - (592 + 28 * (1 - ((xx - 340) / 150) ** 2).clip(0, 1))) / 52, 0, 1) * ((xx > 185) & (xx < 500))   # 首輪の帯（下に ふくらむ弧）
band = np.maximum(band, np.clip(1 - np.hypot(xx - 340, yy - 655) / 52, 0, 1)); band = cv2.GaussianBlur(np.clip(band * 3, 0, 1).astype(np.float32), (0, 0), 6)[..., None]
src = np.roll(bgr, -120, axis=0)                                       # 120 画素 下の 白い毛を 写す
bgr = (bgr * (1 - band) + src * band).astype(np.uint8)
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32); Hh, Ss, Vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
# 体の両わきの下に残った 背景（青っぽい うすい灰色）を消す
ghost = (yy > 1080) & ((xx < 150) | (xx > 640)) & (Ss < 40) & (Vv < 236) & (bgr[..., 0].astype(np.int32) >= bgr[..., 2].astype(np.int32) - 2)
a[cv2.dilate(ghost.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats((a > 128).astype(np.uint8)); a = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), a, 0).astype(np.uint8); a = cv2.GaussianBlur(a, (0, 0), 1.2)
# 毛の色：オレンジ（色が こい）と 黒（暗い）の所を 灰色に。白い毛は そのまま
w = np.maximum(np.clip((Ss - 24) / 40, 0, 1), np.clip((170 - Vv) / 70, 0, 1))
keep = np.zeros((H, W), np.float32)                                   # 目・鼻・口は 色を変えない
for (cx, cy, rx, ry) in [(258, 335, 44, 40), (425, 335, 44, 40), (340, 425, 46, 50)]: cv2.ellipse(keep, (cx, cy), (rx, ry), 0, 0, 360, 1.0, -1)
keep = cv2.GaussianBlur(keep, (0, 0), 5); earin = ((yy < 250) & (Hh < 12) | (Hh > 165)) & (Ss > 25) & (Vv > 150) & (yy < 260)   # 耳の中のピンクは 残す
w = cv2.GaussianBlur(w * (1 - keep) * (1 - earin.astype(np.float32) * 0.8), (0, 0), 1.2)
L = 58 + Vv * 0.30                                                      # 明るい オレンジ → 中くらいの灰色、黒 → こい灰色
grey = np.dstack([L * 0.90, L * 0.95, L * 1.0])                         # BGR：少し あたたかい灰色
# ---------- ここから Tororo の画法に直す（参考にするのは 体型と 模様の位置だけ） ----------
#   線なし／エアブラシのように なめらかな塗り／白い毛の影は うすいピンク／模様は ふちが ぼけた塗り／ふちは 細い短い毛
import math
rng = np.random.RandomState(3)
WHITE = np.array([251, 253, 255], np.float32); SHADOW = np.array([232, 224, 240], np.float32); GREY = np.array([124, 132, 144], np.float32); DARK = np.array([84, 90, 100], np.float32)   # BGR
def ss(a_, b_, v): t = np.clip((v - a_) / (b_ - a_), 0, 1); return t * t * (3 - 2 * t)
# 顔の部品（目・鼻・口）は Tororo の Live2D の部品に置きかえるので、絵からは消す
fm = np.zeros((H, W), np.uint8)
for (cx, cy, rx, ry) in [(258, 335, 52, 46), (425, 335, 52, 46), (340, 430, 50, 56)]: cv2.ellipse(fm, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
# 輪郭の外へ 中の色を のばしておく（ぼかしたときに 背景の色が ふちに まざらないように）
inside = (a > 200).astype(np.uint8); _, lab2 = cv2.distanceTransformWithLabels(1 - inside, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
lut = np.zeros((lab2.max() + 1, 2), np.int32); lut[lab2[inside > 0]] = np.argwhere(inside > 0); bgr = bgr[lut[lab2][..., 0], lut[lab2][..., 1]]; w = w[lut[lab2][..., 0], lut[lab2][..., 1]]
bgr2 = cv2.inpaint(bgr, fm, 12, cv2.INPAINT_TELEA); w2 = cv2.inpaint((w * 255).astype(np.uint8), fm, 12, cv2.INPAINT_TELEA).astype(np.float32) / 255
w2[(yy > 1150) & (xx > 285) & (xx < 395)] = 0                             # 前足のあいだは 模様ではなく 影
w2[(yy > 1380) & (xx > 395) & (xx < 520)] = 0                             # うしろ足の影も 模様にしない
V2 = cv2.cvtColor(bgr2, cv2.COLOR_BGR2HSV)[..., 2].astype(np.float32)
Vs = cv2.GaussianBlur(cv2.edgePreservingFilter(cv2.cvtColor(V2.astype(np.uint8), cv2.COLOR_GRAY2BGR), flags=1, sigma_s=18, sigma_r=0.22)[..., 0].astype(np.float32), (0, 0), 3)   # 明るさ：大きな面だけ残す
gm = cv2.GaussianBlur((cv2.GaussianBlur(w2, (0, 0), 6) > 0.5).astype(np.float32), (0, 0), 7)                     # 灰色の模様（ふちを ぼかす）
kw = ss(196, 247, Vs)[..., None]; k0 = ss(110, 196, Vs)[..., None]; kg = ss(70, 150, Vs)[..., None]   # 白い毛：明るい所は白、かげは うすいピンク、深いかげ（足のあいだ・あごの下）は 少し こいピンク
DEEP = np.array([206, 194, 216], np.float32); whitec = (DEEP * (1 - k0) + SHADOW * k0) * (1 - kw) + WHITE * kw; greyc = DARK * (1 - kg) + GREY * kg
out = whitec * (1 - gm[..., None]) + greyc * gm[..., None]
# 耳の中の ピンク
ear = cv2.GaussianBlur(cv2.erode((earin & (a > 128)).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 7)[..., None]; out = out * (1 - ear * 0.7) + np.array([196, 186, 236], np.float32) * ear * 0.7
out = cv2.GaussianBlur(out, (0, 0), 2)
# 輪郭：なめらかにして、細い短い毛を 外へ（胸の両わきと 体のわきは 少し長く）
m = (cv2.GaussianBlur(a, (0, 0), 5) > 128).astype(np.uint8); a = (np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.6) * 2 - 0.5, 0, 1) * 255).astype(np.uint8)
def fuzz(rgb, al, mask, col, length):
    din = cv2.GaussianBlur(cv2.distanceTransform(mask, cv2.DIST_L2, 5), (0, 0), 3); gx, gy = cv2.Sobel(din, cv2.CV_32F, 1, 0), cv2.Sobel(din, cv2.CV_32F, 0, 1)
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        for (x, y) in c[:, 0]:
            L0 = length(x, y)
            for _ in range(2 if L0 > 12 else 1):
                nx, ny = -gx[y, x], -gy[y, x]; d = math.hypot(nx, ny) + 1e-6; ang = math.atan2(ny / d, nx / d) + rng.uniform(-0.55, 0.55); ang += 0.5 * (1 if (math.pi / 2 - ang + math.pi) % (2 * math.pi) - math.pi > 0 else -1) * min(1, L0 / 24)
                L = L0 * rng.uniform(0.35, 1.0); sx0, sy0 = x - nx / d * 3, y - ny / d * 3
                pp = (np.array([[sx0, sy0], [sx0 + math.cos(ang) * L * 0.6, sy0 + math.sin(ang) * L * 0.6], [x + math.cos(ang) * L, y + math.sin(ang) * L + L * 0.06]]) * 8).astype(np.int32)
                c3 = tuple(float(v) for v in col[int(np.clip(sy0, 0, col.shape[0] - 1)), int(np.clip(sx0, 0, col.shape[1] - 1))].clip(0, 255))
                cv2.polylines(rgb, [pp], False, c3, 2, cv2.LINE_AA, 3); cv2.polylines(al, [pp], False, 235, 2, cv2.LINE_AA, 3)
rgb = np.ascontiguousarray(out.clip(0, 255).astype(np.uint8)); al = np.ascontiguousarray(a)
fuzz(rgb, al, m, out, lambda x, y: 22 if 500 < y < 1250 else 10)
res = np.dstack([rgb, al]); out = rgb.astype(np.float32); a = al
from PIL import Image
Image.fromarray(cv2.cvtColor(res, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', 'ana_ref.webp'), quality=93, method=6)

# ---------- しっぽ（Tororo と同じく、体のうしろから 横へ 床にそって 甩る。長毛なので 太く ふさふさ） ----------
TW, TH, OX = 900, 520, 560                                             # しっぽの絵の大きさ。絵の x = 体の絵の x + OX、y = 体の絵の y - 1120
tm = np.zeros((TH, TW), np.uint8); sp = []
for s_ in np.linspace(0, 1, 220):
    u = 1 - s_; x = u * u * (300 + OX) + 2 * u * s_ * (-40 + OX) + s_ * s_ * (-430 + OX); y = u * u * 400 + 2 * u * s_ * 500 + s_ * s_ * 250
    sp.append((x, y)); cv2.circle(tm, (int(x), int(y)), int(46 + 58 * math.sin(math.pi * min(1, 0.12 + s_ * 0.92)) ** 0.7), 1, -1)
ty, tx = np.mgrid[0:TH, 0:TW].astype(np.float32); hgt = np.zeros((TH, TW), np.float32)
for (x, y) in sp[::10]: hgt = np.maximum(hgt, np.sqrt(np.clip(1 - ((tx - x) / 90) ** 2 - ((ty - y) / 90) ** 2, 0, 1)))
hs = cv2.GaussianBlur(hgt.astype(np.float32), (0, 0), 14); lit = ss(-0.004, 0.006, (cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=5) / 48) * 0.7 + (cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=5) / 48) * 0.3)[..., None]   # 上が明るい
tcol = cv2.GaussianBlur((np.array([70, 74, 82], np.float32) * (1 - lit) + np.array([116, 122, 132], np.float32) * lit), (0, 0), 3)
trgb = np.ascontiguousarray(tcol.clip(0, 255).astype(np.uint8)); tal = np.ascontiguousarray((np.clip(cv2.GaussianBlur(tm.astype(np.float32), (0, 0), 1.6) * 2 - 0.5, 0, 1) * 255).astype(np.uint8))
fuzz(trgb, tal, tm, tcol, lambda x, y: 26)
Image.fromarray(cv2.cvtColor(np.dstack([trgb, tal]), cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', 'ana_tail.webp'), quality=93, method=6)
if len(sys.argv) > 1:
    comp = np.zeros((H, W + OX, 3), np.float32) + (150, 170, 196)
    k = tal[..., None].astype(np.float32) / 255; comp[1120:1120 + TH, 0:TW] = comp[1120:1120 + TH, 0:TW] * (1 - k) + trgb * k
    k = a[..., None].astype(np.float32) / 255; comp[:, OX:] = comp[:, OX:] * (1 - k) + out * k
    cv2.imwrite(os.path.join(sys.argv[1], 'ana_ref_preview.jpg'), cv2.resize(comp.astype(np.uint8), ((W + OX) * 3 // 5, H * 3 // 5)))
print('ok', W, H)
