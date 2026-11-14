# アナちゃん：William と同じ Tororo の Live2D モデルを そのまま使い（＝同じ絵柄）、毛の色・模様と 長毛の部分だけを アナちゃん用に作る
# 使い方: python3 william/ana/make_ana.py [プレビューを書くフォルダ]
#   入力: public/w/tororo.2048/texture_00.png（William のテクスチャ）、william/ana/tororo_parts.json（Tororo の各部品の網目：テクスチャ上の位置 uv と モデル上の位置 pos）
#   出力: public/w/anabody.2048/texture_00.png … 体・足・耳・顔の土台（顔の部品は 透明）
#         public/w/ana.2048/texture_00.png     … 顔の部品だけ（目・まぶた・目玉・口・舌・歯・鼻・ひげ）
#         william/assets/ana_back.webp / ana_mane.webp / ana_tail.webp … 長毛の部分（体のうしろの ふくらみと ほおの毛／胸のたてがみ／太いしっぽ）。Tororo と同じ画法で描く
# 重ねる順（tpl.html）：しっぽ → うしろの毛 → 体のモデル → たてがみ → 顔の部品のモデル
import sys, os, json, math
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
rng = np.random.RandomState(4)
src = cv2.imread(os.path.join(ROOT, 'public', 'w', 'tororo.2048', 'texture_00.png'), cv2.IMREAD_UNCHANGED)
P = json.load(open(os.path.join(HERE, 'tororo_parts.json'))); CV = P['canvas']; PARTS = {p['id']: p for p in P['parts']}
WHITE = np.array([250, 251, 253], np.float32); SHADOW = np.array([232, 226, 240], np.float32); GREY = np.array([118, 122, 130], np.float32); DARK = np.array([92, 94, 100], np.float32)   # BGR
def ss(a, b, v): t = np.clip((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def lum(c): return c[..., 0] * 0.11 + c[..., 1] * 0.59 + c[..., 2] * 0.3

# ---- アナちゃんの模様（モデル上の位置で決める。顔の土台にも まぶたにも 同じ式を使う＝色が つながる） ----
def face_mark(mx, my):
    du = np.abs(mx - 1000)
    blaze = (26 + 34 * ss(520, 700, my) + 150 * ss(770, 880, my))   # 白い筋：ひたい〜両目のあいだは 細い。目より下で 口元へ 広がる（写真）
    yb = 800 + np.clip(du - 100, 0, 300) * 0.5                         # 灰色の下のふち：目のまわりを つつむ。外がわほど 下まで
    return ss(blaze - 14, blaze + 22, du) * ss(yb + 34, yb - 26, my)
GREIGE = np.array([150, 160, 172], np.float32); STREAK = np.array([56, 58, 64], np.float32)   # ほおの あたたかい うすい灰色／ひたいの こい すじ（BGR）
def face_colour(mx, my):
    """顔の色（写真の アナちゃん）：ひたいは こい灰色に たての こい すじ、目の外がわ〜ほおは うすい あたたかい灰色、まん中と 口元は 白。返すのは (灰色の重み, 灰色の色)"""
    du = np.abs(mx - 1000); blaze = (26 + 34 * ss(520, 700, my) + 150 * ss(770, 880, my))
    gt = face_mark(mx, my)
    streak = (0.5 + 0.5 * np.sin(du * 0.105 + 0.6 + np.sin(my * 0.02) * 0.6)) ** 3 * ss(770, 660, my) * ss(blaze + 6, blaze + 34, du)   # ひたいの すじ（M の字の たて線）
    inner = np.exp(-((du - (blaze + 10)) / 16.0) ** 2) * ss(760, 690, my) * ss(540, 600, my)                                             # 白い筋の きわは 少し こい（目頭から上へ のびる線）
    top = (DARK * 0.35 + GREY * 0.65)[None, None] * (1 - np.clip(streak * 1.0 + inner * 0.7, 0, 1))[..., None] + STREAK[None, None] * np.clip(streak * 1.0 + inner * 0.7, 0, 1)[..., None]
    warm = np.clip(ss(690, 840, my) * 0.75 + ss(170, 290, du) * 0.35, 0, 0.85)[..., None]; top = top * (1 - warm) + GREIGE[None, None] * warm   # 下・外がわへ行くほど うすい あたたかい灰色（写真）
    cheek = ss(205, 270, du) * ss(1010, 900, my) * ss(690, 770, my) * 0.9                                                                # ほお：うすい あたたかい灰色
    g = np.maximum(gt, cheek); k = (gt / np.maximum(g, 1e-4))[..., None]
    return g, top * k + GREIGE[None, None] * (1 - k)
def body_mark(mx, my):
    return ss(300, 420, np.abs(mx - 1000) + (1700 - my) * 0.06) * ss(1150, 1350, my)   # せなか：体のわきが灰色

def map_part(tex, pid, fn):
    """部品 pid のテクスチャの画素ごとに、モデル上の位置 (mx, my) を求めて fn(reg, sel, mx, my) で塗る"""
    p = PARTS[pid]; uv = np.array(p['uv'], np.float32).reshape(-1, 2); pos = np.array(p['pos'], np.float32).reshape(-1, 2)
    tx = np.stack([uv[:, 0] * 2048, (1 - uv[:, 1]) * 2048], 1); mxy = np.stack([pos[:, 0] * CV['ppu'] + CV['ox'], -pos[:, 1] * CV['ppu'] + CV['oy']], 1).astype(np.float32)
    for k in range(0, len(p['idx']), 3):
        ii = p['idx'][k:k + 3]; T = cv2.getAffineTransform(tx[ii], mxy[ii])
        x0, y0 = np.floor(tx[ii].min(axis=0)).astype(int) - 1; x1, y1 = np.ceil(tx[ii].max(axis=0)).astype(int) + 2
        m = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillConvexPoly(m, np.round(tx[ii] - [x0, y0]).astype(np.int32), 255); m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32); mx = T[0, 0] * gx + T[0, 1] * gy + T[0, 2]; my = T[1, 0] * gx + T[1, 1] * gy + T[1, 2]
        reg = tex[y0:y1, x0:x1]; fn(reg, (m > 0) & (reg[..., 3] > 0), mx, my)

def drop(a, x0, y0, x1, y1, pred):
    reg = a[y0:y1, x0:x1]; n, lab, st, _ = cv2.connectedComponentsWithStats((reg > 8).astype(np.uint8))
    for i in range(1, n):
        if pred(st[i]): reg[lab == i] = 0

# ================= 体のテクスチャ（顔の部品は 透明） =================
A = src.copy()
def paint_face(reg, sel, mx, my):
    g, gc = face_colour(mx, my); g = g[..., None]; base = reg[..., :3].astype(np.float32); L = lum(base)[..., None]
    white = np.where(L > 222, base, WHITE * np.clip(L / 250 + 0.12, 0.9, 1))          # William の ぶち は 白に戻す（明るい所の 陰影は 残す）
    col = white * (1 - g) + gc * g; reg[sel, :3] = col[sel].clip(0, 255).astype(np.uint8)
map_part(A, 'D_FACE_00', paint_face)
def paint_back(reg, sel, mx, my):
    g = body_mark(mx, my)[..., None]; base = reg[..., :3].astype(np.float32); L = lum(base)[..., None]
    white = np.where(L > 215, base, WHITE); col = white * (1 - g) + GREY * g * np.clip(L / 250, 0.8, 1); reg[sel, :3] = col[sel].clip(0, 255).astype(np.uint8)
map_part(A, 'D_BODY_00', paint_back)
for x in range(1380, 2030):                                                             # 首輪を消す（上と下の色を つなぐ）
    top = A[762, x, :3].astype(np.float32) if A[762, x, 3] else WHITE; bot = A[881, x, :3].astype(np.float32) if A[881, x, 3] else WHITE
    for y in range(764, 880):
        if A[y, x, 3]: A[y, x, :3] = top + (bot - top) * (y - 764) / 116
for (x0, y0, x1, y1) in [(1255, 1695, 1425, 2000), (1640, 1700, 1830, 1965), (1845, 1700, 2030, 1968)]:   # 耳の外がわ：アナちゃんの灰色に
    reg = A[y0:y1, x0:x1]; L = lum(reg[..., :3].astype(np.float32)); sel = (reg[..., 3] > 0) & (L < 190) & (np.ptp(reg[..., :3].astype(np.int32), axis=2) < 40)
    reg[sel, :3] = (GREY * np.clip(L[sel] / 120, 0.75, 1.15)[:, None]).clip(0, 255).astype(np.uint8)
for (x0, y0, x1, y1, sx) in [(1247, 1432, 1400, 1693, -1), (1427, 1427, 1588, 1692, 1)]:                       # 耳の中：長い白い毛（写真）
    reg = A[y0:y1, x0:x1]; lay = np.ascontiguousarray(reg[..., :3]); h_, w_ = reg.shape[:2]
    for i in range(70):
        bx = rng.uniform(0.15, 0.85) * w_; by = h_ - rng.uniform(0.02, 0.4) * h_; L_ = rng.uniform(0.25, 0.7) * h_; dx = rng.uniform(-0.2, 0.2) * L_ + sx * 0.12 * L_
        pts = (np.array([[bx, by], [bx + dx * 0.5, by - L_ * 0.5], [bx + dx, by - L_]]) * 8).astype(np.int32); v = rng.randint(240, 254); cv2.polylines(lay, [pts], False, (v, v, v), 2, cv2.LINE_AA, 3)
    al = reg[..., 3:] > 0; reg[..., :3] = np.where(al, (reg[..., :3].astype(np.float32) * 0.7 + lay.astype(np.float32) * 0.3).astype(np.uint8), reg[..., :3])
reg = A[575:1060, 250:490]; L = lum(reg[..., :3].astype(np.float32)); sel = (reg[..., 3] > 0) & (L < 226) & (np.ptp(reg[..., :3].astype(np.int32), axis=2) < 18); reg[sel, :3] = (246, 243, 244)   # William の 足の ぶち を消す
drop(A[..., 3], 410, 1085, 1400, 1390, lambda s: s[cv2.CC_STAT_AREA] > 20000)          # しっぽは 別に描く
A[1475:, :1240, 3] = 0; A[1270:1475, 495:1240, 3] = 0; A[1960:2040, 1315:1540, 3] = 0   # 顔の部品は 透明
os.makedirs(os.path.join(ROOT, 'public', 'w', 'anabody.2048'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'public', 'w', 'anabody.2048', 'texture_00.png'), A, [cv2.IMWRITE_PNG_COMPRESSION, 9])

# ================= 顔の部品のテクスチャ =================
B = src.copy(); a = B[..., 3]
a[:1085, :] = 0; a[1085:1470, :445] = 0; a[590:1462, 1375:] = 0
drop(a, 410, 1085, 1400, 1390, lambda s: s[cv2.CC_STAT_AREA] > 20000)
drop(a, 1235, 1415, 2040, 2040, lambda s: s[cv2.CC_STAT_AREA] > 3000 and s[cv2.CC_STAT_TOP] + 1415 < 1960)
def paint_rim(reg, sel, mx, my):
    g, gc = face_colour(mx, my); g = g[..., None]; col = WHITE * (1 - g) + gc * g; reg[sel, :3] = col[sel].clip(0, 255).astype(np.uint8)
for pid in ('D_EYE_02', 'D_EYE_03', 'D_EYE_04', 'D_EYE_05'): map_part(B, pid, paint_rim)   # まぶた：顔の土台と 同じ模様の色
# 目：写真の アナちゃんは 明るい 金色〜黄色。目のふちの線は こく はっきり
for (x0, y0, x1, y1) in [(545, 1818, 678, 1946), (780, 1818, 908, 1946)]:
    reg = B[y0:y1, x0:x1]; hsv = cv2.cvtColor(reg[..., :3], cv2.COLOR_BGR2HSV).astype(np.float32); sel = (hsv[..., 1] > 70) & (reg[..., 3] > 0)
    hsv[..., 0] = np.where(sel, 26, hsv[..., 0]); hsv[..., 1] = np.where(sel, hsv[..., 1] * 0.78, hsv[..., 1]); hsv[..., 2] = np.where(sel, np.clip(hsv[..., 2] * 1.3 + 22, 0, 255), hsv[..., 2])
    reg[..., :3] = cv2.cvtColor(hsv.clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
for (x0, y0, x1, y1) in [(530, 1335, 680, 1530), (775, 1335, 920, 1530)]:
    reg = B[y0:y1, x0:x1]; sel = reg[..., 3] > 0; reg[sel, :3] = (reg[sel, :3].astype(np.float32) * 0.62 + np.array([52, 48, 46]) * 0.38).astype(np.uint8)
os.makedirs(os.path.join(ROOT, 'public', 'w', 'ana.2048'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'public', 'w', 'ana.2048', 'texture_00.png'), B, [cv2.IMWRITE_PNG_COMPRESSION, 9])
for nm in ('ana', 'anabody'):
    j = open(os.path.join(ROOT, 'public', 'w', 'tororo.model3.json'), encoding='utf-8').read().replace('tororo.2048/texture_00.png', nm + '.2048/texture_00.png')
    open(os.path.join(ROOT, 'public', 'w', nm + '.model3.json'), 'w', encoding='utf-8').write(j)

# ================= 長毛の部分（Tororo と同じ画法：線なし・なめらかな塗り・白い毛の影は うすいピンク・ふちは 細い毛） =================
SC, X0, Y0, CW, CH = 0.5, 0, 300, 1000, 1000                                            # 絵 1 画素 = モデル 2 画素。絵の左上 = モデルの (0, 300)
yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32); MX, MY = xx / SC + X0, yy / SC + Y0   # 各画素の モデル上の位置
def tuft_shape(cx, cy, rx, ry, tufts, depth, grav, a0=0.0, a1=2 * math.pi):
    """まわりが 毛の房（とがった先が 外・下へ向く）になった 形。モデル上の座標で指定"""
    pts = []; n = tufts * 8
    lens = 0.5 + 0.5 * rng.rand(tufts + 1); skew = 0.3 + 0.4 * rng.rand(tufts + 1)
    for i in range(n + 1):
        t = i / n; ang = a0 + (a1 - a0) * t; u = t * tufts; k = int(min(u, tufts - 1e-6)); f = u - k
        prof = (f / skew[k] if f < skew[k] else (1 - f) / (1 - skew[k])) ** 0.8
        g = 1 - grav + grav * (0.5 + 0.5 * math.sin(ang)) * 2
        r = 1 + depth * lens[k] * prof * max(0.35, g)
        pts.append(((cx + math.cos(ang) * rx * r - X0) * SC, (cy + math.sin(ang) * ry * r + depth * ry * 0.3 * prof * lens[k] * max(0, math.sin(ang)) - Y0) * SC))
    m = np.zeros((CH, CW), np.uint8); cv2.fillPoly(m, [(np.array(pts) * 8).astype(np.int32)], 255, cv2.LINE_AA, 3); return m
def soft_paint(mask, grey, shade):
    """なめらかな塗り。grey=灰色の模様 0〜1、shade=影 0〜1（白い毛では うすいピンク、灰色では こい灰色）"""
    g = cv2.GaussianBlur(grey.astype(np.float32), (0, 0), 6)[..., None]; s = cv2.GaussianBlur(shade.astype(np.float32), (0, 0), 5)[..., None]
    col = (WHITE * (1 - s) + SHADOW * s) * (1 - g) + (GREY * (1 - s) + DARK * s) * g
    return np.dstack([col.clip(0, 255).astype(np.uint8), mask])
def edge_shade(mask, width):
    d = cv2.distanceTransform((mask > 128).astype(np.uint8), cv2.DIST_L2, 5); return np.clip(1 - d / width, 0, 1)
def save(img, name): Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', name), quality=94, method=6)

# うしろの毛：体の両わきと下の ふくらみ（灰色のわき、下は白）＋ ほおの毛（頭の下半分から 外へ）
mb = tuft_shape(1000, 1580, 470, 500, 38, 0.07, 0.6, 0.0, math.pi * 2)
mc = np.maximum(tuft_shape(790, 900, 120, 130, 7, 0.26, 0.7, math.pi * 0.25, math.pi * 1.35), tuft_shape(1210, 900, 120, 130, 7, 0.26, 0.7, -math.pi * 0.35, math.pi * 0.75))
m = np.maximum(mb, mc)
gb = np.maximum(ss(300, 420, np.abs(MX - 1000) + (1700 - MY) * 0.06) * ss(1150, 1350, MY), 0 * MX)
back = soft_paint(m, gb, edge_shade(m, 30) * 0.4)
cg, cc = face_colour(MX, np.minimum(MY, 960)); ck = (cg * (MY < 1060) * ss(170, 230, np.abs(MX - 1000)))[..., None]   # ほおの毛は 顔と同じ色（うすい あたたかい灰色）
back[..., :3] = (back[..., :3] * (1 - ck) + cc * ck * 0.97).clip(0, 255).astype(np.uint8)
save(back, 'ana_back.webp')
# 胸のたてがみ：あごの下から 房になって下がる 白い毛。上は 胸に とけこむ（ふちを 見せない）
mm = tuft_shape(1000, 1300, 300, 330, 13, 0.14, 0.85, 0.0, math.pi)
mm = np.maximum(mm, tuft_shape(1000, 1240, 270, 240, 11, 0.13, 0.85, 0.0, math.pi))
rows = np.zeros((CH, CW), np.float32)                                                   # 毛の重なり：房の下がわに うすい影（Tororo の 胸の やわらかい影）
for (cy, rx, ry, n) in [(1230, 230, 150, 9), (1280, 265, 230, 11)]:
    r = tuft_shape(1000, cy, rx, ry, n, 0.2, 0.85, 0.0, math.pi).astype(np.float32) / 255; e = cv2.GaussianBlur(r, (0, 0), 7) - cv2.GaussianBlur(r, (0, 0), 2); rows = np.maximum(rows, np.clip(-e * 3.2, 0, 1) * (1 - r) + np.clip(e * 0, 0, 1))
mane = soft_paint(mm, np.zeros((CH, CW)), np.clip(edge_shade(mm, 22) * 0.45 * ss(1300, 1420, MY) + rows * 0.45, 0, 1))
fade = ss(1040, 1160, MY) * (1 - ss(0.0, 1.0, np.zeros_like(MY)))                       # 上は 透明に
mane[..., 3] = (mane[..., 3].astype(np.float32) * ss(1150, 1400, MY) * ss(330, 240, np.abs(MX - 1000) - (MY - 1300) * 0.25)).astype(np.uint8)   # 上と 両はしは 胸に とけこむ
save(mane, 'ana_mane.webp')
# しっぽ：Tororo と同じく 体のうしろから 左へ 床にそって。長毛なので 太く ふさふさ
tm = np.zeros((CH, CW), np.uint8); sp = []
for s_ in np.linspace(0, 1, 200):
    u = 1 - s_; x = u * u * 900 + 2 * u * s_ * 430 + s_ * s_ * 150; y = u * u * 2110 + 2 * u * s_ * 2230 + s_ * s_ * 1880
    sp.append((x, y)); cv2.circle(tm, (int((x - X0) * SC), int((y - Y0) * SC)), int((70 + 80 * math.sin(math.pi * min(1, 0.14 + s_ * 0.9)) ** 0.7) * SC), 255, -1, cv2.LINE_AA)
spA = np.array(sp, np.float32); d2 = (MX[..., None] - spA[None, None, ::8, 0]) ** 2 + (MY[..., None] - spA[None, None, ::8, 1]) ** 2; ni = np.argmin(d2, axis=2) * 8
off = (MY - spA[ni, 1]) / 150.0                                                         # しんの線より 下は 影
tail = soft_paint(tm, np.ones((CH, CW)), np.clip(off * 0.9 + 0.25, 0, 1))
tr = np.ascontiguousarray(tail[..., :3]); ta = np.ascontiguousarray(tail[..., 3]); cs, _ = cv2.findContours((tm > 128).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
din = cv2.GaussianBlur(cv2.distanceTransform((tm > 128).astype(np.uint8), cv2.DIST_L2, 5), (0, 0), 3); gx, gy = cv2.Sobel(din, cv2.CV_32F, 1, 0), cv2.Sobel(din, cv2.CV_32F, 0, 1)
for c in cs:
    for (x, y) in c[:, 0]:                                                              # ふちの 細い毛（William のしっぽと 同じ ぼんやりした ふち）
        nx, ny = -gx[y, x], -gy[y, x]; dd = math.hypot(nx, ny) + 1e-6; ang = math.atan2(ny / dd, nx / dd) + rng.uniform(-0.6, 0.6); L = rng.uniform(4, 13)
        pp = (np.array([[x - nx / dd * 2, y - ny / dd * 2], [x + math.cos(ang) * L, y + math.sin(ang) * L]]) * 8).astype(np.int32)
        c3 = tuple(float(v) for v in tail[int(np.clip(y - ny / dd * 2, 0, CH - 1)), int(np.clip(x - nx / dd * 2, 0, CW - 1)), :3]); cv2.polylines(tr, [pp], False, c3, 1, cv2.LINE_AA, 3); cv2.polylines(ta, [pp], False, 230, 1, cv2.LINE_AA, 3)
save(np.dstack([tr, ta]), 'ana_tail.webp')
print('ok')
