#!/bin/sh
# SPDX-License-Identifier: MIT
# CircleFlow の 8 つの場面（2 方式 × 新鮮ガス 多め・低流量 × 人工呼吸・用手換気）の図と経路データを作り、
# 日本語のページ index.html と英語のページ en/index.html にまとめる。必要なもの：Python 3（標準ライブラリだけ）
set -e
cd "$(dirname "$0")"
mkdir -p build/ja build/en en

scene() {   # scene 言語 名前 生成スクリプト [low] [manual]
  lang=$1; name=$2; gen=$3; shift 3
  python3 "src/$gen" "build/$lang/$name.svg" color "build/$lang/$name.json" $( [ "$lang" = en ] && echo en ) "$@"
}
for lang in ja en; do
  scene $lang bellows       make_anim_bellows3.py
  scene $lang bellowsLow    make_anim_bellows3.py low
  scene $lang bellowsMan    make_anim_bellows3.py manual
  scene $lang bellowsLowMan make_anim_bellows3.py low manual
  scene $lang piston        make_anim_piston2.py
  scene $lang pistonLow     make_anim_piston2.py low
  scene $lang pistonMan     make_anim_piston2.py manual
  scene $lang pistonLowMan  make_anim_piston2.py low manual
done

args() {    # args 言語：8 つの場面の「名前 svg 経路データ」
  for name in bellows bellowsLow bellowsMan bellowsLowMan piston pistonLow pistonMan pistonLowMan; do
    printf '%s build/%s/%s.svg build/%s/%s.json ' "$name" "$1" "$name" "$1" "$name"
  done
}
# 公開する URL（GitHub Pages）。言語版どうしの印（hreflang）に使う
URL=https://anesthesia-sims.github.io/circleflow/
python3 src/make_sim_page.py --other en/ --href-ja $URL --href-en ${URL}en/ index.html src/sim_bellows.js src/sim_piston.js $(args ja)
python3 src/make_sim_page.py --lang en --other ../ --href-ja $URL --href-en ${URL}en/ en/index.html src/sim_bellows.js src/sim_piston.js $(args en)
echo "index.html と en/index.html を作りました"
