# アナちゃんの「顔の部品」用テクスチャ：Tororo（William）のテクスチャから、顔の部品（目・まぶた・目玉・口・舌・歯・鼻・ひげ）だけを残す
# 使い方: python3 william/ana/make_face_tex.py   → public/w/ana.2048/texture_00.png
# 体・足・しっぽ・胸・顔の土台・耳は 透明にする（アナちゃんの絵を 別に描いているので）。顔の部品は Tororo と同じ Live2D の仕組みで動く
import os, numpy as np, cv2
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
t = cv2.imread(os.path.join(ROOT, 'public', 'w', 'tororo.2048', 'texture_00.png'), cv2.IMREAD_UNCHANGED)
a = t[..., 3]
a[:1085, :] = 0                     # せなか・足・顔の土台・胸の上
a[1085:1470, :445] = 0              # 足先
a[590:1462, 1375:] = 0              # 胸
def drop_components(x0, y0, x1, y1, pred):
    reg = a[y0:y1, x0:x1]; n, lab, st, _ = cv2.connectedComponentsWithStats((reg > 8).astype(np.uint8))
    for i in range(1, n):
        if pred(st[i]): reg[lab == i] = 0
drop_components(410, 1085, 1400, 1390, lambda s: s[cv2.CC_STAT_AREA] > 20000)                 # しっぽ（大きい かたまり）
drop_components(1235, 1415, 2040, 2040, lambda s: s[cv2.CC_STAT_TOP] < 560 - 0 and s[cv2.CC_STAT_AREA] > 3000 and s[cv2.CC_STAT_TOP] + 1415 < 1960)   # 耳
# 目のまわりの皮（まぶた。D_EYE_02〜05）：その場所の アナちゃんの顔の色を そのまま写す（顔の土台と まぶたが 同じ色で つながる）
#   face_rims.json = まぶたの網目（テクスチャ上の位置 uv と、モデル上の位置 pos）。モデル上の位置 → アナちゃんの絵の座標 → 頭の絵の色
import json
from PIL import Image
FS, EM, EA = 0.80, (993.0, 755.0), (341.0, 345.0)                      # 大きさ、Tororo の 両目のまん中（モデル上）、アナちゃんの絵の 両目のまん中（tpl.html の ANA_FACE と同じ）
rims = json.load(open(os.path.join(ROOT, 'william', 'ana', 'face_rims.json'))); cv_ = rims['canvas']
head = np.array(Image.open(os.path.join(ROOT, 'william', 'assets', 'ana_ref.webp')).convert('RGBA'))[..., [2, 1, 0, 3]].astype(np.float32)
hrgb = cv2.GaussianBlur(head[..., :3], (0, 0), 2)
for part in rims['parts']:
    uv = np.array(part['uv'], np.float32).reshape(-1, 2); pos = np.array(part['pos'], np.float32).reshape(-1, 2)
    tx = np.stack([uv[:, 0] * 2048, (1 - uv[:, 1]) * 2048], 1)                                             # テクスチャ上
    mx = np.stack([pos[:, 0] * cv_['ppu'] + cv_['ox'], -pos[:, 1] * cv_['ppu'] + cv_['oy']], 1)            # モデル上（画素）
    art = np.stack([EA[0] + (mx[:, 0] - EM[0]) * FS, EA[1] + (mx[:, 1] - EM[1]) * FS], 1).astype(np.float32)   # アナちゃんの絵の座標
    for k in range(0, len(part['idx']), 3):
        ii = part['idx'][k:k + 3]; T = cv2.getAffineTransform(tx[ii], art[ii])                             # テクスチャ → 絵
        x0, y0 = np.floor(tx[ii].min(axis=0)).astype(int) - 1; x1, y1 = np.ceil(tx[ii].max(axis=0)).astype(int) + 2
        m = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillConvexPoly(m, np.round(tx[ii] - [x0, y0]).astype(np.int32), 255); m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32); ax = T[0, 0] * gx + T[0, 1] * gy + T[0, 2]; ay = T[1, 0] * gx + T[1, 1] * gy + T[1, 2]
        smp = cv2.remap(hrgb, ax.astype(np.float32), ay.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        reg = t[y0:y1, x0:x1]; sel = (m > 0) & (reg[..., 3] > 0); reg[sel, :3] = smp[sel].clip(0, 255).astype(np.uint8)
os.makedirs(os.path.join(ROOT, 'public', 'w', 'ana.2048'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'public', 'w', 'ana.2048', 'texture_00.png'), t, [cv2.IMWRITE_PNG_COMPRESSION, 9])
print('ok')
