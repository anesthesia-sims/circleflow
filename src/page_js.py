# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""操作ページの JavaScript：場面の切り替え、粒の描画（sim_*.js を呼ぶ）、部品の解説（拡大）、時刻のバー、
使い方のツアー。文は L（page_terms.py・page_en.py）から取る"""

MAIN_JS = r"""
(() => {
  const CYC = 6.0, NS = 'http://www.w3.org/2000/svg';
  const PHASES = L.phases;

  const TYPES = ['bellows', 'bellowsLow', 'bellowsMan', 'bellowsLowMan', 'piston', 'pistonLow', 'pistonMan', 'pistonLowMan', 'reflector', 'reflectorLow'];
  const $ = id => document.getElementById(id);
  const figs = {};
  for (const k of TYPES) figs[k] = document.querySelector('#fig-' + k + ' svg');
  PHASES.bellowsLow = PHASES.bellows; PHASES.pistonLow = PHASES.piston;
  PHASES.bellowsLowMan = PHASES.bellowsMan; PHASES.pistonLowMan = PHASES.pistonMan;
  PHASES.reflectorLow = PHASES.reflector;
  const family = tp => tp.startsWith('piston') ? 'piston' : tp.startsWith('reflector') ? 'reflector' : 'bellows';
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
  const getSim = k => (sims[k] = sims[k] || (family(k) === 'piston' ? new PistonSim(window.SCENE_GEO[k], 7) : family(k) === 'reflector' ? new ReflectorSim(window.SCENE_GEO[k], 7) : new BellowsSim(window.SCENE_GEO[k], 7)));
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
  const rectOf = (id, tp) => TERMS[id].rect ? TERMS[id].rect[family(tp)] || (family(tp) === 'reflector' ? TERMS[id].rect.bellows : null) || null : null;   // ボリュームリフレクタ式の図は上昇式ベローズと同じ配置なので、範囲がなければそちらを使う
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
    $('ventGrp').hidden = family(tp) === 'reflector';   // ボリュームリフレクタ式には用手換気の場面がまだない
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
  document.querySelectorAll('#typeSeg button').forEach(b => b.onclick = () => { show(key(b.dataset.type, low, man && b.dataset.type !== 'reflector')); t = 0; });
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
