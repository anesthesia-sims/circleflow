# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""操作ページの見た目（CSS）。日本語版・英語版で共通"""

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
  #typeSeg .short { display:none; }   /* 狭い画面では方式の名前を短く（ボリュームリフレクタ式 → リフレクタ式） */
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
  .bubble .ttl { display:block; margin-bottom:4px; }
  .bubble .ttl .sub { font-weight:400; font-size:13px; color:#555; margin-left:8px; white-space:nowrap; }
  .bubble .dots { display:flex; gap:5px; margin:8px 0 0; }
  .bubble .dots i { width:7px; height:7px; border-radius:50%; background:#cfd6e3; }
  .bubble .dots i.on { background:var(--blue); }
  .bubble .bb { display:flex; justify-content:flex-end; gap:6px; margin-top:6px; }
  .bubble .bb button { font-size:13px; padding:4px 12px; border-radius:6px; border:1.5px solid var(--blue); background:#fff; color:var(--blue); cursor:pointer; }
  .bubble .bb button.pri { background:var(--blue); color:#fff; }
  .bubble .keys { font-size:11px; color:#888; margin-top:6px; text-align:right; }   /* ツアーのキー操作の案内（2026-11-05）。狭い画面では出さない */
  .bubble kbd { font:inherit; font-size:12px; border:1px solid #aaa; border-radius:4px; padding:0 4px; }
  body.cap .wrap { padding:0; max-width:none; }
  body.cap .chrome { display:none !important; }
  body.cap .stage { border:none; border-radius:0; }
  /* 狭い画面（スマートフォンの縦）：段を決めて組む。見出しは 1 行、方式は幅いっぱい、換気と新鮮ガスは左右に並べて
     名前を上に小さく、図の下は「再生＋バー」「速さ」「吸収剤」の 3 段。成り行きで折り返すと、並びが崩れて見えた（2026-11-02） */
  .cyc { display:none; }          /* 狭い画面だけ：方式・換気・新鮮ガスを、押すたびに切り替わる 3 つのボタン 1 段に */
  #speedCycle { display:none; }   /* 狭い画面だけ：速さを 1 つのボタンで順送り（¼ → ½ → 1× → 4× → 16×） */
  @media (max-width:640px) {
    .wrap { max-width:none; padding:10px 12px 16px; }   /* 画面の高さから決めた幅（最小 620 px）をやめ、画面の幅いっぱいに */
    .top { gap:6px; }
    .top h1 { font-size:19px; }
    .top h1 span { display:none; }
    .top a.lang { font-size:13px; margin-right:0; }
    .top button { font-size:13px; padding:5px 8px; }
    .top button .q { display:none; }
    .bar { display:grid; grid-template-columns:1fr 1fr; gap:6px 8px; }
    #typeSeg, #ventGrp, #flowGrp { display:none; }
    .cyc { grid-column:1 / -1; display:grid; grid-template-columns:1.35fr 1fr 1fr; gap:6px; }
    .cyc button { display:flex; flex-direction:column; align-items:center; gap:1px; padding:4px 4px 5px; border:1.5px solid var(--fg); border-radius:8px; background:#fff; color:var(--fg); min-width:0; }
    .cyc small { font-size:10px; line-height:1.1; color:#555; white-space:nowrap; }
    .cyc small::after { content:' ⇄'; }
    .cyc b { font-size:14px; line-height:1.25; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%; }
    .bar .seg { display:flex; }
    .bar .seg button { flex:1; padding:6px 4px; font-size:13px; white-space:nowrap; }   /* 英語の Manual (bag) が 2 行に折れて段の高さがそろわないのを防ぐ */
    .bar .seg.big button { font-size:14px; padding:7px 4px; }
    #typeSeg .full { display:none; } #typeSeg .short { display:inline; }
    .bar .grp { display:flex; flex-direction:column; align-items:stretch; gap:2px; }
    .bar .grp .lab { font-size:11px; }
    .under { display:grid; grid-template-columns:auto 1fr auto; gap:8px 10px; align-items:center; }
    #speedGrp { display:none; }
    #speedCycle { display:block; min-width:52px; padding:7px 8px; font-size:14px; font-weight:700; border:1.5px solid var(--fg); border-radius:8px; background:#fff; color:var(--fg); }
    .tl { min-width:0; }
    .abs { grid-column:1 / -1; display:flex; }
    #speedGrp .seg { display:flex; flex:1; }
    #speedGrp .seg button { flex:1; padding:5px 0; }
    .abs .meter { flex:1; width:auto; }
    .abs .el { min-width:0; font-size:13px; }
    .card p { font-size:14px; }
    .bubble .keys { display:none; }
    /* 狭い画面では解説カードを図の上に重ねず、図の下に出す（図が小さいので重ねると部品が隠れる） */
    .card { position:relative; left:auto; bottom:auto; max-width:none; margin:0; border:none; border-top:1.5px solid var(--fg); border-radius:0; transform:none; }
    .card:not(.show) { display:none; } }
  /* 背の低い画面（スマートフォンの横）：高さから幅を決めると狭くなりすぎるので、幅いっぱいにして縦に送る */
  @media (max-height:500px) and (min-width:641px) { .wrap { max-width:none; } }
"""
