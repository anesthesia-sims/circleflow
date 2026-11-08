#!/bin/sh
# SPDX-License-Identifier: MIT
# CircleFlow の 17 の場面（ベローズ式（上昇式）・ピストン式・ブロワ（タービン）式・ボリュームリフレクタ式：新鮮ガス 多め・低流量 × 人工呼吸・用手換気、リフレクタ式の人工呼吸だけ新鮮ガス「不足」）の図と経路データを作り、
# 日本語のページ index.html・英語のページ en/index.html・中国語（簡体字）のページ zh/index.html にまとめる。必要なもの：Python 3（標準ライブラリだけ）
set -e
cd "$(dirname "$0")"
mkdir -p build/ja build/en build/zh en zh

scene() {   # scene 言語 名前 生成スクリプト [low] [manual]
  lang=$1; name=$2; gen=$3; shift 3
  python3 "src/$gen" "build/$lang/$name.svg" color "build/$lang/$name.json" $( [ "$lang" != ja ] && echo "$lang" ) "$@"
}
for lang in ja en zh; do
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
  scene $lang reflectorShort figure_reflector.py short
  scene $lang reflectorMan    figure_reflector.py manual
  scene $lang reflectorLowMan figure_reflector.py low manual
  scene $lang blower        figure_blower.py
  scene $lang blowerLow     figure_blower.py low
  scene $lang blowerMan     figure_blower.py manual
  scene $lang blowerLowMan  figure_blower.py low manual
done

args() {    # args 言語：17 の場面の「名前 svg 経路データ」
  for name in bellows bellowsLow bellowsMan bellowsLowMan piston pistonLow pistonMan pistonLowMan reflector reflectorLow reflectorShort reflectorMan reflectorLowMan blower blowerLow blowerMan blowerLowMan; do
    printf '%s build/%s/%s.svg build/%s/%s.json ' "$name" "$1" "$name" "$1" "$name"
  done
}
# 閲覧数の計測（Cloudflare Web Analytics、cookie なし）のサイトのトークン（ページに載る公開の値）。CIRCLEFLOW_CF_TOKEN= と空にして実行すると計測なしで作る。リポジトリを複製して公開するときは自分のトークンに替えるか空にする
export CIRCLEFLOW_CF_TOKEN="${CIRCLEFLOW_CF_TOKEN-8feb87c0f7044d6abf2d925dc0ec7cc1}"
SIMS="src/sim_common.js src/sim_bellows.js src/sim_piston.js src/sim_reflector.js src/sim_blower.js"
# 公開する URL（GitHub Pages）。言語版どうしの印（hreflang）に使う
URL=https://anesthesia-sims.github.io/circleflow/
HREFS="--href-ja $URL --href-en ${URL}en/ --href-zh ${URL}zh/"
python3 src/build_page.py --other en=en/ --other zh=zh/ $HREFS index.html $SIMS $(args ja)
python3 src/build_page.py --lang en --other ja=../ --other zh=../zh/ $HREFS en/index.html $SIMS $(args en)
python3 src/build_page.py --lang zh --other ja=../ --other en=../en/ $HREFS zh/index.html $SIMS $(args zh)
echo "index.html・en/index.html・zh/index.html を作りました"
