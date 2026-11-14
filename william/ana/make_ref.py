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
out = bgr.astype(np.float32) * (1 - w[..., None]) + grey * w[..., None]
res = np.dstack([out.clip(0, 255).astype(np.uint8), a])
from PIL import Image
Image.fromarray(cv2.cvtColor(res, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', 'ana_ref.webp'), quality=92, method=6)
if len(sys.argv) > 1:
    k = a[..., None].astype(np.float32) / 255; comp = (np.zeros((H, W, 3), np.float32) + (150, 170, 196)) * (1 - k) + out * k
    cv2.imwrite(os.path.join(sys.argv[1], 'ana_ref_preview.jpg'), cv2.resize(comp.astype(np.uint8), (W * 3 // 5, H * 3 // 5)))
print('ok', W, H)
