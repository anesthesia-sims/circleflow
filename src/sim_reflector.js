/* SPDX-License-Identifier: MIT
 * CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
 */
/* ボリュームリフレクタ式回路のガスの粒シミュレーション（ブラウザ実行時）。Getinge（Maquet）Flow-i の構成を参考
 *
 * 上昇式ベローズ（sim_bellows.js）と同じ決まりで動く。違いは人工呼吸器の部分：
 *  - ためる場所は「部屋」ではなく、長い管 R（ボリュームリフレクタ、合流点 J → 奥の端 K）。押し出し流れなので
 *    J から入ったガスは J から出る（後入れ先出し）。両端のガスは混ざらない
 *  - 新鮮ガスは流量計から一定に流れる。吸気中は管 A へ、呼気中は吸収装置（D）を逆向きに通ってリフレクタへ入る（2026-11-04 版 1.2.9：
 *    新鮮ガスの管にはガスをためる場所がなく、呼気中の回路内圧は PEEP 程度なので、圧の低い PEEP/APL 弁の側へ流れる。
 *    11-03〜1.2.8 は Flow-i にならって吸気中だけ入れ、呼気中に届いたガスを入口の手前に並べたり管の中で縮めたりしていた）
 *  - 吸気：奥の端 K からリフレクタガス（O2 の粒。灰）が VR 粒/秒で入り、R の中のガスを J 側へ押し出す。
 *    押し出されたガスは吸収装置（D）を通り、新鮮ガスと合わさって吸気弁から患者へ。患者に入る量は VT_P（新鮮ガスの量によらない。
 *    リフレクタが押し出すのは、吸気中に加わる新鮮ガスを引いた残り）
 *  - 呼気：呼気（C）と、吸収装置を逆向きに通ってきた新鮮ガスが J から R へ入る。そのぶん K から出たガス（O2 と最も古いガス）が
 *    PEEP/APL 弁を通って余剰ガス排出装置へ（S）
 *  - 定常状態では、呼吸ごとに新鮮ガスの量だけ境目が K 側へ戻るので、O2 は J まで届かない（届いた回数は reflLeak に数える）
 *  - 用手換気（geo.bag があるとき。2026-11-03）：呼吸バッグが奥の端 K につながり、リフレクタガスは止まる。新鮮ガスは一定。
 *    吸気は手で押したバッグのガスが K から R へ入って J 側へ押し出し、呼気は呼気と新鮮ガスが R へ入って K からバッグへ。
 *    バッグが満杯になると K から出た粒は PEEP/APL 弁（APL 弁として働く）から余剰ガス排出装置へ。決まりは sim_bellows.js の用手換気と同じ
 */
(function () {
  "use strict";

  const { mulberry32, Poly, along, pathLen, interp, hexRGB, DT, WARM_CYCLES, LEAD, MIN_TRIP, RELAX_MIN, RELAX_V, C_FRESH, C_CO2, simText, SimBase } = window.CircleFlowSim;
  const TUBES = ["A", "B", "C", "D", "R"];
  const C_REFL = "#7a7a7a";                               // リフレクタガス（O2）の粒：駆動ガスと同じ灰（押すためのガス）

  class ReflectorSim extends SimBase {
    constructor(geo, seed) {
      super();
      this.g = geo;
      this.seed = seed || 7;
      this.tubes = {};
      for (const k of Object.keys(geo.tubes)) this.tubes[k] = new Poly(geo.tubes[k]);
      this.supply = geo.supply.map(p => new Poly(p));
      this.CYC = geo.CYC; this.TI = geo.TI; this.TE = geo.CYC - geo.TI;
      this.SP = geo.SP;
      this.spc = {};
      for (const k of TUBES) this.spc[k] = geo.SP * ((geo.tubeSpacing || {})[k] || 1);
      this.FG = geo.FG_RATE;                                  // 新鮮ガスの流量（粒/秒。一定）
      this.vr = geo.VR;                                       // リフレクタガス（用手換気では呼吸バッグ）が押し出す流量（粒/秒）
      this.manual = !!geo.bag;                                // 用手換気：呼吸バッグが奥の端 K につながり、リフレクタガスは止まる
      this.bSlotDef = this.manual ? geo.bag.slots : [];
      this.VT = geo.VT_P;                                     // 患者に入る量（粒）
      this.STEPS_PER_CYC = Math.round(this.CYC / DT);
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

    // ---------- 時刻 ----------
    get t() { return this.n * DT; }
    tc(t) { const c = this.CYC; return ((t % c) + c) % c; }

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

    /** 時刻 tc（周期内）の各管の流れの速さ（px/s、＋は管の向き）。R は J → K の向きが＋ */
    flows(tc) {                                                // 新鮮ガスは一定。吸気はリフレクタガス（用手換気では手で押したバッグ）が押し出す
      const s = this.spc;
      if (tc < this.TI) return { A: (this.vr + this.FG) * s.A, B: (this.vr + this.FG) * s.B, C: 0, D: this.vr * s.D, R: -this.vr * s.R };
      const ex = this.exRate(tc - this.TI);
      return { A: 0, B: -ex * s.B, C: ex * s.C, D: -this.FG * s.D, R: (ex + this.FG) * s.R };   // 呼気中は新鮮ガスが D を逆向きに R へ
    }

    bSlotXY(idx, tc) {                                        // 呼吸バッグの席：差し込み口を中心に、バッグの大きさに合わせて動く
      const [x, y] = this.bSlotDef[idx], [px, py] = this.g.bag.pivot, b = this.g.bag;
      const sc = interp(b.keyT, b.keyS, tc === undefined ? this.tc(this.t) : tc);
      return [px + (x - px) * sc, py + (y - py) * sc];
    }
    lSlotXY(idx, tc) {
      const [x, y] = this.lSlotDef[idx], [hx, hy] = this.hilum;
      const sc = this.lungScale(tc === undefined ? this.tc(this.t) : tc);
      return [hx + (x - hx) * sc, hy + (y - hy) * sc];
    }

    // ---------- 初期化 ----------
    reset() {
      const g = this.g;
      this.rng = mulberry32(this.seed);
      this.particles = [];
      this.byId = new Map();
      this.nextId = 1;
      this.lSlots = new Array(this.lSlotDef.length).fill(null);
      this.bSlots = new Array(this.bSlotDef.length).fill(null);   // 呼吸バッグの席（用手換気）
      this.relL = []; this.relB = [];
      this.planned = { i: false, e: false };
      this.vtAct = this.VT;
      this.absUse = new Array(this.absRows.length).fill(0);
      this.absorbed = 0;
      this.reflLeak = 0;                                            // リフレクタガスが J まで届いて回路に入った回数
      this.lastPhase = null;
      this.checkpoints = new Map();
      this.trail = [];
      const t0 = -WARM_CYCLES * this.CYC;
      this.n = Math.round(t0 / DT);
      // 管に粒を敷く。R は呼気の終わりの状態（患者側のガスで満たされ、O2 はない）から始める
      const co2Init = { A: () => false, B: () => true, C: () => true, R: () => true, D: s => s < g.absD[1] };
      for (const nm of TUBES) {
        const L = this.tubes[nm].L, sp = this.spc[nm], n = Math.floor(L / sp);
        for (let i = 0; i < n; i++) {
          const s = (i + 0.5) * sp;
          this.add({ st: "tube", tube: nm, s, co2: co2Init[nm](s) });
        }
      }
      for (let i = 0; i < g.LUNG_MIN; i++) {
        const idx = this.pickLungEntry();
        const p = this.add({ st: "slot", store: "l", slot: idx, co2: true });
        this.lSlots[idx] = p.id;
      }
      for (let i = 0; i < (this.manual ? g.NB_FULL : 0); i++) {   // 呼吸バッグは満杯（呼気の終わり）から
        const p = this.add({ st: "slot", store: "b", slot: i, co2: true });
        this.bSlots[i] = p.id;
      }
      const Lmax = Math.max(...this.supply.map(p => p.L));
      this.setNextKs((t0 - Lmax / g.SUP_V) * this.FG - (g.supplyPhase || 0));   // 供給は一定（到着 k/FG）
      this.spawnSupply();
      while (this.n < 0) this.step();
      this.saveCheckpoint();
    }

    // ---------- 供給路 ----------
    /** k 番目の新鮮ガスの粒を供給路の入口に出す時刻。一定の流量で、合流点 JFG に k/FG 秒に着く */
    spawnTime(k) {
      const path = this.supply[this.supIdx(k)];
      return (k + (this.g.supplyPhase || 0)) / this.FG - path.L / this.g.SUP_V;   // 供給は一定の流量（2026-11-04）
    }
    /** 供給路の粒を出す。O2（偶数 k）と N2O（奇数 k）は経路の長さが違い、同じ到着時刻でも出発時刻が違うので、
     *  別々のカウンターで出す（2026-11-04：1 つのカウンターで交互に出していたため、N2O が O2 より 3 秒遅れて出発し、
     *  配管端末器から 230 px 上に現れていた） */
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
    /** k 番目の粒が通る供給路：偶数は O2・奇数は N2O の流量計から出て、合流管で混ざったあと 6 粒のうち 2 粒（O2 と N2O が 1 粒ずつ）が
     *  気化室を通り、残りはバイパスを通る（供給路 0：O2 → 気化室、1：N2O → バイパス、2：O2 → バイパス、3：N2O → 気化室。2026-11-04） */
    supIdx(k) { return [0, 1, 2, 3, 2, 1][((k % 6) + 6) % 6]; }
    /** 最初に出す k：t0 までに出発している最初の偶数と奇数 */
    setNextKs(k0) { k0 = Math.ceil(k0); this.nextKs = [k0 + (k0 & 1), k0 + 1 - (k0 & 1)]; }
    /** リフレクタガス：吸気中、奥の端 K から O2 の粒を間隔 SP ごとに入れる（速さ VR×SP なので VR 粒/秒） */
    spawnReflGas() {
      const L = this.tubes.R.L, sp = this.spc.R;
      let smax = -Infinity;
      for (const p of this.particles) if (p.st === "tube" && p.tube === "R" && p.s > smax) smax = p.s;
      if (smax === -Infinity || smax + sp <= L) {
        this.add({ st: "tube", tube: "R", s: smax === -Infinity ? L - 1e-6 : smax + sp, kind: "O2", refl: true, co2: false });
      }
    }

    // ---------- 席の選び方 ----------
    pickLungEntry() {
      const free = [], LG = this.g.nodes.LG;
      this.lSlots.forEach((v, i) => { if (v === null) free.push(i); });
      if (!free.length) return -1;
      return this.pickWeighted(free, i => { const [x, y] = this.lSlotXY(i); return 1 / Math.pow(Math.hypot(x - LG[0], y - LG[1]) + 8, 2); });
    }
    pickLungExit() {
      const occ = [];
      this.lSlots.forEach((v, i) => { if (v !== null && this.byId.get(v).st === "slot") occ.push(i); });
      if (!occ.length) return -1;
      return this.pickWeighted(occ, i => Math.pow(this.byId.get(this.lSlots[i]).age + 1, 2));
    }

    // ---------- 呼吸バッグ（用手換気） ----------
    bagCount() { return this.bSlots.reduce((n, v) => n + (v !== null ? 1 : 0), 0); }
    bagWeight(i) { const [x, y] = this.bSlotDef[i], [mx, my] = this.g.nodes.BAGM; return 1 / (Math.hypot(x - mx, y - my) + 15); }   // 口に近い席ほど出入りしやすい
    pickBagEntry() {
      const free = [];
      this.bSlots.forEach((v, i) => { if (v === null) free.push(i); });
      if (!free.length) return -1;
      return this.pickWeighted(free, i => this.bagWeight(i));
    }
    pickBagExit() {
      const occ = [];
      this.bSlots.forEach((v, i) => { if (v !== null && this.byId.get(v).st === "slot") occ.push(i); });
      if (!occ.length) return -1;
      return this.pickWeighted(occ, i => this.bagWeight(i));
    }
    /** 奥の端 K からバッグの口を通って席までの道 */
    bagPath(idx, tc) { const g = this.g; return [g.nodes.K, g.nodes.BAGM, this.bSlotXY(idx, tc)]; }
    planBag(tPhase, gap0, nAvail) {
      const sp = this.spc.R, v = this.vr * sp, out = [];
      const { V1, n } = this.planCount(sp, v * this.TI, gap0, nAvail);
      for (let k = 1; k <= n; k++) out.push(tPhase + (V1 + (k - 1) * sp) / v + DT);
      return out;
    }
    releaseBag(tArr) {
      const idx = this.pickBagExit();
      if (idx < 0) return false;
      const p = this.byId.get(this.bSlots[idx]);
      this.bSlots[idx] = null;
      const path = this.bagPath(idx, this.tc(this.t)).reverse();
      const speed = pathLen(path) / Math.max(tArr - this.t, MIN_TRIP);
      this.startTransit(p, path, speed, { type: "tube", tube: "R", far: true });
      return true;
    }

    // ---------- 管の出入り ----------
    enterTube(p, nm, s) {
      p.st = "tube"; p.tube = nm; p.s = s;
      delete p.path; delete p.dest;
    }
    lungCount() { return this.lSlots.reduce((n, v) => n + (v !== null ? 1 : 0), 0); }

    exitFar(p, over, F) {
      const g = this.g;
      switch (p.tube) {
        case "A": this.enterTube(p, "B", over); break;
        case "B": {                                       // 肺へ
          const idx = this.pickLungEntry();
          if (idx < 0) { p.s = this.tubes.B.L; break; }
          this.lSlots[idx] = p.id;
          p.co2 = true;
          this.startTransit(p, [g.nodes.LG, this.lSlotXY(idx)], Math.max(Math.abs(F.B), 60), { type: "slot", store: "l", slot: idx });
          break;
        }
        case "C": this.enterTube(p, "R", over); break;          // 呼気はリフレクタへ
        case "D": this.enterTube(p, "A", over); break;          // 回路の入口へ
        case "R": {                                       // 奥の端 K：用手換気ではバッグへ（満杯なら PEEP/APL 弁から排出へ）。人工呼吸では PEEP/APL 弁から排出へ
          if (this.manual && this.bagCount() < g.NB_FULL) {
            const idx = this.pickBagEntry();
            this.bSlots[idx] = p.id;
            this.startTransit(p, this.bagPath(idx, this.tc(this.t)), Math.max(Math.abs(F.R), 60), { type: "slot", store: "b", slot: idx });
          } else { p.st = "scav"; p.s = over * (g.SCAV_V / Math.max(F.R, 1)); }
          break;
        }
      }
    }
    exitNear(p, over) {
      switch (p.tube) {
        case "B": this.enterTube(p, "C", over); break;
        case "D": this.enterTube(p, "R", over); break;          // 逆流してきた新鮮ガスはリフレクタへ
        case "R": if (p.refl) this.reflLeak++; this.enterTube(p, "D", over); break;   // 押し出されたガスは吸収装置へ
      }
    }

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
    planAhead(ph, tc) {
      const g = this.g;
      if (ph === "i" && !this.planned.e && tc >= this.TI - LEAD) {
        const dt = this.TI - tc, tPhase = this.t + dt;
        const { gap, leaving } = this.farGapAt("B", dt);
        const n = Math.max(0, this.lungCount() + leaving - g.LUNG_MIN);
        this.relL = this.planLung(tPhase, gap, n); this.planned.e = true;
      }
      if (this.manual && ph === "e" && !this.planned.i && tc >= this.CYC - LEAD) {   // 用手換気：次の吸気でバッグから出る粒の予定
        const dt = this.CYC - tc, tPhase = this.t + dt;
        const { gap, leaving } = this.farGapAt("R", dt);
        const n = Math.max(0, Math.min(g.NB_FULL, this.bagCount() + leaving) - g.NB_MIN);
        this.relB = this.planBag(tPhase, gap, n); this.planned.i = true;
      }
    }
    scheduleReleases(ph, tPhase) {
      const g = this.g;
      if (ph === "i") {
        if (this.manual && !this.planned.i) this.relB = this.planBag(tPhase, this.farGapAt("R", 0).gap, Math.max(0, this.bagCount() - g.NB_MIN));
        this.planned.i = false;
      } else {
        if (!this.planned.e) this.relL = this.planLung(tPhase, this.farGapAt("B", 0).gap, Math.max(0, this.lungCount() - g.LUNG_MIN));
        this.planned.e = false;
      }
    }
    releaseLung(tArr) {
      const g = this.g;
      const idx = this.pickLungExit();
      if (idx < 0) return false;
      const p = this.byId.get(this.lSlots[idx]);
      this.lSlots[idx] = null;
      const path = [this.lSlotXY(idx), g.nodes.LG];
      const speed = pathLen(path) / Math.max(tArr - this.t, MIN_TRIP);
      this.startTransit(p, path, speed, { type: "tube", tube: "B", far: true });
      return true;
    }

    // ---------- 1 刻み ----------
    step() {
      const g = this.g;
      const t = this.t, tc = this.tc(t), ph = tc < this.TI ? "i" : "e";
      const F = this.flows(tc);
      if (ph !== this.lastPhase) {
        const tPhase = t - (ph === "i" ? tc : tc - this.TI);
        this.scheduleReleases(ph, tPhase);
        if (ph === "e") for (const p of this.particles) if (p.st === "slot") p.age++;
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
          const L = this.supply[p.sup].L;                       // 新鮮ガスは一定に回路へ（呼気中は吸収装置を逆向きに）
          p.s += g.SUP_V * DT;
          if (p.s > L) { const over = p.s - L; if (ph === "i") this.enterTube(p, "A", over); else this.enterTube(p, "D", this.tubes.D.L - over); }
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
      if (ph === "i" && !this.manual) this.spawnReflGas();
      for (const nm of TUBES) {
        const arr = this.particles.filter(p => p.st === "tube" && p.tube === nm).sort((a, b) => a.s - b.s);
        const dmin = RELAX_MIN * this.spc[nm], L = this.tubes[nm].L, mv = RELAX_V * DT;
        for (let i = 1; i < arr.length; i++) {
          const a = arr[i - 1], b = arr[i], d = b.s - a.s;
          if (d < dmin) { const m = Math.min(mv, (dmin - d) / 2); a.s = Math.max(0, a.s - m); b.s = Math.min(L, b.s + m); }
        }
      }
      while (this.relL.length && t >= this.relL[0] - LEAD) { const tr = this.relL.shift(); this.releaseLung(tr); }
      while (this.relB.length && t >= this.relB[0] - LEAD) { const tr = this.relB.shift(); this.releaseBag(tr); }
      const rows = this.absRows, sLo = rows[0][0], sHi = rows[rows.length - 1][1];
      for (const p of this.particles) {
        if (p.st !== "tube" || p.tube !== "D" || !p.co2 || p.s < sLo || p.s >= sHi) continue;
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
        case "slot": return p.store === "b" ? this.bSlotXY(p.slot, tc) : this.lSlotXY(p.slot, tc);
        case "trans": {
          const path = p.path.slice();
          if (p.dest.type === "slot") path[path.length - 1] = p.dest.store === "b" ? this.bSlotXY(p.dest.slot, tc) : this.lSlotXY(p.dest.slot, tc);
          return along(path, p.u / p.pathL);
        }
      }
      return [0, 0];
    }
    /** リフレクタの中の O2 の粒の数と、O2 の境目が J から何粒目か（点検用） */
    reflStat() {
      const arr = this.particles.filter(p => p.st === "tube" && p.tube === "R").sort((a, b) => a.s - b.s);
      const n = arr.length, o2 = arr.filter(p => p.refl).length;
      const first = arr.findIndex(p => p.refl);
      return { total: n, o2, depth: first < 0 ? n : first };
    }

    // ---------- 保存と巻き戻し ----------
    snapshot() {
      return JSON.stringify({
        n: this.n, rng: this.rng.state, nextId: this.nextId, nextKs: this.nextKs,
        relL: this.relL, relB: this.relB, lastPhase: this.lastPhase, planned: this.planned, vtAct: this.vtAct,
        absUse: this.absUse, absorbed: this.absorbed, reflLeak: this.reflLeak,
        lSlots: this.lSlots, bSlots: this.bSlots, particles: this.particles,
      });
    }
    restore(snap) {
      const o = JSON.parse(snap);
      this.n = o.n; this.rng.state = o.rng; this.nextId = o.nextId; this.nextKs = o.nextKs;
      this.relL = o.relL; this.relB = o.relB; this.lastPhase = o.lastPhase; this.planned = o.planned; this.vtAct = o.vtAct;
      this.absUse = o.absUse; this.absorbed = o.absorbed; this.reflLeak = o.reflLeak;
      this.lSlots = o.lSlots; this.bSlots = o.bSlots;
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

    // ---------- 描画 ----------
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
        c.setAttribute("fill", p.refl ? C_REFL : p.co2 ? C_CO2 : C_FRESH);
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
      const inAbs = p.st === "tube" && p.tube === "D" && p.s >= this.g.absD[0] && p.s <= this.g.absD[1];
      const T = simText();
      const where = { tube: inAbs ? T.inAbs : { A: T.A, B: T.B, C: T.C, D: T.D, R: T.R }[p.tube],
        sup: T.sup, scav: T.scav, slot: p.store === "b" ? T.bag : T.lung, trans: T.trans }[p.st];
      return T.fmt(p.refl ? T.reflGas : (p.kind === "O2" ? "O₂" : "N₂O"), p.id, p.co2, where);
    }
  }

  window.ReflectorSim = ReflectorSim;
})();
