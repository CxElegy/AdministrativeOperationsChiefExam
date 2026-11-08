# 元の絵（william/assets/bldg_orig.webp：640x1280・各階4窓）から、各階8窓＋中央の柱の下に玄関があるマンションを作る
#   python3 william/compose_bldg.py   → william/assets/bldg.webp（窓の位置は tpl.html の WX / WY と同じ）
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
src = np.asarray(Image.open(os.path.join(A, 'bldg_orig.webp')).convert('RGB')).astype(np.float32)
H = src.shape[0]
SH = 528                      # 右側（右の端・月）をずらす量
W = 640 + SH
dst = np.zeros((H, W, 3), np.float32)
TOP, BOT = 236, 1190          # 外壁の範囲（屋上の下〜地面）
# 左の端と右の端はそのまま
dst[:, :110] = src[:, :110]
dst[:, 528 + SH:] = src[:, 528:]
# 屋上より上：左は 0..300 をそのまま、右は 406.. をずらす、間は手すりを繰り返し、空は横に伸ばす
dst[:TOP, :300] = src[:TOP, :300]
dst[:TOP, 406 + SH:] = src[:TOP, 406:]
mid0, mid1 = 300, 406 + SH
for x in range(mid0, mid1):
    dst[170:TOP, x] = src[170:TOP, 300 + (x - mid0) % 106]
sky = Image.fromarray(src[:170, 300:406].astype(np.uint8)).resize((mid1 - mid0, 170), Image.BICUBIC)
dst[:170, mid0:mid1] = np.asarray(sky).astype(np.float32)
# 外壁：窓と窓の間の縦の帯（x=205..225）の平均を横に伸ばす（明るさの縦のグラデーションと階の帯の線がそのまま残る）
col = src[TOP:BOT, 205:226].mean(1)
dst[TOP:BOT, 110:528 + SH] = col[:, None, :]
# 地面：横に伸ばす
g = Image.fromarray(src[BOT:, 110:528].astype(np.uint8)).resize((528 + SH - 110, H - BOT), Image.BICUBIC)
dst[BOT:, 110:528 + SH] = np.asarray(g).astype(np.float32)
# 窓：暗い窓（8F の左から2番目）を各階8か所に
win = src[258:327, 230:301]
WX = [125, 230, 336, 441, 652, 757, 863, 968]
WY = [259, 377, 495, 613, 732, 850, 968, 1087]   # 8F → 1F
for y in WY:
    for x in WX:
        dst[y:y + win.shape[0], x:x + win.shape[1]] = win
img = Image.fromarray(dst.clip(0, 255).astype(np.uint8))
# 玄関（中央の柱の下）：ひさし＋明かりのついたガラス扉
d = ImageDraw.Draw(img)
cx = (512 + 652) // 2
d.rectangle([cx - 62, 1098, cx + 62, 1116], fill=(58, 38, 44)); d.line([cx - 62, 1098, cx + 62, 1098], fill=(110, 80, 80), width=2)
door = Image.new('RGB', (100, 72)); dd = ImageDraw.Draw(door)
for i in range(72):
    t = i / 71; dd.line([0, i, 99, i], fill=(int(255 - 18 * t), int(214 - 50 * t), int(150 - 55 * t)))
img.paste(door, (cx - 50, 1116))
for x in [cx - 50, cx - 17, cx + 17, cx + 49]: d.line([x, 1116, x, 1188], fill=(92, 52, 36), width=3)
d.line([cx - 50, 1150, cx + 50, 1150], fill=(92, 52, 36), width=2)
# 玄関の明かりが外壁に少しにじむ
glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).ellipse([cx - 110, 1080, cx + 110, 1230], fill=110)
glow = glow.filter(ImageFilter.GaussianBlur(30))
warm = Image.new('RGB', (W, H), (255, 190, 120))
img = Image.composite(warm, img, glow.point(lambda v: v * 0.45))
img.save(os.path.join(A, 'bldg.webp'), 'WEBP', quality=86)
print('william/assets/bldg.webp', W, H)
