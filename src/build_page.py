# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
"""上昇式ベローズとピストン式（どちらも実行時シミュレーション）を 1 つの操作ページにまとめる。
場面は方式ごとに 4 つ：新鮮ガス（多め／低流量）× 換気（人工呼吸／用手換気。2026-11-02 に用手換気を追加）。
初学者向けに、ページの表には図と操作だけを置き、説明は重ねて出す（2026-11-02）：部品の名前をクリックすると
その部品を拡大して解説、時刻のバーを押すとその場面の説明、「使い方」で画面の上を指が動いて操作を順に見せる。
長い説明は「くわしく」の中。初めて開いたときは「使い方」を自動で出す（?notour で出さない）。
?term=inspValve のように部品の名前（TERMS のキー）を付けて開くと、その部品の解説を開いた状態になる。
使い方: python3 build_page.py [--lang en|zh] [--other 言語=URL ...] out.html sim_common.js sim_bellows.js sim_piston.js  名前 svg geo ...
  --lang en：英語版（文は page_en.py、図は生成スクリプトに en を付けて作った英語の SVG を渡す。2026-11-02）
  --lang zh：中国語（簡体字）版（文は page_zh.py、図は zh を付けて作った SVG。2026-11-08）
  --other 言語=URL：見出しの横に、ほかの言語のページへのリンクを置く（繰り返し指定できる）。日本語版では、ブラウザの言語が
    日本語でないときに英語版か中国語版の案内を 1 行出す（自動では移らない）
  --href-ja・--href-en・--href-zh・--href-tw：公開する URL。付けると、言語版どうしの印（<link rel="alternate" hreflang>）を入れる
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
LANG, OTHER, HREF = "ja", {}, {}
while ARGS and ARGS[0].startswith("--"):
    _opt, _val = ARGS.pop(0), ARGS.pop(0)
    if _opt == "--lang":
        LANG = _val
    elif _opt == "--other":
        _k, _u = _val.split("=", 1)
        OTHER[_k] = _u
    elif _opt in ("--href-ja", "--href-en", "--href-zh", "--href-tw"):
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
       "reflector": "r", "reflectorLow": "rl", "reflectorShort": "rs", "reflectorMan": "rm", "reflectorLowMan": "rlm",
       "blower": "w", "blowerLow": "wl", "blowerMan": "wm", "blowerLowMan": "wlm"}
SCENES = {}
for _name, _svg, _geo in zip(_rest[0::3], _rest[1::3], _rest[2::3]):
    SCENES[_name] = (uniq_ids(open(_svg, encoding="utf-8").read(), SUF[_name]), open(_geo, encoding="utf-8").read())
assert set(SCENES) == set(SUF), sorted(SCENES)
FIGS = "\n".join(f'<div class="fig" id="fig-{k}"{"" if k == "bellows" else " hidden"}>{SCENES[k][0]}</div>' for k in SUF)
GEOS = "window.SCENE_GEO = {" + ",\n".join(f'"{k}": {SCENES[k][1]}' for k in SUF) + "};"


# 部品の名前をクリックしたときの解説。rect は拡大して見せる範囲（図の座標 x0, y0, x1, y1）を方式ごとに。
# words は図の中の文字（複数行の名前は行ごと）。図の部品の位置を動かしたら rect も直す。



TITLE, SIM_PRE = "CircleFlow：麻酔器と呼吸回路のガスの流れ", ""
if LANG in ("en", "zh", "tw"):                          # 英語版・中国語版：日本語版の HTML の文を置き換え、解説・画面の文をその言語にする
    import importlib
    page_l = importlib.import_module("page_" + LANG)
    for _a, _b in page_l.HTML_PAIRS:
        assert (BODY_TOP + BODY_MID).count(_a) == 1, _a
        BODY_TOP, BODY_MID = BODY_TOP.replace(_a, _b), BODY_MID.replace(_a, _b)
    _left = re.findall(r"[^\x00-\u2fff]+", re.sub(r"<svg.*?</svg>", "", BODY_TOP + BODY_MID, flags=re.S))
    # 中国語版は漢字が残っても日本語とは限らないので、かなだけを調べる（置き換え残しは HTML_PAIRS が日本語版と同じ組であることで防ぐ）
    _left = [t for t in _left if re.search(r"[\u3040-\u9fff]" if LANG == "en" else r"[\u3040-\u30fa\u30fc-\u30ff]", t)]
    assert not _left, f"{LANG} 版に日本語が残っている：{_left}"
    TITLE, TERMS, L_JS, SIM_PRE = page_l.TITLE, TERMS + page_l.terms_js(), page_l.l_js(), page_l.sim_text_js()
HTMLLANG = {"ja": "ja", "en": "en", "zh": "zh-Hans", "tw": "zh-Hant-TW"}
HREFLANG = {"ja": "ja", "en": "en", "zh": "zh-Hans", "tw": "zh-TW"}   # 言語版どうしの印（検索エンジンが受け付ける言語-地域の形）
FONT_CSS = ("\nbody { font-family:" + {"zh": __import__("palette").FONT_ZH, "tw": __import__("palette").FONT_TW}[LANG] + "; }\n") if LANG in ("zh", "tw") else ""
LINK_NAME = {"ja": ("日本語", "JA"), "en": ("English", "EN"), "zh": ("简体中文", "简"), "tw": ("繁體中文", "繁")}   # 狭い画面の短い表記：日本語版の見出しが 375 px に収まるよう 1 字に（2026-11-08）
# 日本語版で、ブラウザの言語が日本語でないときだけ、中国語なら中国語版、それ以外は英語版を案内する（自動では移らない。閉じたら出さない）
_note = ""
if LANG == "ja" and OTHER:
    _msg = {"en": ("This page is also available in English.", "English version"), "zh": ("本页面也有简体中文版。", "简体中文版"), "tw": ("本頁面也有繁體中文版。", "繁體中文版")}
    _note = ('<div class="langnote chrome" id="langNote" hidden><span id="langNoteMsg"></span>'
             '<a id="langNoteA"></a><button id="langNoteX" aria-label="Close">✕</button></div>\n'
             '<script>(() => { const n = document.getElementById("langNote"); let off = false;'
             ' try { off = localStorage.getItem("circleflow-langnote-off") === "1"; } catch (e) {}'
             ' const ls = (navigator.languages || [navigator.language]).map(l => l || "");'
             ' const ja = ls.some(l => /^ja/i.test(l));'
             ' if (ja || off || /[?&]t=/.test(location.search)) return;'
             ' const L = { ' + ", ".join(f'{k}: {{ href: "{OTHER[k]}", msg: "{_msg[k][0]}", a: "{_msg[k][1]}", lang: "{HTMLLANG[k]}" }}' for k in ("en", "zh", "tw") if k in OTHER) + ' };'
             ' const first = ls.find(l => /^(zh|en)/i.test(l)) || "en";'
             ' const k = /^zh/i.test(first) ? ((/^zh-(tw|hk|mo|hant)/i.test(first) && L.tw) ? "tw" : (L.zh ? "zh" : "en")) : "en"; const c = L[k]; if (!c) return;'
             ' n.lang = c.lang; document.getElementById("langNoteMsg").textContent = c.msg;'
             ' const a = document.getElementById("langNoteA"); a.textContent = c.a; a.href = c.href; a.hreflang = c.lang; n.hidden = false;'
             ' document.getElementById("langNoteX").onclick = () => { n.hidden = true;'
             ' try { localStorage.setItem("circleflow-langnote-off", "1"); } catch (e) {} }; })();</script>\n')
BODY_TOP = BODY_TOP.replace("@@LANGNOTE@@", _note)
# 言語版どうしの印（検索エンジン向け）
ALT = "".join(f'<link rel="alternate" hreflang="{HREFLANG[k]}" href="{v}">\n' for k, v in sorted(HREF.items()))
if "ja" in HREF:
    ALT += f'<link rel="alternate" hreflang="x-default" href="{HREF["ja"]}">\n'
# 検索結果の説明と、SNS でリンクを共有したときのプレビュー（2026-11-08 著者の依頼：英語圏・中華圏へ広めるための土台）。
# 画像は docs/og-ja.png・og-en.png・og-zh.png・og-tw.png（1200×630 の 2 倍。ベローズ式の吸気 1.0 秒のコマで、図の枠全体）
DESC = {"ja": "麻酔器と呼吸回路の中のガスを、1 粒ずつ動く粒で見せる無料の教育用シミュレーター。ベローズ式・ピストン式・ブロワ（タービン）式・ボリュームリフレクタ式の 4 方式、17 場面。ブラウザで動きます。",
        "en": "A free, in-browser educational simulator that shows gas flow in the anesthesia machine and breathing circuit as moving particles. Bellows, piston, blower (turbine) and volume reflector ventilators; 17 scenarios.",
        "zh": "免费的教学用模拟器，用移动的粒子显示麻醉机和呼吸回路中的气体流动。风箱式、活塞式、鼓风机（涡轮）式和容量反射器式 4 种类型，共 17 个场景，在浏览器中运行。",
        "tw": "免費的教學用模擬器，用移動的粒子顯示麻醉機和呼吸迴路中的氣體流動。風箱式、活塞式、鼓風機（渦輪）式和容積反射器式 4 種類型，共 17 個情境，在瀏覽器中執行。"}
IMG_ALT = {"ja": "CircleFlow の画面：ベローズ式（上昇式）の麻酔器と呼吸回路の模式図。ガスの粒が管の中を動く",
           "en": "CircleFlow screen: schematic of an anesthesia machine with an ascending bellows ventilator and the breathing circuit, with gas particles moving through the tubes",
           "zh": "CircleFlow 画面：风箱式（上升式）麻醉机和呼吸回路的示意图，气体粒子在管道中移动",
           "tw": "CircleFlow 畫面：風箱式（上升式）麻醉機和呼吸迴路的示意圖，氣體粒子在管路中移動"}
OG_LOCALE = {"ja": "ja_JP", "en": "en_US", "zh": "zh_CN", "tw": "zh_TW"}
# Google Search Console の所有確認（URL プレフィックス https://anesthesia-sims.github.io/circleflow/。2026-11-08 著者が登録）
GOOGLE_SITE_VERIFICATION = "-b0bVPpqGcbmjM_StmZRZlDOkRZqSF2LKK9xgnGD628"
META = (f'<meta name="description" content="{DESC[LANG]}">\n'
        f'<meta name="google-site-verification" content="{GOOGLE_SITE_VERIFICATION}">\n')
if LANG in HREF and "ja" in HREF:
    _img = HREF["ja"] + f"docs/og-{LANG}.png"
    META += (f'<link rel="canonical" href="{HREF[LANG]}">\n'
             '<meta property="og:type" content="website">\n<meta property="og:site_name" content="CircleFlow">\n'
             f'<meta property="og:title" content="{TITLE}">\n<meta property="og:description" content="{DESC[LANG]}">\n'
             f'<meta property="og:url" content="{HREF[LANG]}">\n<meta property="og:image" content="{_img}">\n'
             '<meta property="og:image:width" content="2400">\n<meta property="og:image:height" content="1260">\n'
             f'<meta property="og:image:alt" content="{IMG_ALT[LANG]}">\n<meta property="og:locale" content="{OG_LOCALE[LANG]}">\n'
             + "".join(f'<meta property="og:locale:alternate" content="{OG_LOCALE[k]}">\n' for k in ("ja", "en", "zh", "tw") if k != LANG and k in HREF)
             + '<meta name="twitter:card" content="summary_large_image">\n')
    # 検索エンジン向けの構造化データ（schema.org。2026-11-08 著者の依頼「周知に役立つ対応」）：無料の教材であること・対象・著者・DOI・言語版の関係
    import json as _json
    _ld = {
        "@context": "https://schema.org",
        "@type": ["LearningResource", "WebApplication"],
        "name": TITLE, "description": DESC[LANG], "url": HREF[LANG], "image": _img,
        "inLanguage": HTMLLANG[LANG], "isAccessibleForFree": True,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "learningResourceType": "Simulation", "applicationCategory": "EducationalApplication",
        "operatingSystem": "Any (web browser)", "softwareVersion": "@@VERSION@@",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "audience": [{"@type": "EducationalAudience", "audienceType": a} for a in
                     ("Medical students", "Anesthesiology residents", "Clinical engineers", "Nurse anesthetists", "Respiratory therapists")],
        "about": ["Anesthesia machine", "Breathing circuit (circle system)", "Anesthesia ventilator", "CO2 absorber"],
        "keywords": "anesthesia machine, breathing circuit, circle system, ventilator, bellows, piston, blower, volume reflector, medical education, simulation",
        "author": {"@type": "Person", "name": "Masaaki Asamoto", "alternateName": "朝元雅明",
                   "sameAs": ["https://orcid.org/0000-0002-0770-2860", "https://researchmap.jp/masaaki_asamoto"],
                   "affiliation": {"@type": "Organization", "name": "Department of Anesthesiology, Graduate School of Medicine, The University of Tokyo"}},
        "identifier": "https://doi.org/10.5281/zenodo.24050136",
        "sameAs": ["https://doi.org/10.5281/zenodo.24050136", "https://github.com/anesthesia-sims/circleflow"],
    }
    if LANG != "ja":
        _ld["translationOfWork"] = {"@id": HREF["ja"]}
    META += '<script type="application/ld+json">' + _json.dumps(_ld, ensure_ascii=False) + "</script>\n"
assert '"' not in "".join(DESC.values()) + "".join(IMG_ALT.values()) + TITLE
BODY_TOP = BODY_TOP.replace("@@LANG@@", " ".join(f'<a class="lang" href="{u}" hreflang="{HREFLANG[k]}" lang="{HTMLLANG[k]}">'
                                                 f'<span class="full">{LINK_NAME[k][0]}</span><span class="short">{LINK_NAME[k][1]}</span></a>' for k, u in OTHER.items()))   # 狭い画面では短い表記（2026-11-05）。中国語版を足して 2 つに（2026-11-08）
# 新しい版の確認（2026-11-05 著者の依頼）：GitHub Pages は HTML を 10 分キャッシュしてよいと指示するので、開いたときに VERSION を
# キャッシュを使わずに取り、ページに埋めた版と違えば 1 回だけ再読み込みする。ファイルとして開いたとき・通信できないときは何もしない。
# 開いて 3 秒以上たっていたら（操作を始めている）再読み込みしない。同じ版への再読み込みは 1 回だけ（公開直後に VERSION だけ先に新しくなる
# ことがあるため）
# 埋め込み（2026-11-07 著者の依頼：東大麻酔科の WordPress に AnesSimulator と同じ形で入れる）：ほかのページの iframe の中にいるときは、
# CSS が当たる前に html に embedded を付ける（画面の高さから幅を決めるのをやめる。高さの通知は page_js.py）
EMBED = "<script>if (self !== top) document.documentElement.classList.add('embedded');</script>"
VCHECK = ("<script>(() => { if (location.protocol !== 'http:' && location.protocol !== 'https:') return; const V = '@@VERSION@@';\n"
          "  fetch(new URL('" + ("../VERSION" if LANG != "ja" else "VERSION") + "', location.href), { cache: 'no-store' }).then(r => r.ok ? r.text() : '').then(v => {\n"
          "    v = v.trim(); if (!v || v === V || performance.now() > 3000) return;\n"
          "    let done = ''; try { done = sessionStorage.getItem('circleflow-reloaded'); } catch (e) {}\n"
          "    if (done === v) return; try { sessionStorage.setItem('circleflow-reloaded', v); } catch (e) {}\n"
          "    location.reload();\n"
          "  }).catch(() => {}); })();</script>")
# 閲覧数の計測（2026-11-08 著者の依頼）：Cloudflare Web Analytics（cookie を使わず、個人を特定する情報を集めない）。
# CF_TOKEN は Cloudflare の管理画面で anesthesia-sims.github.io を足したときに出るサイトのトークン（ページに載る公開の値）。
# 空なら計測の script もページ下の一文も出さない。数えないとき：ファイルとして開いたとき、手元の確認（localhost・127.0.0.1）、
# コマ撮り（?t=）、自動操作のブラウザ（navigator.webdriver。ヘッドレス Chrome での画像撮りなど）
CF_TOKEN = os.environ.get("CIRCLEFLOW_CF_TOKEN", "")
COUNT = ""
if CF_TOKEN:
    assert re.fullmatch(r"[0-9a-f]{32}", CF_TOKEN), "CF_TOKEN は 32 桁の 16 進数"
    COUNT = ("<script>(() => { const l = location;"
             " if (!/^https?:$/.test(l.protocol) || /^(localhost|127\\.0\\.0\\.1|\\[::1\\])$/.test(l.hostname)"
             " || /[?&]t=/.test(l.search) || navigator.webdriver) return;"
             " const s = document.createElement('script'); s.defer = true; s.src = 'https://static.cloudflareinsights.com/beacon.min.js';"
             " s.setAttribute('data-cf-beacon', '{\"token\": \"" + CF_TOKEN + "\", \"spa\": false}');"
             " document.head.appendChild(s); })();</script>\n")
COUNT_NOTE = {"ja": "閲覧数を cookie を使わずに数えています（Cloudflare Web Analytics）。",
              "en": " Page views are counted without cookies (Cloudflare Web Analytics).",
              "zh": "本页面使用 Cloudflare Web Analytics 统计浏览量，不使用 cookie。",
              "tw": "本頁面使用 Cloudflare Web Analytics 統計瀏覽量，不使用 cookie。"}
BODY_MID = BODY_MID.replace("@@COUNTNOTE@@", COUNT_NOTE[LANG] if CF_TOKEN else "")
assert "@@COUNTNOTE@@" not in BODY_TOP + BODY_MID
html = """<!doctype html>
<html lang="@@HTMLLANG@@"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + TITLE + """</title>
""" + META + ALT + """
""" + EMBED + """
""" + VCHECK + """
""" + COUNT + """<style>""" + CSS + FONT_CSS + """</style></head>""" + BODY_TOP + FIGS + BODY_MID + """
<script>""" + GEOS + SIM_PRE + """</script>
""" + "".join(f"<script>\n{_js}\n</script>\n" for _js in SIMS) + """<script>
""" + TERMS + L_JS + MAIN_JS + """
</script>
</body></html>"""
VERSION = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "VERSION"), encoding="utf-8").read().strip()   # 版（ページの下に出す）
open(OUT, "w", encoding="utf-8").write(html.replace("@@HTMLLANG@@", HTMLLANG[LANG], 1).replace("@@VERSION@@", VERSION))
