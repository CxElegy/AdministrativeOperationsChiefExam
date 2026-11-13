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
# 目のまわりの皮（まぶた）：William では 右目に灰色のぶち。アナちゃんは 目の上と外がわが 灰色（グレージュ）、内がわと下は 白 → 顔の模様と つながる色にする
WHITE = np.array([249, 251, 253], np.float32); GREIGE = np.array([156, 166, 180], np.float32)   # BGR
for (x0, y0, x1, y1, outer_left) in [(500, 1535, 710, 1812, True), (728, 1535, 945, 1812, False)]:
    reg = t[y0:y1, x0:x1]; h, w = reg.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (1 - xx / w) if outer_left else (xx / w)                       # 0=鼻がわ、1=外がわ
    k = np.clip((u - 0.34) / 0.3, 0, 1) * np.clip((0.62 - yy / h) / 0.2, 0, 1)   # 外がわ かつ 上がわ ほど 灰色
    k = cv2.GaussianBlur(k, (0, 0), 6)[..., None]
    m = reg[..., 3] > 0; col = WHITE * (1 - k) + GREIGE * k; reg[m, :3] = col[m].astype(np.uint8)
    reg[..., 3] = np.minimum(reg[..., 3], cv2.GaussianBlur(reg[..., 3], (0, 0), 2.5))   # ふちを ぼかして 顔になじませる
os.makedirs(os.path.join(ROOT, 'public', 'w', 'ana.2048'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'public', 'w', 'ana.2048', 'texture_00.png'), t, [cv2.IMWRITE_PNG_COMPRESSION, 9])
print('ok')
