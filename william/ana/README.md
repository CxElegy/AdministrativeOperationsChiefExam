# アナちゃん（playground）

お手本の設定画（長毛の猫の三面図）は **参考**。使うのは 体型と 模様の位置だけ。**絵柄と動きは Tororo（William）と同じ**にする。

- `ref_front_cut.png`：設定画から 正面の猫を切り出して 4 倍に拡大し、背景を消したもの（820×1640）
- `make_ref.py`：
  1. 毛の色を アナちゃんの色（白＋こい あたたかい灰色）に。首輪は消す
  2. Tororo の画法に直す：線なし／エアブラシのように なめらかな塗り／白い毛の影は うすいピンク／模様は ふちが ぼけた塗り／ふちは 細い短い毛
  3. 顔の部品（目・鼻・口）は 絵から消す（Tororo の Live2D の部品に置きかえる）
  4. しっぽ：Tororo と同じく 体のうしろから 横へ 甩る。長毛なので 太く ふさふさ
  → `william/assets/ana_ref.webp`、`ana_tail.webp`
- `make_face_tex.py`：Tororo のテクスチャから 顔の部品（目・まぶた・目玉・口・舌・歯・鼻・ひげ）だけを残す（`public/w/ana.2048/`、モデルは `public/w/ana.model3.json`）。
  まぶたの色は、その場所の アナちゃんの絵の色を写す（網目は `face_rims.json`）
- `tpl.html` の `loadAna` / `anaWarp` / `anaParams` / `drawAna`：
  - 体は 絵に 網目（21×41）を張って 変形させる（呼吸、頭のかたむき、顔の向き、耳、うなずき）
  - 顔は Tororo と同じ Live2D の仕組み（まばたき、目玉、顔の向き、口、舌）。位置は 網目と同じ式で動かすので ずれない
  - しっぽは 網目を曲げて、つけ根から先へ 波が伝わるように ゆらす
- 作り直し：`python3 william/ana/make_ref.py` → `python3 william/ana/make_face_tex.py` → `npm run build`
