// SPDX-License-Identifier: MIT
// CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
// 1 つの場面の粒の動きを点検する（ブラウザなしで Node.js で動かす）。
// 使い方: node tests/check.js build/bellows.json
//  - 回路の外：管・供給路・余剰ガスの粒が、その経路から 5 px より離れた回数（0 であること）
//  - 巻き戻し：ある時刻へ進めた状態と、いったん戻ってから同じ時刻へ進めた状態が同じか（true であること）
//  - 1 回換気量：1 呼吸ごとに肺胞へ入った粒の数（30 呼吸の平均・最小・最大）
//  - 吸収剤：全層を使い切った呼吸（300 呼吸まで）
"use strict";
const fs = require("fs");
const path = require("path");
global.window = global;
global.document = { createElementNS: () => ({ setAttribute() {}, style: {}, dataset: {}, appendChild() {}, insertBefore() {} }) };
const src = path.join(__dirname, "..", "src");
eval(fs.readFileSync(path.join(src, "sim_common.js"), "utf8"));
eval(fs.readFileSync(path.join(src, "sim_bellows.js"), "utf8"));
eval(fs.readFileSync(path.join(src, "sim_piston.js"), "utf8"));

const file = process.argv[2];
const geo = JSON.parse(fs.readFileSync(file, "utf8"));
const make = () => (geo.kind === "piston" ? new PistonSim(geo, 7) : new BellowsSim(geo, 7));
const CYC = geo.CYC;

// 回路の外
const dist = (x, y, pts) => {
  let b = Infinity;
  for (let i = 1; i < pts.length; i++) {
    const [ax, ay] = pts[i - 1], [bx, by] = pts[i], dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy;
    const u = L2 ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / L2)) : 0;
    b = Math.min(b, Math.hypot(x - (ax + u * dx), y - (ay + u * dy)));
  }
  return b;
};
let sim = make(), outside = 0;
for (let k = 0; k <= 120; k++) {
  sim.seek(12 * CYC + k * 0.05);
  for (const p of sim.particles) {
    if (p.st !== "tube" && p.st !== "sup" && p.st !== "scav") continue;
    const pts = p.st === "tube" ? geo.tubes[p.tube] : p.st === "sup" ? geo.supply[p.sup] : geo.tubes.S;
    const [x, y] = sim.xy(p);
    if (dist(x, y, pts) > 5) outside++;
  }
}

// 巻き戻し
const state = () => JSON.stringify(sim.particles.map(p => [p.id, ...sim.xy(p).map(v => v.toFixed(1))]));
sim.seek(30.5 * CYC); const a = state();
sim.seek(3); sim.seek(30.5 * CYC); const rewind = a === state();

// 1 回換気量（肺胞へ入った粒の数）
sim = make();
let inL = 0;
const exitFar = sim.exitFar.bind(sim);
sim.exitFar = (p, over, F) => { if (p.tube === "B") inL++; exitFar(p, over, F); };
const vts = [];
for (let c = 1; c <= 30; c++) { inL = 0; sim.seek(c * CYC); vts.push(inL); }
const mean = vts.reduce((s, v) => s + v, 0) / vts.length;

// 吸収剤
let full = null;
for (let c = 1; c <= 300 && full === null; c++) { sim.seek(c * CYC); if (sim.absUsed() >= 0.999) full = c; }

const ok = outside === 0 && rewind;
console.log(`${path.basename(file, ".json").padEnd(14)} 回路の外 ${outside}  巻き戻し ${rewind}  ` +
            `1回換気量 平均 ${mean.toFixed(2)}（${Math.min(...vts)}〜${Math.max(...vts)}）  ` +
            `吸収剤を使い切る呼吸 ${full === null ? "300 呼吸までに使い切らない" : full}  ${ok ? "OK" : "NG"}`);
process.exitCode = ok ? 0 : 1;
