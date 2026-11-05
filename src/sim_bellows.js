/* SPDX-License-Identifier: MIT
 * CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
 */
/* 上昇式ベローズ回路のガスの粒シミュレーション（ブラウザ実行時）
 *
 * モデル
 *  - 粒 1 個 ＝ 一定体積のガス。1 本の流れの中では、粒は間隔 SP（px）で並ぶ。どの管も同じ断面とみなす
 *    （tubeSpacing で管ごとに係数を変えられる。係数 >1 は細い管）
 *  - 管（A〜E・余剰ガス S・供給路）は「押し出し流れ」。粒は弧長 s で表し、場面ごとの流量（粒/秒）×間隔 の
 *    速さで進む。管の端を越えた分は次の管に持ち越すので、合流点で止まらない
 *  - 粒はいつも管の中心線の上を動く（行き先を目で追いやすくするため）。合流点で 2 つの流れが同じ管に
 *    入って粒が近づきすぎたときは、管の中の均し（RELAX_*）で前後に離れる。
 *    以前は管の幅の中で左右に 2.4 px ずらす「レーン」を使っていたが、粒の直径（約 8.6 px）より小さく
 *    重なりはほとんど防げず、管の中心から外れた粒が目立つだけだったのでやめた（2026-11-02）
 *  - ためる場所（ベローズ・肺）は「よく混ざる部屋」。粒は固定の席に座り、出るときは選ばれた粒だけが
 *    口へ向かう。ほかの粒は動かない。選び方は決定的な擬似乱数（seed 固定）で、ベローズは底に近い席を、
 *    肺は古い粒を選びやすい。出る時刻は等間隔で、口に着いた粒はそのまま管の流れに乗る
 *  - 色：肺に入ると CO2 を含む（紫）、吸収装置で CO2 が除かれる（黒）
 *  - 吸収剤：入口（下）から 9 層。CO2 を含む粒が吸収剤の層に入ると CO2 が除かれ、入口から数えて最初の
 *    まだ使える層とその上の 2 層が少しずつ使われる（0.6・0.3・0.1 の割合）。使用済みの帯（指示薬の紫）は
 *    入口から出口へ進む。全層を使い切ると CO2 は除かれない。押し出し流れの粒は吸収装置の入口付近で
 *    行き来するだけなので、除去の位置は層の入口にまとめ、使われる吸収剤の位置で前線を表す。
 *    容量は実際の数時間を数分に縮めた値。交換は時刻つきの出来事として記録し、巻き戻しても再現する
 *  - 時刻は固定刻み（DT）で進め、周期ごとに状態を保存する。巻き戻しは保存点から計算し直すので、
 *    どの時刻でも同じ状態になる（動画のコマ撮りにも使える）
 *  - 用手換気（geo.bag があるとき。2026-11-02）：切替弁を用手に倒した回路。ベローズの代わりに呼吸バッグが
 *    回路のガスをためる。流れの決まりはベローズと同じ（吸気は手で押したバッグから、呼気はバッグへ戻り、
 *    満杯になると APL 弁から余剰ガス排出装置へ）。管 E は合流点 → 切替弁 → APL 弁の分岐（VP）で、バッグの席は
 *    差し込み口を中心にバッグと一緒にふくらみ・しぼむ
 */
(function () {
  "use strict";

  const { mulberry32, Poly, along, pathLen, interp, hexRGB, DT, WARM_CYCLES, LEAD, MIN_TRIP, RELAX_MIN, RELAX_V, C_FRESH, C_CO2, simText, SimBase } = window.CircleFlowSim;
  const TUBES = ["A", "B", "C", "D", "E"];

  class BellowsSim extends SimBase {
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
      this.FG = geo.FG_RATE;                                  // 粒/秒
      this.vb = geo.VT_B / geo.TI;                            // ベローズが送り出す流量（粒/秒）
      this.VT = geo.VT_P;                                     // 患者に入る量（粒）
      this.STEPS_PER_CYC = Math.round(this.CYC / DT);
      // ベローズの席：3 列 × 5 段のうち 14（最上段の中央は使わない）。用手換気では呼吸バッグの席（満杯時の座標）
      this.manual = !!geo.bag;
      this.bSlotDef = [];
      if (this.manual) this.bSlotDef = geo.bag.slots;
      else for (let r = 0; r < 5; r++) for (let c = 0; c < 3; c++) if (!(r === 4 && c === 1)) this.bSlotDef.push([c, r]);
      // 肺胞の席（左右 2 葉、満杯時の座標）。輪郭と一緒に気管分岐部を中心に伸縮する
      this.lSlotDef = geo.lung.slots;
      this.hilum = geo.lung.hilum;
      // 呼気は受動的：流量は呼気の始めに最大で、時定数 tau で減り、tEnd で吐き終える
      this.tau = geo.exhale.tau; this.tEnd = geo.exhale.tEnd;
      this.exNorm = 1 - Math.exp(-this.tEnd / this.tau);
      // 吸収剤の層（入口側から）と容量
      const ab = geo.absorber;
      this.absRows = ab.rows; this.absCap = ab.cap; this.absSpread = ab.spread;
      this.absFresh = hexRGB(ab.fresh); this.absUsedC = hexRGB(ab.used);
      this.swaps = [];                                        // 吸収剤を交換した時刻（刻みの番号）
      // 吸収装置のバイパス（1.7.0）：開くと管 D の道が吸収装置を迂回する道（geo.bypass）に替わり、CO2 は除かれない。
      // 1.7.1：操作ページからは使っていない（著者の判断でボタンをなくし、図は閉じた姿だけ）。仕組みは残す
      // 開閉は刻みの番号で記録し（bypEvents）、巻き戻して再生しても同じ時刻に開閉する
      this.tubeD = { normal: this.tubes.D, bypass: geo.bypass ? new Poly(geo.bypass) : null };
      this.spcD0 = this.spc.D;
      this.bypEvents = []; this.bypass = false;
      this.tracked = null;                                    // 追跡中の粒の id
      this.trail = [];                                        // 追跡中の粒の足跡 [t, x, y]
      this.reset();
    }

    // ---------- 時刻 ----------
    get t() { return this.n * DT; }
    tc(t) { const c = this.CYC; return ((t % c) + c) % c; }

    /** 呼気開始から dt 秒で吐き出した割合（0〜1） */
    exhFrac(dt) {
      if (dt <= 0) return 0;
      if (dt >= this.tEnd) return 1;
      return (1 - Math.exp(-dt / this.tau)) / this.exNorm;
    }
    /** 呼気開始から dt 秒の呼気流量（粒/秒）。吐く量は、その呼吸で実際に肺胞へ入った粒の数（vtAct） */
    exRate(dt) {
      if (dt < 0 || dt >= this.tEnd) return 0;
      return this.vtAct * Math.exp(-dt / this.tau) / (this.tau * this.exNorm);
    }
    lungScale(tc) {
      const L = this.g.lung;
      return L.s0 + (L.s1 - L.s0) * (this.lungVol(tc) - this.g.LUNG_MIN) / this.VT;
    }

    /** 時刻 tc（周期内）の各管の流れの速さ（px/s、＋は管の向き）＝ 流量（粒/秒）× その管の粒の間隔 */
    flows(tc) {
      const s = this.spc;
      if (tc < this.TI) {
        return { A: (this.vb + this.FG) * s.A, B: (this.vb + this.FG) * s.B, C: 0, D: this.vb * s.D, E: -this.vb * s.E };
      }
      const ex = this.exRate(tc - this.TI);
      return { A: 0, B: -ex * s.B, C: ex * s.C, D: -this.FG * s.D, E: (ex + this.FG) * s.E };
    }

    plateTop(tc) {
      const { keyT, keyS, BBOT, BTOP } = this.g.bellows;
      for (let i = 0; i < keyT.length - 1; i++) {
        if (keyT[i] <= tc && tc <= keyT[i + 1]) {
          const v = keyT[i + 1] > keyT[i] ? keyS[i] + (keyS[i + 1] - keyS[i]) * (tc - keyT[i]) / (keyT[i + 1] - keyT[i]) : keyS[i + 1];
          return BBOT - v * (BBOT - BTOP);
        }
      }
      return BTOP;
    }

    // ---------- 席の位置 ----------
    bSlotXY(idx, tc) {
      if (this.manual) {                                    // 呼吸バッグ：差し込み口を中心に、バッグの大きさに合わせて動く
        const [x, y] = this.bSlotDef[idx], [px, py] = this.g.bag.pivot, b = this.g.bag;
        const sc = interp(b.keyT, b.keyS, tc === undefined ? this.tc(this.t) : tc);
        return [px + (x - px) * sc, py + (y - py) * sc];
      }
      const { HXc, BBOT } = this.g.bellows;
      const [c, r] = this.bSlotDef[idx];
      const top = this.plateTop(tc) + 6;
      const h = Math.max(0, (BBOT - 5) - top);
      return [HXc + (c - 1) * 12, (BBOT - 5) - h * (r + 0.5) / 5];
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
      this.bSlots = new Array(this.bSlotDef.length).fill(null);   // 粒の id または null
      this.lSlots = new Array(this.lSlotDef.length).fill(null);
      this.relB = []; this.relL = [];                               // 部屋から出る粒が口に着く予定時刻
      this.planned = { i: false, e: false };                        // 次の場面の予定を組み済みか
      this.vtAct = this.VT;                                         // この呼吸で吐く量（粒）＝吸った量
      this.absUse = new Array(this.absRows.length).fill(0);        // 吸収剤の層ごとの使用率（0〜1）
      this.absorbed = 0;                                            // 時刻 0 から吸収した CO2 の粒の数
      this.lastPhase = null;
      this.checkpoints = new Map();
      this.trail = [];
      const t0 = -WARM_CYCLES * this.CYC;
      this.n = Math.round(t0 / DT);
      // 管に粒を敷く
      const co2Init = { A: () => false, B: () => true, C: () => true, E: () => true, D: s => s < g.absD[1] };   // B（気管）は吸気の始めには呼気が残っている
      for (const nm of TUBES) {
        const L = this.tubes[nm].L, sp = this.spc[nm], n = Math.floor(L / sp);
        for (let i = 0; i < n; i++) {
          const s = (i + 0.5) * sp;
          this.add({ st: "tube", tube: nm, s, co2: co2Init[nm](s) });
        }
      }
      for (let i = 0; i < g.NB_FULL; i++) {
        const p = this.add({ st: "slot", store: "b", slot: i, co2: true });
        this.bSlots[i] = p.id;
      }
      for (let i = 0; i < g.LUNG_MIN; i++) {
        const idx = this.pickLungEntry();
        const p = this.add({ st: "slot", store: "l", slot: idx, co2: true });
        this.lSlots[idx] = p.id;
      }
      // 供給路：到着時刻 k/FG の粒。開始時点で供給路の中にいる粒も含めて出す
      const Lmax = Math.max(...this.supply.map(p => p.L));
      this.setNextKs((t0 - Lmax / g.SUP_V) * this.FG);
      this.spawnSupply();
      // 開始時刻 0 まで回す
      while (this.n < 0) this.step();
      this.saveCheckpoint();
    }

    // ---------- 供給路 ----------
    spawnTime(k) {
      // 出発時刻は、そのガスのバイパスの経路の長さで決める（1.3.1：気化室を通る粒の経路は 44 px 長いが、その長さで出発を早めると、
      // 合流より手前の共有の管で粒の間隔が 44・88・132 px と乱れる（本人の指摘）。気化室を通る粒は合流点に 0.5 秒遅れて着く）
      return (k + (this.g.supplyPhase || 0)) / this.FG - this.supply[(k & 1) ? 1 : 2].L / this.g.SUP_V;   // supplyPhase：到着時刻を流れの切り替わりからずらす
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

    // ---------- 席の選び方（決定的な擬似乱数） ----------
    pickBellowsEntry() {
      const free = [];
      this.bSlots.forEach((v, i) => { if (v === null) free.push(i); });
      if (!free.length) return -1;
      return this.pickWeighted(free, i => this.storeWeight(i));                     // ベローズは底、バッグは口に近い席ほど入りやすい
    }
    pickBellowsExit() {
      const occ = [];
      this.bSlots.forEach((v, i) => { if (v !== null && this.byId.get(v).st === "slot") occ.push(i); });
      if (!occ.length) return -1;
      return this.pickWeighted(occ, i => this.storeWeight(i));                      // 同じく出やすい
    }
    storeWeight(i) {
      if (!this.manual) return 1 / (this.bSlotDef[i][1] + 1);
      const [x, y] = this.bSlotDef[i], [mx, my] = this.g.nodes.BAGM;
      return 1 / (Math.hypot(x - mx, y - my) + 15);
    }
    /** ベローズ（バッグ）の口から席までの道 */
    storePath(idx, tc) {
      const g = this.g;
      return this.manual ? [g.nodes.VP, g.nodes.BAGM, this.bSlotXY(idx, tc)]
                         : [g.nodes.VP, [g.bellows.HXc, g.bellows.BBOT - 3], this.bSlotXY(idx, tc)];
    }
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
      return this.pickWeighted(occ, i => Math.pow(this.byId.get(this.lSlots[i]).age + 1, 2));   // 古い粒ほど出やすい
    }

    // ---------- 管の出入り ----------
    /** 管 nm の弧長 s に入る。粒はいつも管の中心線の上（近すぎる粒は step() の均しで離れる） */
    enterTube(p, nm, s) {
      p.st = "tube"; p.tube = nm; p.s = s;
      delete p.path; delete p.dest;
    }
    bellowsCount() { return this.bSlots.reduce((n, v) => n + (v !== null ? 1 : 0), 0); }
    lungCount() { return this.lSlots.reduce((n, v) => n + (v !== null ? 1 : 0), 0); }

    exitFar(p, over, F) {
      const g = this.g, tc = this.tc(this.t);
      switch (p.tube) {
        case "A": this.enterTube(p, "B", over); break;
        case "B": {                                       // 肺へ
          const idx = this.pickLungEntry();
          if (idx < 0) { p.s = this.tubes.B.L; break; }
          this.lSlots[idx] = p.id;
          p.co2 = true;
          const path = [g.nodes.LG, this.lSlotXY(idx)];
          this.startTransit(p, path, Math.max(Math.abs(F.B), 60), { type: "slot", store: "l", slot: idx });
          break;
        }
        case "C": this.enterTube(p, "E", over); break;              // 呼気の流れ
        case "D": this.enterTube(p, "A", over); break;          // 回路の入口へ
        case "E": {                                       // 人工呼吸器の口：ベローズへ、満杯なら余剰ガス弁へ
          if (this.bellowsCount() < g.NB_FULL) {
            const idx = this.pickBellowsEntry();
            this.bSlots[idx] = p.id;
            this.startTransit(p, this.storePath(idx, tc), Math.max(Math.abs(F.E), 60), { type: "slot", store: "b", slot: idx });
          } else {
            p.st = "scav"; p.s = over * (g.SCAV_V / Math.max(F.E, 1));
          }
          break;
        }
      }
    }
    exitNear(p, over) {
      switch (p.tube) {
        case "B": this.enterTube(p, "C", over); break;
        case "D": this.enterTube(p, "E", over); break;         // 逆流してきた新鮮ガス
        case "E": this.enterTube(p, "D", over); break;         // 吸収装置へ
      }
    }

    /** 管 nm の遠い端（s=L）の空き。いまの速さが dt 秒続くとして、そのときの最後の粒から端までの距離。
     *  端を越えて出ていく粒は除く。粒がなければ Infinity */
    farGapAt(nm, dt) {
      const v = this.flows(this.tc(this.t))[nm], L = this.tubes[nm].L;
      let smax = -Infinity, leaving = 0;
      for (const p of this.particles) if (p.st === "tube" && p.tube === nm) {
        const s = p.s + v * dt;
        if (s > L) leaving++; else if (s > smax) smax = s;
      }
      return { gap: smax === -Infinity ? Infinity : L - smax, leaving };
    }
    /** 部屋から出る粒の予定（口に着く時刻の列）。最初の粒は管の遠い端の空き gap0 をちょうど埋める時刻に着き、
     *  あとは管の中の間隔 SP ごと。管の進みは、ベローズ側は定常流、肺胞側は受動的な呼気の曲線に従う */
    /** 放出の数は「その場面で管が進む距離 D に乗るスロットの数」で決める（部屋の個数ではなく）。
     *  流入の数え方（端を越えた瞬間）と同じ基準にして、部屋の収支がずれないようにする。nAvail は出せる上限 */
    planCount(sp, D, gap0, nAvail) {
      const V1 = Math.max(0, sp - Math.min(gap0, sp));
      const nDisp = Math.floor((D - V1) / sp + 1e-9) + 1;        // ちょうど端に着く粒も数える（吸気の流入の数え方と合わせ、収支を保つ）
      return { V1, n: Math.max(0, Math.min(nAvail, nDisp)) };
    }
    planBellows(tPhase, gap0, nAvail) {
      const sp = this.spc.E, v = this.vb * sp, out = [];
      const { V1, n } = this.planCount(sp, v * this.TI, gap0, nAvail);
      for (let k = 1; k <= n; k++) out.push(tPhase + (V1 + (k - 1) * sp) / v + DT);
      return out;
    }
    /** 肺胞の放出：吐く量（管の進む距離）は、吸った粒の数 nIn × 間隔。吸った量をそのまま吐く（体積の保存） */
    planLung(tPhase, gap0, nIn) {
      const sp = this.spc.B, out = [];
      this.vtAct = Math.max(1, nIn);
      const D = this.vtAct * sp;
      const { V1, n } = this.planCount(sp, D, gap0, nIn);
      for (let k = 1; k <= n; k++) {
        const f = (V1 + (k - 1) * sp) / D;                                    // 吐き出す量の割合
        const dt = f >= 1 ? this.tEnd : -this.tau * Math.log(1 - f * this.exNorm);
        out.push(tPhase + dt + DT);
      }
      return out;
    }
    /** 場面の切り替わりの LEAD 秒前に、次の場面の放出の予定を組む（端の空きと部屋の個数は切り替わり時点の値を予測） */
    planAhead(ph, tc) {
      const g = this.g;
      if (ph === "i" && !this.planned.e && tc >= this.TI - LEAD) {
        const dt = this.TI - tc, tPhase = this.t + dt;
        const { gap, leaving } = this.farGapAt("B", dt);          // 吸気の終わりまでに肺胞へ入る粒も数える
        const n = Math.max(0, this.lungCount() + leaving - g.LUNG_MIN);
        this.relL = this.planLung(tPhase, gap, n); this.planned.e = true;
      }
      if (ph === "e" && !this.planned.i && tc >= this.CYC - LEAD) {
        const dt = this.CYC - tc, tPhase = this.t + dt;
        const { gap, leaving } = this.farGapAt("E", dt);
        const n = Math.max(0, Math.min(g.NB_FULL, this.bellowsCount() + leaving) - g.NB_MIN);
        this.relB = this.planBellows(tPhase, gap, n); this.planned.i = true;
      }
    }
    /** 場面の始め：予定が組まれていなければ（開始直後など）その場で組む */
    scheduleReleases(ph, tPhase) {
      const g = this.g;
      if (ph === "i") {
        if (!this.planned.i) this.relB = this.planBellows(tPhase, this.farGapAt("E", 0).gap, Math.max(0, this.bellowsCount() - g.NB_MIN));
        this.planned.i = false;
      } else {
        if (!this.planned.e) this.relL = this.planLung(tPhase, this.farGapAt("B", 0).gap, Math.max(0, this.lungCount() - g.LUNG_MIN));
        this.planned.e = false;
      }
    }
    /** 口に着く予定時刻 tArr に合わせて、部屋の粒を 1 個、口へ向かわせる（着く時刻から逆算した速さで動く） */
    releaseBellows(tArr) {
      const g = this.g, tc = this.tc(this.t);
      const idx = this.pickBellowsExit();
      if (idx < 0) return false;
      const p = this.byId.get(this.bSlots[idx]);
      this.bSlots[idx] = null;
      const path = this.storePath(idx, tc).reverse();
      const speed = pathLen(path) / Math.max(tArr - this.t, MIN_TRIP);
      this.startTransit(p, path, speed, { type: "tube", tube: "E", far: true });
      return true;
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
      if (ph !== this.lastPhase) {                           // 場面の切り替わり
        const tPhase = t - (ph === "i" ? tc : tc - this.TI);
        this.scheduleReleases(ph, tPhase);
        for (const p of this.particles) if (p.st === "slot" && p.store === (ph === "i" ? "b" : "l")) p.age++;
        this.lastPhase = ph;
      }
      this.planAhead(ph, tc);
      // 管の粒：流れに乗って進み、管の端を越えたら次へ
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
            if (ph === "i") this.enterTube(p, "A", over);                      // 新鮮ガス
            else this.enterTube(p, "D", this.tubes.D.L - over);               // 呼気中は吸収装置側へ逆流
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
      // 管の中の圧の均し：流れが切り替わる瞬間に管の端で粒が重なると、その塊（並んだ 2〜3 個）は
      // 押し出し流れのまま回路を回り続ける。実際のガスは 1 か所だけ濃いままではいられないので、
      // 近すぎる粒どうしをゆっくり離す（管の端は越えない）
      for (const nm of TUBES) {
        const arr = this.particles.filter(p => p.st === "tube" && p.tube === nm).sort((a, b) => a.s - b.s);
        const dmin = RELAX_MIN * this.spc[nm], L = this.tubes[nm].L, mv = RELAX_V * DT;
        for (let i = 1; i < arr.length; i++) {
          const a = arr[i - 1], b = arr[i], d = b.s - a.s;
          if (d < dmin) { const m = Math.min(mv, (dmin - d) / 2); a.s = Math.max(0, a.s - m); b.s = Math.min(L, b.s + m); }
        }
      }
      // ベローズが送り出す／肺が吐き出す：予定時刻の LEAD 秒前に席を立ち、予定時刻に口に着く
      while (this.relB.length && t >= this.relB[0] - LEAD) { const tr = this.relB.shift(); this.releaseBellows(tr); }
      while (this.relL.length && t >= this.relL[0] - LEAD) { const tr = this.relL.shift(); this.releaseLung(tr); }
      // 吸収装置：CO2 を含む粒が吸収剤の層に入ると、まだ使える吸収剤があれば CO2 が除かれる。
      // 吸収に使われるのは、入口から数えて最初のまだ使える層（使用済みの層を抜けた先の吸収剤）
      const rows = this.absRows, sLo = rows[0][0], sHi = rows[rows.length - 1][1];
      for (const p of this.particles) {
        if (this.bypass) break;                          // バイパス中：粒は吸収剤を通らない（1.7.0）
        if (p.st !== "tube" || p.tube !== "D" || !p.co2 || p.s < sLo || p.s >= sHi) continue;
        const k = this.absUse.findIndex(u => u < 1 - 1e-9);
        if (k < 0) continue;                             // 全層を使い切った：CO2 は除かれない
        p.co2 = false;
        if (this.n >= 0) this.absorb(k);                 // 開始前の慣らし運転では吸収剤を減らさない
      }
      this.n++;
      if (this.swaps.includes(this.n)) this.absUse.fill(0);
      for (const e of this.bypEvents) if (e.n === this.n) this.applyBypass(e.on, true);   // 記録した時刻でバイパスを開閉（再生時）
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
        case "slot": return p.store === "b" ? this.bSlotXY(p.slot, tc) : this.lSlotXY(p.slot, tc);
        case "trans": {
          const path = p.path.slice();
          if (p.dest.type === "slot") path[path.length - 1] = p.dest.store === "b" ? this.bSlotXY(p.dest.slot, tc) : this.lSlotXY(p.dest.slot, tc);
          return along(path, p.u / p.pathL);
        }
      }
      return [0, 0];
    }

    // ---------- 吸収装置のバイパス（1.7.0） ----------
    /** いまの時刻でバイパスを開く／閉じる（記録して、巻き戻し後の再生でも同じ時刻に開閉する） */
    setBypass(on) {
      if (!this.tubeD.bypass || on === this.bypass) return;
      this.bypEvents = this.bypEvents.filter(e => e.n !== this.n + 1);
      this.bypEvents.push({ n: this.n + 1, on });      // 次の刻みで切り替える（step の中で applyBypass が呼ばれる）
      for (const k of [...this.checkpoints.keys()]) if (k * this.STEPS_PER_CYC > this.n) this.checkpoints.delete(k);
    }
    /** 管 D の道を切り替える。rescale のときは D の粒の位置を道の長さの比で合わせる（復元のときは粒の位置がその道のものなので合わせない） */
    applyBypass(on, rescale) {
      const to = on ? this.tubeD.bypass : this.tubeD.normal;
      if (!to) return;
      if (rescale && to !== this.tubes.D) { const k = to.L / this.tubes.D.L; for (const p of this.particles) if (p.st === "tube" && p.tube === "D") p.s *= k; }
      this.tubes.D = to; this.spc.D = this.spcD0 * to.L / this.tubeD.normal.L; this.bypass = on;
    }
    /** 刻み n の時点でバイパスが開いているか（記録から） */
    bypassAt(n) { let on = false; for (const e of this.bypEvents) if (e.n <= n) on = e.on; return on; }
    /** 刻み n0 より後の保存点を捨て、いまが n0 以降ならその前の保存点に戻す（次の seek で記録どおりに進め直す） */
    _resetFrom(n0) {
      for (const k of [...this.checkpoints.keys()]) if (k * this.STEPS_PER_CYC >= n0) this.checkpoints.delete(k);
      if (this.n < n0) return;
      let kk = null;
      for (const k of this.checkpoints.keys()) if (k * this.STEPS_PER_CYC < n0 && (kk === null || k > kk)) kk = k;
      if (kk !== null) { this.restore(this.checkpoints.get(kk)); this.trail = []; }
    }
    /** 時刻（秒）を決めて開閉を予約する（1.7.4、見どころの段）。plan = [[時刻, 開くか], ...]。一時停止・速さ・巻き戻しに関係なく同じ時刻に開閉する */
    scheduleBypass(plan) {
      if (!this.tubeD.bypass) return;
      this.clearBypass();
      this.bypEvents = plan.map(([T, on]) => ({ n: Math.floor(T / DT + 1e-6) + 1, on }));
      this._resetFrom(Math.min(...this.bypEvents.map(e => e.n)));
    }
    /** 開閉の記録をすべて消して、閉じた回路に戻す */
    clearBypass() {
      if (!this.bypEvents.length) return;
      const n0 = Math.min(...this.bypEvents.map(e => e.n));
      this.bypEvents = [];
      this._resetFrom(n0);
      this.applyBypass(false, false);
    }

    // ---------- 保存と巻き戻し ----------
    snapshot() {
      return JSON.stringify({
        n: this.n, rng: this.rng.state, nextId: this.nextId, nextKs: this.nextKs,
        relB: this.relB, relL: this.relL, lastPhase: this.lastPhase, planned: this.planned, vtAct: this.vtAct,
        absUse: this.absUse, absorbed: this.absorbed,
        bSlots: this.bSlots, lSlots: this.lSlots, particles: this.particles,
      });
    }
    restore(snap) {
      const o = JSON.parse(snap);
      this.n = o.n; this.rng.state = o.rng; this.nextId = o.nextId; this.nextKs = o.nextKs;
      this.relB = o.relB; this.relL = o.relL; this.lastPhase = o.lastPhase; this.planned = o.planned; this.vtAct = o.vtAct;
      this.absUse = o.absUse; this.absorbed = o.absorbed;
      this.bSlots = o.bSlots; this.lSlots = o.lSlots;
      this.particles = o.particles;
      this.byId = new Map(this.particles.map(p => [p.id, p]));
      if (this.tubeD) this.applyBypass(this.bypassAt(this.n), false);   // その時刻の道に戻す（1.7.0）
    }
    /** 時刻 T（秒、0 以上）の状態にする */
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
    /** SVG の <g> に粒を描く。要素は使い回す */
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
    /** 吸収剤の粒を使用率に合わせて塗る（未使用：白 → 使い切り：紫）。前線の層では粒ごとに少しずらす */
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
      const where = { tube: inAbs ? T.inAbs : { A: T.A, B: T.B, C: T.C, D: T.D, E: this.manual ? T.Ebag : T.Event }[p.tube],
        sup: T.sup, scav: T.scav, slot: p.store === "b" ? (this.manual ? T.bag : T.bellows) : T.lung, trans: T.trans }[p.st];
      return T.fmt(p.kind === "O2" ? "O₂" : "N₂O", p.id, p.co2, where);
    }
  }

  window.BellowsSim = BellowsSim;
})();
