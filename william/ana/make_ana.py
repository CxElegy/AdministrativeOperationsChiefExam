# アナちゃんのキャラクター絵を 0 から描く（写真の輪郭は使わない）。出力：william/assets/ana_{tail,body,ears,head}.webp（890×980、同じ座標）
# 使い方: python3 william/ana/make_ana.py [プレビューを書くフォルダ]
# 設計：
#   - 形は 立体（だ円体の組み合わせ）として作る：まるい頭＋ほおの毛、洋なし形の体、まるい足先、羽のようなしっぽ、大きな耳
#   - 光は 左上から。立体の向き（法線）で 明るさを決め、あごの下・体の下・右がわに 影を落とす
#   - 毛は 先の細い毛を 1 本ずつ、立体の表面にそって（顔は鼻から外へ、胸は首から下へ）重ねる。ふちは 毛先が はみ出して ふわふわになる
#   - かわいさ：頭を大きく、目は 顔の下より・大きく・はなして、鼻と口は 小さく まん中に
#   - アナちゃんらしさ：灰色は 耳・ひたいの両がわ・目の外がわ・体の両わき・しっぽ。ひたいの白い筋が 口元へ広がる。胸は 白い長い毛
import sys, os, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
W, H = 890, 980; CX = 370
rng = np.random.RandomState(5)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
WHITE = np.array([246, 248, 250], np.float32); GREY = np.array([138, 144, 152], np.float32); DARK = np.array([92, 96, 104], np.float32)   # BGR
LIGHT = np.array([-0.38, -0.55, 0.74]); LIGHT /= np.linalg.norm(LIGHT)

def solid(ells):
    """だ円体の集まり → (中かどうか, 高さ, 法線)"""
    h = np.zeros((H, W), np.float32)
    for cx, cy, rx, ry, rz in ells:
        d2 = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        h = np.maximum(h, np.sqrt(np.clip(1 - d2, 0, 1)) * rz)
    hs = cv2.GaussianBlur(h, (0, 0), 20)                                     # なめらかな ひとつの かたまりに（つなぎ目に 段を作らない）
    gx, gy = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=5) / 48, cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=5) / 48
    n = np.dstack([-gx, -gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return h > 0, hs, n

def shade(n, amb=0.83, k=0.2):
    return (amb + k * np.clip(n @ LIGHT, 0, 1)).astype(np.float32)

def noise(scale, seed):
    r = np.random.RandomState(seed).rand(H // scale + 2, W // scale + 2).astype(np.float32)
    return cv2.resize(r, (W, H), interpolation=cv2.INTER_CUBIC)

def paint(mask, col, flow, n, length, width, order):
    """mask の中に根もとをばらまき、flow の向きへ 先の細い毛を引く。order が大きい毛から先に描く（上の毛が かぶさる）"""
    kk = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)
    rgb = np.ascontiguousarray((col * kk[..., None]).clip(0, 255).astype(np.uint8)); al = np.ascontiguousarray((kk * 255).astype(np.uint8))
    ys, xs = np.where(mask); idx = rng.randint(0, len(xs), n); px, py = xs[idx], ys[idx]
    FX, FY = flow; L0 = length if isinstance(length, np.ndarray) else np.full((H, W), length, np.float32)
    for i in np.argsort(-(order[py, px] + rng.rand(n) * 8)):
        x, y = int(px[i]), int(py[i])
        ang = math.atan2(FY[y, x], FX[y, x]) + (rng.rand() - 0.5) * 0.5
        L = L0[y, x] * (0.55 + rng.rand() * 0.9); w = width * (0.6 + rng.rand() * 0.7)
        tx, ty = x + math.cos(ang) * L, y + math.sin(ang) * L
        bend = (rng.rand() - 0.5) * 0.22 * L; mx, my = (x + tx) / 2 - math.sin(ang) * bend, (y + ty) / 2 + math.cos(ang) * bend
        nx, ny = -math.sin(ang) * w / 2, math.cos(ang) * w / 2
        pts = np.array([[x + nx, y + ny], [mx + nx * 0.6, my + ny * 0.6], [tx, ty], [mx - nx * 0.6, my - ny * 0.6], [x - nx, y - ny]]) * 8
        r = rng.rand(); c = col[y, x] * (1.05 if r > 0.78 else 0.93 if r < 0.2 else 1 + (rng.rand() - 0.5) * 0.05)   # 明るい毛・影の毛を まぜる
        cv2.fillConvexPoly(rgb, pts.astype(np.int32), tuple(float(v) for v in c.clip(0, 255)), cv2.LINE_AA, 3); cv2.fillConvexPoly(al, pts.astype(np.int32), 255, cv2.LINE_AA, 3)
    return np.dstack([rgb, al])

def norm2(fx, fy):
    m = np.hypot(fx, fy) + 1e-6; return fx / m, fy / m
def lerp(a, b, k): return a * (1 - k[..., None]) + b * k[..., None]
def ss(a, b, v): return np.clip((v - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((v - a) / (b - a), 0, 1))

n1, n2 = noise(26, 1), noise(9, 2)
tabby = 0.5 + 0.5 * np.sin(xx * 0.11 + np.sin(yy * 0.045) * 2.4 + n1 * 5)                  # うすい しま
grey_col = lerp(GREY[None, None], DARK[None, None], 0.5 * tabby ** 2 * (0.5 + n2 * 0.5))

# ---------- 体（洋なし形。胸は前へ ふくらむ） ----------
bm, bh, bn = solid([(CX, 560, 205, 185, 190), (CX, 705, 255, 170, 175), (CX, 500, 150, 120, 150)])
edge = np.abs(xx - CX) + n1 * 26
flank = ss(185, 235, edge + (yy - 560) * 0.06) * ss(500, 560, yy)                           # 両わきは灰色（下ほど広い）
flank = np.maximum(flank, ss(150, 205, (xx - CX) + n1 * 22) * ss(540, 600, yy) * ss(820, 760, yy))   # 右がわは 少し広く
bcol = lerp(np.zeros((H, W, 3), np.float32) + WHITE, grey_col, flank) * shade(bn)[..., None]
bcol *= (1 - 0.07 * ss(0, 240, np.abs(xx - CX)) ** 2)[..., None]                               # 体の まるみ：はしへ行くほど 少し暗く
bcol *= (1 - 0.16 * ss(560, 470, yy) * ss(210, 60, np.abs(xx - CX)))[..., None]              # あごの下の影
bcol *= (1 - 0.10 * ss(770, 880, yy))[..., None]                                             # 体の下の影
bflow = norm2((xx - CX) / 330.0, np.ones_like(xx))
body = paint(bm, bcol, bflow, 80000, np.where(yy < 720, 40.0, 24.0).astype(np.float32), 1.9, yy)
# 足先（まるい。体の毛の下から 出る）
pm, ph, pn = solid([(302, 858, 60, 36, 40), (438, 858, 60, 36, 40)])
pcol = (np.zeros((H, W, 3), np.float32) + WHITE) * shade(pn, 0.88, 0.14)[..., None]
paws = paint(pm, pcol, norm2(np.where(xx < CX, xx - 302, xx - 438) * 0.02, np.ones_like(xx)), 9000, 9.0, 1.7, yy)
pb = np.ascontiguousarray(paws[..., :3])
for cx in (302, 438):
    for dx in (-17, 0, 17): cv2.line(pb, (int((cx + dx) * 8), 866 * 8), (int((cx + dx * 1.1) * 8), 886 * 8), (196, 190, 200), 2, cv2.LINE_AA, 3)   # 指のあいだ
paws[..., :3] = pb
k = paws[..., 3:].astype(np.float32) / 255 * (1 - body[..., 3:].astype(np.float32) / 255 * (yy < 838)[..., None])
body[..., :3] = (body[..., :3] * (1 - k) + paws[..., :3] * k).astype(np.uint8); body[..., 3] = np.maximum(body[..., 3], (k[..., 0] * 255).astype(np.uint8))

# ---------- 頭（まるい頭＋ほおの毛） ----------
HX, HY = CX, 330; MX, MY = CX, 395                                                           # 頭のまん中／鼻
hm, hh, hn = solid([(HX, HY, 180, 165, 170), (238, 392, 86, 74, 80), (502, 392, 86, 74, 80), (HX, 425, 150, 84, 120)])
du = np.abs(xx - HX) + (n1 - 0.5) * 18; v = yy
blaze = 16 + 118 * ss(215, 372, v) ** 1.5                                                    # ひたいの白い筋：上は細く、目の高さで 目の内がわまで
g = (du > blaze).astype(np.float32) * ss(398, 352, v - (du - 120) * 0.42)                    # 目より下は白。外がわほど 灰色が下まで
g = cv2.GaussianBlur(np.clip(g, 0, 1), (0, 0), 5)
hcol = lerp(np.zeros((H, W, 3), np.float32) + WHITE, grey_col, g) * shade(hn, 0.84, 0.19)[..., None]
hcol *= (1 - 0.08 * ss(430, 500, yy) * (g < 0.5))[..., None]                                 # ほおの下は 少し影
# 鼻すじ・口元の ふくらみ（マズル）を 少し明るく
muz = np.exp(-(((xx - MX) / 62) ** 2 + ((yy - 412) / 40) ** 2)); hcol = np.clip(hcol * (1 + 0.05 * muz[..., None]), 0, 255)
fx, fy = xx - MX, (yy - (MY - 30)) * 0.9; lowc = (yy > MY - 10) & (np.abs(xx - MX) > 70)
fx, fy = np.where(lowc, (xx - MX) * 0.016, fx), np.where(lowc, 1.0, fy)
hlen = (7 + np.clip(np.hypot(xx - MX, yy - MY) * 0.11, 0, 22)) * np.where(lowc, 1.6, 1.0)
head = paint(hm, hcol, norm2(fx, fy), 62000, hlen.astype(np.float32), 1.6, np.hypot(xx - MX, (yy - MY) * 1.1) + np.where(yy > MY, (yy - MY) * 0.7, 0))
hb = np.ascontiguousarray(head[..., :3])
# 鼻（小さい ピンクの逆三角）
nose = np.array([[MX - 15, MY - 8], [MX + 15, MY - 8], [MX + 6, MY + 5], [MX, MY + 9], [MX - 6, MY + 5]]) * 8
cv2.fillPoly(hb, [nose.astype(np.int32)], (178, 160, 232), cv2.LINE_AA, 3); cv2.polylines(hb, [nose.astype(np.int32)], True, (150, 128, 200), 1, cv2.LINE_AA, 3)
cv2.ellipse(hb, (int((MX - 4) * 8), int((MY - 4) * 8)), (5 * 8, 2 * 8), 0, 0, 360, (215, 205, 248), -1, cv2.LINE_AA, 3)
head[..., :3] = hb

# ---------- 耳（べつの部品。大きく、少し外向き。中は うすいピンクと 白い長い毛、先に 長い毛） ----------
ears = np.zeros((H, W, 4), np.uint8); eb = np.ascontiguousarray(ears[..., :3]); ea = np.ascontiguousarray(ears[..., 3])
for sx in (-1, 1):
    X = lambda d: HX + sx * d
    pts = np.array([[X(46), 236], [X(150), 56], [X(226), 290]], np.float32); tip = pts[1]; cen = pts.mean(axis=0)
    cv2.fillPoly(eb, [(pts * 8).astype(np.int32)], (120, 126, 134), cv2.LINE_AA, 3); cv2.fillPoly(ea, [(pts * 8).astype(np.int32)], 255, cv2.LINE_AA, 3)
    inner = cen + (pts - cen) * 0.66 + [0, 12]
    cv2.fillPoly(eb, [(inner * 8).astype(np.int32)], (188, 180, 224), cv2.LINE_AA, 3)
    for i in range(420):                                                                     # 外側の短い毛（ふちを やわらかく）
        t = rng.rand(); q = (pts[0] if rng.rand() < 0.5 else pts[2]) * (1 - t) + tip * t; q = q + (cen - q) * rng.uniform(-0.03, 0.2)
        L = rng.uniform(5, 12); ang = math.atan2(tip[1] - cen[1], tip[0] - cen[0]) + rng.uniform(-0.7, 0.7); gcol = rng.uniform(100, 150)
        l2 = np.array([q, q + [math.cos(ang) * L, math.sin(ang) * L]]) * 8
        cv2.line(eb, tuple(l2[0].astype(int)), tuple(l2[1].astype(int)), (gcol, gcol + 5, gcol + 12), 2, cv2.LINE_AA, 3); cv2.line(ea, tuple(l2[0].astype(int)), tuple(l2[1].astype(int)), 255, 2, cv2.LINE_AA, 3)
    for i in range(14):                                                                      # 耳の先の長い毛
        L = rng.uniform(18, 40); ang = math.radians(-90 + sx * rng.uniform(0, 26)); q = tip + rng.uniform(-2, 2, 2)
        l2 = (np.array([q, q + [math.cos(ang) * L * 0.5 + sx * 2, math.sin(ang) * L * 0.5], q + [math.cos(ang) * L, math.sin(ang) * L]]) * 8).astype(np.int32)
        cv2.polylines(eb, [l2], False, (84, 88, 96), 1, cv2.LINE_AA, 3); cv2.polylines(ea, [l2], False, 255, 1, cv2.LINE_AA, 3)
    for i in range(80):                                                                      # 耳の中から 外へ流れる 白い長い毛
        t = rng.uniform(0.1, 0.9); q = inner[0] * (1 - t) + inner[2] * t + [0, -rng.uniform(0, 40)]; L = rng.uniform(30, 78); ang = math.radians(-90 + sx * rng.uniform(8, 72))
        l2 = (np.array([q, q + [math.cos(ang) * L * 0.5 + sx * 4, math.sin(ang) * L * 0.5], q + [math.cos(ang) * L, math.sin(ang) * L]]) * 8).astype(np.int32)
        cv2.polylines(eb, [l2], False, (248, 250, 252), 1, cv2.LINE_AA, 3); cv2.polylines(ea, [l2], False, 255, 1, cv2.LINE_AA, 3)
ears = np.dstack([eb, ea])

# ---------- しっぽ（羽のよう。体の右うしろから 上へ） ----------
tm = np.zeros((H, W), np.uint8); spine = []
for s in np.linspace(0, 1, 220):
    u = 1 - s; x = u * u * 560 + 2 * u * s * 760 + s * s * 700; y = u * u * 800 + 2 * u * s * 760 + s * s * 500
    spine.append((x, y)); cv2.circle(tm, (int(x), int(y)), int(26 + 46 * math.sin(math.pi * min(1, 0.12 + s * 0.92)) ** 0.7), 1, -1)
spine = np.array(spine, np.float32)
d = (xx[..., None] - spine[None, None, ::6, 0]) ** 2 + (yy[..., None] - spine[None, None, ::6, 1]) ** 2
ni = np.argmin(d, axis=2) * 6; sx_, sy_ = spine[ni, 0], spine[ni, 1]; nj = np.clip(ni + 6, 0, len(spine) - 1); tx_, ty_ = spine[nj, 0] - sx_, spine[nj, 1] - sy_
rad = np.sqrt(d.min(axis=2)); core = np.clip(1 - rad / 70, 0, 1)
tcol = lerp(DARK[None, None] * 0.92, GREY[None, None] * 1.02, ss(0.2, 1.0, core) * 0.7 + n2 * 0.25) * (0.86 + 0.2 * ss(60, 0, (xx - sx_) * 0.5 + (yy - sy_) * 0.7 + 30))[..., None]
tail = paint(tm > 0, tcol, norm2(tx_ * 0.5 + (xx - sx_) * 1.5, ty_ * 0.5 + (yy - sy_) * 1.5), 26000, 34.0, 2.0, -rad)

def save(img, name):
    from PIL import Image
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', name), quality=92, method=6)
for nm, im in (('tail', tail), ('body', body), ('ears', ears), ('head', head)): save(im, 'ana_%s.webp' % nm)
if len(sys.argv) > 1:
    comp = np.zeros((H, W, 3), np.float32) + (150, 170, 196)
    for im in (tail, body, ears, head): f = im.astype(np.float32); k2 = f[..., 3:] / 255; comp = comp * (1 - k2) + f[..., :3] * k2
    cv2.imwrite(os.path.join(sys.argv[1], 'ana_illust_preview.jpg'), comp.astype(np.uint8))
print('ok')
