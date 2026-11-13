# アナちゃんの一枚絵（細い毛で描いたイラスト）を作り、頭・体・しっぽの部品に分ける
# 使い方: python3 william/ana/make_ana.py <切り抜いた写真 cut.png（正面で座っている写真、1620×1800、背景は透明）>
#   出力: william/assets/ana_body.webp / ana_head.webp / ana_tail.webp（どれも 890×980、同じ座標）
# 考え方（似せるために）：
#   - 顔の形・模様の位置・目・鼻・口・耳は 写真の形を そのまま使う（作り物に置きかえない）。軽く なめらかにして 絵らしくするだけ
#   - 毛は、写真から「その場所の毛の向き」を読み取り（明るさの変化の向き）、その向きに 先の細い毛を 1 本ずつ重ねて描く。色は その場所の写真の色
#   - 毛は輪郭の外へ少し はみ出すので、ふちは 長毛種らしい毛先になる
import sys, os, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SC = 0.5; PAD = 40
rng = np.random.RandomState(11)
src = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
src = cv2.resize(src, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
src = cv2.copyMakeBorder(src, PAD, PAD, PAD, PAD, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
H, W = src.shape[:2]
P = lambda x, y: (x * SC + PAD, y * SC + PAD)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
NX, NY = P(640, 640)
# --- 形（右の床の影を落とす） ---
a = (src[..., 3] > 170).astype(np.uint8); a[:, int(P(1215, 0)[0]):] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats(a); a = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
# --- 色：写真を 軽く なめらかにして 明るくする（模様や影は残す） ---
ae = cv2.erode(a, np.ones((9, 9), np.uint8))
raw = cv2.inpaint(src[..., :3], (1 - ae) * 255, 5, cv2.INPAINT_TELEA)
col = cv2.edgePreservingFilter(raw, flags=1, sigma_s=10, sigma_r=0.18).astype(np.float32)
col = 255 * (col / 255) ** 0.78 * 1.05
hsv = cv2.cvtColor(col.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32); hsv[..., 1] *= 1.12
col = cv2.cvtColor(hsv.clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
# --- 毛の向き：写真の明るさの変化から（構造テンソル）。向きの表裏は「鼻から外へ・上から下へ」に そろえる ---
g = cv2.GaussianBlur(cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2)
gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
J11, J22, J12 = (cv2.GaussianBlur(v, (0, 0), 5) for v in (gx * gx, gy * gy, gx * gy))
th = 0.5 * np.arctan2(2 * J12, J11 - J22) + np.pi / 2                    # 毛の向き（変化の向きと直角）
coh = np.sqrt((J11 - J22) ** 2 + 4 * J12 ** 2) / (J11 + J22 + 1e-3)      # 向きの はっきり度 0〜1
chin = P(0, 790)[1] - 45 * ((xx - NX) / 180) ** 2
inhead = yy < chin
pfx = np.where(inhead, xx - NX, (xx - NX) / 380.0); pfy = np.where(inhead, (yy - (NY - 20)) * 0.9 - 4, 1.0)
cheek = inhead & (yy > NY - 10) & (np.abs(xx - NX) > 60); pfx = np.where(cheek, (xx - NX) * 0.012, pfx); pfy = np.where(cheek, 1.0, pfy)
pn = np.hypot(pfx, pfy) + 1e-6; pfx, pfy = pfx / pn, pfy / pn
vx, vy = np.cos(th), np.sin(th); flip = (vx * pfx + vy * pfy) < 0; vx, vy = np.where(flip, -vx, vx), np.where(flip, -vy, vy)
k = np.clip(coh * 1.6, 0, 1) * 0.75                                       # はっきりしない所は きめた向きを多めに
FX, FY = vx * k + pfx * (1 - k), vy * k + pfy * (1 - k)
# --- 部品：頭（耳もふくむ）と 体 ---
head_m = (a > 0) & inhead
body_m = (a > 0) & (yy > chin - 34)
# 顔の部品（目・鼻・口）は 写真の形のまま のせる（毛をかけない）
feat = np.zeros((H, W), np.uint8)
for (x, y, rx, ry) in [(545, 532, 56, 44), (748, 536, 56, 44), (640, 650, 50, 70)]:
    cv2.ellipse(feat, tuple(int(v) for v in P(x, y)), (int(rx * SC), int(ry * SC)), 0, 0, 360, 255, -1)
feat = cv2.GaussianBlur(feat, (0, 0), 5)

def paint(mask, n, length, width, color=None, flow=None):
    out = np.zeros((H, W, 4), np.float32)
    kk = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]; C = col if color is None else color
    out[..., :3] = C * kk; out[..., 3:] = kk
    layer = (out * 255 / 255).clip(0, 255); rgb = np.ascontiguousarray(layer[..., :3].astype(np.uint8)); al = np.ascontiguousarray((layer[..., 3] * 255).clip(0, 255).astype(np.uint8))
    ys, xs = np.where(mask); idx = rng.randint(0, len(xs), n); px, py = xs[idx], ys[idx]
    for i in np.argsort(-(py + rng.rand(n) * 8)):                          # 下の毛から先に描く
        x, y = int(px[i]), int(py[i])
        if feat[y, x] > 110: continue
        fx, fy = (FX[y, x], FY[y, x]) if flow is None else flow(x, y)
        ang = math.atan2(fy, fx) + (rng.rand() - 0.5) * 0.35
        L = length(x, y) * (0.6 + rng.rand() * 0.8); w = width * (0.6 + rng.rand() * 0.7)
        tx, ty = x + math.cos(ang) * L, y + math.sin(ang) * L
        bend = (rng.rand() - 0.5) * 0.2 * L; mx, my = (x + tx) / 2 - math.sin(ang) * bend, (y + ty) / 2 + math.cos(ang) * bend
        nx, ny = -math.sin(ang) * w / 2, math.cos(ang) * w / 2
        pts = np.array([[x + nx, y + ny], [mx + nx * 0.6, my + ny * 0.6], [tx, ty], [mx - nx * 0.6, my - ny * 0.6], [x - nx, y - ny]]) * 8
        c = C[y, x] * (1 + (rng.rand() - 0.5) * 0.09)                      # 1 本ごとに 明るさを少し変える
        cv2.fillConvexPoly(rgb, pts.astype(np.int32), tuple(float(v) for v in c.clip(0, 255)), cv2.LINE_AA, 3); cv2.fillConvexPoly(al, pts.astype(np.int32), 255, cv2.LINE_AA, 3)
    return np.dstack([rgb, al])

def save(img, name):
    from PIL import Image
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)).save(os.path.join(ROOT, 'william', 'assets', name), quality=92, method=6)

body = paint(body_m, 90000, lambda x, y: 22 if y < P(0, 1400)[1] else 10, 1.9)
EARY = P(0, 400)[1]
head = paint(head_m, 60000, lambda x, y: 6 if y < EARY and abs(x - NX) > 55 else (7 + min(16, math.hypot(x - NX, y - NY) * 0.09)), 1.6)
# 目・鼻・口：写真の形のまま。少し くっきりさせて、目に ハイライト
sharp = cv2.addWeighted(col, 1.5, cv2.GaussianBlur(col, (0, 0), 3), -0.5, 0).clip(0, 255)
kf = (feat.astype(np.float32) / 255)[..., None]
head[..., :3] = (head[..., :3] * (1 - kf) + sharp * kf).astype(np.uint8)
hb = np.ascontiguousarray(head[..., :3])
for (x, y) in [(535, 520), (738, 524)]:
    cv2.circle(hb, tuple(int(v * 8) for v in P(x, y)), 4 * 8, (255, 255, 255), -1, cv2.LINE_AA, 3)
head[..., :3] = hb
# しっぽ：写真では 体の右うしろに こい灰色の ふさふさ（写真では 影と重なって 切り抜けないので、しんの線にそって描く）
tail_m = np.zeros((H, W), np.uint8); spine = []
for s in np.linspace(0, 1, 200):
    u = 1 - s; x = u * u * 1040 + 2 * u * s * 1330 + s * s * 1400; y = u * u * 1330 + 2 * u * s * 1300 + s * s * 880
    spine.append(P(x, y)); cv2.circle(tail_m, tuple(int(v) for v in P(x, y)), int((38 + 70 * math.sin(math.pi * min(1, 0.15 + s * 0.9)) ** 0.7) * SC), 1, -1)
spine = np.array(spine)
tcol = np.zeros((H, W, 3), np.float32) + np.array([96, 100, 108], np.float32) + (rng.rand(H, W, 1).astype(np.float32) - 0.5) * 26
def tail_flow(x, y):
    i = int(np.argmin((spine[:, 0] - x) ** 2 + (spine[:, 1] - y) ** 2)); j = min(len(spine) - 1, i + 3); tx, ty = spine[j] - spine[max(0, i - 3)]
    ox, oy = x - spine[i][0], y - spine[i][1]; return (tx * 0.6 + ox * 1.4, ty * 0.6 + oy * 1.4)
tail = paint(tail_m > 0, 22000, lambda x, y: 30, 2.0, color=tcol, flow=tail_flow)
save(body, 'ana_body.webp'); save(head, 'ana_head.webp'); save(tail, 'ana_tail.webp')
comp = np.zeros((H, W, 4), np.float32)
for im in (tail, body, head):
    f = im.astype(np.float32); k2 = f[..., 3:] / 255; comp[..., :3] = comp[..., :3] * (1 - k2) + f[..., :3] * k2; comp[..., 3:] = np.maximum(comp[..., 3:], f[..., 3:])
bgc = np.full((H, W, 3), (150, 170, 196), np.float32); k2 = comp[..., 3:] / 255
cv2.imwrite(os.path.join(os.path.dirname(sys.argv[1]), 'ana_illust_preview.jpg'), (bgc * (1 - k2) + comp[..., :3] * k2).astype(np.uint8))
print('ok')
