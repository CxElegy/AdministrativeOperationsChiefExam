# アナちゃんを Tororo（William）と同じ絵柄で 0 から描く。出力：william/assets/ana_{tail,body,ears,head}.webp（890×980、同じ座標）
# 使い方: python3 william/ana/make_ana.py [プレビューを書くフォルダ]
# Tororo の絵柄（観察して決めたこと）：
#   - 線（ふち取り）はない。ふちは 細い短い毛で ぼんやり
#   - 塗りは エアブラシのように なめらか。白い毛の影は 灰色ではなく うすいピンクがかった色
#   - 体型は 本物の猫に近い（頭は小さめ、体と足が長い）
#   - 模様（灰色）は ふちが ぼけた やわらかい塗り
# アナちゃんらしさ：長毛（ふちの毛が長い・ほおと胸に ゆたかな毛・太いしっぽ）、灰色は 耳・ひたいの両がわ・目の外がわ・体のわき・しっぽ、ひたいの白い筋
import sys, os, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
W, H = 890, 980; CX = 370
rng = np.random.RandomState(5)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
WHITE = np.array([251, 253, 255], np.float32); SHADOW = np.array([234, 226, 240], np.float32)      # BGR：白と、ピンクがかった影
GREY = np.array([126, 128, 134], np.float32); DARK = np.array([98, 98, 106], np.float32)
LIGHT = np.array([-0.3, -0.6, 0.74]); LIGHT /= np.linalg.norm(LIGHT)
def ss(a, b, v): t = np.clip((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def lerp(a, b, k): return a * (1 - k[..., None]) + b * k[..., None]
def noise(scale, seed): return cv2.resize(np.random.RandomState(seed).rand(H // scale + 2, W // scale + 2).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
n1 = noise(40, 1)

def solid(ells, blur=22):
    h = np.zeros((H, W), np.float32)
    for cx, cy, rx, ry, rz in ells: h = np.maximum(h, np.sqrt(np.clip(1 - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2, 0, 1)) * rz)
    hs = cv2.GaussianBlur(h.astype(np.float32), (0, 0), blur); gx, gy = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=5) / 48, cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=5) / 48
    n = np.dstack([-gx, -gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return h > 0, ss(0.15, 0.62, n @ LIGHT)                                 # 形、明るさ 0〜1（左上が明るい）

def soft(mask, lit, grey, fuzz, extra_shadow=None):
    """なめらかな塗り＋ふちの細い毛。lit=明るさ、grey=灰色の模様 0〜1、fuzz=ふちの毛の長さ（画素。場所ごと）"""
    k = lit if extra_shadow is None else lit * (1 - extra_shadow)
    col = lerp(lerp(np.zeros((H, W, 3), np.float32) + SHADOW, np.zeros((H, W, 3), np.float32) + WHITE, k), lerp(np.zeros((H, W, 3), np.float32) + DARK, np.zeros((H, W, 3), np.float32) + GREY, k), grey)
    col = cv2.GaussianBlur(col, (0, 0), 3)
    m = mask.astype(np.uint8); a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.6)
    rgb = np.ascontiguousarray(col.clip(0, 255).astype(np.uint8)); al = np.ascontiguousarray((np.clip(a * 2 - 0.5, 0, 1) * 255).astype(np.uint8))
    # ふちの細い毛：輪郭から 外へ、1 本ずつ（色は その場所の毛の色）
    din = cv2.GaussianBlur(cv2.distanceTransform(m, cv2.DIST_L2, 5), (0, 0), 3); gx, gy = cv2.Sobel(din, cv2.CV_32F, 1, 0), cv2.Sobel(din, cv2.CV_32F, 0, 1)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        for (x, y) in c[:, 0]:
            L0 = fuzz[y, x] if isinstance(fuzz, np.ndarray) else fuzz
            for _ in range(2 if L0 > 9 else 1):
                nx, ny = -gx[y, x], -gy[y, x]; d = math.hypot(nx, ny) + 1e-6; ang = math.atan2(ny / d, nx / d) + rng.uniform(-0.55, 0.55) + (0.35 if ny > -0.2 else 0) * np.sign(nx) * 0   # 外向き
                ang += 0.5 * (1 if (math.pi / 2 - ang + math.pi) % (2 * math.pi) - math.pi > 0 else -1) * min(1, L0 / 20)                                                    # 長い毛は 重さで 下へ たれる
                L = L0 * rng.uniform(0.35, 1.0); sx0, sy0 = x - nx / d * 3, y - ny / d * 3
                p = (np.array([[sx0, sy0], [sx0 + math.cos(ang) * L * 0.6, sy0 + math.sin(ang) * L * 0.6], [x + math.cos(ang) * L, y + math.sin(ang) * L + L * 0.06]]) * 8).astype(np.int32)
                c3 = tuple(float(v) for v in col[int(np.clip(sy0, 0, H - 1)), int(np.clip(sx0, 0, W - 1))].clip(0, 255))
                cv2.polylines(rgb, [p], False, c3, 1, cv2.LINE_AA, 3); cv2.polylines(al, [p], False, 235, 1, cv2.LINE_AA, 3)
    return np.dstack([rgb, al])

def clumps(img, mask, n, ybox, size=(34, 64), strength=0.5):
    """長い毛の重なり：うすいピンクの影で 毛の束の先（下向きの「く」）を ぼかして描く"""
    lay = np.zeros((H, W), np.float32); ys, xs = np.where(mask & (yy > ybox[0]) & (yy < ybox[1]))
    for _ in range(n):
        i = rng.randint(len(xs)); x, y = xs[i], ys[i]; tw = rng.uniform(*size); th = tw * rng.uniform(0.9, 1.5); lean = (x - CX) / 300.0
        p = (np.array([[x - tw / 2, y - th], [x - tw * 0.2 + lean * th * 0.5, y - th * 0.3], [x + lean * th, y]]) * 8).astype(np.int32)
        cv2.polylines(lay, [p if rng.rand() < 0.5 else (p * [-1, 1] + [int(2 * (x + lean * th) * 8), 0])], False, 1.0, 4, cv2.LINE_AA, 3)
    lay = cv2.GaussianBlur(lay, (0, 0), 4).clip(0, 1) * strength
    white = (img[..., :3].astype(np.float32).min(axis=2) > 205) & (img[..., 3] > 200)
    kk = (lay * white)[..., None]; img[..., :3] = (img[..., :3] * (1 - kk) + (SHADOW * 0.96) * kk).astype(np.uint8)

# ---------- 体（Tororo と同じく たて長。胸の毛が ゆたかで、前足は 毛の下から出る） ----------
bm, bl = solid([(CX, 470, 150, 150, 170), (CX, 560, 185, 170, 180), (CX, 700, 215, 175, 180)])
legs_m, legs_l = solid([(326, 770, 44, 110, 60), (414, 770, 44, 110, 60), (322, 866, 54, 27, 50), (418, 866, 54, 27, 50)], blur=8)
flank = ss(150, 200, np.abs(xx - CX) + n1 * 30 + (700 - yy) * 0.05) * ss(520, 600, yy)                 # 体のわきは灰色
shadow = 0.45 * ss(450, 385, yy) * ss(150, 40, np.abs(xx - CX)) + 0.25 * ss(820, 890, yy)             # あごの下・体の下の影
body = soft(bm, bl, cv2.GaussianBlur(flank, (0, 0), 12), np.where(yy < 640, 22.0, 16.0).astype(np.float32), shadow)
clumps(body, bm, 46, (430, 700))
legs = soft(legs_m, legs_l * 0.75 + 0.25, np.zeros((H, W), np.float32), 4.0, 0.5 * ss(790, 700, yy) + 0.5 * ss(22, 0, np.abs(xx - CX)) * (yy < 850))
lb = np.ascontiguousarray(legs[..., :3])
for cx in (322, 418):
    for dx in (-16, 0, 16): cv2.line(lb, (int((cx + dx) * 8), 866 * 8), (int((cx + dx * 1.1) * 8), 888 * 8), (214, 204, 222), 2, cv2.LINE_AA, 3)   # 指のあいだ（うすい線）
legs[..., :3] = lb
# 胸の毛が 足の上に かぶさる：足は 体の毛より下の部分だけ 見える
cover = cv2.GaussianBlur(((bm) & (yy < 700 + 22 * np.sin(xx * 0.09))).astype(np.float32), (0, 0), 3)
k = legs[..., 3:].astype(np.float32) / 255 * (1 - cover[..., None])
out = body.astype(np.float32); out[..., :3] = out[..., :3] * (1 - k) + legs[..., :3] * k; out[..., 3] = np.maximum(out[..., 3], k[..., 0] * 255); body = out.astype(np.uint8)

# ---------- 頭（小さめの まるい頭＋ほおの ゆたかな毛） ----------
HX, HY = CX, 255
hm, hl = solid([(HX, HY, 140, 118, 130), (262, 302, 68, 58, 60), (478, 302, 68, 58, 60), (HX, 322, 112, 60, 90)], blur=16)
du = np.abs(xx - HX) + (n1 - 0.5) * 16
blaze = 12 + 78 * ss(170, 262, yy) ** 1.4                                                            # ひたいの白い筋：上は細く、目の高さで 目の内がわまで
g = (du > blaze).astype(np.float32) * ss(290, 250, yy - (du - 80) * 0.5)                             # 目より下は白、外がわほど 灰色が下まで
head = soft(hm, hl, cv2.GaussianBlur(g, (0, 0), 9), np.where((yy > 285) & (np.abs(xx - HX) > 50), 20.0, 7.0).astype(np.float32), 0.25 * ss(330, 372, yy))
clumps(head, hm, 10, (300, 372), size=(22, 40), strength=0.4)

# ---------- 耳（大きい。外は灰色、中は ピンクの ぼかしと 細い白い毛） ----------
em = np.zeros((H, W), np.uint8); inner = np.zeros((H, W), np.float32); hairs = []
for sx in (-1, 1):
    X = lambda d: HX + sx * d
    pts = np.array([[X(28), 196], [X(118), 34], [X(172), 240]], np.float32); cv2.fillPoly(em, [pts.astype(np.int32)], 1)
    cen = pts.mean(axis=0); inn = cen + (pts - cen) * 0.62 + [0, 12]; cv2.fillPoly(inner, [inn.astype(np.int32)], 1.0)
    for i in range(34): t = rng.uniform(0.05, 0.95); q = inn[0] * (1 - t) + inn[2] * t + [0, -rng.uniform(0, 26)]; hairs.append((q, rng.uniform(22, 52), math.radians(-90 + sx * rng.uniform(6, 62)), sx, (250, 251, 253)))
    for i in range(7): hairs.append((pts[1] + rng.uniform(-2, 2, 2), rng.uniform(10, 24), math.radians(-90 + sx * rng.uniform(0, 22)), sx, (112, 112, 120)))
em = cv2.GaussianBlur(em.astype(np.float32), (0, 0), 3) > 0.5; _, el = solid([(HX - 112, 160, 70, 100, 40), (HX + 112, 160, 70, 100, 40)], blur=10)
ears = soft(em, np.clip(el * 0.5 + 0.55, 0, 1), np.ones((H, W), np.float32), 5.0)
ki = cv2.GaussianBlur(inner, (0, 0), 7)[..., None] * 0.92; pink = lerp(np.zeros((H, W, 3), np.float32) + (176, 162, 222), np.zeros((H, W, 3), np.float32) + (214, 206, 244), ss(120, 230, yy))
ears[..., :3] = (ears[..., :3] * (1 - ki) + pink * ki).astype(np.uint8)
eb = np.ascontiguousarray(ears[..., :3]); ea = np.ascontiguousarray(ears[..., 3])
for q, L, ang, sx, c in hairs:
    l2 = (np.array([q, q + [math.cos(ang) * L * 0.5 + sx * 3, math.sin(ang) * L * 0.5], q + [math.cos(ang) * L, math.sin(ang) * L]]) * 8).astype(np.int32)
    cv2.polylines(eb, [l2], False, c, 1, cv2.LINE_AA, 3); cv2.polylines(ea, [l2], False, 255, 1, cv2.LINE_AA, 3)
ears = np.dstack([eb, ea])

# ---------- しっぽ（太い羽のよう。体の右うしろから 床にそって 先が上がる） ----------
tm = np.zeros((H, W), np.uint8); sp = []
for s in np.linspace(0, 1, 200):
    u = 1 - s; x = u * u * 520 + 2 * u * s * 760 + s * s * 790; y = u * u * 850 + 2 * u * s * 880 + s * s * 640
    sp.append((x, y)); cv2.circle(tm, (int(x), int(y)), int(24 + 40 * math.sin(math.pi * min(1, 0.15 + s * 0.9)) ** 0.7), 1, -1)
_, tl = solid([(x, y, 70, 70, 60) for x, y in sp[::12]], blur=14)
tail = soft(tm > 0, tl * 0.8, np.ones((H, W), np.float32), 26.0)

def save(img, name):
    from PIL import Image
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', name), quality=93, method=6)
for nm, im in (('tail', tail), ('body', body), ('ears', ears), ('head', head)): save(im, 'ana_%s.webp' % nm)
if len(sys.argv) > 1:
    comp = np.zeros((H, W, 3), np.float32) + (150, 170, 196)
    for im in (tail, body, ears, head): f = im.astype(np.float32); k2 = f[..., 3:] / 255; comp = comp * (1 - k2) + f[..., :3] * k2
    cv2.imwrite(os.path.join(sys.argv[1], 'ana_illust_preview.jpg'), comp.astype(np.uint8))
print('ok')
