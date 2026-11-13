# Ana（ノルウェージャンフォレストキャット）のテクスチャ：Tororo のテクスチャの色だけを塗り替える（形は変えない）
# 使い方: python3 william/ana/gen_ana.py <元のテクスチャ> public/w/ana.2048/texture_00.png
#   元のテクスチャ = 足の模様を直す前の William のテクスチャ（git show 0856962^:public/w/tororo.2048/texture_00.png）
import sys, math, random
from PIL import Image, ImageFilter, ImageChops
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGBA'); W, H = im.size
px = im.load()
random.seed(7)
GREY = (138, 128, 120); GREY_D = (106, 99, 94); GREY_L = (174, 165, 156); WHITE = (249, 247, 245)

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
    du = abs(u - 0.5)
    blaze = 0.03 + 0.22 * max(0, min(1, (v - 0.18) / 0.42)) ** 1.6  # 上は細く、下へ広がる
    if du < blaze and v > 0.06: return 0
    if v > 0.60 and du < 0.30 + (v - 0.60) * 1.1: return 0  # 口元・ほお
    if v > 0.80: return 0
    return 1
def head_col(u, v):
    return mix(GREY_D, GREY, min(1, v / 0.55)) if v < 0.55 else mix(GREY, GREY_L, min(1, (v - 0.55) / 0.3))
paint(HEAD, head_grey, head_col, blur=10)

# --- まぶた（目を閉じたときに見える皮）：目のまわりと同じ灰色に ---
for box in [(510, 1540, 700, 1690), (740, 1540, 930, 1690), (510, 1690, 700, 1800), (760, 1690, 940, 1800)]:
    paint(box, lambda u, v: 1, lambda u, v: GREY, blur=0)

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
paint(BACK, back_grey, lambda u, v: mix(GREY_D, GREY, v), blur=18)

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

# --- 目：黄みどりがかった金色に（写真のアナちゃん） ---
import colorsys
for y in range(1810, 1940):
    for x in range(530, 910):
        r, g, b, a = px[x, y]
        if a == 0: continue
        h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if sat > 0.35 and 0.03 < h < 0.16:
            h = h + 0.05; l = min(1, l * 1.05)
            rr, gg, bb = colorsys.hls_to_rgb(h, l, sat)
            px[x, y] = (int(rr * 255), int(gg * 255), int(bb * 255), a)
im.save(out)
print('saved', out)
# （このあと、しっぽの絵は透明にしている：x 420〜1402, y 1080〜1392。ただし x 600〜860, y 1270〜1330 は残す。
#   太いしっぽは tpl.html の anaFluff で描く）
