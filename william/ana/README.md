# アナちゃん（playground）

細い毛を 1 本ずつ描いた一枚絵を作り、頭・体・しっぽの部品に分けて動かす。William のモデル（Tororo）は使わない。

- `make_ana.py`：アナちゃんを Tororo（William）と同じ絵柄で 0 から描く（写真の輪郭は使わない）。
  - Tororo の絵柄（観察して決めたこと）：線（ふち取り）なし／ふちは細い短い毛／エアブラシのようになめらかな塗り／白い毛の影はうすいピンク／
    本物の猫に近い体型（頭は小さめ）／模様はふちがぼけた塗り／目は細い灰色のまぶたの線・こはく色に放射状のすじ・まるい黒目
  - アナちゃんらしさ：長毛（ふちの毛が長い、ほおと胸にゆたかな毛、太いしっぽ、耳の中と先の毛）、灰色は 耳・ひたいの両がわ・目の外がわ・体のわき・しっぽ、ひたいの白い筋
  - 出力は `william/assets/ana_{tail,body,ears,head}.webp`（同じ座標の 4 枚）
- `tpl.html` の `drawAna`：4 枚を しっぽ → 体 → 耳 → 頭 の順に重ね、目・鼻・口・ひげを描いて動かす。動きも Tororo と同じ考え方（ポインターを追って頭が回る＝顔の部品が頭の上でずれる、目玉、まばたき、耳、しっぽ、呼吸）＋ もぐもぐ・ぺろっ
- 作り直し：`python3 william/ana/make_ana.py` → `npm run build`
- 入れたスキル（`.claude/skills/`、リポジトリには入れない）：cli-anything-live2d（Live2D モデルの点検・編集用。絵から moc3 は作れない）、gimp / krita / inkscape / blender の CLI

本式の Live2D（moc3）にする場合の工程（See-through で部品分け → PSD → Cubism Editor）は、GMO の記事を参照：
https://recruit.group.gmo/engineer/jisedai/blog/see-through-x-kaggle-x-claude-code/

