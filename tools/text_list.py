# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""できあがったページ（index.html）から、画面に出る解説文をすべて取り出して、確認用の一覧（Markdown）を作る。
使い方: python3 tools/text_list.py index.html 一覧.md
文を手で写さないので、一覧とページの文は必ず同じになる。解説文を直したら作り直す（書き込み済みの一覧は上書きしないこと）。
必要なもの：Node.js（ページの中の JavaScript のオブジェクトをそのまま読むため）"""
import json
import subprocess
import sys

JS = r"""
const fs = require("fs");
const html = fs.readFileSync(process.argv[1], "utf8");
const grab = re => { const m = html.match(re); if (!m) throw new Error("not found " + re); return m[0]; };
const ev = (src, name) => eval("(" + src.replace(new RegExp("^const " + name + " = "), "").replace(/;$/, "") + ")");
const out = {
  TERMS: ev(grab(/const TERMS = \{[\s\S]*?\n\};/), "TERMS"),
  TERM_ORDER: ev(grab(/const TERM_ORDER = \[[\s\S]*?\];/), "TERM_ORDER"),
  PHASES: ev(grab(/const L = \{[\s\S]*?\n\};/), "L").phases,          // 場面の説明と使い切りの文は L の中（2026-11-04：ページの構造に合わせた）
  exh: ev(grab(/const L = \{[\s\S]*?\n\};/), "L").exhausted,
  steps: [...grab(/const STEPS = \[[\s\S]*?\n    \];/).matchAll(/txt: '([^']+)'/g)].map(m => m[1].replace(/<[^>]+>/g, "")),
};
console.log(JSON.stringify(out));
"""

# 書いた側として根拠が弱い・言い方に迷った点（確認してほしい点）
FLAG = {
    "pipeline": "識別色（O₂ 緑・空気 黄・N₂O 青）と「差し込み口の形がガスごとに違う」は日本の配管端末器の規格どおりか。",
    "cylinder": "空気のボンベも「灰色」でよいか（医療用ボンベの色帯などを書き足すべきか）。",
    "regulator": "「配管より少し低い圧にするので、配管のガスが先に使われる」は米国の機種の説明（配管 50 psi・ボンベ側 45 psi）に基づく。日本の機種・規格でも同じ説明でよいか。",
    "n2ocut": "実機には、O₂ の圧に比例して N₂O を減らす型もある。また、この装置だけでは低酸素の混合ガスを完全には防げない（それは流量計の比率制御の役目）。どこまで書くか。",
    "flowmeter": "「目盛りはフロートの上の面で読む」はボビン形の場合。球形のフロートは中心で読む。注記するか。",
    "flush": "流量「毎分 35〜75 L ほど」の数字（規格により 25〜75 L/分 とするものもある）。",
    "patient": "「吸気の始めには、気管に残っていた前の呼気がまず肺胞へ戻る」の言い方（死腔の再吸入）。",
    "peep": "2026-11-02 に差し替えた。「吸気中は閉じている」「PEEP を保ち、ピストンが肺からガスを引き込むのを防ぐ」は Miller 10e 図 20.44・20.45 の説明どおり。「回路の圧が Pmax を超えたときだけ開く」は弁の名前と仕組みからの推測で、Miller の本文にはない（Dräger の技術資料で要確認）。実機の開く圧は電子制御で、図の「ばね」は模式化。",
    "bellows": "「回路にもれがあると上がりきらないので、気づきやすい」の言い方。",
    "spill": "「開くのに 2〜3 cmH₂O」の数字（「くわしく」の比較表と同じ値）。",
    "bypass": "2026-11-02 に図に描き足した部品。「人工呼吸中は開き、余ったガスは排気の逆止弁を通って排出装置へ」「用手・自発呼吸では閉じて APL 弁が働く」は Miller 10e 図 20.44 の説明どおり。図では弁板を下の操作部の棒で動かす形にしたが、実機の開閉の仕組み（空気圧か電気か）は確かめていない。",
    "exhaust": "2026-11-02 に図に描き足した部品。Miller は名前（exhaust check valve）と「バイパス弁を通ったガスがここを通って排出装置へ」としか書いていない。APL 弁とバイパス弁の合流のあとに置いたこと、用手換気で APL 弁のガスもここを通ることは、図にするための推測。",
}
FAM = {"bellows": "上昇式ベローズ", "piston": "ピストン式", "reflector": "ボリュームリフレクタ式"}
SCENE = {"bellows": "上昇式ベローズ・人工呼吸", "piston": "ピストン式・人工呼吸", "reflector": "ボリュームリフレクタ式・人工呼吸",
         "bellowsMan": "上昇式ベローズ・用手換気", "pistonMan": "ピストン式・用手換気", "reflectorMan": "ボリュームリフレクタ式・用手換気"}


def main(page, out):
    d = json.loads(subprocess.run(["node", "-e", JS, page], capture_output=True, text=True, check=True).stdout)
    T, order = d["TERMS"], d["TERM_ORDER"]
    num = {k: i + 1 for i, k in enumerate(order)}
    L = ["# CircleFlow 解説文の一覧（確認用）\n",
         "CircleFlow のページで、部品の名前や時刻のバーを押したときに出る解説文を、すべて書き出したものです（`tools/text_list.py` でページから自動で取り出しました。図の中の文字と、動画用の字幕は含みません）。\n",
         "**書いた人**：Claude（朝元の指示で作成）。2026-11-04 までの内容は専門家の確認済み。それ以降に追加・変更した文（ボリュームリフレクタ式、実機化に伴う修正）が確認の対象。\n",
         "**確認のしかた**：各項目の「□ 確認」に印を付け、直したいところは「修正：」の後に書いてください。書き込んだこのファイルを渡してもらえれば、ページに反映します。\n",
         "**書き方の方針**：初めて学ぶ人向けに、1 項目 2〜3 文。仕組みを形と動きで見せる図に添える文なので、図で見えることは短く、見えないこと（なぜそうなっているか）を書いています。\n",
         "**更新**：2026-11-02 作成。同日、PEEP/Pmax 弁の解説を差し替え、ピストン式に APL バイパス弁と排気逆止弁を描き足して解説を追加、APL 弁（ピストン式）の解説を直した。2026-11-04、ボリュームリフレクタ式（3 方式・12 場面）に対応し、上昇式ベローズの安全性の言い方・APL 弁が開く条件・リフレクタガスが患者に届かない条件を直した。\n",
         "## 1. 特に確かめてほしい点\n", "書いた側として、根拠が弱い・言い方に迷った点です。"]
    L += [f"- **{T[k]['name']}**（2-{num[k]}）：{FLAG[k]}" for k in order if k in FLAG]
    L += ["", f"## 2. 部品の解説（{len(order)} 件、ガスの流れの順）\n",
          "部品の名前（図の中で点線の下線が付いた文字）をクリックすると、その部品へ拡大して出る文です。「前へ・次へ」もこの順に回ります。\n"]
    for k in order:
        t = T[k]
        fams = [FAM[f] for f in FAM if t["rect"] and t["rect"].get(f)]
        L.append(f"### 2-{num[k]}. {t['name']}\n")
        L.append(f"- 出る図：{'・'.join(fams)}　／　押せる文字：{'、'.join('「' + w + '」' for w in t['words'])}")
        if isinstance(t["text"], str):
            L.append(f"\n> {t['text']}\n")
        else:
            for f in FAM:
                if f in t["text"]:
                    L.append(f"\n**{FAM[f]}**\n\n> {t['text'][f]}\n")
        if k in FLAG:
            L.append(f"- ⚠ {FLAG[k]}")
        L.append("- □ 確認　修正：\n")
    L += ["## 3. 粒の凡例と、吸収剤を使い切ったとき\n",
          "### 3-1. ガスの粒（図の下の凡例「CO₂ を含まないガス」「CO₂ を含むガス」を押したとき）\n",
          f"> {T['particles']['text']}\n\n- □ 確認　修正：\n",
          "### 3-2. 吸収剤を使い切ったとき（「使い切り」になったメーターを押したとき。場面により 2 通り）\n",
          f"**吸気側に CO₂ が戻っている場面**\n\n> {d['exh'][0]}\n",
          f"**吸気側にほとんど戻らない場面**\n\n> {d['exh'][1]}\n\n- □ 確認　修正：\n",
          "## 4. 場面の説明（吸気・呼気のバーを押して止めたとき）\n"]
    for k in SCENE:
        L.append(f"### 4. {SCENE[k]}（新鮮ガスの多め・低流量で共通）\n")
        L += [f"- **{lab}**（{a:g}〜{b:g} 秒）：{txt}" for lab, a, b, kind, txt in d["PHASES"][k]]
        L.append("- □ 確認　修正：\n")
    L += ["## 5. 使い方（ツアー）の 9 段階\n", "「使い方」ボタンで、指が操作する場所へ動きながら出る文です。\n"]
    L += [f"{i}. {s}" for i, s in enumerate(d["steps"], 1)]
    L += ["\n- □ 確認　修正：\n", "## 6. この一覧に入れていない文\n",
          "- 「くわしく」の中の説明（3 つの方式の比較表・設計の考え方・用手換気・吸収剤）",
          "- 図の中の部品の名前と、動画用の字幕（`?t=` で開いたコマに出る 1 行）：生成スクリプト `src/figure_bellows.py`・`src/figure_piston.py`・`src/figure_reflector.py` にあります"]
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
