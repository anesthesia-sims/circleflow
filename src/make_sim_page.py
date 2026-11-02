# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
"""上昇式ベローズとピストン式（どちらも実行時シミュレーション）を 1 つの操作ページにまとめる。
場面は方式ごとに 4 つ：新鮮ガス（多め／低流量）× 換気（人工呼吸／用手換気。2026-11-02 に用手換気を追加）。
初学者向けに、ページの表には図と操作だけを置き、説明は重ねて出す（2026-11-02）：部品の名前をクリックすると
その部品を拡大して解説、時刻のバーを押すとその場面の説明、「使い方」で画面の上を指が動いて操作を順に見せる。
長い説明は「くわしく」の中。初めて開いたときは「使い方」を自動で出す（?notour で出さない）。
?term=inspValve のように部品の名前（TERMS のキー）を付けて開くと、その部品の解説を開いた状態になる。
使い方: python3 make_sim_page.py [--lang en] [--other 別の言語のページの URL] out.html sim_bellows.js sim_piston.js  名前 svg geo ...
  --lang en：英語版（文は page_en.py、図は生成スクリプトに en を付けて作った英語の SVG を渡す。2026-11-02）
  --other：見出しの横に、もう一方の言語のページへのリンクを置く。日本語版では、ブラウザの言語が日本語でないときに
    英語版の案内を 1 行出す（自動では移らない）
  --href-ja・--href-en：公開する URL。付けると、言語版どうしの印（<link rel="alternate" hreflang>）を入れる
  名前は bellows・bellowsLow・bellowsMan・bellowsLowMan・piston・pistonLow・pistonMan・pistonLowMan の 8 つ
（bellows* は make_anim_bellows3.py、piston* は make_anim_piston2.py で作る。low を付けると低流量、manual を付けると用手換気）
?type=（名前）&t=秒 を付けて開くと、その時刻で止めた 1 コマになる（動画のコマ撮り用）。"""
import re
import sys

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
rd = lambda i: open(ARGS[i - 1], encoding="utf-8").read()     # i は旧来の sys.argv の番号


def uniq_ids(svg, suf):
    """同じページに 4 枚の図を置くので、SVG 内の id に図ごとの印を付けて重複を避ける"""
    for name in sorted(set(re.findall(r'id="([^"]+)"', svg)), key=len, reverse=True):
        svg = (svg.replace(f'id="{name}"', f'id="{name}-{suf}"').replace(f'url(#{name})', f'url(#{name}-{suf})')
               .replace(f'href="#{name}"', f'href="#{name}-{suf}"'))
    return svg


OUT = ARGS[0]
sim_js, sim_pjs = rd(2), rd(3)
SUF = {"bellows": "b", "bellowsLow": "bl", "bellowsMan": "bm", "bellowsLowMan": "blm",
       "piston": "p", "pistonLow": "pl", "pistonMan": "pm", "pistonLowMan": "plm"}
SCENES = {}
for i in range(4, len(ARGS) + 1, 3):
    SCENES[ARGS[i - 1]] = (uniq_ids(rd(i + 1), SUF[ARGS[i - 1]]), rd(i + 2))
assert set(SCENES) == set(SUF), sorted(SCENES)
FIGS = "\n".join(f'<div class="fig" id="fig-{k}"{"" if k == "bellows" else " hidden"}>{SCENES[k][0]}</div>' for k in SUF)
GEOS = "window.SCENE_GEO = {" + ",\n".join(f'"{k}": {SCENES[k][1]}' for k in SUF) + "};"

CSS = r"""
  :root { --fg:#1a1a1a; --sub:#555; --bg:#ffffff; --blue:#1f5fae; --violet:#5e3fae; --line:#d9dde6; --red:#c62828; --panel:#ffffff; }
  * { box-sizing:border-box; }
  html,body { margin:0; background:var(--bg); color:var(--fg);
    font-family:'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif; }
  button { font:inherit; }
  /* 図・操作・時刻のバーが 1 画面に入るよう、画面の高さから幅を決める（--ar は図の横 ÷ 縦。場面を切り替えると変わる） */
  .wrap { max-width:max(620px, min(1300px, calc((100vh - 170px) * var(--ar, 1.515) + 32px))); margin:0 auto; padding:10px 16px 20px; }
  .top { display:flex; align-items:center; gap:10px; margin:2px 0 8px; }
  .top h1 { font-size:20px; margin:0; flex:1; }
  .top h1 span { font-size:14px; font-weight:400; color:var(--sub); margin-left:10px; }
  .top a.lang { font-size:14px; color:var(--blue); margin-right:4px; white-space:nowrap; }
  .top button { white-space:nowrap; }   /* 狭い画面で「How to use」などが 2 行に折れないように（2026-11-02） */
  .langnote { display:flex; align-items:center; gap:10px; margin:0 0 8px; padding:6px 8px 6px 12px; font-size:14px;
    border:1.5px solid var(--blue); border-radius:8px; }
  .langnote[hidden] { display:none; }
  .langnote a { color:var(--blue); font-weight:700; }
  .langnote span { flex:1; }
  .langnote button { border:none; background:none; font-size:16px; cursor:pointer; color:var(--sub); }
  .top button { font-size:14px; padding:6px 12px; border-radius:18px; cursor:pointer;
    border:1.5px solid var(--blue); background:#fff; color:var(--blue); display:inline-flex; align-items:center; gap:6px; }
  .top button .q { display:inline-grid; place-items:center; width:20px; height:20px; border-radius:50%;
    background:var(--blue); color:#fff; font-weight:700; font-size:13px; }
  .bar { display:flex; flex-wrap:wrap; align-items:center; gap:8px 14px; margin:0 0 8px; }
  .seg { display:inline-flex; border:1.5px solid var(--blue); border-radius:8px; overflow:hidden; }
  .seg button { font-size:14px; padding:5px 11px; cursor:pointer; border:none; background:#fff; color:var(--blue); }
  .seg button + button { border-left:1.5px solid var(--blue); }
  .seg button.on { background:var(--blue); color:#fff; }
  .seg.big button { font-size:15px; font-weight:700; padding:6px 14px; }
  .grp { display:inline-flex; align-items:center; gap:6px; }
  .grp .lab { font-size:13px; color:var(--sub); }
  #play { width:40px; height:34px; border-radius:50%; border:1.5px solid var(--blue); background:var(--blue); color:#fff; cursor:pointer;
    display:grid; place-items:center; padding:0; }
  #play svg { width:16px; height:16px; }
  .stage { position:relative; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
  .fig svg { width:100%; height:auto; display:block; }
  .fig[hidden] { display:none; }
  .fig .svgcap { display:none; }
  /* 押せる部品の名前：下の点線は文字の下線（text-decoration）ではなく、文字の幅に合わせて引いた線（uline）。
     文字の下線は字の大きさと図の拡大縮小で太さ・点の間隔がばらつき、白い縁取りにも欠かれて不揃いに見えた（2026-11-02） */
  .fig text.term { cursor:pointer; }
  .fig line.uline { stroke:var(--fg); stroke-width:1.4; stroke-linecap:round; stroke-dasharray:0.1 3.4; pointer-events:none; }
  .fig text.term:hover + line.uline { stroke-dasharray:none; }
  body.cap .fig .svgcap { display:inline; }
  body:not(.cap) .fig .svgnote { display:none; }
  .card { position:absolute; left:12px; bottom:12px; max-width:min(560px, calc(100% - 24px)); background:var(--panel);
    border:1.5px solid var(--fg); border-radius:10px; padding:12px 14px 10px; box-shadow:none;
    transform:translateY(16px); opacity:0; pointer-events:none; transition:transform .35s ease, opacity .35s ease; }
  .card.show { transform:none; opacity:1; pointer-events:auto; }
  .card h3 { margin:0 28px 4px 0; font-size:17px; }
  .card h3 .ph { display:inline-block; color:#fff; border-radius:6px; padding:1px 9px; margin-right:8px; font-size:15px; }
  .card h3 .ph.insp { background:var(--fg); } .card h3 .ph.exp { background:var(--violet); }
  .card p { margin:0; font-size:15px; line-height:1.7; }
  .card .x { position:absolute; right:8px; top:6px; width:28px; height:28px; border:none; background:none; font-size:20px; cursor:pointer; color:var(--sub); }
  .card nav { display:flex; justify-content:flex-end; gap:6px; margin-top:8px; }
  .card nav[hidden] { display:none; }
  .card nav button { font-size:13px; padding:3px 10px; border-radius:6px; border:1.5px solid var(--blue); background:#fff; color:var(--blue); cursor:pointer; }
  .chip { position:absolute; left:12px; top:10px; display:flex; align-items:center; gap:8px; font-size:14px;
    background:#fff; border:1.5px solid var(--red); border-radius:18px; padding:4px 6px 4px 12px; max-width:calc(100% - 24px); }
  .chip[hidden] { display:none; }
  .chip b { color:var(--red); }
  .chip button { border:none; background:none; font-size:16px; cursor:pointer; color:var(--sub); }
  .under { display:flex; flex-wrap:wrap; align-items:center; gap:8px 16px; margin-top:8px; }
  .tl { flex:1 1 170px; display:flex; align-items:center; gap:8px; min-width:200px; }
  .tl-bar { position:relative; flex:1; height:30px; display:flex; border-radius:6px; overflow:hidden; cursor:pointer; touch-action:none; user-select:none; }
  .tl-bar span { display:grid; place-items:center; color:#fff; font-size:13px; font-weight:700; border-right:2px solid #fff; }
  .tl-bar span:last-of-type { border-right:none; }
  .tl-bar span.insp { background:#3a3a3a; } .tl-bar span.exp { background:var(--violet); }
  .tl-bar i { position:absolute; top:0; bottom:0; width:3px; margin-left:-1.5px; background:#fff; box-shadow:0 0 0 1px #1a1a1a; pointer-events:none; }
  .tl output { font-variant-numeric:tabular-nums; font-size:13px; color:var(--sub); width:3.8em; text-align:right; }
  .abs { display:flex; align-items:center; gap:8px; font-size:14px; }
  /* 吸収剤のメーター：使用率をメーターの中に書き、使い切るとメーター自体が「使い切り」のボタンになる（幅は変わらない） */
  .abs .meter { position:relative; width:104px; height:22px; border:1.5px solid #555; border-radius:5px; background:#fff; overflow:hidden; padding:0; cursor:pointer; }
  .abs .meter i { position:absolute; left:0; top:0; bottom:0; width:0; background:#8f6fd0; }
  .abs .meter output { position:relative; font-size:12px; font-weight:700; color:var(--fg); }
  .abs .meter.out { border:2px solid var(--red); }
  .abs output, .abs .el { font-variant-numeric:tabular-nums; }
  .abs .el { color:var(--sub); min-width:5.6em; }
  .lk { border:none; background:none; padding:0; cursor:pointer; color:inherit; text-decoration:underline dotted 1.6px; text-underline-offset:3px; }
  .abs #absSwap { font-size:13px; padding:3px 10px; border-radius:6px; cursor:pointer; border:1.5px solid var(--violet); background:#fff; color:var(--violet); }
  .foot { margin-top:16px; padding-top:8px; border-top:1px solid var(--line); font-size:12px; line-height:1.7; color:var(--sub); }
  .foot a { color:var(--blue); }
  /* くわしい解説 */
  .modal { position:fixed; inset:0; background:rgba(0,0,0,.45); display:grid; place-items:center; padding:16px; z-index:20;
    opacity:0; pointer-events:none; transition:opacity .25s; }
  .modal.show { opacity:1; pointer-events:auto; }
  .modal .sheet { position:relative; background:#fff; border-radius:12px; max-width:860px; width:100%; max-height:calc(100vh - 32px); overflow:auto;
    padding:18px 22px 22px; font-size:14px; line-height:1.75; transform:translateY(12px); transition:transform .25s; }
  .modal.show .sheet { transform:none; }
  .modal h2 { font-size:16px; margin:16px 0 6px; border-left:4px solid var(--blue); padding-left:8px; }
  .modal h2:first-of-type { margin-top:0; }
  .modal .x { position:sticky; float:right; top:0; width:32px; height:32px; border:none; background:#fff; font-size:22px; cursor:pointer; color:var(--sub); }
  table { border-collapse:collapse; width:100%; font-size:14px; }
  th, td { border:1px solid var(--line); padding:6px 8px; vertical-align:top; text-align:left; }
  th { background:#eef3fa; }
  th:first-child, td:first-child { width:24%; min-width:6.5em; }
  .small { font-size:12px; color:var(--sub); }
  /* 使い方のツアー */
  .tour { position:fixed; inset:0; z-index:30; display:none; }
  .tour.show { display:block; }
  .tour > svg { position:absolute; inset:0; width:100%; height:100%; }
  .hand { position:absolute; left:0; top:0; width:44px; height:53px; pointer-events:none; transition:transform .75s cubic-bezier(.4,0,.2,1), opacity .3s; }
  .hand.press svg { transform:scale(.9); transform-origin:12px 2px; transition:transform .12s; }
  .ripple { position:absolute; width:16px; height:16px; margin:-8px 0 0 -8px; border-radius:50%; border:3px solid var(--blue); pointer-events:none; animation:rip .7s ease-out forwards; }
  @keyframes rip { from { transform:scale(.4); opacity:1; } to { transform:scale(3.2); opacity:0; } }
  /* 説明の吹き出しは、明るく切り抜いた場所（穴）の外に置き、青い枠で図と見分ける（2026-11-02。旧：図の中に重ねると図の一部に見えた） */
  .bubble { position:absolute; width:min(360px, calc(100vw - 24px)); background:#fff; border:2px solid var(--blue); border-radius:10px; padding:12px 14px 10px; font-size:15px; line-height:1.65;
    transition:left .45s ease, top .45s ease; }
  .bubble .dots { display:flex; gap:5px; margin:8px 0 0; }
  .bubble .dots i { width:7px; height:7px; border-radius:50%; background:#cfd6e3; }
  .bubble .dots i.on { background:var(--blue); }
  .bubble .bb { display:flex; justify-content:flex-end; gap:6px; margin-top:6px; }
  .bubble .bb button { font-size:13px; padding:4px 12px; border-radius:6px; border:1.5px solid var(--blue); background:#fff; color:var(--blue); cursor:pointer; }
  .bubble .bb button.pri { background:var(--blue); color:#fff; }
  .bubble kbd { font:inherit; font-size:12px; border:1px solid #aaa; border-radius:4px; padding:0 4px; }
  body.cap .wrap { padding:0; max-width:none; }
  body.cap .chrome { display:none !important; }
  body.cap .stage { border:none; border-radius:0; }
  @media (max-width:640px) { .top h1 span { display:none; } .top { flex-wrap:wrap; } .top h1 { flex:1 0 100%; } .seg button { padding:5px 8px; } .card p { font-size:14px; }
    /* 狭い画面では解説カードを図の上に重ねず、図の下に出す（図が小さいので重ねると部品が隠れる） */
    .card { position:relative; left:auto; bottom:auto; max-width:none; margin:0; border:none; border-top:1.5px solid var(--fg); border-radius:0; transform:none; }
    .card:not(.show) { display:none; } }
"""

# 部品の名前をクリックしたときの解説。rect は拡大して見せる範囲（図の座標 x0, y0, x1, y1）を方式ごとに。
# words は図の中の文字（複数行の名前は行ごと）。図の部品の位置を動かしたら rect も直す。
TERMS = r"""
const TERMS = {
  supply:   { name: 'ガス供給機構・気化器', words: ['ガス供給機構・気化器'],
              text: '病院の配管やボンベから来る O₂・空気・N₂O を、流量計で量を決めて混ぜ、気化器で麻酔薬を加えます。できたガス（新鮮ガス）は共通ガス出口から呼吸回路へ送られます。',
              rect: { bellows: [10, 15, 690, 740], piston: [10, 15, 690, 740] } },
  pipeline: { name: '中央配管', words: ['中央配管'],
              text: '壁の中の配管から O₂・空気・N₂O が届きます。取り違えないよう、色（O₂ は緑、空気は黄、N₂O は青）と差し込み口の形がガスごとに違います。',
              rect: { bellows: [30, 650, 580, 722], piston: [30, 650, 580, 722] } },
  cylinder: { name: 'ボンベ', words: ['ボンベ'],
              text: '配管が使えないときの予備です。高い圧でガスが詰めてあります。O₂ は黒、そのほかは灰色に塗られています。',
              rect: { bellows: [95, 535, 555, 650], piston: [95, 535, 555, 650] } },
  regulator:{ name: '減圧弁', words: ['減圧弁'],
              text: 'ボンベの高い圧を下げます。配管より少し低い圧にするので、配管がつながっていれば配管のガスが先に使われます。',
              rect: { bellows: [100, 497, 555, 545], piston: [100, 497, 555, 545] } },
  check:    { name: '逆止弁', words: ['逆止弁'],
              text: 'ガスを一方向（上）にだけ通す弁です。配管とボンベのガスが、互いの側へ逆に流れ込みません。図では流れている系統だけ弁板が開いています。',
              rect: { bellows: [50, 455, 555, 503], piston: [50, 455, 555, 503] } },
  n2ocut:   { name: '亜酸化窒素遮断弁', words: ['亜酸化窒素', '遮断弁', 'O₂の圧で開閉'],
              text: 'O₂ の圧で開いている弁です。O₂ の供給が止まって圧が下がると、ばねが戻って N₂O を止めます。O₂ のない N₂O だけを送らないための安全装置です。',
              rect: { bellows: [70, 285, 430, 362], piston: [70, 285, 430, 362] } },
  flowmeter:{ name: '流量計', words: ['流量計'],
              text: '下のつまみ（ニードル弁）を開けると、ガラス管の中のフロートが浮き上がります。管は上ほど太いので、流量が多いほど高く浮きます。目盛りはフロートの上の面で読みます。',
              rect: { bellows: [10, 140, 465, 275], piston: [10, 140, 465, 275] } },
  vaporizer:{ name: '気化器', words: ['気化器', '使用中', '停止中'],
              text: '液体の吸入麻酔薬を蒸発させます。ガスの一部を気化室に通して薬の蒸気を含ませ、残り（バイパス）と混ぜる割合をダイヤルで変えて濃度を決めます。',
              rect: { bellows: [455, 85, 630, 300], piston: [455, 85, 630, 300] } },
  interlock:{ name: 'インターロック', words: ['インターロック'],
              text: '2 台の気化器を同時に使えないようにする仕組みです。片方のダイヤルを回すと、青い棒がもう片方のダイヤルを止めます。',
              rect: { bellows: [470, 180, 610, 262], piston: [470, 180, 610, 262] } },
  flush:    { name: '酸素フラッシュ', words: ['酸素フラッシュ'],
              text: 'ボタンを押すと、流量計と気化器を通らずに O₂ を大量（毎分 35〜75 L ほど）に回路へ送ります。麻酔薬を含まないガスです（このシミュレーターでは押しません）。',
              rect: { bellows: [420, 355, 645, 452], piston: [420, 355, 645, 452] } },
  cgo:      { name: '共通ガス出口', words: ['共通ガス出口'],
              text: '流量計と気化器で作った新鮮ガスが、麻酔器から呼吸回路へ出る口です。',
              rect: { bellows: [550, 40, 700, 140], piston: [550, 40, 700, 140] } },
  circuit:  { name: '呼吸回路', words: ['呼吸回路'],
              text: '患者が吸って吐くガスがぐるりと回る輪（circle system）です。吸気と呼気の向きは一方向弁で決まり、呼気の CO₂ を吸収装置で除いてもう一度吸わせます。',
              rect: { bellows: [690, 15, 1195, 740], piston: [690, 15, 1335, 740] } },
  decouple: { name: '新鮮ガス・デカップリング弁', words: ['新鮮ガス・', 'デカップリング弁'],
              text: '吸気のあいだは閉じて、新鮮ガスを患者へ行かせず呼吸バッグへ向けます。そのため新鮮ガスの量を変えても、患者に入る量（1 回換気量）が変わりません。',
              rect: { piston: [795, 35, 945, 140] } },
  inspValve:{ name: '吸気弁', words: ['吸気弁'],
              text: '患者へ向かう向きにだけ開く一方向弁です。ガスが来るとドームの中の弁板（青）が持ち上がって開き、逆向きには弁板が押しつけられて閉じます。',
              rect: { bellows: [835, 50, 935, 142], piston: [1010, 45, 1105, 142] } },
  gauge:    { name: '回路内圧計', words: ['回路内圧計', 'cmH₂O'],
              text: '呼吸回路の中の圧（cmH₂O）を示します。吸気で上がり、呼気で下がります。',
              rect: { bellows: [810, 150, 958, 212], piston: [940, 22, 1025, 100] } },
  hose:     { name: '蛇管・Y ピース', words: ['蛇管・', 'Yピース'],
              text: '吸気と呼気の 2 本の蛇管が Y ピースで 1 本になり、マスクや気管チューブにつながります。Y ピースから先は、吸気と呼気が同じ道を行き来します。',
              rect: { bellows: [915, 95, 1130, 485], piston: [1090, 100, 1255, 497] } },
  patient:  { name: '患者・気管（死腔）', words: ['患者', '気管', '（死腔）'],
              text: '気管のガスは肺胞まで届かないので、CO₂ を受け取りません（死腔）。吸気の始めには、気管に残っていた前の呼気がまず肺胞へ戻ります。',
              rect: { bellows: [1045, 225, 1197, 515], piston: [1170, 250, 1335, 545] } },
  alveoli:  { name: '肺胞', words: ['肺胞'],
              text: '血液から CO₂ を受け取る場所です。黒い粒はここでオレンジ（CO₂ を含むガス）に変わります。吸気でふくらみ、呼気でしぼみます。',
              rect: { bellows: [1095, 350, 1197, 515], piston: [1220, 385, 1315, 545] } },
  expValve: { name: '呼気弁', words: ['呼気弁'],
              text: '患者から戻る向きにだけ開く一方向弁です。吸気のあいだは閉じて、吸気が呼気側へ流れないようにします。',
              rect: { bellows: [935, 385, 1015, 482], piston: [1062, 405, 1158, 500] } },
  peep:     { name: 'PEEP/Pmax 弁', words: ['PEEP/Pmax弁'],
              text: '呼気側の管にある弁で、ピストンとあわせて働きます。吸気中は閉じて、ピストンが送るガスを呼吸バッグ側へ逃がさず患者へ向けます（回路の圧が上限 Pmax を超えたときだけ開く）。呼気中は呼気を呼吸バッグへ通しつつ肺の圧を PEEP より下げないので、ピストンが下がるときに肺からガスを吸い出しません。',
              rect: { piston: [935, 435, 1068, 530] } },
  absorber: { name: '二酸化炭素吸収装置', words: ['二酸化炭素', '吸収装置', '二酸化炭素吸収剤'],
              text: '呼気の CO₂ を、吸収剤が化学反応で取り除きます。オレンジの粒が通ると黒に戻ります。CO₂ を吸った吸収剤は、指示薬で白から紫に変わります（時間を縮めて表示。早送りで変化が見えます）。',
              rect: { bellows: [735, 265, 955, 440], piston: [730, 285, 945, 448] } },
  apl:      { name: 'APL 弁', words: ['APL弁'],
              text: { bellows: '回路の圧が、つまみで決めた値を超えると開き、余ったガスを余剰ガス排出装置へ逃がします。用手換気でバッグを押す圧の上限を決めます。人工呼吸中は切替弁で回路から外れます。',
                      piston: '回路の圧が、つまみで決めた値を超えると開き、余ったガスを余剰ガス排出装置へ逃がします。用手換気でバッグを押す圧の上限を決めます。人工呼吸中は APL バイパス弁が開いているので、APL 弁は閉じたままです。' },
              rect: { bellows: [748, 538, 845, 668], piston: [750, 538, 855, 650] } },
  bypass:   { name: 'APL バイパス弁', words: ['APLバイパス弁', '（人工呼吸中に開く）'],
              text: 'APL 弁と並んで、呼吸バッグの管から分かれる弁です。人工呼吸中は開いていて、呼吸バッグが満杯になると、余ったガスは APL 弁を通らずにここから排出へ出ます。用手換気では閉じて、APL 弁で圧を調節できるようにします。',
              rect: { piston: [852, 584, 1018, 640] } },
  exhaust:  { name: '排気逆止弁', words: ['排気逆止弁'],
              text: '余剰ガス排出装置へ向かう向きにだけ開く逆止弁です。APL 弁と APL バイパス弁から出たガスは、ここを通って排出装置へ流れ、逆には戻りません。',
              rect: { piston: [768, 630, 866, 680] } },
  bag:      { name: '呼吸バッグ', words: ['呼吸バッグ', '手で押す'],
              text: { bellows: '用手換気では、この袋を手で押して患者へガスを送ります。呼気でふくらみ、満杯になると余ったガスは APL 弁から出ます。人工呼吸中は切替弁で回路から外れて動きません。',
                      piston: '人工呼吸中もリザーバー（ガスのため）として回路に残り、呼気と新鮮ガスをためて、ピストンが吸い込むとしぼみます。用手換気ではピストンが止まり、この袋を手で押して患者へガスを送ります。' },
              rect: { bellows: [685, 515, 780, 645], piston: [692, 505, 798, 652] } },
  selector: { name: '切替弁', words: ['切替弁', '用手', '人工呼吸'],
              text: '用手換気（呼吸バッグ）と人工呼吸（ベローズ）を切り替えます。中の栓（青）が回り、L 字の穴でつなぐ道を変えます。',
              rect: { bellows: [835, 540, 965, 650] } },
  bellows:  { name: 'ベローズ', words: ['ベローズ'],
              text: '蛇腹の袋です。吸気では、まわりに入る駆動ガスに押されて下がり、中のガスを患者へ送ります。呼気では、呼気と新鮮ガスで上がります（上昇式）。回路にもれがあると上がりきらないので、気づきやすい形です。用手換気では回路から外れて止まります。',
              rect: { bellows: [960, 500, 1162, 615] } },
  drive:    { name: '駆動ガス', words: ['駆動ガス（O₂）'],
              text: 'ハウジング（ベローズを囲む筒）に入って、ベローズを外から押す O₂ です。ベローズの壁で隔てられているので、患者の吸うガスとは混ざりません。',
              rect: { bellows: [960, 500, 1162, 615] } },
  spill:    { name: '余剰ガス弁', words: ['余剰ガス弁'],
              text: 'ベローズが上がりきったあと、余ったガスを余剰ガス排出装置へ逃がします。吸気のあいだは駆動ガスの圧で閉じています。開くのに 2〜3 cmH₂O かかるので、呼気の終わりにこの圧が回路に残ります。',
              rect: { bellows: [970, 585, 1090, 650] } },
  piston:   { name: 'ピストン', words: ['ピストン', 'モーター'],
              text: 'モーターがピストンを押し上げ、シリンダーのガスを患者へ送ります。押し出した量がそのまま 1 回換気量になります。駆動ガスは使いません。呼気の後半に下がり、次のガスを吸い込みます。用手換気では上で止まります。',
              rect: { piston: [890, 140, 1000, 322] } },
  ambient:  { name: '外気取り込み弁', words: ['外気取り込み弁', '（陰圧防止）'],
              text: 'ピストンが下がるときに回路のガスが足りないと、外気を取り込んで、回路が陰圧になるのを防ぎます（このシミュレーターでは開きません）。',
              rect: { piston: [965, 145, 1128, 200] } },
  scav:     { name: '余剰ガス排出装置', words: ['余剰ガス排出装置', '→ 手術室外へ', '大気', '吸引'],
              text: '余った麻酔ガスを、吸引で手術室の外へ出します。大気に開いた口があるので、回路に吸引の陰圧や陽圧がかかりません。',
              rect: { bellows: [750, 650, 1185, 725], piston: [750, 647, 1285, 725] } },
  particles:{ name: 'ガスの粒', words: ['CO₂ を含まないガス', 'CO₂ を含むガス'],
              text: '粒 1 つが少しの量のガスです。黒は CO₂ を含まないガス、オレンジは CO₂ を含むガス。肺胞でオレンジになり、吸収装置で黒に戻ります。粒をクリックすると、その粒を追いかけます。',
              rect: null },
  exhausted:{ name: '吸収剤を使い切りました', words: [], text: '', rect: { bellows: [735, 265, 955, 440], piston: [730, 285, 945, 448] } },
};
// 「前へ・次へ」で回る順（ガスの流れの順）
const TERM_ORDER = ['supply', 'pipeline', 'cylinder', 'regulator', 'check', 'n2ocut', 'flowmeter', 'vaporizer', 'interlock', 'flush', 'cgo',
  'circuit', 'decouple', 'inspValve', 'gauge', 'hose', 'patient', 'alveoli', 'expValve', 'peep', 'selector', 'bellows', 'drive', 'spill',
  'bag', 'apl', 'bypass', 'exhaust', 'piston', 'ambient', 'absorber', 'scav'];
"""

# 画面の文（言語ごと。英語版は page_en.py。2026-11-02）
L_JS = r"""
const L = {
  phases: {
    bellows: [["吸気", 0, 2, "insp", "駆動ガス（O₂）がベローズを押し下げ、ガスは吸収装置と吸気弁を通って患者へ送られる。新鮮ガスも吸気に加わる。"],
              ["呼気", 2, 6, "exp", "呼気と新鮮ガスがベローズを下から押し上げる。上まで上がると、余ったガスは余剰ガス弁から排出装置へ流れる。"]],
    piston:  [["吸気", 0, 2, "insp", "ピストンが押し上がり、ガスを吸気弁から患者へ送る。新鮮ガス・デカップリング弁は閉じ、新鮮ガスは吸収装置を逆に通って呼吸バッグへ向かう。"],
              ["呼気①", 2, 3.6, "exp", "呼気は呼気弁と PEEP/Pmax 弁を通って呼吸バッグへ入る。人工呼吸中もバッグがふくらみ、満杯になると余ったガスは余剰ガス排出装置へ流れる。"],
              ["呼気②", 3.6, 6, "exp", "ピストンが下がり、呼吸バッグのガス（吸収装置を通る）と新鮮ガスを、デカップリング弁からシリンダーへ吸い込む。"]],
    bellowsMan: [["吸気", 0, 2, "insp", "呼吸バッグを手で押すと、ガスは切替弁（用手）から吸収装置と吸気弁を通って患者へ送られる。新鮮ガスも吸気に加わる。ベローズは止まっている。"],
                 ["呼気", 2, 6, "exp", "呼気と新鮮ガスが呼吸バッグへ戻ってふくらませる。バッグが満杯になると、余ったガスは APL 弁から余剰ガス排出装置へ流れる。"]],
    pistonMan:  [["吸気", 0, 2, "insp", "ピストンは止まっている。呼吸バッグを手で押すと、ガスは吸収装置を通り、新鮮ガスと合わさって新鮮ガス・デカップリング弁と吸気弁から患者へ送られる。"],
                 ["呼気", 2, 6, "exp", "呼気は呼気弁と PEEP/Pmax 弁を通って呼吸バッグへ戻り、新鮮ガスも吸収装置を逆に通ってバッグへ向かう。バッグが満杯になると、余ったガスは APL 弁から余剰ガス排出装置へ流れる。"]],
  },
  now: 'いま起きていること', usedUp: '使い切り', pause: '一時停止', play: '再生', start: 'はじめる', next: '次へ',
  breath: n => `${n} 呼吸目`, sec: c => c.toFixed(1) + ' 秒',
  exhausted: ['吸収剤の全層が紫になり、CO₂ が除かれなくなりました。オレンジの粒が吸気側の管を通って患者へ戻っています（再呼吸）。「交換」で新しい吸収剤に戻せます。',
    '吸収剤の全層が紫になり、CO₂ が除かれなくなりました。この場面では CO₂ の多くが余剰ガスとして出ていくため、吸気側にはほとんど戻りません。「交換」で新しい吸収剤に戻せます。'],
  steps: [
    '図の中を動く粒の 1 つ 1 つがガスで、<b>黒</b>は CO₂ を含まないガス、<b style="color:#e8590c">オレンジ</b>は CO₂ を含むガス。粒の動きでガスの流れが見えます。',
    '再生・一時停止（<kbd>スペース</kbd>キーでも）。',
    '人工呼吸器の方式を切り替えます。',
    '場面を切り替えます。呼吸バッグを手で押す<b>用手換気</b>、新鮮ガスを減らした<b>低流量</b>。',
    '吸気・呼気のバーです。押すとその時刻で止まり、いま起きていることが出ます（<kbd>←</kbd> <kbd>→</kbd> で 0.1 秒ずつ）。',
    '粒をクリックすると、その粒を赤い輪と足跡で追いかけます（<kbd>Esc</kbd> でやめる）。',
    '点線の下線がある部品の名前をクリックすると、その部品を拡大して説明します。',
    '二酸化炭素吸収剤の減り具合です。速さを 4×・16× にすると、紫に変わっていく様子が見えます。',
    '2 つの方式の違いなど、くわしい解説はここにあります。もう一度この説明を見るときは「使い方」へ。'],
};
"""

BODY_TOP = r"""
<body><div class="wrap">
@@LANGNOTE@@<header class="top chrome">
  <h1>CircleFlow<span>麻酔器と呼吸回路のガスの流れ</span></h1>
  @@LANG@@
  <button id="helpBtn" aria-label="使い方"><span class="q">?</span>使い方</button>
  <button id="moreBtn">くわしく</button>
</header>
<div class="bar chrome">
  <div class="seg big" role="tablist" id="typeSeg">
    <button class="on" data-type="bellows" role="tab">上昇式ベローズ</button><button data-type="piston" role="tab">ピストン式</button>
  </div>
  <div class="grp" id="ventGrp"><span class="lab">換気</span><div class="seg">
    <button data-vent="auto" class="on">人工呼吸</button><button data-vent="man">用手換気</button></div></div>
  <div class="grp" id="flowGrp"><span class="lab">新鮮ガス</span><div class="seg">
    <button data-flow="high" class="on">多め</button><button data-flow="low">低流量</button></div></div>
</div>
<div class="stage" id="stage">
"""
BODY_MID = r"""
  <div class="chip chrome" id="chip" hidden><b>追跡中</b><span id="chipMsg"></span><button id="chipX" aria-label="追跡をやめる">✕</button></div>
  <div class="card chrome" id="card" role="dialog" aria-live="polite">
    <button class="x" id="cardX" aria-label="閉じる">✕</button>
    <h3 id="cardTtl"></h3><p id="cardTxt"></p>
    <nav id="cardNav"><button id="cardPrev">‹ 前へ</button><button id="cardNext">次へ ›</button></nav>
  </div>
</div>
<div class="under chrome">
  <button id="play" aria-label="一時停止"></button>
  <div class="tl"><div class="tl-bar" id="tlBar" role="slider" aria-label="時刻" aria-valuemin="0" aria-valuemax="6"></div><output id="tout">0.0 秒</output></div>
  <div class="grp" id="speedGrp"><span class="lab">速さ</span><div class="seg">
    <button data-speed="0.25">¼</button><button data-speed="0.5">½</button><button data-speed="1" class="on">1×</button><button data-speed="4">4×</button><button data-speed="16">16×</button></div></div>
  <div class="abs" id="absbox">
    <button class="lk" data-term="absorber">吸収剤</button>
    <button class="meter" id="absMeter" aria-label="吸収剤の使用率"><i id="absBar"></i><output id="absPct">0%</output></button>
    <span class="el" id="absEl">1 呼吸目</span>
    <button id="absSwap">交換</button>
  </div>
</div>
<footer class="foot chrome">
  CircleFlow © 2026 朝元雅明（Masaaki Asamoto）。プログラムは <a href="https://opensource.org/license/mit" rel="license">MIT</a>、図と文章は <a href="https://creativecommons.org/licenses/by/4.0/deed.ja" rel="license">CC BY 4.0</a>。教育用の模式図で、臨床の判断や機器の操作に用いるものではありません。特定のメーカーとは関係ありません。<br>
  謝辞：帝京大学医学部附属溝口病院 麻酔科の平林剛先生から、呼吸回路と人工呼吸器の方式について助言をいただきました。内容の誤りは著者の責任です。
</footer>
</div>
<div class="modal chrome" id="more" role="dialog" aria-label="くわしい解説"><div class="sheet">
  <button class="x" id="moreX" aria-label="閉じる">✕</button>
  <h2>2 つの方式の違い</h2>
  <table>
    <tr><th></th><th>上昇式ベローズ</th><th>ピストン式</th></tr>
    <tr><td>人工呼吸器を動かす力</td><td>駆動ガス（O₂）がハウジング内でベローズを押し下げる</td><td>モーターがロッドでピストンを押し引きする（駆動ガスを使わない）</td></tr>
    <tr><td>次の吸気ガスのため方</td><td>呼気と新鮮ガスがベローズを下から押し上げてためる</td><td>ピストンが下がって、呼吸バッグのガスと新鮮ガスを吸い込む</td></tr>
    <tr><td>吸気中の新鮮ガス</td><td>吸気に加わって患者へ</td><td>新鮮ガス・デカップリング弁が閉じ、呼吸バッグへ向かう</td></tr>
    <tr><td>人工呼吸中の呼吸バッグ</td><td>切替弁で回路から外れ、動かない</td><td>リザーバーとして回路に残り、ふくらみ・しぼむ</td></tr>
    <tr><td>回路の陰圧</td><td>ガスを吸い込む動きがないため、構造上起こらない</td><td>吸い込む動きがあるため、PEEP/Pmax 弁と外気取り込み弁で防ぐ</td></tr>
    <tr><td>余ったガスの出口</td><td>ベローズが上がりきると、余剰ガス弁から排出装置へ</td><td>呼吸バッグが満杯になると、APL バイパス弁から排気逆止弁を通って排出装置へ（用手換気では APL 弁から）</td></tr>
    <tr><td>新鮮ガスを減らしたときの 1 回換気量</td><td>吸気中に加わる新鮮ガスのぶん減る（本図の低流量の場面では、ベローズの送り出しを増やしてそろえた）</td><td>変わらない（デカップリング弁があり、患者へ送るのはピストンが押し出す量だけ）</td></tr>
    <tr><td>呼気終末の回路内圧</td><td>余剰ガス弁の開放圧（2〜3 cmH₂O）が残る</td><td>PEEP/Pmax 弁の設定値まで下がる（設定 0 なら 0 付近）</td></tr>
  </table>
  <h2>設計の考え方</h2>
  <p>上昇式ベローズは、ベローズが上がりきらなければ次の吸気を送れない代わりに、どのような機械的不具合が起きても患者の気道が陰圧にならない、安全を優先した設計です。ピストン式は、ガスを吸い込む動きによって陰圧が生じうる構造を、新鮮ガス・デカップリングや弁などの制御で補い、正確な換気量や多様な換気モードを実現しています。</p>
  <h2>用手換気</h2>
  <p>人工呼吸器を使わず、呼吸バッグを手で押して換気します。上昇式ベローズでは切替弁を「用手」に倒し、栓の L 字の穴が呼気側の合流点と APL 弁・呼吸バッグの側をつなぎます（ベローズは回路から外れて止まります）。ピストン式では切替弁はなく、ピストンが止まり、もともと回路にある呼吸バッグを押します。どちらも吸気では、押されたバッグのガスが吸収装置を通って CO₂ を除かれ、新鮮ガスと合わさって吸気弁から患者へ送られます（ピストン式では新鮮ガス・デカップリング弁を通ります）。呼気では、呼気と新鮮ガスがバッグへ戻ってふくらませ、満杯になると余ったガスは APL 弁から余剰ガス排出装置へ出ていきます。本図では、手で押す量を人工呼吸の場面の 1 回換気量にそろえています（実際には呼吸ごとに変わります）。</p>
  <h2>二酸化炭素吸収剤の色の変化</h2>
  <p>呼気は吸収装置の下から入るため、吸収剤は入口側（下）から使われ、紫の帯が出口側（上）へ進みます。実際には数時間以上かけて進む変化を、数分から十数分に縮めて表示しています（吸収剤の量はどの場面でも同じ）。</p>
  <p>「新鮮ガス：多め」では、新鮮ガス流量を分時換気量に近く設定しています。上昇式ベローズでは、呼気の CO₂ の多くは吸収装置に届く前に余剰ガスとして排出されるため、吸収剤の消費は遅く（約 140 呼吸）、使い切っても吸気側に CO₂ はほとんど戻りません。ピストン式では、呼気がいったん呼吸バッグにたまり、ピストンが吸収装置を通して吸い込むため、約 50 呼吸で使い切り、使い切ると吸気側に CO₂ がわずかに戻ります。</p>
  <p>「新鮮ガス：低流量」では、新鮮ガスを 4 分の 1 に減らしています。呼気のほとんどが吸収装置を通って再び吸われるため、消費が速くなります（約 20〜25 呼吸）。使い切るとオレンジの粒が吸気側の管を通って患者へ戻り、吸気の CO₂ が上がります（カプノグラムの基線が 0 に戻らなくなる）。上昇式ベローズの低流量の場面では、ベローズの送り出しを増やして、1 回換気量を「多め」と同じにしています。</p>
  <p>2 つの方式で使い切るまでの呼吸数が違うのは、本図の回路の管の長さや余ったガスの出口の位置の違いによるもので、実際の機種どうしの比較ではありません。指示薬の色は、使用後にしばらく置くと白に戻ることがあります。交換の判断は色だけでなく、吸気の CO₂ も合わせて行います。</p>
  <p class="small">本図は模式図です。部品の形・位置・弁の構成は機種によって異なります（ピストン式は Dräger Fabius 型の構成を参考にしています）。1 呼吸は 6 秒（吸気 2 秒・呼気 4 秒）で表示しています。ガスの量や時間、吸収剤の容量は見やすさのために整えた値です。</p>
</div></div>
<div class="tour chrome" id="tour" aria-live="polite">
  <svg id="tourSvg"><path id="tourDim" fill="rgba(0,0,0,0.55)" fill-rule="evenodd"/></svg>
  <div class="hand" id="hand"><svg viewBox="-3 -3 42 52" width="44" height="53" aria-hidden="true">
    <g stroke="#1a1a1a" stroke-width="4.4" stroke-linejoin="round">
      <rect x="8" y="0" width="9" height="26" rx="4.5"/><rect x="15.5" y="14" width="8" height="14" rx="4"/>
      <rect x="22.5" y="16" width="8" height="13" rx="4"/><rect x="29" y="19" width="7" height="12" rx="3.5"/>
      <rect x="6" y="20" width="30" height="20" rx="8"/><rect x="0" y="23" width="9" height="15" rx="4.5" transform="rotate(-28 4.5 30)"/>
      <rect x="10" y="38" width="22" height="9" rx="2"/></g>
    <g fill="#fff">
      <rect x="8" y="0" width="9" height="26" rx="4.5"/><rect x="15.5" y="14" width="8" height="14" rx="4"/>
      <rect x="22.5" y="16" width="8" height="13" rx="4"/><rect x="29" y="19" width="7" height="12" rx="3.5"/>
      <rect x="6" y="20" width="30" height="20" rx="8"/><rect x="0" y="23" width="9" height="15" rx="4.5" transform="rotate(-28 4.5 30)"/></g>
    <rect x="10" y="38" width="22" height="9" rx="2" fill="#c8c8c8"/>
    <path d="M19.5 20 v6 M26.5 22 v5" stroke="#1a1a1a" stroke-width="1.6" stroke-linecap="round"/></svg></div>
  <div class="bubble" id="bubble"><div id="bubbleTxt"></div><div class="dots" id="bubbleDots"></div>
    <div class="bb"><button id="tourSkip">閉じる</button><button id="tourPrev">戻る</button><button id="tourNext" class="pri">次へ</button></div></div>
</div>
"""

MAIN_JS = r"""
(() => {
  const CYC = 6.0, NS = 'http://www.w3.org/2000/svg';
  const PHASES = L.phases;

  const TYPES = ['bellows', 'bellowsLow', 'bellowsMan', 'bellowsLowMan', 'piston', 'pistonLow', 'pistonMan', 'pistonLowMan'];
  const $ = id => document.getElementById(id);
  const figs = {};
  for (const k of TYPES) figs[k] = document.querySelector('#fig-' + k + ' svg');
  PHASES.bellowsLow = PHASES.bellows; PHASES.pistonLow = PHASES.piston;
  PHASES.bellowsLowMan = PHASES.bellowsMan; PHASES.pistonLowMan = PHASES.pistonMan;
  const family = tp => tp.startsWith('piston') ? 'piston' : 'bellows';
  const key = (fam, lo, mn) => fam + (lo ? 'Low' : '') + (mn ? 'Man' : '');
  let low = false, man = false;                                  // 新鮮ガス：低流量、換気：用手換気
  Object.values(figs).forEach(s => s.pauseAnimations());
  const q = new URLSearchParams(location.search);
  const BASE = {}, vbCur = {};                                   // 図ごとのもとの表示範囲と、いまの表示範囲（拡大用）
  for (const k of TYPES) {
    const s = figs[k], vb = s.viewBox.baseVal;
    BASE[k] = [0, 0, vb.width, q.has('t') ? vb.height : vb.height - 68];   // 操作ページでは下の字幕の帯を切る
    if (!q.has('t')) { s.setAttribute('viewBox', BASE[k].join(' ')); s.removeAttribute('height'); }
    vbCur[k] = BASE[k].slice();
  }
  let type = TYPES.includes(q.get('type')) ? q.get('type') : 'bellows';

  // 粒：実行時シミュレーション。8 つの場面はそれぞれ独立に動く（初めて表示するときに作る）
  const sims = {}, layers = {};
  for (const k of TYPES) layers[k] = figs[k].querySelector('g[id^="particles"]');
  const getSim = k => (sims[k] = sims[k] || (family(k) === 'piston' ? new PistonSim(window.SCENE_GEO[k], 7) : new BellowsSim(window.SCENE_GEO[k], 7)));
  let sim = null, layer = null;
  const drawSim = tt => { sim.seek(tt); sim.render(layer); };

  if (q.has('t')) {                     // コマ撮り用：指定時刻で止める
    document.body.classList.add('cap');
    sim = getSim(type); layer = layers[type];
    for (const k of TYPES) $('fig-' + k).hidden = k !== type;
    const tt = parseFloat(q.get('t'));
    figs[type].setCurrentTime(tt);
    drawSim(tt);
    return;
  }

  // ---------- 部品の名前：クリックで拡大して解説 ----------
  const WORD = {};
  for (const [id, tm] of Object.entries(TERMS)) for (const w of tm.words) WORD[w] = id;
  const rectOf = (id, tp) => TERMS[id].rect ? TERMS[id].rect[family(tp)] || null : null;
  for (const k of TYPES) figs[k].querySelectorAll('text').forEach(el => {
    if (el.closest('.svgcap') || el.closest('.svgnote')) return;
    const id = WORD[el.textContent.trim()];
    if (!id || (TERMS[id].rect && !rectOf(id, k))) return;
    el.classList.add('term'); el.dataset.term = id;
  });
  // 押せる名前の下に点線を引く。隠れている図では文字の幅が測れないので、初めて表示したときに引く
  const ulined = {};
  const underline = k => {
    if (ulined[k]) return; ulined[k] = true;
    figs[k].querySelectorAll('text.term').forEach(el => {
      const b = el.getBBox(), ln = document.createElementNS(NS, 'line');
      const y = (b.y + b.height + 0.5).toFixed(1);                 // 文字の枠のすぐ下（英語の g・p・y の下がりにかからない）
      ln.setAttribute('class', 'uline');
      ln.setAttribute('x1', (b.x + 1).toFixed(1)); ln.setAttribute('x2', (b.x + b.width - 1).toFixed(1));
      ln.setAttribute('y1', y); ln.setAttribute('y2', y);
      el.after(ln);
    });
  };
  const dims = {}, holeCur = {};
  for (const k of TYPES) {
    const d = document.createElementNS(NS, 'path');
    d.setAttribute('fill', '#000'); d.setAttribute('fill-opacity', '0'); d.setAttribute('fill-rule', 'evenodd');
    d.setAttribute('pointer-events', 'none');
    figs[k].appendChild(d); dims[k] = d; holeCur[k] = null;
  }
  const holePath = (r, outer) => {
    const [x0, y0, x1, y1] = r, R = Math.min(14, (x1 - x0) / 2, (y1 - y0) / 2);
    return `${outer} M${x0 + R},${y0} H${x1 - R} A${R},${R} 0 0 1 ${x1},${y0 + R} V${y1 - R} A${R},${R} 0 0 1 ${x1 - R},${y1} ` +
           `H${x0 + R} A${R},${R} 0 0 1 ${x0},${y1 - R} V${y0 + R} A${R},${R} 0 0 1 ${x0 + R},${y0} Z`;
  };
  const setVB = (k, vb) => { vbCur[k] = vb; figs[k].setAttribute('viewBox', vb.map(v => v.toFixed(2)).join(' ')); };
  const setHole = (k, r) => { holeCur[k] = r; dims[k].setAttribute('d', r ? holePath(r, 'M-6000,-6000 H8000 V8000 H-6000 Z') : 'M-6000,-6000 H8000 V8000 H-6000 Z'); };
  const ease = u => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
  const lerp = (a, b, e) => a.map((v, i) => v + (b[i] - v) * e);
  let tw = null;                                                  // 拡大・縮小の動き（frame の中で進める）
  const tween = (k, toVB, toHole, toOp, ms = 600) => {
    const fromVB = vbCur[k].slice(), op0 = parseFloat(dims[k].getAttribute('fill-opacity'));
    const fromHole = holeCur[k] && op0 > 0.01 ? holeCur[k].slice() : toHole;
    const t0 = performance.now();
    tw = { k, step: now => {
      const u = Math.min(1, (now - t0) / ms), e = ease(u);
      setVB(k, lerp(fromVB, toVB, e));
      setHole(k, toHole ? lerp(fromHole || toHole, toHole, e) : holeCur[k]);
      dims[k].setAttribute('fill-opacity', (op0 + (toOp - op0) * e).toFixed(3));
      if (u >= 1) tw = null;
    } };
  };
  const card = $('card'), cardTtl = $('cardTtl'), cardTxt = $('cardTxt'), cardNav = $('cardNav'), stage = $('stage');
  const targetVB = (k, r) => {
    const [, , W0, H0] = BASE[k], ar = H0 / W0, pad = 24;
    const rw = r[2] - r[0] + 2 * pad, rh = r[3] - r[1] + 2 * pad;
    const over = getComputedStyle(card).position === 'absolute';               // 狭い画面ではカードは図の下（重ならない）
    const c = over ? Math.min(0.55, (card.offsetHeight + 28) / stage.clientHeight) : 0;   // 下の解説カードに隠れる割合
    const vw = Math.min(W0 * 1.6, Math.max(rw, rh / (ar * (1 - c)), W0 / 2.6)), vh = vw * ar;
    return [(r[0] + r[2]) / 2 - vw / 2, (r[1] + r[3]) / 2 - vh * (1 - c) / 2, vw, vh];
  };
  let focus = null;                                               // {kind:'term', id} または {kind:'phase'}
  let exhaustedMsg = '';
  const textOf = id => id === 'exhausted' ? exhaustedMsg : typeof TERMS[id].text === 'string' ? TERMS[id].text : TERMS[id].text[family(type)];
  const termsHere = () => TERM_ORDER.filter(id => figs[type].querySelector(`text[data-term="${id}"]`));
  const openTerm = id => {
    focus = { kind: 'term', id };
    cardTtl.textContent = TERMS[id].name; cardTxt.textContent = textOf(id);
    cardNav.hidden = !termsHere().includes(id);
    card.classList.add('show');
    const r = rectOf(id, type);
    if (r) tween(type, targetVB(type, r), [r[0] - 12, r[1] - 12, r[2] + 12, r[3] + 12], 0.5);
    else tween(type, BASE[type], null, 0);
  };
  const openPhase = ph => {
    focus = { kind: 'phase' };
    cardTtl.innerHTML = `<span class="ph ${ph[3]}">${ph[0]}</span>${L.now}`;
    cardTxt.textContent = ph[4]; cardNav.hidden = true;
    card.classList.add('show');
    tween(type, BASE[type], null, 0);
  };
  const closeCard = () => {
    if (!focus) return;
    focus = null; card.classList.remove('show');
    tween(type, BASE[type], null, 0);
  };
  const closeCardNow = k => {                                      // 場面を切り替えるとき：動きなしで戻す
    focus = null; card.classList.remove('show'); tw = null;
    setVB(k, BASE[k].slice()); dims[k].setAttribute('fill-opacity', '0'); setHole(k, null);
  };
  const stepTerm = d => {
    const ids = termsHere(), i = ids.indexOf(focus && focus.id);
    if (i >= 0) openTerm(ids[(i + d + ids.length) % ids.length]);
  };
  $('cardX').onclick = closeCard;
  $('cardPrev').onclick = () => stepTerm(-1);
  $('cardNext').onclick = () => stepTerm(1);
  document.querySelectorAll('.lk[data-term]').forEach(b => b.onclick = () => openTerm(b.dataset.term));

  // ---------- 吸収剤 ----------
  const absBar = $('absBar'), absPct = $('absPct'), absEl = $('absEl'), absMeter = $('absMeter');
  let absOut = false;
  const updateAbs = tt => {
    const u = sim.absUsed();
    absBar.style.width = (u * 100).toFixed(1) + '%';
    absEl.textContent = L.breath(Math.floor(tt / CYC) + 1);
    const ni = sim.inspCO2(), used = u >= 0.999;
    absOut = used;
    const pt = used ? L.usedUp : Math.round(u * 100) + '%';
    if (absPct.textContent !== pt) { absPct.textContent = pt; absMeter.classList.toggle('out', used); }
    exhaustedMsg = ni > 0 ? L.exhausted[0] : L.exhausted[1];
  };
  absMeter.onclick = () => openTerm(absOut ? 'exhausted' : 'absorber');

  // ---------- 時刻のバー ----------
  const tlBar = $('tlBar'), tout = $('tout');
  let tlCur = null;
  const buildTimeline = tp => {
    tlBar.innerHTML = '';
    PHASES[tp].forEach(([lab, a, b, kind]) => {
      const s = document.createElement('span');
      s.className = kind; s.style.width = ((b - a) / CYC * 100) + '%'; s.textContent = lab;
      tlBar.appendChild(s);
    });
    tlCur = document.createElement('i'); tlBar.appendChild(tlCur);
  };
  const phaseAt = c => PHASES[type].find(([, a, e]) => c >= a && c < e) || PHASES[type][0];

  const show = tp => {
    if (focus) closeCardNow(type);
    type = tp;
    sim = getSim(tp); layer = layers[tp]; low = tp.includes('Low'); man = tp.endsWith('Man');
    for (const k of Object.keys(figs)) $('fig-' + k).hidden = k !== tp;
    document.querySelectorAll('#typeSeg button').forEach(b => b.classList.toggle('on', b.dataset.type === family(tp)));
    document.querySelectorAll('[data-flow]').forEach(b => b.classList.toggle('on', (b.dataset.flow === 'low') === low));
    document.querySelectorAll('[data-vent]').forEach(b => b.classList.toggle('on', (b.dataset.vent === 'man') === man));
    buildTimeline(tp);
    underline(tp);
    document.documentElement.style.setProperty('--ar', (BASE[tp][2] / BASE[tp][3]).toFixed(4));
  };

  let t = 0, speed = 1, playing = true, last = null;
  const playBtn = $('play');
  const ICON_PAUSE = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="3.6" height="12" fill="#fff"/><rect x="9.4" y="2" width="3.6" height="12" fill="#fff"/></svg>';
  const ICON_PLAY = '<svg viewBox="0 0 16 16"><path d="M4 2 L14 8 L4 14 Z" fill="#fff"/></svg>';
  const setPlaying = p => {
    playing = p;
    playBtn.innerHTML = p ? ICON_PAUSE : ICON_PLAY;
    playBtn.setAttribute('aria-label', p ? L.pause : L.play);
    if (p && focus && focus.kind === 'phase') closeCard();
  };
  const chip = $('chip'), chipMsg = $('chipMsg');
  const updateTrack = () => {
    const p = sim.tracked !== null ? sim.byId.get(sim.tracked) : null;
    if (chip.hidden === !!p) chip.hidden = !p;
    if (p) { const m = sim.describe(p); if (chipMsg.innerHTML !== m) chipMsg.innerHTML = m; }
  };
  const untrack = () => { sim.tracked = null; sim.trail = []; updateTrack(); };
  $('chipX').onclick = untrack;
  const frame = now => {
    if (last !== null && playing) t += (now - last) / 1000 * speed;
    last = now;
    if (tw) tw.step(now);
    figs[type].setCurrentTime(t);
    drawSim(t); updateTrack(); updateAbs(t);
    const c = ((t % CYC) + CYC) % CYC;
    tlCur.style.left = (c / CYC * 100).toFixed(2) + '%';
    tlBar.setAttribute('aria-valuenow', c.toFixed(1));
    tout.textContent = L.sec(c);
    if (tour.isOpen) tour.follow();
    requestAnimationFrame(frame);
  };

  // 図のクリック：部品の名前なら解説、拡大中に外側なら閉じる、ほかは粒の追跡
  const toSvg = (k, ev) => {
    const pt = figs[k].createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
    return pt.matrixTransform(figs[k].getScreenCTM().inverse());
  };
  for (const k of TYPES) figs[k].addEventListener('click', ev => {
    const tEl = ev.target.closest && ev.target.closest('text.term');
    if (tEl) { openTerm(tEl.dataset.term); return; }
    const loc = toSvg(k, ev);
    if (focus && focus.kind === 'term') {
      const r = holeCur[k];
      if (!r || loc.x < r[0] || loc.x > r[2] || loc.y < r[1] || loc.y > r[3]) { closeCard(); return; }
    }
    getSim(k).trackNear(loc.x, loc.y, 14);
    updateTrack();
  });

  // 時刻のバー：押す・ずらすとその時刻で止まり、離すとその場面の説明を出す
  let dragging = false;
  const setFromX = x => {
    const r = tlBar.getBoundingClientRect();
    t = Math.floor(t / CYC) * CYC + Math.max(0, Math.min(CYC - 0.01, (x - r.left) / r.width * CYC));
  };
  tlBar.addEventListener('pointerdown', e => { dragging = true; tlBar.setPointerCapture(e.pointerId); setPlaying(false); setFromX(e.clientX); });
  tlBar.addEventListener('pointermove', e => { if (dragging) setFromX(e.clientX); });
  tlBar.addEventListener('pointerup', () => { if (!dragging) return; dragging = false; openPhase(phaseAt(((t % CYC) + CYC) % CYC)); });

  // 方式の切り替え：新鮮ガスと換気の選択はそのまま、時刻は 0 から
  document.querySelectorAll('#typeSeg button').forEach(b => b.onclick = () => { show(key(b.dataset.type, low, man)); t = 0; });
  // 新鮮ガス・換気の切り替え：経過時間はそのまま（同じ時間での吸収剤の減り方を比べられる）
  document.querySelectorAll('[data-flow]').forEach(b => b.onclick = () => show(key(family(type), b.dataset.flow === 'low', man)));
  document.querySelectorAll('[data-vent]').forEach(b => b.onclick = () => show(key(family(type), low, b.dataset.vent === 'man')));
  playBtn.onclick = () => setPlaying(!playing);
  $('absSwap').onclick = () => { sim.seek(t); sim.swapAbsorbent(); sim.render(layer); updateAbs(t); };
  document.querySelectorAll('[data-speed]').forEach(b => b.onclick = () => {
    speed = parseFloat(b.dataset.speed);
    document.querySelectorAll('[data-speed]').forEach(x => x.classList.toggle('on', x === b));
  });

  // くわしい解説
  const more = $('more');
  const openMore = () => more.classList.add('show');
  const closeMore = () => more.classList.remove('show');
  $('moreBtn').onclick = openMore; $('moreX').onclick = closeMore;
  more.addEventListener('click', e => { if (e.target === more) closeMore(); });

  // ---------- 使い方：画面の上で指が動いて、操作を順に見せる ----------
  const tour = (() => {
    const box = $('tour'), dim = $('tourDim'), hand = $('hand'), bubble = $('bubble');
    const btxt = $('bubbleTxt'), dots = $('bubbleDots'), next = $('tourNext'), prev = $('tourPrev');
    let i = -1, timers = [], hole = null, holeTw = null, cleanup = null, target = null, wasPlaying = true;
    const later = (f, ms) => timers.push(setTimeout(f, ms));
    const rectOfEls = els => {
      const rs = els.map(e => e.getBoundingClientRect());
      return [Math.min(...rs.map(r => r.left)) - 6, Math.min(...rs.map(r => r.top)) - 6,
              Math.max(...rs.map(r => r.right)) + 6, Math.max(...rs.map(r => r.bottom)) + 6];
    };
    const drawHole = r => {
      const W = innerWidth, H = innerHeight;
      dim.setAttribute('d', r ? holePath(r, `M0,0 H${W} V${H} H0 Z`) : `M0,0 H${W} V${H} H0 Z`);
    };
    const moveHole = r => {
      const from = hole || r, t0 = performance.now();
      holeTw = now => { const u = Math.min(1, (now - t0) / 450), e = ease(u); hole = lerp(from, r, e); drawHole(hole); if (u >= 1) holeTw = null; };
    };
    // 吹き出しは穴の外へ：下 → 上 → 右 → 左の順に入る場所を探す。どこにも入らなければ画面の右下
    const placeBubble = r => {
      const bw = bubble.offsetWidth, bh = bubble.offsetHeight, W = innerWidth, H = innerHeight, g = 14;
      const cx = Math.max(12, Math.min(W - bw - 12, (r[0] + r[2]) / 2 - bw / 2));
      const cy = Math.max(12, Math.min(H - bh - 12, (r[1] + r[3]) / 2 - bh / 2));
      const pos = r[3] + g + bh < H ? [cx, r[3] + g] : r[1] - g - bh > 0 ? [cx, r[1] - g - bh]
        : r[2] + g + bw < W ? [r[2] + g, cy] : r[0] - g - bw > 0 ? [r[0] - g - bw, cy] : [W - bw - 12, H - bh - 12];
      bubble.style.left = pos[0] + 'px'; bubble.style.top = pos[1] + 'px';
    };
    const unionRect = rs => [Math.min(...rs.map(r => r[0])), Math.min(...rs.map(r => r[1])), Math.max(...rs.map(r => r[2])), Math.max(...rs.map(r => r[3]))];
    const focusRect = () => {                                     // 拡大した部品（図の中の明るい穴）の画面上の位置
      const h = holeCur[type]; if (!h) return rectOfEls([stage]);
      const [a, b] = svgToScreen(h[0], h[1]), [c, d] = svgToScreen(h[2], h[3]);
      return [a, b, c, d];
    };
    const handTo = (x, y) => { hand.style.opacity = '1'; hand.style.transform = `translate(${x - 16}px, ${y - 3}px)`; };
    const tap = (x, y) => {
      hand.classList.add('press'); setTimeout(() => hand.classList.remove('press'), 180);
      const rp = document.createElement('div'); rp.className = 'ripple'; rp.style.left = x + 'px'; rp.style.top = y + 'px';
      box.appendChild(rp); setTimeout(() => rp.remove(), 800);
    };
    const svgToScreen = (x, y) => {
      const pt = figs[type].createSVGPoint(); pt.x = x; pt.y = y;
      const s = pt.matrixTransform(figs[type].getScreenCTM()); return [s.x, s.y];
    };
    const STEPS = [
      { els: () => [...figs[type].querySelectorAll('text[data-term="particles"]')], padLeft: 22, hand: false,
        txt: L.steps[0] },
      { els: () => [playBtn], txt: L.steps[1] },
      { els: () => [$('typeSeg')], txt: L.steps[2] },
      { els: () => [$('ventGrp'), $('flowGrp')], at: r => [r[0] + 60, (r[1] + r[3]) / 2],
        txt: L.steps[3] },
      { els: () => [tlBar], at: r => [r[0] + (r[2] - r[0]) * 0.55, (r[1] + r[3]) / 2],
        txt: L.steps[4],
        act: () => { setPlaying(false); t = Math.floor(t / CYC) * CYC + 3.3; openPhase(phaseAt(3.3)); }, after: () => [tlBar, card],
        undo: () => { closeCard(); setPlaying(wasPlaying); } },
      { particle: true, txt: L.steps[5] },
      { els: () => [figs[type].querySelector('text[data-term="inspValve"]')],
        txt: L.steps[6],
        act: () => openTerm('inspValve'), afterFocus: true, undo: () => closeCard() },
      { els: () => [$('absbox'), $('speedGrp')], at: r => [r[2] - 40, (r[1] + r[3]) / 2],
        txt: L.steps[7] },
      { els: () => [$('moreBtn')], txt: L.steps[8] },
    ];
    dots.innerHTML = STEPS.map(() => '<i></i>').join('');
    const go = n => {
      timers.forEach(clearTimeout); timers = [];
      if (cleanup) { cleanup(); cleanup = null; }
      i = n; const st = STEPS[i];
      let els = null, pt = null, pid = null;
      if (st.particle) {
        setPlaying(false);
        const cand = sim.particles.filter(p => p.st === 'tube' && p.tube === 'A');
        const p = cand[Math.floor(cand.length / 2)] || sim.particles.find(p => p.st === 'tube');
        pid = p ? p.id : null;
        const [x, y] = p ? svgToScreen(...sim.xy(p)) : [innerWidth / 2, innerHeight / 2];
        stage.scrollIntoView({ block: 'nearest' });
        pt = [x, y]; target = () => { const pp = pid !== null && sim.byId.get(pid); const [a, b] = pp ? svgToScreen(...sim.xy(pp)) : pt; return [a - 22, b - 22, a + 22, b + 22]; };
      } else {
        els = st.els(); els[0].scrollIntoView({ block: 'nearest' });
        target = st.padLeft ? () => { const q = rectOfEls(els); q[0] -= st.padLeft; return q; } : () => rectOfEls(els);
      }
      const r = target();
      moveHole(r);
      btxt.innerHTML = st.txt;
      [...dots.children].forEach((d, j) => d.classList.toggle('on', j === i));
      prev.disabled = i === 0;
      next.textContent = i === STEPS.length - 1 ? L.start : L.next;
      placeBubble(r);
      if (st.hand === false) hand.style.opacity = '0';
      else {
        const [x, y] = st.particle ? [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2] : st.at ? st.at(r) : [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2 + 4];
        handTo(x, y);
        later(() => {
          tap(x, y);
          if (st.particle && pid !== null) {
            sim.tracked = pid; sim.trail = []; updateTrack();
            later(() => setPlaying(true), 400);
            cleanup = () => untrack();
          }
          if (st.act) { st.act(); cleanup = st.undo || null; }
          // 操作のあと：明るくする場所を広げる（バーの説明カード、拡大した部品とその解説カード）
          const widen = st.after ? () => rectOfEls(st.after()) : st.afterFocus ? () => unionRect([focusRect(), rectOfEls([card])]) : null;
          if (widen) later(() => { target = widen; const r2 = target(); moveHole(r2); placeBubble(r2); hand.style.opacity = '0'; }, 700);
        }, 850);
      }
    };
    const open = () => {
      closeMore(); closeCard(); wasPlaying = playing;
      box.classList.add('show'); hole = null;
      hand.style.transition = 'none'; hand.style.transform = `translate(${innerWidth - 80}px, ${innerHeight - 80}px)`; hand.style.opacity = '0';
      void hand.offsetWidth; hand.style.transition = '';
      tour.isOpen = true; go(0);
    };
    const close = () => {
      timers.forEach(clearTimeout); timers = [];
      if (cleanup) { cleanup(); cleanup = null; }
      box.classList.remove('show'); tour.isOpen = false; setPlaying(wasPlaying);
      try { localStorage.setItem('circleflow-tour-seen', '1'); } catch (e) {}
    };
    next.onclick = () => i < STEPS.length - 1 ? go(i + 1) : close();
    prev.onclick = () => i > 0 && go(i - 1);
    $('tourSkip').onclick = close;
    const follow = () => {                                        // 毎フレーム：穴を目標に合わせる（粒は動く、画面はずれる）
      if (holeTw) { holeTw(performance.now()); return; }
      if (target) { hole = target(); drawHole(hole); }
    };
    addEventListener('resize', () => { if (tour.isOpen && target) placeBubble(target()); });
    return { isOpen: false, open, close, follow };
  })();
  $('helpBtn').onclick = tour.open;

  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'Escape') {
      if (tour.isOpen) tour.close();
      else if (more.classList.contains('show')) closeMore();
      else if (focus) closeCard();
      else untrack();
      return;
    }
    if (tour.isOpen) return;
    if (e.key === ' ') { e.preventDefault(); setPlaying(!playing); }
    if (e.key === 'ArrowRight') { t += 0.1; setPlaying(false); }
    if (e.key === 'ArrowLeft') { t = Math.max(0, t - 0.1); setPlaying(false); }
    if (e.key === '?') tour.open();
  });
  show(type);
  setPlaying(true);
  requestAnimationFrame(frame);
  let seen = false;
  try { seen = localStorage.getItem('circleflow-tour-seen') === '1'; } catch (e) {}
  // ?term=（部品の名前）で開くと、その部品の解説を開いた状態になる（教科書から部品へ直接つなぐ用）
  if (TERMS[q.get('term')]) setTimeout(() => openTerm(q.get('term')), 100);
  else if (!seen && !q.has('notour')) setTimeout(tour.open, 700);
})();
"""

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
html = """<!doctype html>
<html lang="@@HTMLLANG@@"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + TITLE + """</title>
""" + ALT + """
<style>""" + CSS + """</style></head>""" + BODY_TOP + FIGS + BODY_MID + """
<script>""" + GEOS + SIM_PRE + """</script>
<script>
""" + sim_js + """
</script>
<script>
""" + sim_pjs + """
</script>
<script>
""" + TERMS + L_JS + MAIN_JS + """
</script>
</body></html>"""
open(OUT, "w", encoding="utf-8").write(html.replace("@@HTMLLANG@@", LANG, 1))
