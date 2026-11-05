/* SPDX-License-Identifier: MIT
 * CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
 */
/* ブロワ（タービン）式回路（Dräger Perseus 型）のガスの粒シミュレーション（ブラウザ実行時。1.6.0、2026-11-05）
 *
 * ピストン式（sim_piston.js）の用手換気の枝と同じ決まりで動かす。違うのは回路のつながり：
 *  - 管：A 吸気側（新鮮ガスの入口 → 吸気弁 → Y）、B 気管（死腔）、C 呼気側（Y → 呼気弁 → PEEP/Pmax 弁 → 分岐 NX）、
 *        F 吸収装置側（NX → 吸収装置 → ブロワの入口）、W ブロワ（入口 → ファンの中 → 出口 → 新鮮ガスの入口）、
 *        H 呼吸バッグ側（NX → APL 弁の分岐）、S 余剰ガス
 *  - 部屋：呼吸バッグ（g）、肺胞（l）。「よく混ざる部屋」で、粒は固定の席に座る。シリンダーはない
 *  - 場面：吸気（0〜TI）ブロワ（用手換気では手）が呼吸バッグのガスを吸収装置とブロワを通して引き、新鮮ガスと合わさって患者へ。
 *    新鮮ガス・デカップリング弁がないので吸気中の新鮮ガスも患者へ届くが、実機は流量センサーで換気量を一定に保つので、
 *    バッグから引く量は VT_P から吸気中の新鮮ガスを引いた分（一定の速さ）。
 *    呼気（TI〜周期の終わり）PEEP/Pmax 弁が開き、呼気はバッグへ。新鮮ガスは止まったブロワと吸収装置を逆に通ってバッグへ。
 *    バッグが満杯（NG_FULL）になると、入ってきたガスは APL バイパス弁（用手換気では APL 弁）から余剰ガス排出装置へ
 *  - 人工呼吸と用手換気で粒の動きは同じ形（違いは図の側：ファンの回転、手の印、APL 弁と APL バイパス弁の姿、余るガスの出口）
 *  - 部屋から出る粒の予定・吸収剤・圧の均し・新鮮ガスの到着のずらし（supplyPhase）・交換の記録はピストン式と同じ
 */
(function () {
  "use strict";

  const { mulberry32, Poly, along, pathLen, interp, hexRGB, DT, WARM_CYCLES, LEAD, MIN_TRIP, RELAX_MIN, RELAX_V, C_FRESH, C_CO2, simText, SimBase } = window.CircleFlowSim;
  const TUBES = ["A", "B", "C", "F", "W", "H"];

  class BlowerSim extends SimBase {
    constructor(geo, seed) {
      super();
      this.g = geo;
      this.seed = seed || 7;
      this.tubes = {};
      for (const k of Object.keys(geo.tubes)) this.tubes[k] = new Poly(geo.tubes[k]);
      this.supply = geo.supply.map(p => new Poly(p));
      this.CYC = geo.CYC; this.TI = geo.TI;
      this.SP = geo.SP;
      this.spc = {};
      for (const k of TUBES) this.spc[k] = geo.SP * ((geo.tubeSpacing || {})[k] || 1);
      this.FG = geo.FG_RATE;
      this.VT = geo.VT_P;
      this.manual = !!geo.manual;
      this.vbag = (this.VT - this.FG * this.TI) / this.TI;  // 吸気でバッグから引く量（粒/秒）
      this.STEPS_PER_CYC = Math.round(this.CYC / DT);
      this.gSlotDef = geo.bag.slots;
      this.lSlotDef = geo.lung.slots;
      this.hilum = geo.lung.hilum;
      this.tau = geo.exhale.tau; this.tEnd = geo.exhale.tEnd;
      this.exNorm = 1 - Math.exp(-this.tEnd / this.tau);
      const ab = geo.absorber;
      this.absRows = ab.rows; this.absCap = ab.cap; this.absSpread = ab.spread;
      this.absFresh = hexRGB(ab.fresh); this.absUsedC = hexRGB(ab.used);
      this.swaps = [];
      this.tracked = null;
      this.trail = [];
      this.reset();
    }

    // ---------- 時刻と場面 ----------
    get t() { return this.n * DT; }
    tc(t) { const c = this.CYC; return ((t % c) + c) % c; }
    phase(tc) { return tc < this.TI ? "i" : "e1"; }
    phaseStart(ph) { return { i: 0, e1: this.TI }[ph]; }

    exhFrac(dt) {
      if (dt <= 0) return 0;
      if (dt >= this.tEnd) return 1;
      return (1 - Math.exp(-dt / this.tau)) / this.exNorm;
    }
    exRate(dt) {
      if (dt < 0 || dt >= this.tEnd) return 0;
      return this.vtAct * Math.exp(-dt / this.tau) / (this.tau * this.exNorm);
    }
    lungScale(tc) {
      const L = this.g.lung;
      return L.s0 + (L.s1 - L.s0) * (this.lungVol(tc) - this.g.LUNG_MIN) / this.VT;
    }

    /** 各管の流れの速さ（px/s、＋は管の向き） */
    flows(tc) {
      const s = this.spc, FG = this.FG;
      if (this.phase(tc) === "i") {                           // 吸気：バッグ → 吸収装置 → ブロワ → 新鮮ガスと合流 → 患者
        const v = this.vbag;
        return { A: (v + FG) * s.A, B: (v + FG) * s.B, C: 0, F: v * s.F, W: v * s.W, H: -v * s.H };
      }
      const ex = this.exRate(tc - this.TI);                   // 呼気：呼気はバッグへ、新鮮ガスはブロワと吸収装置を逆に通ってバッグへ
      return { A: 0, B: -ex * s.B, C: ex * s.C, F: -FG * s.F, W: -FG * s.W, H: (ex + FG) * s.H };
    }

    // ---------- 席の位置 ----------
    bagScale(tc) { const b = this.g.bag; return interp(b.keyT, b.keyS, tc); }
    gSlotXY(idx, tc) {
      const [x, y] = this.gSlotDef[idx], [px, py] = this.g.bag.pivot;
      const sc = this.bagScale(tc === undefined ? this.tc(this.t) : tc);
      return [px + (x - px) * sc, py + (y - py) * sc];
    }
    lSlotXY(idx, tc) {
      const [x, y] = this.lSlotDef[idx], [hx, hy] = this.hilum;
      const sc = this.lungScale(tc === undefined ? this.tc(this.t) : tc);
      return [hx + (x - hx) * sc, hy + (y - hy) * sc];
    }
    slotXY(store, idx, tc) { return store === "g" ? this.gSlotXY(idx, tc) : this.lSlotXY(idx, tc); }

    // ---------- 初期化 ----------
    reset() {
      const g = this.g;
      this.rng = mulberry32(this.seed);
      this.particles = [];
      this.byId = new Map();
      this.nextId = 1;
      this.gSlots = new Array(this.gSlotDef.length).fill(null);
      this.lSlots = new Array(this.lSlotDef.length).fill(null);
      this.relL = []; this.relG = [];
      this.planned = { i: false, e1: false };
      this.vtAct = this.VT;
      this.absUse = new Array(this.absRows.length).fill(0);
      this.absorbed = 0;
      this.lastPhase = null;
      this.checkpoints = new Map();
      this.trail = [];
      const t0 = -WARM_CYCLES * this.CYC;
      this.n = Math.round(t0 / DT);
      const co2Init = { A: () => false, B: () => true, C: () => true, F: s => s < g.absD[0], W: () => false, H: () => true };
      for (const nm of TUBES) {
        const L = this.tubes[nm].L, sp = this.spc[nm], n = Math.floor(L / sp);
        for (let i = 0; i < n; i++) this.add({ st: "tube", tube: nm, s: (i + 0.5) * sp, co2: co2Init[nm]((i + 0.5) * sp) });
      }
      for (let i = 0; i < Math.round(g.bag.keyN[0]); i++) {
        const idx = this.pickBagEntry();
        const p = this.add({ st: "slot", store: "g", slot: idx, co2: true }); this.gSlots[idx] = p.id;
      }
      for (let i = 0; i < g.LUNG_MIN; i++) {
        const idx = this.pickLungEntry();
        const p = this.add({ st: "slot", store: "l", slot: idx, co2: true }); this.lSlots[idx] = p.id;
      }
      const Lmax = Math.max(...this.supply.map(p => p.L));
      this.setNextKs((t0 - Lmax / g.SUP_V) * this.FG - (g.supplyPhase || 0));
      this.spawnSupply();
      while (this.n < 0) this.step();
      this.saveCheckpoint();
    }

    // ---------- 供給路（ピストン式と同じ） ----------
    spawnTime(k) {
      return (k + (this.g.supplyPhase || 0)) / this.FG - this.supply[(k & 1) ? 1 : 2].L / this.g.SUP_V;
    }
    spawnSupply() {
      const t = this.t;
      for (const par of [0, 1]) {
        while (this.spawnTime(this.nextKs[par]) <= t + 1e-9) {
          const k = this.nextKs[par]; this.nextKs[par] += 2;
          const path = this.supply[this.supIdx(k)];
          const s = (t - this.spawnTime(k)) * this.g.SUP_V;
          if (s < path.L) this.add({ st: "sup", sup: this.supIdx(k), s, k, kind: par ? "N2O" : "O2", co2: false });
        }
      }
    }
    supIdx(k) { return [0, 1, 2, 3, 2, 1][((k % 6) + 6) % 6]; }
    setNextKs(k0) { k0 = Math.ceil(k0); this.nextKs = [k0 + (k0 & 1), k0 + 1 - (k0 & 1)]; }

    // ---------- 席の選び方 ----------
    freeOf(slots) { const a = []; slots.forEach((v, i) => { if (v === null) a.push(i); }); return a; }
    seatedOf(slots) { const a = []; slots.forEach((v, i) => { if (v !== null && this.byId.get(v).st === "slot") a.push(i); }); return a; }
    bagMouthDist(i) { const [x, y] = this.gSlotDef[i], [mx, my] = this.g.nodes.BAGM; return Math.hypot(x - mx, y - my); }
    pickBagEntry() { const f = this.freeOf(this.gSlots); return f.length ? this.pickWeighted(f, i => 1 / (this.bagMouthDist(i) + 15)) : -1; }
    pickBagExit() { const o = this.seatedOf(this.gSlots); return o.length ? this.pickWeighted(o, i => 1 / (this.bagMouthDist(i) + 15)) : -1; }
    pickLungEntry() {
      const free = this.freeOf(this.lSlots), LG = this.g.nodes.LG;
      if (!free.length) return -1;
      return this.pickWeighted(free, i => { const [x, y] = this.lSlotXY(i); return 1 / Math.pow(Math.hypot(x - LG[0], y - LG[1]) + 8, 2); });
    }
    pickLungExit() {
      const occ = this.seatedOf(this.lSlots);
      if (!occ.length) return -1;
      return this.pickWeighted(occ, i => Math.pow(this.byId.get(this.lSlots[i]).age + 1, 2));
    }
    countOf(slots) { return slots.reduce((n, v) => n + (v !== null ? 1 : 0), 0); }
    bagCount() { return this.countOf(this.gSlots); }
    lungCount() { return this.countOf(this.lSlots); }

    // ---------- 管の出入り ----------
    enterTube(p, nm, s) {
      p.st = "tube"; p.tube = nm; p.s = s;
      delete p.path; delete p.dest;
    }
    toRoom(p, store, idx, path, speed) {
      ({ g: this.gSlots, l: this.lSlots })[store][idx] = p.id;
      this.startTransit(p, path, speed, { type: "slot", store, slot: idx });
    }

    exitFar(p, over, F) {
      const g = this.g, nd = g.nodes, tc = this.tc(this.t);
      switch (p.tube) {
        case "A": this.enterTube(p, "B", over); break;
        case "B": {                                                   // 肺胞へ
          const idx = this.pickLungEntry();
          if (idx < 0) { p.s = this.tubes.B.L; break; }
          p.co2 = true;
          this.toRoom(p, "l", idx, [nd.LG, this.lSlotXY(idx)], Math.max(Math.abs(F.B), 60));
          break;
        }
        case "C": this.enterTube(p, "H", over); break;               // 呼気はバッグ側へ
        case "F": this.enterTube(p, "W", over); break;               // 吸収装置を抜けてブロワへ
        case "W": this.enterTube(p, "A", over); break;               // ブロワを抜けて吸気側へ（新鮮ガスの入口で合流）
        case "H": {                                                   // 呼吸バッグへ。満杯なら余剰ガス排出装置へ
          if (this.bagCount() < g.NG_FULL) {
            const idx = this.pickBagEntry();
            this.toRoom(p, "g", idx, [nd.APL, nd.BAGM, this.gSlotXY(idx, tc)], Math.max(Math.abs(F.H), 60));
          } else {
            p.st = "scav"; p.s = over * (g.SCAV_V / Math.max(F.H, 1));
          }
          break;
        }
      }
    }
    exitNear(p, over) {
      switch (p.tube) {
        case "B": this.enterTube(p, "C", over); break;
        case "F": this.enterTube(p, "H", over); break;        // 逆流してきた新鮮ガスはバッグへ
        case "W": this.enterTube(p, "F", this.tubes.F.L - over); break;   // 止まったブロワを逆に抜けて吸収装置へ
        case "H": this.enterTube(p, "F", over); break;        // バッグのガスは吸収装置へ
      }
    }

    // ---------- 部屋から出る粒の予定（ピストン式の用手換気と同じ） ----------
    farGapAt(nm, dt) {
      const v = this.flows(this.tc(this.t))[nm], L = this.tubes[nm].L;
      let smax = -Infinity, leaving = 0;
      for (const p of this.particles) if (p.st === "tube" && p.tube === nm) {
        const s = p.s + v * dt;
        if (s > L) leaving++; else if (s > smax) smax = s;
      }
      return { gap: smax === -Infinity ? Infinity : L - smax, leaving };
    }
    planCount(sp, D, gap0, nAvail) {
      const V1 = Math.max(0, sp - Math.min(gap0, sp));
      const nDisp = Math.floor((D - V1) / sp + 1e-9) + 1;
      return { V1, n: Math.max(0, Math.min(nAvail, nDisp)) };
    }
    planLung(tPhase, gap0, nIn) {
      const sp = this.spc.B, out = [];
      this.vtAct = Math.max(1, nIn);
      const D = this.vtAct * sp;
      const { V1, n } = this.planCount(sp, D, gap0, nIn);
      for (let k = 1; k <= n; k++) {
        const f = (V1 + (k - 1) * sp) / D;
        const dt = f >= 1 ? this.tEnd : -this.tau * Math.log(1 - f * this.exNorm);
        out.push(tPhase + dt + DT);
      }
      return out;
    }
    /** 吸気：ブロワ（用手換気では手）が呼吸バッグから一定の速さで引く */
    planBag(tPhase, gap0, nAvail) {
      const sp = this.spc.H, v = this.vbag * sp, out = [];
      const { V1, n } = this.planCount(sp, v * this.TI, gap0, nAvail);
      for (let k = 1; k <= n; k++) out.push(tPhase + (V1 + (k - 1) * sp) / v + DT);
      return out;
    }
    planAhead(ph, tc) {
      const g = this.g;
      if (ph === "i" && !this.planned.e1 && tc >= this.TI - LEAD) {
        const dt = this.TI - tc, { gap, leaving } = this.farGapAt("B", dt);
        this.relL = this.planLung(this.t + dt, gap, Math.max(0, this.lungCount() + leaving - g.LUNG_MIN)); this.planned.e1 = true;
      }
      if (ph === "e1" && !this.planned.i && tc >= this.CYC - LEAD) {
        const dt = this.CYC - tc, { gap, leaving } = this.farGapAt("H", dt);
        this.relG = this.planBag(this.t + dt, gap, Math.max(0, Math.min(g.NG_FULL, this.bagCount() + leaving) - 1)); this.planned.i = true;
      }
    }
    scheduleReleases(ph, tPhase) {
      const g = this.g;
      if (ph === "i") {
        if (!this.planned.i) this.relG = this.planBag(tPhase, this.farGapAt("H", 0).gap, Math.max(0, this.bagCount() - 1));
        this.planned.i = false;
      } else {
        if (!this.planned.e1) this.relL = this.planLung(tPhase, this.farGapAt("B", 0).gap, Math.max(0, this.lungCount() - g.LUNG_MIN));
        this.planned.e1 = false;
      }
    }
    releaseFrom(store, tArr) {
      const nd = this.g.nodes, tc = this.tc(this.t);
      const slots = { g: this.gSlots, l: this.lSlots }[store];
      const idx = store === "g" ? this.pickBagExit() : this.pickLungExit();
      if (idx < 0) return false;
      const p = this.byId.get(slots[idx]);
      slots[idx] = null;
      const from = this.slotXY(store, idx, tc);
      const path = store === "g" ? [from, nd.BAGM, nd.APL] : [from, nd.LG];
      const tube = store === "g" ? "H" : "B";
      this.startTransit(p, path, pathLen(path) / Math.max(tArr - this.t, MIN_TRIP), { type: "tube", tube, far: true });
      return true;
    }

    // ---------- 1 刻み ----------
    step() {
      const g = this.g;
      const t = this.t, tc = this.tc(t), ph = this.phase(tc);
      const F = this.flows(tc);
      if (ph !== this.lastPhase) {
        const tPhase = t - (tc - this.phaseStart(ph));
        this.scheduleReleases(ph, tPhase);
        const aging = { i: "g", e1: "l" }[ph];
        for (const p of this.particles) if (p.st === "slot" && p.store === aging) p.age++;
        this.lastPhase = ph;
      }
      this.planAhead(ph, tc);
      for (const p of this.particles.slice()) {
        if (p.st === "tube") {
          const v = F[p.tube];
          if (!v) continue;
          p.s += v * DT;
          const L = this.tubes[p.tube].L;
          if (p.s > L) this.exitFar(p, p.s - L, F);
          else if (p.s < 0) this.exitNear(p, -p.s);
        } else if (p.st === "sup") {
          p.s += g.SUP_V * DT;
          const L = this.supply[p.sup].L;
          if (p.s > L) {
            const over = p.s - L;
            if (F.A > 0) this.enterTube(p, "A", over);                      // 吸気中：そのまま患者へ
            else this.enterTube(p, "W", this.tubes.W.L - over);           // 呼気中：止まったブロワと吸収装置を逆に通ってバッグへ
          }
        } else if (p.st === "trans") {
          p.u += p.speed * DT;
          if (p.u >= p.pathL) {
            const d = p.dest;
            if (d.type === "slot") { p.st = "slot"; p.store = d.store; p.slot = d.slot; delete p.path; delete p.dest; }
            else this.enterTube(p, d.tube, d.far ? this.tubes[d.tube].L - 1e-6 : 0);
          }
        } else if (p.st === "scav") {
          p.s += g.SCAV_V * DT;
          if (p.s > this.tubes.S.L) this.remove(p);
        }
      }
      for (const nm of TUBES) {                                      // 管の中の圧の均し
        const arr = this.particles.filter(p => p.st === "tube" && p.tube === nm).sort((a, b) => a.s - b.s);
        const dmin = RELAX_MIN * this.spc[nm], L = this.tubes[nm].L, mv = RELAX_V * DT;
        for (let i = 1; i < arr.length; i++) {
          const a = arr[i - 1], b = arr[i], d = b.s - a.s;
          if (d < dmin) { const m = Math.min(mv, (dmin - d) / 2); a.s = Math.max(0, a.s - m); b.s = Math.min(L, b.s + m); }
        }
      }
      while (this.relL.length && t >= this.relL[0] - LEAD) this.releaseFrom("l", this.relL.shift());
      while (this.relG.length && t >= this.relG[0] - LEAD) this.releaseFrom("g", this.relG.shift());
      const rows = this.absRows, sLo = rows[0][0], sHi = rows[rows.length - 1][1];   // 吸収装置
      for (const p of this.particles) {
        if (p.st !== "tube" || p.tube !== "F" || !p.co2 || p.s < sLo || p.s >= sHi) continue;
        const k = this.absUse.findIndex(u => u < 1 - 1e-9);
        if (k < 0) continue;
        p.co2 = false;
        if (this.n >= 0) this.absorb(k);
      }
      this.n++;
      if (this.swaps.includes(this.n)) this.absUse.fill(0);
      this.spawnSupply();
      if (this.tracked !== null) {
        const p = this.byId.get(this.tracked);
        if (p) { const [x, y] = this.xy(p); this.trail.push([this.t, x, y]); }
      }
      if (this.n >= 0 && this.n % this.STEPS_PER_CYC === 0) this.saveCheckpoint();
    }

    // ---------- 吸収剤 ----------
    absorb(k) {
      this.absorbed++;
      let carry = 0;
      for (let i = 0; k + i < this.absUse.length; i++) {
        const amt = (i < this.absSpread.length ? this.absSpread[i] : 0) / this.absCap + carry;
        if (amt <= 1e-12) break;
        const take = Math.min(1 - this.absUse[k + i], amt);
        this.absUse[k + i] += take;
        carry = amt - take;
      }
    }

    // ---------- 位置 ----------
    xy(p) {
      const tc = this.tc(this.t);
      switch (p.st) {
        case "tube": return this.tubes[p.tube].xy(p.s);
        case "sup": return this.supply[p.sup].xy(p.s);
        case "scav": return this.tubes.S.xy(p.s);
        case "slot": return this.slotXY(p.store, p.slot, tc);
        case "trans": {
          const path = p.path.slice();
          if (p.dest.type === "slot") path[path.length - 1] = this.slotXY(p.dest.store, p.dest.slot, tc);
          return along(path, p.u / p.pathL);
        }
      }
      return [0, 0];
    }

    // ---------- 保存と巻き戻し ----------
    snapshot() {
      return JSON.stringify({
        n: this.n, rng: this.rng.state, nextId: this.nextId, nextKs: this.nextKs,
        relL: this.relL, relG: this.relG, lastPhase: this.lastPhase, planned: this.planned, vtAct: this.vtAct,
        absUse: this.absUse, absorbed: this.absorbed,
        gSlots: this.gSlots, lSlots: this.lSlots, particles: this.particles,
      });
    }
    restore(snap) {
      const o = JSON.parse(snap);
      this.n = o.n; this.rng.state = o.rng; this.nextId = o.nextId; this.nextKs = o.nextKs;
      this.relL = o.relL; this.relG = o.relG; this.lastPhase = o.lastPhase; this.planned = o.planned; this.vtAct = o.vtAct;
      this.absUse = o.absUse; this.absorbed = o.absorbed;
      this.gSlots = o.gSlots; this.lSlots = o.lSlots;
      this.particles = o.particles;
      this.byId = new Map(this.particles.map(p => [p.id, p]));
    }
    seek(T) {
      T = Math.max(0, T);
      const nT = Math.floor(T / DT + 1e-6);
      if (nT < this.n || nT - this.n > this.STEPS_PER_CYC * 2) {
        const k = Math.floor(nT / this.STEPS_PER_CYC);
        let kk = k;
        while (kk > 0 && !this.checkpoints.has(kk)) kk--;
        if (nT < this.n || kk > Math.floor(this.n / this.STEPS_PER_CYC)) {
          this.restore(this.checkpoints.get(kk));
          this.trail = [];
        }
      }
      while (this.n < nT) this.step();
    }

    // ---------- 描画（ピストン式と同じ） ----------
    render(layer) {
      if (!layer._pool) { layer._pool = []; layer._trail = null; layer._ring = null; }
      const pool = layer._pool;
      const ns = "http://www.w3.org/2000/svg";
      if (!layer._trail) {
        const pl = document.createElementNS(ns, "polyline");
        pl.setAttribute("fill", "none"); pl.setAttribute("stroke", "#d33"); pl.setAttribute("stroke-width", "2");
        pl.setAttribute("stroke-opacity", "0.6"); pl.setAttribute("stroke-linejoin", "round");
        layer.appendChild(pl); layer._trail = pl;
        const ring = document.createElementNS(ns, "circle");
        ring.setAttribute("r", "8"); ring.setAttribute("fill", "none"); ring.setAttribute("stroke", "#d33"); ring.setAttribute("stroke-width", "2.2");
        layer.appendChild(ring); layer._ring = ring;
      }
      let i = 0;
      for (const p of this.particles) {
        let c = pool[i];
        if (!c) {
          c = document.createElementNS(ns, "circle");
          c.setAttribute("r", "3.3"); c.setAttribute("stroke", "#fff"); c.setAttribute("stroke-width", "1");
          c.style.cursor = "pointer";
          layer.insertBefore(c, layer._trail);
          pool.push(c);
        }
        const [x, y] = this.xy(p);
        c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1));
        c.setAttribute("fill", p.co2 ? C_CO2 : C_FRESH);
        c.dataset.id = p.id;
        c.style.display = "";
        i++;
      }
      for (; i < pool.length; i++) pool[i].style.display = "none";
      this.renderAbsorbent(layer);
      const tp = this.tracked !== null ? this.byId.get(this.tracked) : null;
      if (tp) {
        const [x, y] = this.xy(tp);
        layer._ring.style.display = ""; layer._ring.setAttribute("cx", x.toFixed(1)); layer._ring.setAttribute("cy", y.toFixed(1));
        const tNow = this.t, pts = this.trail.filter(q => tNow - q[0] <= this.CYC * 2);
        layer._trail.setAttribute("points", pts.map(q => q[1].toFixed(1) + "," + q[2].toFixed(1)).join(" "));
        layer._trail.style.display = "";
      } else {
        layer._ring.style.display = "none"; layer._trail.style.display = "none";
      }
    }
    renderAbsorbent(layer) {
      const svg = layer.ownerSVGElement;
      if (!svg) return;
      if (!layer._abs) {
        layer._abs = Array.from(svg.querySelectorAll("[data-absrow]")).map((el, i) => ({
          el, row: +el.getAttribute("data-absrow"), j: ((i * 0.6180339887) % 1 - 0.5) * 0.5, last: "",
        }));
      }
      const f = this.absFresh, u = this.absUsedC;
      for (const gr of layer._abs) {
        const a = this.absUse[gr.row];
        const v = Math.min(1, Math.max(0, a + gr.j * 4 * a * (1 - a)));
        const col = "rgb(" + [0, 1, 2].map(i => Math.round(f[i] + (u[i] - f[i]) * v)).join(",") + ")";
        if (col !== gr.last) { gr.el.setAttribute("fill", col); gr.last = col; }
      }
    }
    describe(p) {
      if (!p) return "";
      const inAbs = p.st === "tube" && p.tube === "F" && p.s >= this.g.absD[0] && p.s <= this.g.absD[1];
      const T = simText();
      const where = { tube: inAbs ? T.inAbs : { A: T.A, B: T.B, C: T.C, F: T.F, W: T.W, H: T.H }[p.tube],
        sup: T.sup, scav: T.scav, slot: { g: T.bag, l: T.lung }[p.store], trans: T.trans }[p.st];
      return T.fmt(p.kind === "O2" ? "O₂" : "N₂O", p.id, p.co2, where);
    }
  }

  window.BlowerSim = BlowerSim;
})();
