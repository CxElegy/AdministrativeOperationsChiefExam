# アナちゃん（playground）

細い毛を 1 本ずつ描いた一枚絵を作り、頭・体・しっぽの部品に分けて動かす。William のモデル（Tororo）は使わない。

- `make_ana.py`：正面で座っている写真（背景を消したもの）から「どこが どの色か」と「形」だけをもらい、先の細い毛を 約 12 万本、
  毛の流れ（顔は鼻から外へ、ほおと体は上から下へ）にそって 下の毛から順に重ねて描く。色の面では塗らない。
  出力は `william/assets/ana_body.webp` `ana_head.webp` `ana_tail.webp`（同じ座標の 3 枚）。
- `tpl.html` の `drawAna`：3 枚を 首・足もと・しっぽのつけ根を中心に動かす（呼吸、頭のかたむき、まばたき、もぐもぐ、ぺろっ、しっぽ）。
- 作り直し：`python3 william/ana/make_ana.py <切り抜いた写真>` → `npm run build`

本式の Live2D（moc3）にする場合の工程（See-through で部品分け → PSD → Cubism Editor）は、GMO の記事を参照：
https://recruit.group.gmo/engineer/jisedai/blog/see-through-x-kaggle-x-claude-code/

## デザインの決まり（animation-studio スキルの「新しいキャラクターの作り方」を当てはめた）

- 足もとを原点にして、うしろから順に描く：しっぽ → 体 → 耳 → 頭 → 目・口・ひげ → おさら
- 部品ごとに 自分の動きを持たせる：しっぽ（つけ根で ふる）、耳（つけ根で ぴくっ）、頭（首で かたむく）、体（呼吸）
- 表情は パラメータ：目の開き（まぶた）、ひとみの大きさ、口、舌
- 猫（ノルウェージャン）らしさ：大きく 高い位置の耳と 先の長い毛、耳の中の白い毛、ほおと胸の長い毛、太いしっぽ、
  まるみのあるアーモンド形の こはく色の目
- 目は 写真の目を使わず デザインして描く（`drawAna`）。耳は べつの部品（`ana_ears.webp`）
