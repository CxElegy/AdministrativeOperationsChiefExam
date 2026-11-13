# Ana（ノルウェージャンフォレストキャット）のテクスチャ：Tororo のテクスチャの色だけを塗り替える（形は変えない）
# 使い方: python3 william/ana/gen_ana.py <元のテクスチャ> public/w/ana.2048/texture_00.png
#   元のテクスチャ = 足の模様を直す前の William のテクスチャ（git show 0856962^:public/w/tororo.2048/texture_00.png）
import sys, math, random
from PIL import Image, ImageFilter, ImageChops
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGBA'); W, H = im.size
px = im.load()
random.seed(7)
GREY = (146, 130, 115); GREY_D = (112, 98, 86); GREY_L = (182, 168, 152); WHITE = (249, 247, 245)  # 写真に合わせて、茶色がかった あたたかい灰色

def lum(c): return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
def mix(a, b, k): return tuple(int(a[i] * (1 - k) + b[i] * k) for i in range(3))

def paint(box, maskfn, colfn, blur=8, keep_shade=True):
    """box の中で、maskfn(u,v) の強さ（0〜1）で colfn(u,v) の色にする。輪郭はぼかす"""
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    m = Image.new('L', (w, h), 0); mp = m.load()
    for y in range(h):
        for x in range(w):
            mp[x, y] = int(255 * max(0, min(1, maskfn(x / w, y / h))))
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    mp = m.load()
    for y in range(h):
        for x in range(w):
            k = mp[x, y] / 255
            if k <= 0.003: continue
            r, g, b, a = px[x0 + x, y0 + y]
            if a == 0: continue
            c = colfn(x / w, y / h)
            if keep_shade:
                s = min(1.0, max(0.75, lum((r, g, b)) / 245))  # 元の陰影を少し残す
                c = tuple(int(v * s) for v in c)
            # 長い毛のざらつき
            n = random.uniform(-6, 6); c = tuple(max(0, min(255, int(v + n))) for v in c)
            px[x0 + x, y0 + y] = (*mix((r, g, b), c, k), a)

def tabby(u, v, base, dark, freq=34):
    # 毛色のむら（うすい しま）：写真では 頭やせなかの灰色に こい すじが入っている
    k = 0.5 + 0.5 * math.sin(u * freq + math.sin(v * 7.0) * 2.2 + v * 3.0)
    return mix(base, dark, 0.55 * k * k)

def clean_white(box, thresh=200):
    """William の灰色の模様を白にもどす（明るい所はそのまま）"""
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            if a and lum((r, g, b)) < thresh and abs(r - g) < 30 and abs(g - b) < 30:
                px[x, y] = (*WHITE, a)

# --- 足：正面の前足の模様を消す（写真では前足は真っ白） ---
ref = {}
for x in range(0, 260):
    cs = [px[x, y] for y in range(636, 664) if px[x, y][3] > 0]
    if cs: ref[x] = tuple(sum(v[i] for v in cs) // len(cs) for i in range(3))
for y in range(668, 900):
    w = 1.0 if 685 <= y <= 880 else (y - 668) / 17 if y < 685 else (900 - y) / 20
    for x in range(0, 260):
        r, g, b, a = px[x, y]
        if a == 0 or x not in ref: continue
        px[x, y] = (*mix((r, g, b), ref[x], w), a)

# --- 頭（正面の顔）：上と目のまわりは灰色、まん中に白い筋（ブレーズ）、口元・あご・ほおは白 ---
HEAD = (1431, 19, 2000, 537)
clean_white(HEAD, 238)
def head_grey(u, v):
    # 写真のアナちゃん：顔は ほとんど白。灰色は ひたいの上と 目の上・外がわ、耳のつけ根だけ。目の下・ほお・口元は白
    du = abs(u - 0.5)
    blaze = 0.07 + 0.30 * max(0, min(1, (v - 0.10) / 0.36)) ** 1.4   # ひたいの白い筋（上は細く、目の高さで 目の内がわまで広がる）
    if du < blaze: return 0
    if v > 0.50: return 0                       # 目の下は白
    if v > 0.40 and du < 0.36: return 0         # 目の下〜横も白
    return 1
def head_col(u, v):
    return tabby(u, v, mix(GREY_D, GREY, min(1, v / 0.55)), (88, 76, 66), 46) if v < 0.55 else mix(GREY, GREY_L, min(1, (v - 0.55) / 0.3))
paint(HEAD, head_grey, head_col, blur=10)

# --- 目のふち・まぶた：William では こい灰色の太いふち。写真のアナちゃんは 細くて うすいので、まわりの毛に近い色にする ---
for box in [(505, 1535, 705, 1810), (730, 1535, 940, 1810)]:   # 目のふち（上下）
    paint(box, lambda u, v: 1, lambda u, v: mix((150, 132, 116), (228, 220, 212), min(1, max(0, (v - 0.35) / 0.3))), blur=0, keep_shade=False)  # 上は灰色、下は白に近く
for box in [(535, 1340, 675, 1528), (780, 1340, 915, 1528)]:   # まぶた
    paint(box, lambda u, v: 1, lambda u, v: (198, 186, 172), blur=0, keep_shade=False)
# --- 耳の内側：写真では 白い長い毛で ほとんど かくれている。ピンクを うすくして 白い毛を描く ---
from PIL import ImageDraw
for box in [(1247, 1432, 1400, 1693), (1427, 1427, 1588, 1692)]:
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            if a: px[x, y] = (*mix((r, g, b), (236, 224, 214), 0.72), a)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(46):
        bx = x0 + random.uniform(0.15, 0.85) * (x1 - x0); by = y1 - random.uniform(0.02, 0.35) * (y1 - y0); L = random.uniform(0.3, 0.75) * (y1 - y0); dx = random.uniform(-0.18, 0.18) * L
        d.line([(bx, by), (bx + dx * 0.5, by - L * 0.5), (bx + dx, by - L)], fill=(252, 250, 246, random.randint(150, 235)), width=random.choice([2, 3, 3, 4]))
    lp = lay.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]; lr, lg, lb, la = lp[x, y]
            if a and la: px[x, y] = (*mix((r, g, b), (lr, lg, lb), la / 255), a)

# --- 耳の外側（灰色） ---
for box in [(1260, 1700, 1590, 1990), (1600, 1450, 2020, 1700)]:
    clean_white(box, 120)
    paint(box, lambda u, v: 1, lambda u, v: mix(GREY_D, GREY, v), blur=0)

# --- 体の前（胸）：首輪を消して白に。肩の両わきに灰色 ---
FRONT = (1380, 609, 2025, 1460)
for x in range(FRONT[0], FRONT[2]):
    top = px[x, 762][:3] if px[x, 762][3] else WHITE; bot = px[x, 880][:3] if px[x, 880][3] else WHITE
    for y in range(764, 879):
        r, g, b, a = px[x, y]
        if a: px[x, y] = (*mix(top, bot, (y - 764) / 115), a)  # 首輪を消して、上と下の色をなめらかにつなぐ
def front_grey(u, v):
    side = max(0, (0.16 - min(u, 1 - u)) / 0.16)  # 外側ほど灰色
    return side * (1 if v < 0.55 else max(0, 1 - (v - 0.55) / 0.2))
paint(FRONT, front_grey, lambda u, v: GREY, blur=14)

# --- 体のうしろ（せなか・おしり）：灰色のまだら、まん中下は白 ---
BACK = (520, 22, 1400, 1082)
def back_grey(u, v):
    if u < 0.09 and v < 0.5: return 0  # うしろ足の絵と重なる所はぬらない
    du = abs(u - 0.5)
    if v < 0.30: return 1                      # 肩・せなか
    if du > 0.30 - (v - 0.30) * 0.15: return 1  # わき腹・おしりの外側
    return 0
paint(BACK, back_grey, lambda u, v: tabby(u, v, mix(GREY_D, GREY, v), (90, 78, 68), 30), blur=18)

# --- しっぽ：濃い灰色、ふさふさ（根もとは少し明るい） ---
TAIL = (420, 1080, 1400, 1390)
x0, y0, x1, y1 = TAIL
for y in range(y0, y1):
    for x in range(x0, x1):
        r, g, b, a = px[x, y]
        if a == 0 or lum((r, g, b)) > 180 or max(r, g, b) - min(r, g, b) > 30: continue  # しっぽ（灰色）だけ
        u = (x - x0) / (x1 - x0)
        c = mix(GREY_L, (76, 73, 72), min(1, u * 1.25)); n = random.uniform(-8, 8)
        px[x, y] = (*(max(0, min(255, int(v + n))) for v in c), a)

# --- 目：こはく色（外は金色、ひとみの近くは 少し黄みどり）。ひとみは 写真のように 大きめのたて長 ---
for (cx, cy) in [(610, 1882), (845, 1882)]:
    for y in range(cy - 62, cy + 62):
        for x in range(cx - 66, cx + 66):
            r, g, b, a = px[x, y]
            if a == 0: continue
            d = math.hypot((x - cx) / 56, (y - cy) / 56)
            if max(r, g, b) - min(r, g, b) > 40 or lum((r, g, b)) < 90:   # 目の色の所と ひとみ
                c = mix((176, 168, 70), (204, 150, 38), min(1, d * 1.15))
                if d > 0.86: c = mix(c, (96, 66, 24), min(1, (d - 0.86) / 0.14))
                e = math.hypot((x - cx) / 21, (y - cy) / 40)
                if e < 1: c = (22, 18, 14)
                elif e < 1.12: c = mix((22, 18, 14), c, (e - 1) / 0.12)
                px[x, y] = (*c, a)
im.save(out)
print('saved', out)
