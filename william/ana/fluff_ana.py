# アナちゃんのテクスチャに「長い毛」を入れる（Tororo のモデルの形はそのまま）
# 使い方: python3 william/ana/fluff_ana.py
#   入力: william/ana/ana_base_texture.png（gen_ana.py で作った、柄だけのテクスチャ）、william/ana/tororo_meshes.json（Tororo の部品ごとのメッシュ）
#   出力: public/w/ana.2048/texture_00.png
# しくみ：Tororo のメッシュは絵にぴったり（余白は 5〜20px）なので、絵の外へ毛を足すことはできない。
#   そこで 顔・胸・せなか の絵を メッシュの中で S 倍に縮め、あいた外側の輪に 毛の房を描く。
#   ページの側でモデル全体を 1/S 倍に大きく描くので、体の大きさは元のまま、まわりに毛の房が付く（房はメッシュと一緒に動く）。
import json, os, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
S = 0.86
tex = cv2.imread(os.path.join(HERE, 'ana_base_texture.png'), cv2.IMREAD_UNCHANGED)  # BGRA
meshes = {d['id']: d for d in json.load(open(os.path.join(HERE, 'tororo_meshes.json')))['drawables']}
rng = np.random.RandomState(7)

def mesh_mask(d):
    uv = np.array(d['uvs'], np.float32).reshape(-1, 2); pts = np.stack([uv[:, 0] * 2048, (1 - uv[:, 1]) * 2048], 1)
    m = np.zeros((2048, 2048), np.uint8)
    for i in range(0, len(d['idx']), 3): cv2.fillConvexPoly(m, np.round(pts[d['idx'][i:i + 3]]).astype(np.int32), 255)
    return m

def fluff(did, tufts, grav=0.5, lmax_k=1.0, shrink=S):
    m = mesh_mask(meshes[did]); ys, xs = np.where(m > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    reg = tex[y0:y1, x0:x1].copy(); mm = m[y0:y1, x0:x1]; h, w = reg.shape[:2]; cx, cy = w / 2, h / 2
    reg[mm == 0] = 0
    # 1) 絵を まん中へ S 倍に縮める
    M = np.float32([[shrink, 0, cx * (1 - shrink)], [0, shrink, cy * (1 - shrink)]])
    small = cv2.warpAffine(reg, M, (w, h), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
    a = (small[..., 3] > 128).astype(np.uint8)
    # 2) 外側の各点から、いちばん近い絵の点（色をもらう相手）と そこまでの距離
    core = cv2.erode(a, np.ones((5, 5), np.uint8))  # ふちの うすい色をさけて、少し内側の色を使う
    dist, lab = cv2.distanceTransformWithLabels(1 - core, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    cyx = np.argwhere(core > 0); order = lab[core > 0]; lut = np.zeros((lab.max() + 1, 2), np.int32); lut[order] = cyx
    ny, nx = lut[lab][..., 0], lut[lab][..., 1]
    col = small[ny, nx, :3].astype(np.float32)
    # 3) 毛の房：まわりを tufts 個の房に分け、房のまん中ほど長く・房ごとに長さがちがう・下向きの房は長い
    th = np.arctan2(ny - cy, (nx - cx) * (h / w))
    u = (th / (2 * math.pi) + 0.5) * tufts; tid = np.floor(u).astype(np.int32) % tufts; f = u - np.floor(u)
    lens = 0.45 + 0.55 * rng.rand(tufts); skew = 0.35 + 0.3 * rng.rand(tufts)
    prof = np.where(f < skew[tid], f / skew[tid], (1 - f) / (1 - skew[tid])) ** 0.8  # とがった房
    ring = min(w, h) * (1 - shrink) / 2 - 3
    L = ring * lmax_k * lens[tid] * (0.25 + 0.75 * prof) * (1 - grav + grav * (0.5 + 0.5 * np.sin(th)) * 2).clip(0.55, 1.5)
    d2 = dist - 2  # core を 2px けずった分
    alpha = np.clip((L - d2) / 1.6, 0, 1)
    # 細い毛のすじ（房の中の 明るい・暗い）
    fine = 1 + 0.06 * np.sin(u * 2 * math.pi * 3 + rng.rand() * 6) * np.clip(d2 / max(ring, 1), 0, 1) - 0.05 * np.clip(1 - prof, 0, 1) * np.clip(d2 / max(ring, 1), 0, 1)
    furc = np.clip(col * fine[..., None], 0, 255)
    out = small.astype(np.float32); sa = out[..., 3:4] / 255
    rgb = out[..., :3] * sa + furc * (1 - sa); al = np.maximum(out[..., 3], alpha * 255)
    res = np.dstack([rgb, al]).astype(np.uint8)
    cur = tex[y0:y1, x0:x1]; cur[mm > 0] = res[mm > 0]

fluff('D_FACE_00', 34, grav=0.55)     # 顔：ほおの毛（下が長い）
fluff('D_CHEST_00', 30, grav=0.6)     # 胸：たてがみ
fluff('D_BODY_00', 40, grav=0.45)     # せなか・おしり
os.makedirs(os.path.join(ROOT, 'public', 'w', 'ana.2048'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'public', 'w', 'ana.2048', 'texture_00.png'), tex, [cv2.IMWRITE_PNG_COMPRESSION, 9])
print('ok')
