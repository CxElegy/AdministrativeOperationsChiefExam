# アナちゃんの一枚絵（細い毛で描いたイラスト）を作り、Live2D と同じ考え方で 部品（頭・体・しっぽ）に分ける
# 使い方: python3 william/ana/make_ana.py <切り抜いた写真 cut.png（正面で座っている写真、1620×1800、背景は透明）>
#   出力: william/assets/ana_body.webp / ana_head.webp / ana_tail.webp（どれも 890×980、同じ座標）
# しくみ：写真は そのまま使わない。写真からもらうのは「どこが どの色か」と「形」だけ。
#   絵は、先の細い毛を 数万本、毛の流れ（顔は鼻から外へ、体は上から下へ）にそって 下の毛から順に重ねて描く。
#   毛は輪郭の外へ はみ出すので、ふちは 長毛種らしい ふわふわの毛先になる。
import sys, os, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SC = 0.5; PAD = 40
rng = np.random.RandomState(11)
src = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)                      # BGRA 1620×1800
src = cv2.resize(src, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
src = cv2.copyMakeBorder(src, PAD, PAD, PAD, PAD, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
H, W = src.shape[:2]
P = lambda x, y: (x * SC + PAD, y * SC + PAD)                            # 写真の座標 → 絵の座標
# --- 形：体の影（右の床）と うすい所を落として、いちばん大きい かたまりだけ残す ---
a = (src[..., 3] > 170).astype(np.uint8); a[:, int(P(1215, 0)[0]):] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats(a); a = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
# --- 色：写真のざらつきを消して 明るくする（白い毛は ほぼ白、灰色は そのまま）。足りない外側は 近くの色でうめる ---
ae = cv2.erode(a, np.ones((15, 15), np.uint8))                       # ふちの暗い色をさけて、内がわの色を外へ のばす
bgr = cv2.inpaint(src[..., :3], (1 - ae) * 255, 5, cv2.INPAINT_TELEA)
bgr = cv2.edgePreservingFilter(bgr, flags=1, sigma_s=30, sigma_r=0.35).astype(np.float32)
bgr = 255 * (bgr / 255) ** 0.72 * 1.06
hsv = cv2.cvtColor(bgr.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32); hsv[..., 1] *= 1.15
col = cv2.cvtColor(hsv.clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
# --- 部品の境目：頭（あごの線より上）と 体 ---
NX, NY = P(640, 640)                                                     # 鼻
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
chin = P(0, 790)[1] - 45 * ((xx - NX) / 180) ** 2                        # あご〜ほおの毛の下のふち
head_m = (a > 0) & (yy < chin)
body_m = (a > 0) & (yy > chin - 34)
# 顔の部品（目・鼻・口）には 毛をかけない
feat = np.zeros((H, W), np.uint8)
for (x, y, rx, ry) in [(545, 532, 48, 38), (748, 536, 48, 38), (640, 640, 40, 36)]:
    cv2.ellipse(feat, tuple(int(v) for v in P(x, y)), (int(rx * SC), int(ry * SC)), 0, 0, 360, 255, -1)
feat = cv2.GaussianBlur(feat, (0, 0), 4)

def paint(mask, flow, order, n, length, width, base=True):
    """mask の中に根もとをばらまいて、flow の向きへ 先の細い毛を引く。order が大きい毛から先に描く"""
    out = np.zeros((H, W, 4), np.float32)
    if base:                                                             # 下ぬり（すきま防止）
        k = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]
        out[..., :3] = col * k; out[..., 3:] = k
    ys, xs = np.where(mask); idx = rng.randint(0, len(xs), n)
    px, py = xs[idx].astype(np.float32), ys[idx].astype(np.float32)
    o = order(px, py) + rng.rand(n) * 6; srt = np.argsort(-o)
    layer = (out * 255).clip(0, 255).astype(np.uint8)
    rgb = np.ascontiguousarray(layer[..., :3]); al = np.ascontiguousarray(layer[..., 3])
    for i in srt:
        x, y = px[i], py[i]
        if feat[int(y), int(x)] > 90: continue
        fx, fy = flow(x, y); ang = math.atan2(fy, fx) + (rng.rand() - 0.5) * 0.7
        lum = col[int(y), int(x)].mean()
        L = length(x, y) * (0.55 + rng.rand() * 0.9); w = width * (0.6 + rng.rand() * 0.7)
        tx, ty = x + math.cos(ang) * L, y + math.sin(ang) * L
        bend = (rng.rand() - 0.5) * 0.22 * L; mx, my = (x + tx) / 2 - math.sin(ang) * bend, (y + ty) / 2 + math.cos(ang) * bend
        nx, ny = -math.sin(ang) * w / 2, math.cos(ang) * w / 2
        pts = np.array([[x + nx, y + ny], [mx + nx * 0.6, my + ny * 0.6], [tx, ty], [mx - nx * 0.6, my - ny * 0.6], [x - nx, y - ny]]) * 8
        # 1 本ごとに 明るさを少し変える（白い毛にも うすい影の毛を混ぜて、毛の 1 本 1 本が見えるように）
        r = rng.rand(); k = 1.0 + (0.05 if r > 0.75 else -0.07 if r < 0.25 else (rng.rand() - 0.5) * 0.04)
        c = col[int(y), int(x)] * k
        if lum > 215 and r < 0.25: c = c * np.array([1.0, 0.985, 0.965])  # 白い毛の影は 少し青みのある灰色（BGR）
        c = tuple(float(v) for v in c.clip(0, 255))
        cv2.fillConvexPoly(rgb, pts.astype(np.int32), c, cv2.LINE_AA, 3); cv2.fillConvexPoly(al, pts.astype(np.int32), 255, cv2.LINE_AA, 3)
    return np.dstack([rgb, al])

def save(img, name):
    from PIL import Image
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', name), quality=90, method=6)

# 体：毛は上から下へ、外へ少し広がる。胸は長い毛
body = paint(body_m, lambda x, y: ((x - NX) / 380.0, 1.0), lambda x, y: y, 60000, lambda x, y: 50 if y < P(0, 1150)[1] else 34 if y < P(0, 1400)[1] else 12, 2.3)
# 頭：毛は鼻から外へ。ほおの毛は下へ流れて長い。顔のまん中は短い
def head_flow(x, y):
    dx, dy = x - NX, y - (NY - 20)
    if y > NY - 10 and abs(dx) > 60: return (dx * 0.012, 1.0)
    return (dx, dy * 0.9 - 4)
EARS = [P(445, 300), P(850, 300)]
def head_len(x, y):
    if min(math.hypot(x - e[0], y - e[1]) for e in EARS) < 48 and y < P(0, 400)[1]: return 7      # 耳は短い毛（形をくずさない）
    d = math.hypot(x - NX, (y - NY) * 1.1)
    return (8 + min(30, d * 0.16)) * (1.5 if y > NY and abs(x - NX) > 60 else 1)                  # ほおの毛は長い
head = paint(head_m, head_flow, lambda x, y: np.hypot(x - NX, (y - NY) * 1.1) + np.where(y > NY, (y - NY) * 0.6, 0), 36000, head_len, 2.0)
# 耳：頭の毛に うもれないように、あとから 短い毛で 上に描く（耳の中の白い長い毛も）
ear_m = np.zeros((H, W), np.uint8)
for poly in ([(400, 395), (392, 150), (415, 215), (470, 225), (545, 330), (540, 400)], [(770, 400), (790, 300), (870, 232), (905, 175), (912, 300), (900, 400)]):
    cv2.fillPoly(ear_m, [np.array([P(*q) for q in poly], np.int32)], 1)
ear_m = (ear_m > 0) & (a > 0)
ears = paint(ear_m, lambda x, y: ((x - NX) * 0.25, -1.0), lambda x, y: -y, 5000, lambda x, y: 9, 1.8)
eb = np.ascontiguousarray(ears[..., :3]); ea = np.ascontiguousarray(ears[..., 3])
for (cx, cy, sx) in [(470, 330, -1), (835, 335, 1)]:                       # 耳の中から 外へ出る 白い長い毛
    for i in range(46):
        x0, y0 = P(cx + rng.uniform(-30, 30), cy + rng.uniform(-10, 45)); L = rng.uniform(26, 60); ang = math.radians(-90 + sx * rng.uniform(15, 75))
        pts = np.array([[x0, y0], [x0 + math.cos(ang) * L * 0.5 + sx * 3, y0 + math.sin(ang) * L * 0.5], [x0 + math.cos(ang) * L, y0 + math.sin(ang) * L]]) * 8
        cv2.polylines(eb, [pts.astype(np.int32)], False, (246, 248, 250), 1, cv2.LINE_AA, 3); cv2.polylines(ea, [pts.astype(np.int32)], False, 255, 1, cv2.LINE_AA, 3)
k = (ea.astype(np.float32) / 255)[..., None]
head[..., :3] = (head[..., :3] * (1 - k) + eb * k).astype(np.uint8); head[..., 3] = np.maximum(head[..., 3], ea)
# 顔の部品は 写真の形のまま（なめらかにした色）を上にのせる
k = (feat.astype(np.float32) / 255)[..., None]
head[..., :3] = (head[..., :3] * (1 - k) + col * k).astype(np.uint8)
# 口：鼻の下の たての線と、左右へ上がる口もと（写真の形）
hb = np.ascontiguousarray(head[..., :3]); mc = (176, 170, 200)
m0, m1 = P(640, 672), P(640, 700)
cv2.line(hb, tuple(int(v * 8) for v in m0), tuple(int(v * 8) for v in m1), mc, 1, cv2.LINE_AA, 3)
for sx in (-1, 1):
    pts = np.array([P(640, 700), P(640 + sx * 22, 716), P(640 + sx * 48, 708)]) * 8
    cv2.polylines(hb, [pts.astype(np.int32)], False, mc, 1, cv2.LINE_AA, 3)
head[..., :3] = hb
# しっぽ：写真では 体の右うしろに こい灰色の ふさふさ。しんの線にそって 毛を外へ
tail_m = np.zeros((H, W), bool); spine = []
for s in np.linspace(0, 1, 200):
    u = 1 - s; x = u * u * 1040 + 2 * u * s * 1330 + s * s * 1400; y = u * u * 1330 + 2 * u * s * 1300 + s * s * 880
    spine.append(P(x, y)); cv2.circle(tail_m.view(np.uint8), tuple(int(v) for v in P(x, y)), int((38 + 70 * math.sin(math.pi * min(1, 0.15 + s * 0.9)) ** 0.7) * SC), 1, -1)
spine = np.array(spine)
tcol = col.copy(); g = (np.clip((yy - P(0, 880)[1]) / (P(0, 1330)[1] - P(0, 880)[1]), 0, 1))[..., None]
col = np.array([92, 96, 104], np.float32) * (1 - g * 0.25) + rng.rand(H, W, 1).astype(np.float32) * 14   # こい灰色（BGR）。根もとは少し明るい
def tail_flow(x, y):
    i = int(np.argmin((spine[:, 0] - x) ** 2 + (spine[:, 1] - y) ** 2)); j = min(len(spine) - 1, i + 3); tx, ty = spine[j] - spine[max(0, i - 3)]
    ox, oy = x - spine[i][0], y - spine[i][1]; return (tx * 0.6 + ox * 1.4, ty * 0.6 + oy * 1.4)
tail = paint(tail_m, tail_flow, lambda x, y: -np.hypot(x - spine[100][0], y - spine[100][1]), 16000, lambda x, y: 34, 2.6)
col = tcol
save(body, 'ana_body.webp'); save(head, 'ana_head.webp'); save(tail, 'ana_tail.webp')
comp = np.zeros((H, W, 4), np.float32)
for im in (tail, body, head):
    f = im.astype(np.float32); k = f[..., 3:] / 255; comp[..., :3] = comp[..., :3] * (1 - k) + f[..., :3] * k; comp[..., 3:] = np.maximum(comp[..., 3:], f[..., 3:])
bgc = np.full((H, W, 3), (150, 170, 196), np.float32); k = comp[..., 3:] / 255
cv2.imwrite(os.path.join(os.path.dirname(sys.argv[1]), 'ana_illust_preview.jpg'), (bgc * (1 - k) + comp[..., :3] * k).astype(np.uint8))
print('ok', W, H, 'nose', NX, NY)
