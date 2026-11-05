// SPDX-License-Identifier: MIT
// CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
/* 粒のシミュレーションの共通部分（sim_bellows.js・sim_piston.js の前に読み込む）。
 *  - 乱数（決まった種から同じ列。巻き戻しのため状態を取り出せる）、折れ線上の位置、キー列の補間
 *  - 刻みなどの定数と、粒の色
 *  - SimBase：2 つの方式で同じメソッド（粒の出し入れ、重みつきの選択、部屋から口への移動、吸収剤、検査点、追跡）
 * window.CircleFlowSim に置き、各シミュレーションの先頭で取り出す */
(function () {
  "use strict";

  function mulberry32(a) {
    return {
      next() {
        a |= 0; a = (a + 0x6D2B79F5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      },
      get state() { return a; },
      set state(v) { a = v | 0; },
    };
  }

  class Poly {
    constructor(pts) {
      this.pts = pts;
      this.cum = [0];
      for (let i = 1; i < pts.length; i++) {
        const [ax, ay] = pts[i - 1], [bx, by] = pts[i];
        this.cum.push(this.cum[i - 1] + Math.hypot(bx - ax, by - ay));
      }
      this.L = this.cum[this.cum.length - 1];
    }
    xy(s) {
      s = Math.min(Math.max(s, 0), this.L);
      const c = this.cum, p = this.pts;
      let i = 1;
      while (i < c.length - 1 && s > c[i]) i++;
      const seg = c[i] - c[i - 1];
      const r = seg ? (s - c[i - 1]) / seg : 0;
      let x = p[i - 1][0] + (p[i][0] - p[i - 1][0]) * r, y = p[i - 1][1] + (p[i][1] - p[i - 1][1]) * r;
      return [x, y];
    }
  }

  function along(pts, u) {
    const lens = [];
    let total = 0;
    for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); lens.push(l); total += l; }
    let d = Math.min(Math.max(u, 0), 1) * total;
    for (let i = 0; i < lens.length; i++) {
      if (d <= lens[i] || i === lens.length - 1) {
        const r = lens[i] ? Math.min(d / lens[i], 1) : 0;
        return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r];
      }
      d -= lens[i];
    }
    return pts[pts.length - 1];
  }
  function pathLen(pts) {
    let t = 0;
    for (let i = 1; i < pts.length; i++) t += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    return t;
  }

  const DT = 1 / 120;                      // シミュレーションの刻み（秒）
  const WARM_CYCLES = 6;                   // 開始前に回しておく周期の数（定常状態に近づける）
  const LEAD = 0.35;                       // 部屋から出る粒が、口に着く時刻より前に動き始める時間（秒）
  const MIN_TRIP = 0.12;                   // 部屋から口までの移動にかける最短時間（秒）
  const RELAX_MIN = 0.5;                   // 同じ管の粒がこれ×間隔より近いと、少しずつ離す
  const RELAX_V = 60;                      // 離す速さ（px/秒）
  const C_FRESH = "#2b2b2b", C_CO2 = "#e8590c";   // CO2 を含む粒はオレンジ（2026-11-02。旧：紫）
  function hexRGB(h) { return [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)); }
  function interp(keyT, keyV, x) {
    for (let i = 0; i < keyT.length - 1; i++) {
      if (keyT[i] <= x && x <= keyT[i + 1]) {
        return keyT[i + 1] > keyT[i] ? keyV[i] + (keyV[i + 1] - keyV[i]) * (x - keyT[i]) / (keyT[i + 1] - keyT[i]) : keyV[i + 1];
      }
    }
    return keyV[keyV.length - 1];
  }

  // 粒の説明（追跡中の札）の文。英語版のページは window.SIM_TEXT で置き換える（2026-11-02）
  const SIM_TEXT_JA = {
    inAbs: "二酸化炭素吸収装置の中", A: "吸気側の管", B: "気管（死腔）", C: "呼気側の管", D: "吸収装置側の管",
    Ebag: "呼吸バッグ側の管", Event: "人工呼吸器側の管", F: "吸収装置側の管", G: "デカップリング弁側の管", P: "ピストンの口",
    H: "呼吸バッグ側の管", sup: "供給路", scav: "余剰ガス", bag: "呼吸バッグの中", bellows: "ベローズの中", lung: "肺胞の中",
    cyl: "ピストンのシリンダーの中", trans: "移動中", R: "ボリュームリフレクタの中", M: "ガスモジュールの管", reflGas: "リフレクタガス（O₂）",
    fmt: (gas, id, co2, where) => `${gas} として供給された粒 #${id}（${co2 ? "CO₂ を含む" : "CO₂ なし"}、${where}）`,
  };
  const simText = () => Object.assign({}, SIM_TEXT_JA, (typeof window !== "undefined" && window.SIM_TEXT) || {});

  /** 2 つの方式で同じ部分。方式ごとのクラス（BellowsSim・PistonSim）がこれを継承する */
  class SimBase {
    /** 時刻 tc（周期内）の肺胞の粒の数（連続値） */
    lungVol(tc) {
      return tc < this.TI ? this.g.LUNG_MIN + this.VT * tc / this.TI : this.g.LUNG_MIN + this.VT * (1 - this.exhFrac(tc - this.TI));
    }
    add(fields) {
      const p = Object.assign({ id: this.nextId++, kind: (this.nextId % 2) ? "O2" : "N2O", co2: false, age: 0 }, fields);
      this.particles.push(p);
      this.byId.set(p.id, p);
      return p;
    }
    remove(p) {
      const i = this.particles.indexOf(p);
      if (i >= 0) this.particles.splice(i, 1);
      this.byId.delete(p.id);
      if (this.tracked === p.id) { this.tracked = null; this.trail = []; }
    }
    pickWeighted(items, weightFn) {
      let total = 0;
      const ws = items.map(it => { const w = weightFn(it); total += w; return w; });
      let r = this.rng.next() * total;
      for (let i = 0; i < items.length; i++) { r -= ws[i]; if (r <= 0) return items[i]; }
      return items[items.length - 1];
    }
    startTransit(p, path, speed, dest) {
      p.st = "trans"; p.path = path; p.u = 0; p.speed = speed; p.dest = dest;
      p.pathL = pathLen(path);
    }
    /** 吸収剤全体の使用率（0〜1） */
    absUsed() { return this.absUse.reduce((a, b) => a + b, 0) / this.absUse.length; }
    /** 吸気側の管（吸収装置の出口〜Y ピース）にいる、CO2 を含む粒の数 */
    inspCO2() { return this.particles.filter(p => p.st === "tube" && p.tube === "A" && p.co2).length; }
    /** いまの時刻で吸収剤を新しいものに交換する（巻き戻して再生しても同じ時刻に交換される） */
    swapAbsorbent() {
      const n = this.n;
      if (!this.swaps.includes(n)) this.swaps.push(n);
      this.absUse.fill(0);
      for (const k of [...this.checkpoints.keys()]) {
        if (k * this.STEPS_PER_CYC > n) this.checkpoints.delete(k);
        else if (k * this.STEPS_PER_CYC === n) this.checkpoints.set(k, this.snapshot());
      }
    }
    saveCheckpoint() {
      const k = Math.round(this.n / this.STEPS_PER_CYC);
      if (this.checkpoints.has(k)) return;
      this.checkpoints.set(k, this.snapshot());
    }
    /** 図の座標 (x, y) にいちばん近い粒を追跡対象にする（遠ければ解除） */
    trackNear(x, y, maxDist) {
      let best = null, bd = (maxDist || 14);
      for (const p of this.particles) {
        const [px, py] = this.xy(p);
        const d = Math.hypot(px - x, py - y);
        if (d < bd) { bd = d; best = p; }
      }
      this.tracked = best ? best.id : null;
      this.trail = [];
      return best;
    }
  }

  window.CircleFlowSim = { mulberry32, Poly, along, pathLen, interp, hexRGB, DT, WARM_CYCLES, LEAD, MIN_TRIP, RELAX_MIN, RELAX_V, C_FRESH, C_CO2, simText, SimBase };
})();
