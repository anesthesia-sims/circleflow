#!/bin/sh
# SPDX-License-Identifier: MIT
# CircleFlow の 10 の場面（上昇式ベローズ・ピストン式：新鮮ガス 多め・低流量 × 人工呼吸・用手換気、ボリュームリフレクタ式：多め・低流量）の図と経路データを作り、
# 日本語のページ index.html と英語のページ en/index.html にまとめる。必要なもの：Python 3（標準ライブラリだけ）
set -e
cd "$(dirname "$0")"
mkdir -p build/ja build/en en

scene() {   # scene 言語 名前 生成スクリプト [low] [manual]
  lang=$1; name=$2; gen=$3; shift 3
  python3 "src/$gen" "build/$lang/$name.svg" color "build/$lang/$name.json" $( [ "$lang" = en ] && echo en ) "$@"
}
for lang in ja en; do
  scene $lang bellows       figure_bellows.py
  scene $lang bellowsLow    figure_bellows.py low
  scene $lang bellowsMan    figure_bellows.py manual
  scene $lang bellowsLowMan figure_bellows.py low manual
  scene $lang piston        figure_piston.py
  scene $lang pistonLow     figure_piston.py low
  scene $lang pistonMan     figure_piston.py manual
  scene $lang pistonLowMan  figure_piston.py low manual
  scene $lang reflector     figure_reflector.py
  scene $lang reflectorLow  figure_reflector.py low
done

args() {    # args 言語：8 つの場面の「名前 svg 経路データ」
  for name in bellows bellowsLow bellowsMan bellowsLowMan piston pistonLow pistonMan pistonLowMan reflector reflectorLow; do
    printf '%s build/%s/%s.svg build/%s/%s.json ' "$name" "$1" "$name" "$1" "$name"
  done
}
SIMS="src/sim_common.js src/sim_bellows.js src/sim_piston.js src/sim_reflector.js"
# 公開する URL（GitHub Pages）。言語版どうしの印（hreflang）に使う
URL=https://anesthesia-sims.github.io/circleflow/
python3 src/build_page.py --other en/ --href-ja $URL --href-en ${URL}en/ index.html $SIMS $(args ja)
python3 src/build_page.py --lang en --other ../ --href-ja $URL --href-en ${URL}en/ en/index.html $SIMS $(args en)
echo "index.html と en/index.html を作りました"
