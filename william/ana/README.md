# アナちゃん（playground）

細い毛を 1 本ずつ描いた一枚絵を作り、頭・体・しっぽの部品に分けて動かす。William のモデル（Tororo）は使わない。

- `make_ana.py`：アナちゃんを 0 から描く（写真の輪郭は使わない）。
  - 形は立体（だ円体の組み合わせ）：まるい頭＋ほおの毛、洋なし形の体、まるい足先、羽のようなしっぽ、大きな耳
  - 光は左上から。立体の向きで明るさを決め、あごの下・体の下に影
  - 絵柄は Tororo（William）と同じ：なめらかな塗り＋やわらかい影。長毛は 輪郭の毛の房と、中の 少しの房のしるしで表す
  - かわいさ：頭を大きく、目は顔の下より・大きく・はなして、鼻と口は小さく
  - アナちゃんらしさ：灰色は 耳・ひたいの両がわ・目の外がわ・体のわき・しっぽ。ひたいの白い筋が口元へ広がる。胸は白い長い毛
  - 出力は `william/assets/ana_{tail,body,ears,head}.webp`（同じ座標の 4 枚）
- `tpl.html` の `drawAna`：4 枚を しっぽ → 体 → 耳 → 頭 の順に重ね、目・鼻・口・ひげを描いて動かす。動きも Tororo と同じ考え方（ポインターを追って頭が回る＝顔の部品が頭の上でずれる、目玉、まばたき、耳、しっぽ、呼吸）＋ もぐもぐ・ぺろっ
- 作り直し：`python3 william/ana/make_ana.py` → `npm run build`
- 入れたスキル（`.claude/skills/`、リポジトリには入れない）：cli-anything-live2d（Live2D モデルの点検・編集用。絵から moc3 は作れない）、gimp / krita / inkscape / blender の CLI

本式の Live2D（moc3）にする場合の工程（See-through で部品分け → PSD → Cubism Editor）は、GMO の記事を参照：
https://recruit.group.gmo/engineer/jisedai/blog/see-through-x-kaggle-x-claude-code/

