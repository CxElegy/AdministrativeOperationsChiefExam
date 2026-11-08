#!/usr/bin/env python3
"""マンション管理業協会が公開している「試験問題・正解」PDFを、サイト用の JSON に変換する。

使い方:
    pip install pdfplumber
    python3 scripts/import_kakomon.py <PDFを置いたディレクトリ>

ディレクトリには年度ごとに次のファイルを置く（ファイル名の rNN は令和の年度）:
    rNN_mondai.pdf  … https://www.kanrikyo.or.jp/kanri/shiken_rNN/pdf/mondai_011.pdf
    rNN_kekka.pdf   … https://www.kanrikyo.or.jp/kanri/shiken_rNN/pdf/goukakugaiyou.pdf （任意）

出力: src/data/kakomon/rNN.json
既存の JSON に手で書いた explanation（解説）や category の修正がある場合は、それを引き継ぐ。

過去問の使用について（協会の方針）: 教育目的での使用は無償・許諾不要。出典の明記が必要。
https://www.kanrikyo.or.jp/kanri/pdf/kakomonshiyou.pdf
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "src" / "data" / "kakomon"

# 試験日（各年度の結果報告より）
EXAM_DATES = {
    "r01": "2019-12-01",
    "r02": "2020-12-06",
    "r03": "2021-12-05",
    "r04": "2022-12-04",
    "r05": "2023-12-03",
    "r06": "2024-12-01",
    "r07": "2025-12-07",
}


def nfkc_digits(s: str) -> str:
    """全角数字だけを半角にする（本文の全角英字などはそのまま残す）。"""
    return re.sub(r"[０-９]", lambda m: str("０１２３４５６７８９".index(m.group())), s)


# 一部の年度の PDF は数字が (cid:N) という番号になっている（令和元年度・3年度など）。
# 「N - CID_BASE」がその数字になる。CID_BASE は年度ごとに【問1】の番号から求める。
CID_BASE = 1


def detect_cid_base(text: str) -> int:
    m = re.search(r"【\s*問\s*\(cid:(\d+)\)\s*】", text)
    return int(m.group(1)) - 1 if m else 1


def fix_cid(s: str) -> str:
    def rep(m):
        d = int(m.group(1)) - CID_BASE
        return str(d) if 0 <= d <= 9 else ""
    return re.sub(r"\(cid:(\d+)\)", rep, s)


PAGE_FIGS: dict = {}


def page_lines(page, page_no):
    """ふりがな（小さい文字）を除いた行のリスト。

    各行は dict: text / item（選択肢・記述の始まりなら番号や記号）/ fig（図表と重なるか）/
    page / top / bottom
    """
    sizes = [round(c["size"], 1) for c in page.chars if c["text"].strip()]
    if not sizes:
        return []
    body = max(set(sizes), key=sizes.count)
    p = page.filter(lambda o: o.get("object_type") != "char" or o["size"] >= body * 0.8)
    figs = figure_spans(p)
    PAGE_FIGS[page_no] = figs
    out = []
    for ln in p.extract_text_lines(x_tolerance=1.5):
        chars = [c for c in ln["chars"] if c["text"].strip()]
        text = fix_cid(ln["text"]).strip()
        if not text:
            continue
        if re.fullmatch(r"\d+", text) or ".indd" in text:
            continue  # ページ番号・印刷用フッター
        # 「1 　本文」のように番号の後ろに大きな空白がある行だけを選択肢・記述の始まりとみなす
        item = None
        if len(chars) >= 2:
            gap = chars[1]["x0"] - chars[0]["x1"]
            is_cid = chars[0]["text"].startswith("(cid:")
            lead = re.match(r"^(\d|[アイウエオ])\s*", text)
            if lead and (gap >= body * 0.6 or is_cid):
                item = lead.group(1)
        fig = any(t0 - 4 <= ln["bottom"] and ln["top"] <= b0 + 4 for t0, b0 in figs)
        out.append({"text": text, "item": item, "fig": fig, "page": page_no, "top": ln["top"], "bottom": ln["bottom"]})
    # 行と行の間にある図（文字と重ならない図）は、直前の行の問題に含める
    for t0, _ in figs:
        before = [ln for ln in out if ln["bottom"] <= t0 + 4]
        if before:
            before[-1]["fig"] = True
    return out


def text_column(page):
    """本文の左右の端（x0, x1）と、ページ番号などを除いた本文の下端。"""
    chars = [c for c in page.chars if c["text"].strip() and c["size"] >= 8]
    if not chars:
        return 0, page.width, page.height
    body_chars = [c for c in chars if c["bottom"] < page.height * 0.93]
    return (
        min(c["x0"] for c in chars),
        max(c["x1"] for c in chars),
        max(c["bottom"] for c in body_chars) if body_chars else page.height,
    )


def figure_spans(page):
    """本文の範囲内にある罫線・図形・画像の縦方向の範囲（トンボなど余白の線は除く）。"""
    chars = [c for c in page.chars if c["text"].strip()]
    if not chars:
        return []
    x0 = min(c["x0"] for c in chars) - 2
    x1 = max(c["x1"] for c in chars) + 2
    top = min(c["top"] for c in chars) - 2
    bottom = max(c["bottom"] for c in chars) + 2
    spans = []
    for o in page.lines + page.rects + page.curves + page.images:
        if o["x0"] >= x0 and o["x1"] <= x1 and o["top"] >= top and o["bottom"] <= bottom:
            if o["bottom"] - o["top"] > page.height * 0.8:
                continue
            spans.append((o["top"], o["bottom"]))
    return spans


def answer_page_text(pdf_path: Path) -> str:
    """正解一覧のページの文字列。表の行がくずれにくい pdfium で読む。"""
    import pypdfium2

    doc = pypdfium2.PdfDocument(str(pdf_path))
    for i in range(len(doc) - 1, -1, -1):
        t = doc[i].get_textpage().get_text_range()
        if "正解肢" in t:
            return t
    return ""


def parse_answers(text: str):
    """「問 正解肢 問 正解肢」の表から {問番号: [正解肢,...]} を作る。"""
    key = {}
    ans = r"\d(?:\s*[,、・，]\s*\d)*"
    for line in nfkc_digits(text).splitlines():
        m = re.fullmatch(rf"\s*(\d{{1,2}})\s+({ans})\s+(\d{{1,2}})\s+({ans})\s*", line)
        pairs = [(m.group(1), m.group(2)), (m.group(3), m.group(4))] if m else []
        if not m:
            m = re.fullmatch(rf"\s*(\d{{1,2}})\s+({ans})\s*", line)
            pairs = [(m.group(1), m.group(2))] if m else []
        for q, a in pairs:
            key[int(q)] = [int(x) for x in re.findall(r"\d", a)]
    return key


def classify(stem: str) -> str:
    s = stem
    if "マンション管理適正化法" in s or "マンションの管理の適正化" in s:
        return "tekiseika"
    if "標準管理委託契約書" in s:
        return "itaku"
    if "標準管理規約" in s:
        return "kiyaku"
    if "区分所有法" in s or "被災区分所有" in s or "建替え" in s:
        return "kubun"
    if "民法" in s or "借地借家法" in s or "不動産登記" in s:
        return "minpo"
    if re.search(r"仕訳|会計|貸借対照表|収支|税|消費税|源泉", s):
        return "kaikei"
    if re.search(r"建築|設備|修繕|給水|排水|消防|防火|エレベーター|劣化|耐震|換気|水道|電気|長寿命|省エネ|構造|中性化|コンクリート", s):
        return "kenchiku"
    return "sonota"


def split_questions(lines):
    questions = []
    cur = None
    for ln in lines:
        text = ln["text"]
        m = re.match(r"^【\s*問\s*[^】]*】\s*(.*)$", text)
        if m:
            cur = {"lines": [], "fig": ln["fig"], "spans": {}}
            questions.append(cur)
            first = m.group(1).strip()
            if first:
                cur["lines"].append((first, None))
        elif cur is None:
            continue
        elif "正解肢" in text or re.search(r"管理業務主任者\s*試験(問題)?\s*正解", text):
            cur = None
            continue
        else:
            cur["lines"].append((text, ln["item"]))
            cur["fig"] = cur["fig"] or ln["fig"]
        sp = cur["spans"].setdefault(ln["page"], [ln["top"], ln["bottom"]])
        sp[0] = min(sp[0], ln["top"])
        sp[1] = max(sp[1], ln["bottom"])
    return questions


def render_figures(pdf, raw, tag):
    """図表のある問題を、PDF から画像として切り出す。public/kakomon/rNN/問番号-連番.png"""
    out_dir = ROOT / "public" / "kakomon" / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for i, rq in enumerate(raw, start=1):
        if not rq["fig"]:
            continue
        paths = []
        for k, (pno, (top, bottom)) in enumerate(sorted(rq["spans"].items()), start=1):
            page = pdf.pages[pno]
            x0, x1, _ = text_column(page)
            # 問題の文字の範囲に、次の問題が始まるまでにある図表を加えた範囲を切り出す
            nexts = [q["spans"][pno][0] for q in raw[i:] if pno in q["spans"]]
            limit = nexts[0] if nexts else page.height
            fig_bottoms = [b for t, b in PAGE_FIGS.get(pno, []) if t >= top - 4 and b <= limit]
            end = max([bottom, *fig_bottoms]) + 6
            bbox = (max(0, x0 - 6), max(0, top - 8), min(page.width, x1 + 6), min(page.height, end))
            name = f"{i:02d}-{k}.png"
            page.crop(bbox).to_image(resolution=160).save(out_dir / name)
            paths.append(f"kakomon/{tag}/{name}")
        result[i] = paths
    return result


def join(parts):
    s = "".join(parts)
    return s.strip()


def build_question(no, q):
    stem, statements, choices = [], [], []
    target = stem
    for text, item in q["lines"]:
        if item and item.isdigit() and 1 <= int(item) <= 9 and int(item) == len(choices) + 1:
            choices.append([re.sub(r"^\d\s*", "", text, count=1)])
            target = choices[-1]
        elif item and item in "アイウエオ" and not choices:
            statements.append({"label": item, "parts": [re.sub(r"^[アイウエオ]\s*", "", text, count=1)]})
            target = statements[-1]["parts"]
        else:
            target.append(text)
    data = {
        "no": no,
        "stem": join(stem),
        "statements": [{"label": s["label"], "text": join(s["parts"])} for s in statements],
        "choices": [join(c) for c in choices],
    }
    if not data["statements"]:
        del data["statements"]
    return data


def parse_kekka(path: Path):
    if not path.exists():
        return {}
    with pdfplumber.open(path) as pdf:
        t = nfkc_digits("\n".join(p.extract_text() or "" for p in pdf.pages))
    t = t.replace(",", "").replace("，", "")
    info = {}
    m = re.search(r"受験者数?\D{0,10}?(\d{4,6})\s*人", t)
    if m:
        info["examinees"] = int(m.group(1))
    m = re.search(r"合格者数?\D{0,10}?(\d{3,6})\s*人", t)
    if m:
        info["passers"] = int(m.group(1))
    m = re.search(r"合格率\D{0,10}?(\d+\.\d)\s*[%％]", t)
    if m:
        info["passRate"] = float(m.group(1))
    return info


def era_label(n: int) -> str:
    return "令和元年度" if n == 1 else f"令和{n}年度"


def main(src_dir: Path):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf_path in sorted(src_dir.glob("r[0-9][0-9]_mondai.pdf")):
        tag = pdf_path.name[:3]
        n = int(tag[1:])
        with pdfplumber.open(pdf_path) as pdf:
            if sum(len(p.chars) for p in pdf.pages) < 1000:
                print(f"{tag}: 文字情報のない（画像の）PDF のためスキップ（OCR が必要）")
                continue
            global CID_BASE
            CID_BASE = detect_cid_base("\n".join(p.extract_text() or "" for p in pdf.pages[:6]))
            lines = [ln for i, p in enumerate(pdf.pages) for ln in page_lines(p, i)]
            raw = split_questions(lines)
            images = render_figures(pdf, raw, tag)
        tail = answer_page_text(pdf_path)
        answers = parse_answers(tail)
        m = re.search(r"合格基準点\D*?50問中\s*(\d+)\s*問", nfkc_digits(tail))
        pass_mark = int(m.group(1)) if m else None
        m = re.search(r"免除者\D*?45問中\s*(\d+)\s*問", nfkc_digits(tail))
        pass_mark_exempt = int(m.group(1)) if m else None

        out_path = OUT_DIR / f"{tag}.json"
        old = {}
        if out_path.exists():
            old = {q["no"]: q for q in json.loads(out_path.read_text())["questions"]}

        qs, warn = [], []
        for i, rq in enumerate(raw, start=1):
            q = build_question(i, rq)
            q["category"] = classify(q["stem"])
            q["answer"] = answers.get(i, [])
            q["source"] = f"出典：{era_label(n)} 管理業務主任者試験問題 問{i}"
            if images.get(i):
                q["images"] = images[i]
                if len(q["choices"]) != 4:
                    # 図の中に選択肢がある問題。番号だけのボタンにする
                    q["choices"] = ["1", "2", "3", "4"]
            if len(q["choices"]) != 4 or not q["answer"]:
                q["needsReview"] = True
                warn.append(i)
            prev = old.get(i)
            if prev:
                for k in ("explanation", "tags"):
                    if prev.get(k):
                        q[k] = prev[k]
                if prev.get("categoryLocked"):
                    q["category"], q["categoryLocked"] = prev["category"], True
                if prev.get("manual"):
                    q = prev  # 手で直した問題は上書きしない
            qs.append(q)

        exam = {
            "id": tag,
            "year": 2018 + n,
            "label": era_label(n),
            "examDate": EXAM_DATES.get(tag),
            "passMark": pass_mark,
            "passMarkExempt": pass_mark_exempt,
            **parse_kekka(src_dir / f"{tag}_kekka.pdf"),
            "sourceUrl": f"https://www.kanrikyo.or.jp/kanri/shiken_{tag}/pdf/" + ("mondai_021.pdf" if tag == "r02" else "mondai_011.pdf"),
            "questions": qs,
        }
        out_path.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n")
        figs = [q["no"] for q in qs if q.get("images")]
        print(f"{tag}: {len(qs)}問, 正解 {len(answers)}件, 合格点 {pass_mark}, 要確認 {warn}, 図表あり {figs}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
