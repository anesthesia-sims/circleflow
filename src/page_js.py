# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""操作ページの JavaScript：場面の切り替え、粒の描画（sim_*.js を呼ぶ）、部品の解説（拡大）、時刻のバー、
使い方のツアー。文は L（page_terms.py・page_en.py）から取る"""

MAIN_JS = r"""
(() => {
  const CYC = 6.0, NS = 'http://www.w3.org/2000/svg';
  const PHASES = L.phases;

  const TYPES = ['bellows', 'bellowsLow', 'bellowsMan', 'bellowsLowMan', 'piston', 'pistonLow', 'pistonMan', 'pistonLowMan', 'reflector', 'reflectorLow', 'reflectorShort', 'reflectorMan', 'reflectorLowMan', 'blower', 'blowerLow', 'blowerMan', 'blowerLowMan'];
  const $ = id => document.getElementById(id);
  const figs = {};
  for (const k of TYPES) figs[k] = document.querySelector('#fig-' + k + ' svg');
  PHASES.bellowsLow = PHASES.bellows; PHASES.pistonLow = PHASES.piston;
  PHASES.bellowsLowMan = PHASES.bellowsMan; PHASES.pistonLowMan = PHASES.pistonMan;
  PHASES.reflectorLow = PHASES.reflector; PHASES.reflectorLowMan = PHASES.reflectorMan;
  PHASES.blowerLow = PHASES.blower; PHASES.blowerLowMan = PHASES.blowerMan;
  const family = tp => tp.startsWith('piston') ? 'piston' : tp.startsWith('reflector') ? 'reflector' : tp.startsWith('blower') ? 'blower' : 'bellows';
  const key = (fam, fl, mn) => fam + (fl === 'low' ? 'Low' : fl === 'short' ? 'Short' : '') + (mn ? 'Man' : '');
  const avail = (fam, fl, mn) => fl === 'short' && !(fam === 'reflector' && !mn) ? 'low' : fl;   // 「不足」はリフレクタ式の人工呼吸だけ。ほかへ移るときは低流量に
  let flow = 'high', man = false;                                // 新鮮ガス：high（多め）・low（低流量）・short（不足）、換気：用手換気
  Object.values(figs).forEach(s => s.pauseAnimations());
  // 拡大縮小で動かす部品（呼吸バッグ・ばね・ベローズ）は線の太さを画面の画素で固定している（vector-effect）。そのままだと図を縮めても
  // 線が細くならず、狭い画面で太く黒い塊に見えるので、図の縮尺を掛ける（2026-11-04）
  const fitStroke = s => { const m = s.getScreenCTM(); if (m && m.a > 0) s.style.setProperty('--vs', m.a.toFixed(4)); };
  const strokeRO = new ResizeObserver(es => es.forEach(e => fitStroke(e.target)));
  for (const s of Object.values(figs)) {
    s.querySelectorAll('[vector-effect="non-scaling-stroke"]').forEach(el => { el.style.strokeWidth = `calc(${el.getAttribute('stroke-width')}px * var(--vs, 1))`; });
    strokeRO.observe(s);
  }
  const q = new URLSearchParams(location.search);
  const BASE = {}, vbCur = {};                                   // 図ごとのもとの表示範囲と、いまの表示範囲（拡大用）
  for (const k of TYPES) {
    const s = figs[k], vb = s.viewBox.baseVal;
    BASE[k] = [0, 0, vb.width, q.has('t') ? vb.height : vb.height - 68];   // 操作ページでは下の字幕の帯を切る
    if (!q.has('t')) { s.setAttribute('viewBox', BASE[k].join(' ')); s.removeAttribute('height'); }
    vbCur[k] = BASE[k].slice();
  }
  let type = TYPES.includes(q.get('type')) ? q.get('type') : 'bellows';
  // ---------- 図の表示範囲（2026-11-05 著者と相談：スマートフォン対応）----------
  // 狭い画面で幅 1340 の図を幅いっぱいに縮めると文字が約 5 px になって読めない。そこで図の左右（ガス供給機構・気化器／呼吸回路。
  // 図の点線の枠は x 12〜680 と 692〜1328）を幅 692・高さは全体の範囲として用意し、縦向きの狭い画面では「呼吸回路」から始める。
  // 2 本指で拡大縮小・指でずらしたあとは custom。部品の解説を閉じたとき・場面を切り替えたときは、この「ふだんの範囲」に戻る。
  // 3 方式の図は同じ座標（幅 1340）なので範囲は共通
  const RANGES = { all: k => BASE[k].slice(), supply: k => [0, 0, 692, BASE[k][3]], circuit: k => [BASE[k][2] - 692, 0, 692, BASE[k][3]] };
  const narrowMq = matchMedia('(max-width:640px)');
  let range = 'all', userVB = null;
  const homeVB = k => range === 'custom' && userVB ? userVB.slice() : (RANGES[range] || RANGES.all)(k);
  const sameVB = (a, b) => a.every((v, i) => Math.abs(v - b[i]) < 0.5);

  // 粒：実行時シミュレーション。8 つの場面はそれぞれ独立に動く（初めて表示するときに作る）
  const sims = {}, layers = {};
  for (const k of TYPES) layers[k] = figs[k].querySelector('g[id^="particles"]');
  const getSim = k => (sims[k] = sims[k] || (family(k) === 'piston' ? new PistonSim(window.SCENE_GEO[k], 7) : family(k) === 'reflector' ? new ReflectorSim(window.SCENE_GEO[k], 7) : family(k) === 'blower' ? new BlowerSim(window.SCENE_GEO[k], 7) : new BellowsSim(window.SCENE_GEO[k], 7)));
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
  const rectOf = (id, tp) => TERMS[id].rect ? TERMS[id].rect[family(tp)] || (family(tp) === 'reflector' ? TERMS[id].rect.bellows : family(tp) === 'blower' ? TERMS[id].rect.piston : null) || null : null;   // リフレクタ式の図はベローズ式、ブロワ式の図はピストン式と同じ配置なので、範囲がなければそちらを使う
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
  const setVB = (k, vb) => { vbCur[k] = vb; figs[k].setAttribute('viewBox', vb.map(v => v.toFixed(2)).join(' ')); fitStroke(figs[k]);
    stage.classList.toggle('zoomed', vb[3] < BASE[k][3] - 0.5); };   // 縦に動かす余地があるか（全体の高さより狭く見ている）。ふだんの範囲と比べると、2 本指で広げたあとに外れて縦の指がページのスクロールになった（2026-11-05 iPhone で確認）
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
    const [, , W0] = BASE[k], h = homeVB(k), ar = h[3] / h[2], pad = 24;   // 縦横比はふだんの範囲に合わせる（図の高さが変わらないように）
    const rw = r[2] - r[0] + 2 * pad, rh = r[3] - r[1] + 2 * pad;
    const over = getComputedStyle(card).position === 'absolute';               // 狭い画面ではカードは図の下（重ならない）
    const c = over ? Math.min(0.55, (card.offsetHeight + 28) / stage.clientHeight) : 0;   // 下の解説カードに隠れる割合
    const vw = Math.min(W0 * 1.6, Math.max(rw, rh / (ar * (1 - c)), W0 / 2.6)), vh = vw * ar;
    return [(r[0] + r[2]) / 2 - vw / 2, (r[1] + r[3]) / 2 - vh * (1 - c) / 2, vw, vh];
  };
  let focus = null;                                               // {kind:'term', id} または {kind:'phase'}
  let exhaustedMsg = '';
  const textOf = id => { if (id === 'exhausted') return exhaustedMsg; const t = TERMS[id].text; return typeof t === 'string' ? t : (t[family(type)] ?? t.piston ?? t.bellows); };   // 方式の文がなければピストン式・ベローズ式の文（ブロワ式は多くの部品をピストン式と共有）
  const termsHere = () => TERM_ORDER.filter(id => figs[type].querySelector(`text[data-term="${id}"]`));
  const openTerm = id => {
    focus = { kind: 'term', id };
    cardTtl.textContent = TERMS[id].name; cardTxt.textContent = textOf(id);
    cardNav.hidden = !termsHere().includes(id);
    card.classList.add('show');
    const r = rectOf(id, type);
    if (r) tween(type, targetVB(type, r), [r[0] - 12, r[1] - 12, r[2] + 12, r[3] + 12], 0.5);
    else tween(type, homeVB(type), null, 0);
  };
  const openPhase = ph => {
    focus = { kind: 'phase' };
    cardTtl.innerHTML = `<span class="ph ${ph[3]}">${ph[0]}</span>${L.now}`;
    cardTxt.textContent = ph[4]; cardNav.hidden = true;
    card.classList.add('show');
    tween(type, homeVB(type), null, 0);
  };
  const closeCard = () => {
    if (!focus) return;
    focus = null; card.classList.remove('show');
    tween(type, homeVB(type), null, 0);
  };
  const closeCardNow = k => {                                      // 場面を切り替えるとき：動きなしで戻す
    focus = null; card.classList.remove('show'); tw = null;
    setVB(k, homeVB(k)); dims[k].setAttribute('fill-opacity', '0'); setHole(k, null);
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
    sim = getSim(tp); layer = layers[tp]; flow = tp.includes('Short') ? 'short' : tp.includes('Low') ? 'low' : 'high'; man = tp.endsWith('Man');
    for (const k of Object.keys(figs)) $('fig-' + k).hidden = k !== tp;
    tw = null; setVB(tp, homeVB(tp));
    document.querySelectorAll('#typeSeg button').forEach(b => b.classList.toggle('on', b.dataset.type === family(tp)));
    document.querySelectorAll('[data-flow]').forEach(b => b.classList.toggle('on', b.dataset.flow === flow));
    document.querySelector('[data-flow="short"]').hidden = !(family(tp) === 'reflector' && !man);
    document.querySelectorAll('[data-vent]').forEach(b => b.classList.toggle('on', (b.dataset.vent === 'man') === man));
    {   // 狭い画面の切り替えボタンに、いまの選択を出す
      const tb = document.querySelector('#typeSeg button.on'); $('typeCycle').querySelector('b').textContent = (tb.querySelector('.short') || tb).textContent;
      $('ventCycle').querySelector('b').textContent = document.querySelector('[data-vent].on').textContent.replace(/\s*\(.*\)$/, '');   // 英語の Manual (bag) は括弧を省く
      $('flowCycle').querySelector('b').textContent = document.querySelector('[data-flow].on').textContent;
    }
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
    if (gestured) { gestured = false; return; }               // 指でずらした・広げた直後の click（タップではない）
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

  // ---------- 表示範囲の切り替え（狭い画面のボタン）----------
  const setRange = (r, animate) => {
    range = r; if (r !== 'custom') userVB = null;
    document.querySelectorAll('[data-range]').forEach(b => b.classList.toggle('on', b.dataset.range === r));
    if (focus) { closeCard(); return; }                           // 解説を閉じると、新しい範囲へ戻る
    if (animate) tween(type, homeVB(type), null, 0); else { tw = null; setVB(type, homeVB(type)); }
  };
  document.querySelectorAll('[data-range]').forEach(b => b.onclick = () => setRange(b.dataset.range, true));
  // 狭い画面（縦向き）になったら「呼吸回路」から、広い画面に戻ったら全体
  const applyNarrow = () => { if (narrowMq.matches) { if (range === 'all') setRange('circuit', false); } else if (range !== 'all') setRange('all', false); };
  narrowMq.addEventListener('change', applyNarrow);

  // ---------- 指の操作（2026-11-05）：2 本指で拡大縮小、1 本指でずらす ----------
  // 図の上の pointerdown から指を追い、動かした量が 8 px 未満ならタップ（粒の追跡・部品の名前の click）として扱う。
  // 範囲は図の中に収め、幅は全体の 1/5 まで。縦横比は変えない。解説を開いているあいだの操作は一時的で、閉じるとふだんの範囲へ戻る。
  // pointer capture は使わない（Chrome では捕まえた要素に click が行き、部品の名前の click が取れなくなる）
  let gestured = false;
  const ptrs = new Map();
  let g0 = null, moved = false;
  const gestureStart = () => ({ vb: vbCur[type].slice(), r: figs[type].getBoundingClientRect(), p: [...ptrs.values()].map(p => ({ x: p.x, y: p.y })) });
  const clampVB = (k, vb) => {
    const [, , W0, H0] = BASE[k], ar = vb[3] / vb[2];
    const vw = Math.max(W0 / 5, Math.min(W0, H0 / ar, vb[2])), vh = vw * ar;
    return [Math.max(0, Math.min(W0 - vw, vb[0])), Math.max(0, Math.min(H0 - vh, vb[1])), vw, vh];
  };
  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const applyGesture = vb => {
    moved = true; tw = null; setVB(type, vb);
    if (!focus) {                                                 // ふだんの範囲を指で決めた（custom）。ふだんの範囲と同じなら変えない
      if (!sameVB(vb, homeVB(type))) { range = 'custom'; userVB = vb.slice(); document.querySelectorAll('[data-range]').forEach(b => b.classList.remove('on')); }
    }
  };
  stage.addEventListener('pointerdown', e => {
    if (!e.target.closest('.fig')) return;                        // 解説カード・追跡の札の上は図の操作にしない
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    gestured = false;
    ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (ptrs.size === 1) moved = false;
    g0 = gestureStart();
  });
  addEventListener('pointermove', e => {
    if (!ptrs.has(e.pointerId) || !g0) return;
    ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const ps = [...ptrs.values()], p0 = g0.p, r = g0.r, vb0 = g0.vb, k = vb0[2] / r.width;   // k：画面 1 px あたりの図の座標
    if (ps.length >= 2 && p0.length >= 2) {
      const d0 = dist(p0[0], p0[1]), d1 = dist(ps[0], ps[1]); if (d0 < 1 || d1 < 1) return;
      const s = d0 / d1;                                          // 指を広げると範囲は狭く（拡大）
      const m0 = { x: (p0[0].x + p0[1].x) / 2, y: (p0[0].y + p0[1].y) / 2 }, m1 = { x: (ps[0].x + ps[1].x) / 2, y: (ps[0].y + ps[1].y) / 2 };
      const fx = vb0[0] + (m0.x - r.left) * k, fy = vb0[1] + (m0.y - r.top) * k;   // 始めに 2 本指の中点にあった図の点を、いまの中点に置く
      applyGesture(clampVB(type, [fx - (m1.x - r.left) * k * s, fy - (m1.y - r.top) * k * s, vb0[2] * s, vb0[3] * s]));
    } else if (ps.length === 1) {
      const dx = ps[0].x - p0[0].x, dy = ps[0].y - p0[0].y;
      if (!moved && Math.hypot(dx, dy) < 8) return;
      applyGesture(clampVB(type, [vb0[0] - dx * k, vb0[1] - dy * k, vb0[2], vb0[3]]));
    }
  });
  const endPtr = e => {
    if (!ptrs.has(e.pointerId)) return;
    ptrs.delete(e.pointerId);
    if (ptrs.size) g0 = gestureStart();                            // 残った指で続ける（基準を取り直す）
    else { g0 = null; gestured = moved; moved = false; }
  };
  addEventListener('pointerup', endPtr); addEventListener('pointercancel', endPtr);
  // iOS の Safari は touch-action だけではページの拡大（2 本指）を止めないので、図の上の 2 本指と、狭く見ているときの指の動きは既定の動作を止める
  stage.addEventListener('touchmove', e => { if (e.target.closest && e.target.closest('.fig') && (e.touches.length >= 2 || stage.classList.contains('zoomed'))) e.preventDefault(); }, { passive: false });

  // ---------- 全画面（2026-11-05）：ブラウザの枠を消す。スマートフォンの横向きと、勉強会のスクリーン投影用 ----------
  const fsBtns = [...document.querySelectorAll('.fsBtn')];
  const fsEl = () => document.fullscreenElement || document.webkitFullscreenElement;
  // 出す条件は「全画面にする関数があること」（document.fullscreenEnabled で判定すると iPhone の Safari で偽になりボタンが出なかった。2026-11-05 著者の報告）。
  // 押して 1 秒たっても全画面にならないブラウザ（iPhone の Chrome など）では、ボタンを隠して以後は出さない
  const docEl = document.documentElement, canFs = !!(docEl.requestFullscreen || docEl.webkitRequestFullscreen);
  let noFs = false; try { noFs = localStorage.getItem('circleflow-nofs') === '1'; } catch (e) {}
  if (!canFs || noFs) fsBtns.forEach(b => b.hidden = true);
  const giveUpFs = () => { fsBtns.forEach(b => b.hidden = true); try { localStorage.setItem('circleflow-nofs', '1'); } catch (e) {} };
  const toggleFs = () => {
    const d = document;
    if (fsEl()) { const p = (d.exitFullscreen || d.webkitExitFullscreen).call(d); if (p && p.catch) p.catch(() => {}); return; }
    let p = null; try { p = (docEl.requestFullscreen || docEl.webkitRequestFullscreen).call(docEl); } catch (e) {}
    if (p && p.catch) p.catch(() => {});
    setTimeout(() => { if (!fsEl()) giveUpFs(); }, 1000);
  };
  fsBtns.forEach(b => b.onclick = toggleFs);
  const fsChanged = () => fsBtns.forEach(b => { b.classList.toggle('on', !!fsEl()); b.setAttribute('aria-pressed', fsEl() ? 'true' : 'false'); });
  document.addEventListener('fullscreenchange', fsChanged); document.addEventListener('webkitfullscreenchange', fsChanged);

  // ---------- 横向きの案内（2026-11-05）：指で触れる狭い画面の縦向きで出す。閉じるか、横向きにしたら、以後は出さない ----------
  {
    const hint = $('rotHint'), land = matchMedia('(orientation: landscape)');
    let off = false; try { off = localStorage.getItem('circleflow-rotate-hint-off') === '1'; } catch (e) {}
    const dismiss = () => { hint.hidden = true; try { localStorage.setItem('circleflow-rotate-hint-off', '1'); } catch (e) {} };
    if (!off && navigator.maxTouchPoints > 0 && narrowMq.matches && !land.matches) hint.hidden = false;
    $('rotHintX').onclick = dismiss;
    land.addEventListener('change', () => { if (land.matches && !hint.hidden) dismiss(); });
  }

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
  document.querySelectorAll('#typeSeg button').forEach(b => b.onclick = () => { show(key(b.dataset.type, avail(b.dataset.type, flow, man), man)); t = 0; });
  // 新鮮ガス・換気の切り替え：経過時間はそのまま（同じ時間での吸収剤の減り方を比べられる）
  document.querySelectorAll('[data-flow]').forEach(b => b.onclick = () => show(key(family(type), b.dataset.flow, man)));
  document.querySelectorAll('[data-vent]').forEach(b => b.onclick = () => { const mn = b.dataset.vent === 'man'; show(key(family(type), avail(family(type), flow, mn), mn)); });
  playBtn.onclick = () => setPlaying(!playing);
  $('absSwap').onclick = () => { sim.seek(t); sim.swapAbsorbent(); sim.render(layer); updateAbs(t); };
  $('typeCycle').onclick = () => { const bs = [...document.querySelectorAll('#typeSeg button')], i = bs.findIndex(x => x.classList.contains('on')); bs[(i + 1) % bs.length].click(); };
  $('ventCycle').onclick = () => document.querySelector('[data-vent]:not(.on)').click();
  $('flowCycle').onclick = () => { const bs = [...document.querySelectorAll('[data-flow]')].filter(b => !b.hidden), i = bs.findIndex(x => x.classList.contains('on')); bs[(i + 1) % bs.length].click(); };
  $('speedCycle').onclick = () => {                           // 狭い画面：速さを順送り
    const bs = [...document.querySelectorAll('[data-speed]')], i = bs.findIndex(x => x.classList.contains('on'));
    bs[(i + 1) % bs.length].click();
  };
  document.querySelectorAll('[data-speed]').forEach(b => b.onclick = () => {
    speed = parseFloat(b.dataset.speed);
    document.querySelectorAll('[data-speed]').forEach(x => x.classList.toggle('on', x === b));
    $('speedCycle').textContent = b.textContent;
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
    let i = -1, timers = [], hole = null, holeTw = null, cleanup = null, target = null, wasPlaying = true, savedRange = null;
    // 狭い画面の見どころ用：図の範囲 r が入る表示範囲。縦横比は r に合わせる（全体の横長 〜 呼吸回路の範囲の縦長の間。
    // 図の高さがそれに合わせて変わる）。幅は全体の 1/3 より狭くしない（文字が大きくなりすぎず、まわりも見える）。2026-11-05 著者の指摘で直した
    const fitVB = r => {
      const [, , W0, H0] = BASE[type], pad = 30, rw = r[2] - r[0] + 2 * pad, rh = r[3] - r[1] + 2 * pad;
      const ar = Math.max(H0 / W0, Math.min(H0 / 692, rh / rw));
      const vw = Math.max(W0 / 3, rw, rh / ar), vh = vw * ar;
      return clampVB(type, [(r[0] + r[2]) / 2 - vw / 2, (r[1] + r[3]) / 2 - vh / 2, vw, vh]);
    };
    const rectAfter = (vb, q) => {                                // 表示範囲が vb になったとき、図の範囲 q が画面のどこに来るか（寄る動きの終わりの位置）
      const r = figs[type].getBoundingClientRect(), s = r.width / vb[2];
      return [r.left + (q[0] - vb[0]) * s - 6, r.top + (q[1] - vb[1]) * s - 6, r.left + (q[2] - vb[0]) * s + 6, r.top + (q[3] - vb[1]) * s + 6];
    };
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
    const STEPS_HELP = [
      { els: () => [...figs[type].querySelectorAll('text[data-term="particles"]')], padLeft: 22, hand: false,
        txt: L.steps[0] },
      { els: () => [playBtn], txt: L.steps[1] },
      { els: () => [$('typeSeg').offsetParent ? $('typeSeg') : $('typeCycle')], txt: L.steps[2] },
      { els: () => $('ventGrp').offsetParent ? [$('ventGrp'), $('flowGrp')] : [$('ventCycle'), $('flowCycle')], at: r => [r[0] + 60, (r[1] + r[3]) / 2],
        txt: L.steps[3] },
      { els: () => [tlBar], at: r => [r[0] + (r[2] - r[0]) * 0.55, (r[1] + r[3]) / 2],
        txt: L.steps[4],
        act: () => { setPlaying(false); t = Math.floor(t / CYC) * CYC + 3.3; openPhase(phaseAt(3.3)); }, after: () => [tlBar, card],
        undo: () => { closeCard(); setPlaying(wasPlaying); } },
      { particle: true, txt: L.steps[5] },
      { els: () => [figs[type].querySelector('text[data-term="inspValve"]')],
        txt: L.steps[6],
        act: () => openTerm('inspValve'), afterFocus: true, undo: () => closeCard() },
      { els: () => [$('absbox'), $('speedGrp').offsetParent ? $('speedGrp') : $('speedCycle')], at: r => [r[2] - 40, (r[1] + r[3]) / 2],
        txt: L.steps[7] },
      { els: () => [$('hlBtn')], txt: L.steps[8] },                     // 見どころの紹介（2026-11-05 著者の依頼）
      { els: () => [$('moreBtn')], txt: L.steps[9] },
    ];
    // 見どころのツアー（2026-11-05 著者と相談）：場面・速さ・時刻を自動で切り替え、図の範囲（図の座標）を明るく残して説明する。文は L.hl
    // 見どころのツアー（2026-11-05 著者と相談）：細部を方式ごとに切り替えて見比べる 25 段。場面・速さ・時刻・図の範囲（図の座標）。文は L.hl
    const HL = [
      { scene: 'bellows', speed: 1, t: 0, svgRect: [800, 140, 970, 222] },
      { scene: 'piston', speed: 1, t: 0, svgRect: [925, 12, 1040, 108] },
      { scene: 'blower', speed: 1, t: 0, svgRect: [925, 12, 1040, 108] },
      { scene: 'reflector', speed: 1, t: 0, svgRect: [800, 140, 970, 222] },
      { scene: 'bellows', speed: 0.5, t: 0, svgRect: [1185, 225, 1337, 515] },
      { scene: 'bellows', speed: 1, t: 2.3, svgRect: [735, 95, 990, 445] },
      { scene: 'piston', speed: 1, t: 2.3, svgRect: [690, 30, 950, 660] },
      { scene: 'blower', speed: 1, t: 2.3, svgRect: [690, 30, 1335, 520] },
      { scene: 'reflector', speed: 1, t: 2.3, svgRect: [10, 56, 990, 445] },
      { scene: 'bellows', speed: 1, t: 0, svgRect: [735, 40, 1000, 250] },
      { scene: 'piston', speed: 1, t: 0, svgRect: [690, 30, 950, 660] },
      { scene: 'blower', speed: 1, t: 0.5, svgRect: [690, 30, 1010, 300] },
      { scene: 'reflector', speed: 1, t: 0, svgRect: [755, 470, 1335, 700] },
      { scene: 'bellows', speed: 16, t: 0, svgRect: [735, 265, 1150, 650] },
      { scene: 'bellowsLow', speed: 16, t: 0, svgRect: [735, 265, 955, 445] },
      { scene: 'blower', speed: 16, t: 0, svgRect: [690, 265, 1150, 650] },
      { scene: 'bellowsMan', speed: 1, t: 2.0, svgRect: [680, 510, 850, 672] },
      { scene: 'pistonMan', speed: 1, t: 2.0, svgRect: [690, 500, 1020, 685] },
      { scene: 'blowerMan', speed: 1, t: 2.0, svgRect: [690, 500, 1020, 685] },
      { scene: 'reflectorMan', speed: 1, t: 2.0, svgRect: [1100, 590, 1335, 705] },
      { scene: 'bellows', speed: 1, t: 0, svgRect: [10, 85, 640, 300] },
      { scene: 'reflector', speed: 1, t: 0, svgRect: [10, 40, 640, 300] },
      { scene: 'blower', speed: 1, t: 0, svgRect: [10, 40, 640, 300] },
      { scene: 'blower', speed: 0.5, t: 0, svgRect: [795, 40, 1130, 240] },
      { scene: 'reflectorShort', speed: 1, t: 30, svgRect: [690, 15, 1335, 740] },
    ].map((h, k) => Object.assign(h, { hand: false, txt: '<b class="ttl">' + L.hl[k][0] + (L.hl[k][1] ? '<span class="sub">' + L.hl[k][1] + '</span>' : '') + '</b>' + L.hl[k][2] }));
    let STEPS = STEPS_HELP;
    const go = n => {
      timers.forEach(clearTimeout); timers = [];
      if (cleanup) { cleanup(); cleanup = null; }
      i = n; const st = STEPS[i];
      let els = null, pt = null, pid = null;
      let zoomTo = null;                                         // 狭い画面：寄る動きの終わりの、示す範囲の画面上の位置
      if (st.scene) {                                            // 見どころ：場面・速さ・時刻を切り替えて再生
        if (type !== st.scene) { const prev = vbCur[type].slice(); show(st.scene); if (narrowMq.matches) setVB(type, prev); }   // 狭い画面：前の範囲を引き継いで、そこから寄る
        const sb = document.querySelector(`[data-speed="${st.speed}"]`); if (sb) sb.click();
        t = st.t; setPlaying(true);
      }
      if (st.svgRect) {
        stage.scrollIntoView({ block: 'nearest' });
        if (narrowMq.matches) {                                // 狭い画面：示す範囲へ寄せる。吹き出しは終わりの位置に置き、動きが終わってから置き直す（終わる前に置き直すと穴に重なる）
          const vb = fitVB(st.svgRect); zoomTo = rectAfter(vb, st.svgRect); tween(type, vb, null, 0);
          const settle = () => { if (tw) later(settle, 150); else placeBubble(target()); }; later(settle, 650);
        }
        target = () => { const q = st.svgRect, [a, b] = svgToScreen(q[0], q[1]), [c, d] = svgToScreen(q[2], q[3]); return [a - 6, b - 6, c + 6, d + 6]; };
      } else if (st.particle) {
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
      if (zoomTo) { holeTw = null; hole = null; }                 // 寄る動きのあいだは穴を毎コマ目標に合わせる（follow）。寄る前の位置へ動かしてから跳ばない
      else moveHole(r);
      btxt.innerHTML = st.txt;
      [...dots.children].forEach((d, j) => d.classList.toggle('on', j === i));
      prev.disabled = i === 0;
      next.textContent = i === STEPS.length - 1 ? (STEPS === STEPS_HELP ? L.start : L.hlEnd) : L.next;
      placeBubble(zoomTo || r);
      if (st.svgRect && !zoomTo) later(() => placeBubble(target()), 120);   // 場面の切り替えやスクロールで画面がずれたあとに置き直す
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
    const open = kind => {
      closeMore(); closeCard(); wasPlaying = playing;
      STEPS = kind === 'hl' ? HL : STEPS_HELP;
      if (narrowMq.matches) { savedRange = { range, userVB }; if (kind !== 'hl') setRange('all', false); }   // 狭い画面：使い方は全体を見せる。見どころは今の範囲から寄り始める。閉じたら戻す
      dots.innerHTML = STEPS.map(() => '<i></i>').join('');
      box.classList.add('show'); hole = null;
      hand.style.transition = 'none'; hand.style.transform = `translate(${innerWidth - 80}px, ${innerHeight - 80}px)`; hand.style.opacity = '0';
      void hand.offsetWidth; hand.style.transition = '';
      tour.isOpen = true; go(0);
    };
    const close = () => {
      timers.forEach(clearTimeout); timers = [];
      if (cleanup) { cleanup(); cleanup = null; }
      box.classList.remove('show'); tour.isOpen = false;
      if (savedRange) { range = savedRange.range; userVB = savedRange.userVB; savedRange = null; setRange(range, true); }
      if (STEPS === HL) { const sb = document.querySelector('[data-speed="1"]'); if (sb) sb.click(); setPlaying(true); return; }   // 見どころ：その場面のまま 1 倍速で続ける
      setPlaying(wasPlaying);
      try { localStorage.setItem('circleflow-tour-seen', '1'); } catch (e) {}
    };
    const goNext = () => i < STEPS.length - 1 ? go(i + 1) : close();
    const goPrev = () => { if (i > 0) go(i - 1); };
    next.onclick = goNext;
    prev.onclick = goPrev;
    $('tourSkip').onclick = close;
    const follow = () => {                                        // 毎フレーム：穴を目標に合わせる（粒は動く、画面はずれる）
      if (holeTw) { holeTw(performance.now()); return; }
      if (target) { hole = target(); drawHole(hole); }
    };
    addEventListener('resize', () => { if (tour.isOpen && target) placeBubble(target()); });
    addEventListener('scroll', () => { if (tour.isOpen && target) placeBubble(target()); }, { passive: true });
    return { isOpen: false, open, close, follow, goNext, goPrev };
  })();
  $('helpBtn').onclick = () => tour.open('help');
  $('hlBtn').onclick = () => tour.open('hl');

  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'Escape') {
      if (tour.isOpen) tour.close();
      else if (more.classList.contains('show')) closeMore();
      else if (focus) closeCard();
      else untrack();
      return;
    }
    if (tour.isOpen) {                                         // ツアー中のキー（2026-11-05 著者の依頼）：→ Enter スペース で進む、← BS で戻る（Esc は上で閉じる）
      const fwd = e.key === 'ArrowRight' || e.key === 'Enter' || e.key === ' ', back = e.key === 'ArrowLeft' || e.key === 'Backspace';
      if (!fwd && !back) return;
      e.preventDefault();                                      // BS でページが戻ったり、スペースでスクロールしたりしないように
      if (document.activeElement && document.activeElement.closest && document.activeElement.closest('.bubble')) document.activeElement.blur();   // ボタンに焦点があると二重に進むので外す
      if (fwd) tour.goNext(); else tour.goPrev();
      return;
    }
    if (e.key === ' ') { e.preventDefault(); setPlaying(!playing); }
    if (e.key === 'ArrowRight') { t += 0.1; setPlaying(false); }
    if (e.key === 'ArrowLeft') { t = Math.max(0, t - 0.1); setPlaying(false); }
    if (e.key === '?') tour.open();
  });
  show(type);
  applyNarrow();
  setPlaying(true);
  requestAnimationFrame(frame);
  let seen = false;
  try { seen = localStorage.getItem('circleflow-tour-seen') === '1'; } catch (e) {}
  // ?term=（部品の名前）で開くと、その部品の解説を開いた状態になる（教科書から部品へ直接つなぐ用）
  if (TERMS[q.get('term')]) setTimeout(() => openTerm(q.get('term')), 100);
  else if (!seen && !q.has('notour')) setTimeout(tour.open, 700);
})();
"""
