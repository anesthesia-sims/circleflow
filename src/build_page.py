# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
"""上昇式ベローズとピストン式（どちらも実行時シミュレーション）を 1 つの操作ページにまとめる。
場面は方式ごとに 4 つ：新鮮ガス（多め／低流量）× 換気（人工呼吸／用手換気。2026-11-02 に用手換気を追加）。
初学者向けに、ページの表には図と操作だけを置き、説明は重ねて出す（2026-11-02）：部品の名前をクリックすると
その部品を拡大して解説、時刻のバーを押すとその場面の説明、「使い方」で画面の上を指が動いて操作を順に見せる。
長い説明は「くわしく」の中。初めて開いたときは「使い方」を自動で出す（?notour で出さない）。
?term=inspValve のように部品の名前（TERMS のキー）を付けて開くと、その部品の解説を開いた状態になる。
使い方: python3 build_page.py [--lang en] [--other 別の言語のページの URL] out.html sim_common.js sim_bellows.js sim_piston.js  名前 svg geo ...
  --lang en：英語版（文は page_en.py、図は生成スクリプトに en を付けて作った英語の SVG を渡す。2026-11-02）
  --other：見出しの横に、もう一方の言語のページへのリンクを置く。日本語版では、ブラウザの言語が日本語でないときに
    英語版の案内を 1 行出す（自動では移らない）
  --href-ja・--href-en：公開する URL。付けると、言語版どうしの印（<link rel="alternate" hreflang>）を入れる
  名前は bellows・bellowsLow・bellowsMan・bellowsLowMan・piston・pistonLow・pistonMan・pistonLowMan の 8 つ
（bellows* は figure_bellows.py、piston* は figure_piston.py で作る。low を付けると低流量、manual を付けると用手換気、en で英語）
?type=（名前）&t=秒 を付けて開くと、その時刻で止めた 1 コマになる（動画のコマ撮り用）。"""
import os
import re
import sys

from page_css import CSS
from page_html import BODY_MID, BODY_TOP
from page_js import MAIN_JS
from page_terms import L_JS, TERMS

ARGS = sys.argv[1:]
LANG, OTHER, HREF = "ja", None, {}
while ARGS and ARGS[0].startswith("--"):
    _opt, _val = ARGS.pop(0), ARGS.pop(0)
    if _opt == "--lang":
        LANG = _val
    elif _opt == "--other":
        OTHER = _val
    elif _opt in ("--href-ja", "--href-en"):
        HREF[_opt[-2:]] = _val


def uniq_ids(svg, suf):
    """同じページに 4 枚の図を置くので、SVG 内の id に図ごとの印を付けて重複を避ける"""
    for name in sorted(set(re.findall(r'id="([^"]+)"', svg)), key=len, reverse=True):
        svg = (svg.replace(f'id="{name}"', f'id="{name}-{suf}"').replace(f'url(#{name})', f'url(#{name}-{suf})')
               .replace(f'href="#{name}"', f'href="#{name}-{suf}"'))
    return svg


OUT, _rest = ARGS[0], ARGS[1:]
SIM_FILES = []                                     # 粒のシミュレーション（sim_common.js → sim_bellows.js → sim_piston.js の順）
while _rest and _rest[0].endswith(".js"):
    SIM_FILES.append(_rest.pop(0))
SIMS = [open(f, encoding="utf-8").read() for f in SIM_FILES]
SUF = {"bellows": "b", "bellowsLow": "bl", "bellowsMan": "bm", "bellowsLowMan": "blm",
       "piston": "p", "pistonLow": "pl", "pistonMan": "pm", "pistonLowMan": "plm",
       "reflector": "r", "reflectorLow": "rl", "reflectorShort": "rs", "reflectorMan": "rm", "reflectorLowMan": "rlm"}
SCENES = {}
for _name, _svg, _geo in zip(_rest[0::3], _rest[1::3], _rest[2::3]):
    SCENES[_name] = (uniq_ids(open(_svg, encoding="utf-8").read(), SUF[_name]), open(_geo, encoding="utf-8").read())
assert set(SCENES) == set(SUF), sorted(SCENES)
FIGS = "\n".join(f'<div class="fig" id="fig-{k}"{"" if k == "bellows" else " hidden"}>{SCENES[k][0]}</div>' for k in SUF)
GEOS = "window.SCENE_GEO = {" + ",\n".join(f'"{k}": {SCENES[k][1]}' for k in SUF) + "};"


# 部品の名前をクリックしたときの解説。rect は拡大して見せる範囲（図の座標 x0, y0, x1, y1）を方式ごとに。
# words は図の中の文字（複数行の名前は行ごと）。図の部品の位置を動かしたら rect も直す。



TITLE, SIM_PRE = "CircleFlow：麻酔器と呼吸回路のガスの流れ", ""
if LANG == "en":                                   # 英語版：日本語版の HTML の文を置き換え、解説・画面の文を英語にする
    import page_en
    for _a, _b in page_en.HTML_PAIRS:
        assert (BODY_TOP + BODY_MID).count(_a) == 1, _a
        BODY_TOP, BODY_MID = BODY_TOP.replace(_a, _b), BODY_MID.replace(_a, _b)
    _left = re.findall(r"[^\x00-\u2fff]+", re.sub(r"<svg.*?</svg>", "", BODY_TOP + BODY_MID, flags=re.S))
    _left = [t for t in _left if re.search(r"[\u3040-\u9fff]", t)]
    assert not _left, f"英語版に日本語が残っている：{_left}"
    TITLE, TERMS, L_JS, SIM_PRE = page_en.TITLE, TERMS + page_en.terms_js(), page_en.l_js(), page_en.sim_text_js()
_other = "ja" if LANG == "en" else "en"
# 日本語版で、ブラウザの言語が日本語でないときだけ英語版を案内する（自動では移らない。閉じたら出さない）
_note = ""
if LANG == "ja" and OTHER:
    _note = (f'<div class="langnote chrome" id="langNote" lang="en" hidden><span>This page is also available in English.</span>'
             f'<a href="{OTHER}" hreflang="en">English version</a><button id="langNoteX" aria-label="Close">✕</button></div>\n'
             '<script>(() => { const n = document.getElementById("langNote"); let off = false;'
             ' try { off = localStorage.getItem("circleflow-langnote-off") === "1"; } catch (e) {}'
             ' const ja = (navigator.languages || [navigator.language]).some(l => /^ja/i.test(l || ""));'
             ' if (!ja && !off && !/[?&]t=/.test(location.search)) n.hidden = false;'
             ' document.getElementById("langNoteX").onclick = () => { n.hidden = true;'
             ' try { localStorage.setItem("circleflow-langnote-off", "1"); } catch (e) {} }; })();</script>\n')
BODY_TOP = BODY_TOP.replace("@@LANGNOTE@@", _note)
# 言語版どうしの印（検索エンジン向け）
ALT = "".join(f'<link rel="alternate" hreflang="{k}" href="{v}">\n' for k, v in sorted(HREF.items()))
if "ja" in HREF:
    ALT += f'<link rel="alternate" hreflang="x-default" href="{HREF["ja"]}">\n'
BODY_TOP = BODY_TOP.replace("@@LANG@@", f'<a class="lang" href="{OTHER}" hreflang="{_other}" lang="{_other}">{"日本語" if _other == "ja" else "English"}</a>' if OTHER else "")
# 新しい版の確認（2026-11-05 著者の依頼）：GitHub Pages は HTML を 10 分キャッシュしてよいと指示するので、開いたときに VERSION を
# キャッシュを使わずに取り、ページに埋めた版と違えば 1 回だけ再読み込みする。ファイルとして開いたとき・通信できないときは何もしない。
# 開いて 3 秒以上たっていたら（操作を始めている）再読み込みしない。同じ版への再読み込みは 1 回だけ（公開直後に VERSION だけ先に新しくなる
# ことがあるため）
VCHECK = ("<script>(() => { if (location.protocol !== 'http:' && location.protocol !== 'https:') return; const V = '@@VERSION@@';\n"
          "  fetch(new URL('" + ("../VERSION" if LANG == "en" else "VERSION") + "', location.href), { cache: 'no-store' }).then(r => r.ok ? r.text() : '').then(v => {\n"
          "    v = v.trim(); if (!v || v === V || performance.now() > 3000) return;\n"
          "    let done = ''; try { done = sessionStorage.getItem('circleflow-reloaded'); } catch (e) {}\n"
          "    if (done === v) return; try { sessionStorage.setItem('circleflow-reloaded', v); } catch (e) {}\n"
          "    location.reload();\n"
          "  }).catch(() => {}); })();</script>")
html = """<!doctype html>
<html lang="@@HTMLLANG@@"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + TITLE + """</title>
""" + ALT + """
""" + VCHECK + """
<style>""" + CSS + """</style></head>""" + BODY_TOP + FIGS + BODY_MID + """
<script>""" + GEOS + SIM_PRE + """</script>
""" + "".join(f"<script>\n{_js}\n</script>\n" for _js in SIMS) + """<script>
""" + TERMS + L_JS + MAIN_JS + """
</script>
</body></html>"""
VERSION = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "VERSION"), encoding="utf-8").read().strip()   # 版（ページの下に出す）
open(OUT, "w", encoding="utf-8").write(html.replace("@@HTMLLANG@@", LANG, 1).replace("@@VERSION@@", VERSION))
