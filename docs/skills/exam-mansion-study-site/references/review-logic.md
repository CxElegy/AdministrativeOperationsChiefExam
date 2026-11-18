# まとめノートの判定式

```js
const needQ = (id) => { const r = ST.q[id]; return !!r && (!r.last || r.box !== undefined); };   // 要復習
const missQ = (id) => { const r = ST.q[id]; return r ? r.a - r.c : 0; };                          // まちがえた回数
// 部屋：要復習 > 克服（まちがえた問題があり、ぜんぶ克服）> 習得（点灯）> まだ
roomState = n ? 'need' : missed ? 'kok' : isLit ? 'got' : 'yet'
// 階：要復習が 1 つでも → need、全室 got/kok → got、kok があれば kok、他 → yet
// 節（章立て）：出典に要復習 → need、出典を全部解いて要復習なし → got、他 → yet
```

- 再テストで正解：`recordAnswer` のあと `delete r.box; delete r.due` → 克服。まちがい：`box = 0`。
- ふつうの正解は `box` を 1 つ進める（間隔 1・3・7・14・30 日、最後まで行くと要復習から外れる）。
- 月のラベル（aria-label）に要復習の数。画面には数字を出さない。
- まとめの描き直しで光の位相がずれないよう `--ph: -(now % 周期)ms` を親に入れて `animation-delay` に使う。
- スクロール位置：`top = 目標.top − 容器.top + 容器.scrollTop − ヘッダー高さ − 8`。
