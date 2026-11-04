# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
"""麻酔器・呼吸回路の模式図（上昇式ベローズ）実行時シミュレーション用の土台 SVG。
弁・ベローズ・駆動ガスの動きは SMIL、ガスの粒はブラウザ側の JS（sim_bellows.js）が描く。
管の経路や部屋の位置は JSON（argv[3]）に書き出す。

使い方: python3 figure_bellows.py out.svg color out_geo.json [low] [manual] [en]
  low を付けると低流量の場面（新鮮ガスを 1/4 に減らし、ベローズの送り出しを増やして患者に入る量はそろえる）
B5判の本文幅（約150 mm）に縮小して、本文の文字が約7.5 pt になる大きさで描く。
"""
import json
import math
import sys

import palette
import svg
from geometry import cum, plen, qpts, unit
from palette import *   # noqa: F401,F403  色と字体（K・B・METAL・GLASS など）
from parts import (FM_W_BOT, FM_W_TOP, alveoli_path, breathing_bag, bronchus, channels, check_valve, collar, hose, one_way_valve,
                   port, squeeze_mark, valve_detour)
from svg import CYC, GAS_W, TI, add, anim, dashed, flush_pipes, gate_open, label, leader, out, pipe, rect, text


MODE = sys.argv[2] if len(sys.argv) > 2 else "2c"
LUNG_TISSUE, EXP_C, EXP_ARROW, PIPE, CYL, WICK = (palette.by_mode(MODE)[k] for k in ("LUNG_TISSUE", "EXP_C", "EXP_ARROW", "PIPE", "CYL", "WICK"))
W, H = 1340, 860           # 2026-11-03：ピストン式と同じ幅にそろえた（患者の側を右へ 140 px、蛇管を長く）
_FLAGS = set(sys.argv[4:])
LOW_FLOW = "low" in _FLAGS
MANUAL = "manual" in _FLAGS               # 用手換気の場面（切替弁を用手に倒し、呼吸バッグを手で押して換気する。2026-11-02）
LANG = "en" if "en" in _FLAGS else "ja"       # en：図の中の文字を英語にする（labels_en.py。2026-11-02）
svg.configure(LANG, "b")
# 新鮮ガス（粒/秒）。通常は 2（1 呼吸 12 粒、分時換気量に近い）。低流量は 0.5（1 呼吸 3 粒、分時換気量の約 1/4）
FG_RATE = 0.5 if LOW_FLOW else 2.0
# ベローズの中の粒（満杯・吸気の終わり）。低流量では吸気中の新鮮ガスが減るぶん、ベローズが多く送り出す
# （患者に入る量 VT_P はどちらも 13 粒：9＋4 と 12＋1）
NB_FULL, NB_MIN = (14, 2) if LOW_FLOW else (14, 5)
VT_B = NB_FULL - NB_MIN    # ベローズが送り出す量
VT_P = VT_B + FG_RATE * TI # 患者に入る量（ベローズ＋吸気中の新鮮ガス）
# 呼気は受動的：流量は呼気の始めに最大で、時定数 TAU で指数関数的に減る。T_EXH で吐き終える（残りは無視）
TAU = 1.2                  # 呼気の時定数（秒）。模式として I:E と図の大きさに合わせた値（実機の肺は 0.5〜1 秒程度）
T_EXH = (CYC - TI) - 0.3   # 吐き終わるまでの時間（秒）
LUNG_MIN = 6               # 肺胞に残る粒（機能的残気量の模式）


def exh_frac(dt):
    """呼気開始から dt 秒で吐き出した割合（0〜1）"""
    if dt <= 0:
        return 0.0
    if dt >= T_EXH:
        return 1.0
    return (1 - math.exp(-dt / TAU)) / (1 - math.exp(-T_EXH / TAU))


def _bellows_fill(t):
    """呼気開始 t 秒後にベローズへ届いた粒の数（呼気＋新鮮ガス）"""
    return VT_P * exh_frac(t) + FG_RATE * t


T_FULL = TI + next(k * 0.005 for k in range(1, 20000) if _bellows_fill(k * 0.005) >= VT_B)   # ベローズが満杯になる時刻
BELLOWS_KT = [0.0, TI] + [TI + k * 0.05 for k in range(1, int((T_FULL - TI) / 0.05))] + [T_FULL, CYC]
BELLOWS_SC = [1.0, NB_MIN / NB_FULL] + [min(1.0, (NB_MIN + _bellows_fill(t - TI)) / NB_FULL) for t in BELLOWS_KT[2:]]
assert len(BELLOWS_KT) == len(BELLOWS_SC)
# 用手換気：呼吸バッグがベローズの代わりに回路のガスをためる。バッグの中の粒の数はベローズと同じ決まり
# （吸気で NB_FULL → NB_MIN、呼気で呼気と新鮮ガスがたまり、満杯になると APL 弁から逃がす）なので、
# ベローズの伸びのキーをそのまま使って大きさに直す。ベローズは止まっている（縮んだまま）
BAG_S = [0.72 + 0.33 * v for v in BELLOWS_SC]      # 呼吸バッグの大きさ（満杯で 1.05 倍）
_BSC = [NB_MIN / NB_FULL] * len(BELLOWS_SC) if MANUAL else BELLOWS_SC


def lung_vol(t):
    """時刻 t（周期内）の肺胞の粒の数"""
    if t < TI:
        return LUNG_MIN + VT_P * t / TI
    return LUNG_MIN + VT_P * (1 - exh_frac(t - TI))


LUNG_S0, LUNG_S1 = 0.82, 1.0                         # 肺の輪郭の大きさ（機能的残気量のとき／吸気終末）


def lung_scale(t):
    return LUNG_S0 + (LUNG_S1 - LUNG_S0) * (lung_vol(t) - LUNG_MIN) / VT_P


    # 2026-11-02：本体の下の流れの向きの矢印はやめた（粒の動きで分かる）


# ================= 配置の基準 =================
# 左：ガス供給機構・気化器（x 12〜680）、右：呼吸回路（x 692〜1188）
PANEL_B = 740
MAN_Y = 120                       # 流量計の出口がつながる合流管
FM_T, FM_B = 150, 250             # 流量計のフロート管
CUT_Y = 320                       # 亜酸化窒素遮断弁
FLUSH_Y = 392                     # 酸素フラッシュの分岐
JOIN_Y = 452                      # 中央配管とボンベの合流
CHK_Y, REG_Y = 484, 524           # 逆止弁・減圧弁
CYL_T, CYL_B = 560, 646           # ボンベ
OUT_Y = 676                       # 配管端末器
GASES = [("N₂O", 100), ("Air", 260), ("O₂", 420)]
OX = 420
VAPS = (500, 580)                 # 気化器 2 台
FLUSH_X = 632
CGO_X = 650                       # 共通ガス出口

AX = 790                          # 二酸化炭素吸収装置
ABS_CAP = 15.0                    # 吸収剤 1 層が吸える CO2 の粒の数（実際の数時間以上を数分に縮めた値）。
                                  # 低流量では約 27 呼吸、新鮮ガス多めでは約 150 呼吸で全層を使い切る（どちらも同じ吸収剤）
CT, CB = 286, 426                 # 2026-11-02：呼気側の横の管を上げるのに合わせて 14 px 上げた
EXP_Y = 462                       # 呼気側の横の管（2026-11-02：呼気弁がベローズのハウジングに接していたので 18 px 上げた）
SX, SY = 900, 592                 # 切替弁（2026-11-01：人工呼吸器の基部の高さに合わせて 12 px 下げた）
IV_X = 940                        # 吸気弁（2026-11-03：幅をそろえたぶん 60 px 右へ）
EV_X = 1060                       # 呼気弁（2026-11-03：75 px 右へ）
YX, YY = 1210, 270                # Y ピース（2026-11-03：幅をそろえるため患者の側を 140 px 右へ）

# ================= 土台 =================
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add(f'<rect width="{W}" height="{H}" fill="#fff"/>')
add(f'<rect x="12" y="12" width="668" height="{PANEL_B-12}" rx="10" fill="none" stroke="{B}" stroke-width="1.8" stroke-dasharray="7 6"/>')
add(f'<rect x="692" y="12" width="636" height="{PANEL_B-12}" rx="10" fill="none" stroke="{B}" stroke-width="1.8" stroke-dasharray="7 6"/>')
text("ガス供給機構・気化器", 28, 44, 22, weight=700, color=B)
text("呼吸回路", 708, 44, 22, weight=700, color=B)
PIPE_MARK = len(out)

# ================= ガス供給（下 → 上） =================
for name, x in GASES:
    xp, xc = x - 30, x + 30
    pipe([(xp, OUT_Y), (xp, JOIN_Y)], inner=PIPE[name] if MODE == "color" else "#fff")
    pipe([(xp, JOIN_Y), (xc, JOIN_Y)])
    pipe([(xc, CYL_T), (xc, JOIN_Y)])
    pipe([(x, JOIN_Y), (x, FM_B + 20)])
    pipe([(x, FM_T), (x, MAN_Y)])
    # 配管端末器：識別色（2色版は色名）
    # 配管端末器（2026-11-02）：壁（斜線）に取り付けた金属の端末器。識別色の帯に色名、上に差し込んだホースの口金（金属）。
    # 口金と端末器の中の道は、配管の内腔と同じ色
    _lum = PIPE[name] if MODE == "color" else "#fff"
    add(f'<line x1="{xp-30}" y1="{OUT_Y+34}" x2="{xp+30}" y2="{OUT_Y+34}" stroke="{K}" stroke-width="2"/>')
    for _k in range(7):
        add(f'<line x1="{xp-28+9*_k}" y1="{OUT_Y+40}" x2="{xp-22+9*_k}" y2="{OUT_Y+34}" stroke="{K}" stroke-width="1.2"/>')
    rect(xp - 22, OUT_Y + 2, 44, 32, fill=METAL, rx=4)
    add(f'<rect x="{xp-17}" y="{OUT_Y+8}" width="34" height="21" rx="3" fill="{PIPE[name]}" stroke="{K}" stroke-width="1.2"/>')
    tc = K if (MODE == "2c" or name == "Air") else "#fff"
    text(PIPE_NAME[name], xp, OUT_Y + 25, 17, "middle", 700, tc, halo=False)
    rect(xp - 7, OUT_Y - 7, 14, 10, fill=METAL, rx=2, sw=1.4)                                      # ホースの口金
    add(f'<rect x="{xp-3.5}" y="{OUT_Y-8.2}" width="7" height="11.4" fill="{_lum}"/>')
    add(f'<line x1="{xp-7}" y1="{OUT_Y-2}" x2="{xp-3.5}" y2="{OUT_Y-2}" stroke="{K}" stroke-width="1.2"/>')
    add(f'<line x1="{xp+3.5}" y1="{OUT_Y-2}" x2="{xp+7}" y2="{OUT_Y-2}" stroke="{K}" stroke-width="1.2"/>')
    # ボンベ：塗色
    # ボンベ（2026-11-02）：肩の丸い鋼の円筒（塗色は充填ガスの識別色）。円筒に見えるよう、左に照り（白・半透明）、
    # 右に影（黒・半透明）の平らな線。上に金属の容器弁と、横に回すハンドル（使っていないので閉じている）
    _cw, _sh = 26, 16
    add(f'<path d="M {xc-_cw},{CYL_B-6} L {xc-_cw},{CYL_T+_sh} Q {xc-_cw},{CYL_T} {xc-9},{CYL_T} L {xc+9},{CYL_T} '
        f'Q {xc+_cw},{CYL_T} {xc+_cw},{CYL_T+_sh} L {xc+_cw},{CYL_B-6} Q {xc+_cw},{CYL_B} {xc+_cw-6},{CYL_B} '
        f'L {xc-_cw+6},{CYL_B} Q {xc-_cw},{CYL_B} {xc-_cw},{CYL_B-6} Z" fill="{CYL[name]}" stroke="{K}" stroke-width="2.2"/>')
    add(f'<line x1="{xc-20.5}" y1="{CYL_T+18}" x2="{xc-20.5}" y2="{CYL_B-9}" stroke="#fff" stroke-opacity="0.45" stroke-width="3" stroke-linecap="round"/>')
    add(f'<line x1="{xc+20.5}" y1="{CYL_T+18}" x2="{xc+20.5}" y2="{CYL_B-9}" stroke="#000" stroke-opacity="0.28" stroke-width="3" stroke-linecap="round"/>')
    add(f'<rect x="{xc-6}" y="{CYL_T-4}" width="12" height="5" fill="{METAL}" stroke="{K}" stroke-width="1.4"/>')       # 首
    rect(xc - 10, CYL_T - 14, 20, 11, fill=METAL, rx=2, sw=1.8)                                                       # 容器弁
    add(f'<line x1="{xc+10}" y1="{CYL_T-8.5}" x2="{xc+16}" y2="{CYL_T-8.5}" stroke="{K}" stroke-width="2"/>')
    add(f'<rect x="{xc+16}" y="{CYL_T-13}" width="4" height="9" rx="1" fill="{METAL}" stroke="{K}" stroke-width="1.4"/>')  # ハンドル
    text(name, xc, CYL_T + 50, 18, "middle", 700, "#fff", halo=False)
    # 減圧弁・逆止弁
    # 減圧弁の断面（2026-11-02）：ボンベの高い圧のガスが下から弁座を通って低圧室へ入り、上へ出る。低圧室の右の壁は
    # ダイアフラム（青＝動く膜）で、反対側のばねと押し合い、低圧室の圧が設定値を超えると、てこで弁体（青）を弁座へ
    # 押しつけて閉じる。ボンベは使っていないので弁体は閉じた姿
    rect(xc - 17, REG_Y - 16, 34, 32, fill=METAL)
    add(f'<rect x="{xc-3}" y="{REG_Y+4}" width="6" height="13.2" fill="#fff"/>')        # 高圧の入口
    add(f'<rect x="{xc-10}" y="{REG_Y-8}" width="16" height="12" fill="#fff"/>')       # 低圧室
    add(f'<rect x="{xc-3}" y="{REG_Y-17.2}" width="6" height="9.4" fill="#fff"/>')      # 出口
    add(f'<rect x="{xc+8.5}" y="{REG_Y-8}" width="6.5" height="12" fill="#fff"/>')     # ばねの部屋
    add(f'<path d="M {xc+8.5},{REG_Y-2} l 1.6,-4 l 1.6,8 l 1.6,-8 l 1.6,8 l 0.1,-4" fill="none" stroke="{K}" stroke-width="1.1" stroke-linejoin="round"/>')
    add(f'<rect x="{xc+6}" y="{REG_Y-10}" width="2.5" height="16" fill="{B}" stroke="{K}" stroke-width="0.8"/>')   # ダイアフラム
    add(f'<line x1="{xc+6}" y1="{REG_Y-1}" x2="{xc+1}" y2="{REG_Y+1.5}" stroke="{K}" stroke-width="1.2"/>')          # てこ
    add(f'<rect x="{xc-5}" y="{REG_Y+1}" width="10" height="3" rx="0.8" fill="{B}" stroke="{K}" stroke-width="0.8"/>')  # 弁体
    check_valve(xc, CHK_Y)                                       # ボンベ側：使っていない（閉じた姿）
    check_valve(xp, CHK_Y, PIPE[name] if MODE == "color" else "#fff", is_open=(name != "Air"))   # 中央配管側：流れている系統は開いた姿
    # 流量計：フロート管と、下端（入口）のニードル弁・つまみ
    # ガラス管は上ほど太いテーパー管（太さが変わるので、フロートの高さが流量を表す）。
    # 素材がわかるよう薄い青で塗り、円筒に見えるよう左に白い照り、右に濃いめの青の影を平らな線で入れる。
    # 上端は金属の口金（灰）。目盛りは右側に付ける（2026-11-02）
    gt = FM_T + 8                                  # ガラスの上端（口金の下）
    def gx(yy, f):                                 # 高さ yy での管の中心からの距離 × f
        return f * (FM_W_BOT + (FM_W_TOP - FM_W_BOT) * (FM_B - yy) / (FM_B - gt))
    add(f'<path d="M {x-gx(FM_B,1):.1f},{FM_B} L {x-gx(gt,1):.1f},{gt} L {x+gx(gt,1):.1f},{gt} L {x+gx(FM_B,1):.1f},{FM_B} Z" '
        f'fill="{GLASS}" stroke="{K}" stroke-width="2.2" stroke-linejoin="round"/>')
    add(f'<line x1="{x-gx(gt+5,0.55):.1f}" y1="{gt+5}" x2="{x-gx(FM_B-5,0.55):.1f}" y2="{FM_B-5}" stroke="#fff" stroke-width="3" stroke-linecap="round"/>')
    add(f'<line x1="{x+gx(gt+3,0.72):.1f}" y1="{gt+3}" x2="{x+gx(FM_B-3,0.72):.1f}" y2="{FM_B-3}" stroke="{GLASS_SHADE}" stroke-width="3" stroke-linecap="round"/>')
    for k in range(1, 5):
        yy = gt + k * (FM_B - gt) / 5
        add(f'<line x1="{x+gx(yy,1)-6:.1f}" y1="{yy:.0f}" x2="{x+gx(yy,1):.1f}" y2="{yy:.0f}" stroke="{K}" stroke-width="1.5"/>')
    rect(x - 16, FM_T, 32, 9, fill=METAL, rx=2)
    fy = FM_B - 14 if name == "Air" else (FM_B - 24 if LOW_FLOW else FM_B - 46)     # Air は流していない（フロートが底）。低流量ではフロートが低い
    if name != "Air":
        add('<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 1;0 0" dur="0.9s" repeatCount="indefinite"/>')
    # フロートはボビン形：上に溝を刻んだ縁（ガスが当たって回る）、下は細くなる円錐。目盛りは縁の上面で読む
    add(f'<path d="M {x-5.5},{fy+5} L {x+5.5},{fy+5} L {x+1.8},{fy+13} L {x-1.8},{fy+13} Z" fill="{FLOAT_C}" stroke="{K}" stroke-width="1.6" stroke-linejoin="round"/>')
    add(f'<rect x="{x-8}" y="{fy}" width="16" height="5.5" rx="1" fill="{FLOAT_C}" stroke="{K}" stroke-width="1.6"/>')
    for dx in (-4.5, 0, 4.5):
        add(f'<line x1="{x+dx-1.3}" y1="{fy+1}" x2="{x+dx+1.3}" y2="{fy+4.5}" stroke="{K}" stroke-width="1.2"/>')
    if name != "Air":
        add('</g>')
    # ニードル弁の断面（2026-11-02）：金属の本体を下から上へ通る道に、つまみの軸の先の先細りの針が横から入り、
    # 道の細いところ（のど）のすき間を変えて流量を決める。流している O2・N2O は針を少し引いた姿、Air は奥まで入れて閉じた姿
    _my = FM_B + 10
    rect(x - 12, FM_B, 24, 20, fill=METAL, rx=3)
    add(f'<rect x="{x-3.5}" y="{FM_B-1.2}" width="7" height="22.4" fill="#fff"/>')
    add(f'<path d="M {x-3.5},{_my-4} L {x-1.8},{_my} L {x-3.5},{_my+4} Z" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # のど（弁座）
    _tip = x - 1.8 if name == "Air" else x + 1.5
    add(f'<path d="M {x+20},{_my-2} L {x+5},{_my-2} L {_tip},{_my} L {x+5},{_my+2} L {x+20},{_my+2} Z" fill="{METAL}" stroke="{K}" stroke-width="1" stroke-linejoin="round"/>')
    add(f'<circle cx="{x+27}" cy="{_my}" r="8" fill="{METAL}" stroke="{K}" stroke-width="2.2"/>')                  # つまみ
    for _a in range(0, 360, 45):
        _r = math.radians(_a)
        add(f'<line x1="{x+27+5*math.cos(_r):.1f}" y1="{_my+5*math.sin(_r):.1f}" x2="{x+27+7.8*math.cos(_r):.1f}" y2="{_my+7.8*math.sin(_r):.1f}" stroke="{K}" stroke-width="1"/>')
    text(name, x - 22, FM_T + 24, 18, "end", 700)
    if name == "Air":
        text("停止", x - 22, FM_T + 48, 15, "end", 700, color="#666")
    # 2026-11-02：流量計の下の流れの矢印はやめた


# 2026-11-02：ガスの流れの向きを示す三角形の矢印はやめた（粒の動きで分かるため。著者の指摘）。弁の開閉は弁板の動きで示す
# 亜酸化窒素遮断弁（O2 の供給圧で開閉）
NX = 100
# 断面（2026-11-02）：N2O の道を横切るすべり弁（スプール、青＝動く部品）。O2 の圧が右の部屋からスプールを左へ押し、
# ばねが縮んでスプールの穴が N2O の道にそろうと通す（今の姿）。O2 の圧がなくなると、ばねがスプールを右へ戻し、
# 穴のない部分で道をふさぐ。粒の通り道（道の中心）は変えていない
rect(NX - 18, CUT_Y - 17, 36, 34, fill=METAL)
add(f'<rect x="{NX-3.5}" y="{CUT_Y-18.2}" width="7" height="36.4" fill="#fff"/>')       # N2O の道
add(f'<rect x="{NX-16}" y="{CUT_Y-5}" width="30" height="10" fill="#fff"/>')           # スプールの穴（シリンダー）
add(f'<rect x="{NX+11}" y="{CUT_Y}" width="3" height="12" fill="#fff"/>')               # O2 の部屋へ通じる道
add(f'<rect x="{NX+11}" y="{CUT_Y+8}" width="7.2" height="4" fill="#fff"/>')
add(f'<path d="M {NX-16},{CUT_Y} l 0.7,-3.5 l 0.8,7 l 0.8,-7 l 0.8,7 l 0.9,-3.5" fill="none" stroke="{K}" stroke-width="1"/>')   # ばね（縮んでいる）
add(f'<rect x="{NX-12}" y="{CUT_Y-4}" width="23" height="8" rx="1" fill="{B}" stroke="{K}" stroke-width="1"/>')             # スプール
add(f'<rect x="{NX-3.5}" y="{CUT_Y-4.6}" width="7" height="9.2" fill="#fff"/>')        # スプールの穴（N2O の道にそろっている）
dashed([(OX, CUT_Y + 10), (NX + 18, CUT_Y + 10)])
text("O₂の圧で開閉", 340, CUT_Y + 34, 16, "middle", color="#333")

# 酸素フラッシュ
pipe([(OX, FLUSH_Y), (FLUSH_X, FLUSH_Y), (FLUSH_X, MAN_Y + 5)])
# 弁の本体（白い箱）の表面に、緑の押しボタン。誤って押さないよう灰色の囲い（ガード）で囲む。
# 図のほかの部品と同じく、黒い輪郭線と平らな塗りだけで描く（陰影・グラデーションは使わない。2026-11-02）。
# 緑は O2 の色。配管の緑（#1e9e4a）のままでは白い字が読みにくいので、同じ緑の濃い色にする
FB_X = 520
FB_GREEN = "#157a3a" if PIPE["O₂"] != "#ffffff" else "#ffffff"
FB_TEXT = "#fff" if FB_GREEN != "#ffffff" else K
rect(FB_X - 25, FLUSH_Y - 23, 50, 46, rx=7)
add(f'<circle cx="{FB_X}" cy="{FLUSH_Y}" r="19" fill="{METAL}" stroke="{K}" stroke-width="2.2"/>')
add(f'<circle cx="{FB_X}" cy="{FLUSH_Y}" r="14" fill="{FB_GREEN}" stroke="{K}" stroke-width="2.2"/>')
add(f'<text x="{FB_X}" y="{FLUSH_Y + 4.5}" font-family="{FONT}" font-size="13" font-weight="700" fill="{FB_TEXT}" text-anchor="middle">O₂</text>')

# 気化器とインターロック
# 気化器は合流管に並べて取り付けるが、ガスが入るのはダイヤルを開けた 1 台だけ。
# 使用中（左）：合流管のガスは入口ポートから気化器に入り、出口ポートから合流管へ戻る。
# 停止中（右）：ポートは閉じていて、ガスは合流管をそのまま通り過ぎる。
VW, VT, VB = 70, MAN_Y + 26, MAN_Y + 96
ON = VAPS[0]
PIN, POUT = ON - VW / 2 + 14, ON + VW / 2 - 14
pipe([(100, MAN_Y), (PIN, MAN_Y), (PIN, VT + 2)])
pipe([(POUT, VT + 2), (POUT, MAN_Y), (CGO_X, MAN_Y)])


for vx in VAPS:
    on = vx == ON
    x0, x1 = vx - VW / 2, vx + VW / 2
    pin, pout = x0 + 14, x1 - 14
    cy0, by, hw = VT + 26, VT + 13, (GAS_W - 5) / 2
    if not on:
        # 閉じたポート：合流管と気化器の間をふさいだ継ぎ手
        for px in (pin, pout):
            add(f'<rect x="{px-7}" y="{MAN_Y+6}" width="14" height="{VT-MAN_Y-4}" fill="{METAL}" stroke="{K}" stroke-width="1.6"/>')
            add(f'<line x1="{px-7}" y1="{(MAN_Y + 6 + VT + 2) / 2:.1f}" x2="{px+7}" y2="{(MAN_Y + 6 + VT + 2) / 2:.1f}" stroke="{K}" stroke-width="1.2"/>')
    add(f'<rect x="{x0}" y="{VT}" width="{VW}" height="{VB-VT}" rx="7" fill="{METAL}" stroke="{K}" stroke-width="2.2"/>')
    # 気化室（中はガス）と液体の麻酔薬
    add(f'<rect x="{x0+8}" y="{cy0}" width="{VW-16}" height="{VB-cy0-8}" rx="3" fill="#fff" stroke="{K}" stroke-width="1.2"/>')
    add(f'<path d="M {x0+8},{VB-26} q 6,-5 12,0 t 12,0 t 12,0 t 12,0 t 6,0 L {x1-8},{VB-8} L {x0+8},{VB-8} Z" fill="{B_TINT}" stroke="none"/>')
    # 灯心：気化室の壁ぞいに天井から液の中まで垂れる布（斜めの細線で布目）
    for wx in (x0 + 9, x1 - 12):
        add(f'<rect x="{wx}" y="{cy0+1}" width="3" height="{VB-cy0-10}" fill="{WICK}"/>')
        for k in range(int((VB - cy0 - 10) // 4)):
            add(f'<line x1="{wx}" y1="{cy0+4+4*k}" x2="{wx+3}" y2="{cy0+1+4*k}" stroke="#8a7a50" stroke-width="0.7"/>')
    add(f'<path d="M {x0+8},{VB-26} q 6,-5 12,0 t 12,0 t 12,0 t 12,0 t 6,0" fill="none" stroke="{B}" stroke-width="1.8"/>')
    if on:
        # 通路：本体の上面から入って、バイパス路（横の道）と気化室へ下りる道に分かれ、また合流して上面から出る
        for px in (pin, pout):
            add(f'<rect x="{px-hw}" y="{VT-1.2}" width="{2*hw}" height="{cy0-VT+1.8}" fill="#fff"/>')
        add(f'<rect x="{pin-hw}" y="{by-hw}" width="{pout-pin+2*hw}" height="{2*hw}" fill="#fff"/>')
    # 濃度ダイヤル（使用中は開、停止中は 0）
    add(f'<circle cx="{vx}" cy="{VB}" r="15" fill="{METAL}" stroke="{K}" stroke-width="2.2"/>')
    add(f'<circle cx="{vx}" cy="{VB}" r="10.5" fill="#fff" stroke="{K}" stroke-width="1.2"/>')
    for a in (0, 30, 60, 90, 120):
        r = math.radians(a)
        add(f'<line x1="{vx + 7.5*math.sin(r):.1f}" y1="{VB - 7.5*math.cos(r):.1f}" x2="{vx + 10.5*math.sin(r):.1f}" y2="{VB - 10.5*math.cos(r):.1f}" stroke="{K}" stroke-width="1.1"/>')
    pa = math.radians(60 if on else 0)
    add(f'<line x1="{vx}" y1="{VB}" x2="{vx + 9*math.sin(pa):.1f}" y2="{VB - 9*math.cos(pa):.1f}" stroke="{K}" stroke-width="2.4" stroke-linecap="round"/>')
    add(f'<circle cx="{vx}" cy="{VB}" r="2" fill="{K}"/>')
    if on:
        text("使用中", vx, MAN_Y - 16, 15, "middle", 700)
    else:
        text("停止中", vx, MAN_Y - 16, 15, "middle", 700, color="#555")
# インターロック：2 台のダイヤルの間の棒（青＝動く部品）。使用中のダイヤルを回すと棒が押し出され、
# 停止中のダイヤルの縁の切り欠きに入って回らないようにする
add(f'<rect x="{VAPS[0]+15}" y="{VB-3}" width="{VAPS[1]-VAPS[0]-26}" height="6" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')
text("インターロック", sum(VAPS) / 2, VB + 34, 16, "middle", 700, B)

# 共通ガス出口
# 2026-11-02：金属の継ぎ手の断面。中を合流管のガスが通り、右の先細りの口に呼吸回路側の管をつなぐ
rect(CGO_X, MAN_Y - 16, 14, 32, fill=METAL, rx=2)
add(f'<path d="M {CGO_X+14},{MAN_Y-10} L {CGO_X+22},{MAN_Y-8} L {CGO_X+22},{MAN_Y+8} L {CGO_X+14},{MAN_Y+10} Z" fill="{METAL}" stroke="{K}" stroke-width="1.6" stroke-linejoin="round"/>')
add(f'<rect x="{CGO_X-1.2}" y="{MAN_Y-3.5}" width="{24.4}" height="7" fill="#fff"/>')

# ================= 呼吸回路 =================
INSP, EXP = INSP_C, EXP_C
# 新鮮ガス → 吸収装置の出口側
pipe([(CGO_X + 20, MAN_Y), (720, MAN_Y), (720, 230), (AX - 6, 230)], inner=INSP)
# 吸収装置 → 吸気弁 → 吸気蛇管
pipe([(AX, CT), (AX, MAN_Y), (IV_X + 32, MAN_Y)], inner=INSP)
one_way_valve(IV_X, MAN_Y, 1, INSP_FILL, open_phase="insp")


# 吸気弁・呼気弁の蛇管の差し込み口
IP = (IV_X + 32 + 16, MAN_Y)               # 吸気弁の口（つばの位置）
EP = (EV_X + 32 + 16, EXP_Y)               # 呼気弁の口
# Y ピース：枝の向きは、つながる蛇管の終わりの向きに合わせる
C_I = (1130, MAN_Y)                         # 吸気蛇管の曲がり具合（制御点）
C_E = (1248, EXP_Y)                        # 呼気蛇管の曲がり具合
YL = 36
_ui = unit(C_I[0], C_I[1], YX, YY)
_ue = unit(C_E[0], C_E[1], YX, YY)
YI = (YX - YL * _ui[0], YY - YL * _ui[1])  # 吸気側の枝の口
YE = (YX - YL * _ue[0], YY - YL * _ue[1])  # 呼気側の枝の口
YP = (1238, YY)                            # 患者側の口
# 回路内圧計
pipe([(AX, 180), (AX + 30, 180)], inner=INSP, w=9)
add(f'<circle cx="{AX+50}" cy="180" r="20" fill="#fff" stroke="{K}" stroke-width="2.2"/>')
for k in range(7):
    aa = math.radians(150 + k * 40)
    add(f'<line x1="{AX+50+14*math.cos(aa):.1f}" y1="{180+14*math.sin(aa):.1f}" x2="{AX+50+19*math.cos(aa):.1f}" y2="{180+19*math.sin(aa):.1f}" stroke="{K}" stroke-width="1.5"/>')
# 針：回路内圧（cmH2O）に合わせて回る。目盛は 0〜30 cmH2O を 240°（150°→390°）に割り当てる
# 従量式・定常流の波形：吸気の始めに抵抗分だけ跳ね上がり、吸気中は直線的に上がって吸気終末で最高。
# 呼気に入ると急に下がり、ベローズが上がりきって余剰ガス弁が開いたあとは弁の開放圧が残る
GX, GY = AX + 50, 180
P_KEYS = [(0.0, 2.5), (0.12, 6.0), (TI, 16.0), (TI + 0.12, 3.0), (max(TI + 0.4, T_FULL - 0.15), 1.5), (T_FULL + 0.15, 2.5), (CYC, 2.5)]
def _ang(pv):
    return 150 + 240 * pv / 30
add(f'<g><animateTransform attributeName="transform" type="rotate" '
    f'values="{";".join(f"{_ang(pv):.1f} {GX} {GY}" for _, pv in P_KEYS)}" '
    f'keyTimes="{";".join(f"{tk/CYC:.4f}" for tk, _ in P_KEYS)}" calcMode="linear" dur="{CYC}s" repeatCount="indefinite"/>'
    f'<line x1="{GX}" y1="{GY}" x2="{GX+15}" y2="{GY}" stroke="{B}" stroke-width="3" stroke-linecap="round"/></g>')
add(f'<circle cx="{GX}" cy="{GY}" r="3" fill="{K}"/>')
for pv, lab in ((0, "0"), (15, "15"), (30, "30")):
    a = math.radians(_ang(pv))
    text(lab, GX + 10.5 * math.cos(a), GY + 10.5 * math.sin(a) + 3, 7.5, "middle", color="#333", halo=False)
text("回路内圧計", AX + 76, 187, 17)
text("cmH₂O", AX + 76, 203, 11, color="#555")
# 呼気側の管：呼気弁 → 吸収装置
pipe([(EV_X + 32, EXP_Y), (AX, EXP_Y), (AX, CB)], inner=EXP)
# 弁の差し込み口
port(IV_X + 32, MAN_Y, IP[0], IP[1])
port(EV_X + 32, EXP_Y, EP[0], EP[1])
# 蛇管：差し込み口から Y ピースの枝まで、わずかに曲げて柔らかさを表す
hose((IP[0] + 3, IP[1]), C_I, YI, INSP)
hose((EP[0] + 3, EP[1]), C_E, YE, EXP)
# 患者（2026-11-01 変更）：Y ピースの口から気管（死腔）が右へ、そして下へ降り、気管分岐部で 2 葉の肺胞につながる。
# 気管の中のガスは CO2 を受け取らない。肺胞の輪郭は容量に合わせて伸び縮みする（SMIL）
TR_X = 1290                                 # 気管の縦の部分の x
HIL = (TR_X, 362)                           # 気管分岐部（肺胞の入口。肺の伸縮の中心）
LOBES = (TR_X - 19, TR_X + 19)              # 左右の肺葉の中心 x
LOBE_W, LOBE_T, LOBE_B = 30, 386, 492       # 肺葉の幅と上下（気管支に長さをもたせるため分岐部から 24 px 下）
LOBE = (LOBE_W, LOBE_T, LOBE_B)
# 描画順：気管と気管支の外形（黒）→ 肺葉の輪郭（伸縮）→ 内腔（白）。内腔は肺葉の壁を越えて少し中まで伸ばし、
# 気管支が肺胞の中へ開いて見えるようにする
_tr = f"M {YP[0]},{YY} L {TR_X},{YY} L {TR_X},{HIL[1]}"
add(f'<path d="{_tr}" fill="none" stroke="{K}" stroke-width="16" stroke-linecap="butt" stroke-linejoin="round"/>')


for lx in LOBES:
    x0, y0, x1, y1 = bronchus(lx, 0.0, 1.0, HIL, LOBE_T)
    add(f'<path d="M {x0},{y0} L {x1:.1f},{y1:.1f}" stroke="{K}" stroke-width="12" stroke-linecap="butt"/>')
add(f'<circle cx="{HIL[0]}" cy="{HIL[1]}" r="8" fill="{K}"/>')
# 肺葉：容量に合わせて気管分岐部を中心に伸縮
_lk = [0.0, TI] + [TI + k * 0.1 for k in range(1, int(T_EXH / 0.1) + 1)] + [CYC]
add(f'<g transform="translate({HIL[0]},{HIL[1]})"><g><animateTransform attributeName="transform" type="scale" '
    f'values="{";".join(f"{lung_scale(t):.4f}" for t in _lk)}" keyTimes="{";".join(f"{t/CYC:.4f}" for t in _lk)}" '
    f'calcMode="linear" dur="{CYC}s" repeatCount="indefinite"/><g transform="translate({-HIL[0]},{-HIL[1]})">')
for lx in LOBES:
    # 肺葉は肺胞の房：輪郭を小さな袋の並び（波形）にし、壁（肺胞壁と毛細血管）を薄い赤の帯で示す。
    # 中のガスの空間は白（管の内腔と同じ）。中に肺胞を薄い赤の輪で並べる。輪は粒の座席（GEO の lung.slots）
    # と同じ位置なので、粒は 1 つずつ肺胞の中に入って見える（2026-11-02）
    add(f'<path d="{alveoli_path(lx, 0, LOBE)}" fill="{LUNG_TISSUE}" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>')
    add(f'<path d="{alveoli_path(lx, 3, LOBE)}" fill="#fff"/>')
    for r in range(8):
        for dx in (-6, 6):
            add(f'<circle cx="{lx + dx}" cy="{LOBE_T + 10 + 11.5 * r}" r="5.4" fill="none" stroke="{LUNG_TISSUE}" stroke-width="1.5"/>')
add('</g></g></g>')
# 内腔
add(f'<path d="{_tr}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="butt" stroke-linejoin="round"/>')
add(f'<circle cx="{HIL[0]}" cy="{HIL[1]}" r="5" fill="#fff"/>')
for lx in LOBES:
    # 気管支の内腔（外形と同じ軸線上）：肺葉の壁の手前までは白、壁をまたぐ部分は肺葉の色
    # （壁の線を途切れさせて肺胞へ開いて見せる。肺葉が縮んでいるときも壁が途切れるよう、手前から奥までまたがせる）
    x0, y0, x1, y1 = bronchus(lx, 0.0, 0.62, HIL, LOBE_T)
    add(f'<path d="M {x0},{y0} L {x1:.1f},{y1:.1f}" stroke="#fff" stroke-width="6" stroke-linecap="butt"/>')
    x0, y0, x1, y1 = bronchus(lx, 0.62, 1.22, HIL, LOBE_T)
    add(f'<path d="M {x0:.1f},{y0:.1f} L {x1:.1f},{y1:.1f}" stroke="{B_TINT2}" stroke-width="6" stroke-linecap="butt"/>')
text("患者", TR_X, 250, 15, "middle", 700)
text("気管", TR_X - 10, 322, 12, "end", color="#333")     # 2026-11-04：図の枠の点線にかからないよう気管の左へ
text("(死腔)", TR_X - 10, 338, 11, "end", color="#333")
if LANG == "en":                                  # 英語は 1 行では蛇管にかかるので、(dead と space) の 2 行に分ける
    text("space)", TR_X - 10, 344, 9, "end", color="#333")
text("肺胞", TR_X, 508, 13, "middle", color="#333")   # 2026-11-02：輪郭の袋のふくらみと重ならないよう 8 px 下げた
# Y ピース本体：3 本の管を、外形→内腔の順に描いて継ぎ目なく合流させる
_legs = [(YI, (YX, YY)), (YE, (YX, YY)), ((YX, YY), YP)]
for (ax, ay), (bx, by) in _legs:
    add(f'<path d="M {ax:.1f},{ay:.1f} L {bx:.1f},{by:.1f}" stroke="{K}" stroke-width="20" stroke-linecap="butt"/>')
add(f'<circle cx="{YX}" cy="{YY}" r="10" fill="{K}"/>')
for (ax, ay), (bx, by) in _legs:
    add(f'<path d="M {ax:.1f},{ay:.1f} L {bx:.1f},{by:.1f}" stroke="#fff" stroke-width="14" stroke-linecap="butt"/>')
add(f'<circle cx="{YX}" cy="{YY}" r="7" fill="#fff"/>')
for (cx, cy), (ux, uy) in [(YI, _ui), (YE, _ue), (YP, (-1, 0))]:
    collar(cx, cy, ux, uy)
one_way_valve(EV_X, EXP_Y, -1, EXP, open_phase="exp")
# 二酸化炭素吸収装置：下から入った呼気が吸収剤の層を上へ抜ける
# 容器は透明な樹脂：流量計のガラス管と同じ薄い青で「透けて中の吸収剤が見える」ことを示し、
# 左の白い照りと右の青い影（平らな線）で円筒に見せる。上下は回路につながる金属の口金（2026-11-02）
add(f'<rect x="{AX-40}" y="{CT}" width="80" height="{CB-CT}" rx="10" fill="{GLASS}" stroke="{K}" stroke-width="2.2"/>')
add(f'<line x1="{AX-35.5}" y1="{CT+12}" x2="{AX-35.5}" y2="{CB-12}" stroke="#fff" stroke-width="3" stroke-linecap="round"/>')
add(f'<line x1="{AX+35.5}" y1="{CT+12}" x2="{AX+35.5}" y2="{CB-12}" stroke="{GLASS_SHADE}" stroke-width="3" stroke-linecap="round"/>')
PT, PB = CT + 14, CB - 14
# 吸収剤の粒：9 層。層の番号はガスの入口（下）から 0, 1, …, 8。色はシミュレーターが
# 吸収した CO2 の累計に合わせて塗り替える（未使用：白 → 使い切り：紫）。最初は全層が未使用
ABS_ROWS = 9
ABS_PITCH = 12.6
for r in range(ABS_ROWS):
    yy = PT + 7 + r * ABS_PITCH
    off = 0 if r % 2 == 0 else 6.5
    for c in range(5):
        xx = AX - 26 + off + c * 13
        if xx > AX + 30:
            continue
        add(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="5.6" fill="{INSP}" stroke="#555" stroke-width="1.1" data-absrow="{ABS_ROWS - 1 - r}"/>')
# 吸収剤を上下から押さえる金属の穴あき板（黒い点が穴。ガスは穴を通り、粒は通さない）
for yy in (PT, PB):
    add(f'<rect x="{AX-38}" y="{yy-2.5}" width="76" height="5" fill="{METAL}" stroke="{K}" stroke-width="1.2"/>')
    add(f'<line x1="{AX-35}" y1="{yy}" x2="{AX+35}" y2="{yy}" stroke="{K}" stroke-width="2" stroke-dasharray="2 3.8"/>')
for yy in (CT - 5, CB - 7):
    rect(AX - 44, yy, 88, 12, fill=METAL, rx=3)
# 切替弁
pipe([(SX, EXP_Y), (SX, SY - 22)], inner=EXP)
# 切替弁の断面（2026-11-02）：本体（灰）に 3 本の通路（上：呼気側の合流点から、左：APL 弁・呼吸バッグへ、
# 右：人工呼吸器へ）。真ん中の回る栓（青＝動く部品）に L 字の穴があり、人工呼吸の位置では上と右をつなぎ、
# 左（用手側）をふさぐ。レバーを用手に倒すと栓が回り、上と左がつながる
rect(SX - 36, SY - 22, 72, 44, fill=METAL, rx=6)
_hw = 4
add(f'<rect x="{SX-_hw}" y="{SY-23.2}" width="{2*_hw}" height="{23.2}" fill="{EXP}"/>')
add(f'<rect x="{SX-37.2}" y="{SY-_hw}" width="{74.4}" height="{2*_hw}" fill="{EXP}"/>')
add(f'<circle cx="{SX}" cy="{SY}" r="14" fill="{B}" stroke="{K}" stroke-width="2.2"/>')
add(f'<rect x="{SX-_hw}" y="{SY-15.2}" width="{2*_hw}" height="{15.2+_hw}" fill="{EXP}"/>')
if MANUAL:                                     # 用手：栓の L 字の穴が上と左（APL 弁・呼吸バッグ）をつなぐ
    add(f'<rect x="{SX-15.2}" y="{SY-_hw}" width="{15.2+_hw}" height="{2*_hw}" fill="{EXP}"/>')
else:                                          # 人工呼吸：上と右（人工呼吸器）をつなぐ
    add(f'<rect x="{SX-_hw}" y="{SY-_hw}" width="{15.2+_hw}" height="{2*_hw}" fill="{EXP}"/>')
text("用手", SX - 30, SY - 30, 15, "middle", 700, color="#333")
text("人工呼吸", SX + 34, SY - 30, 13, "middle", 700, color="#333")
# 用手換気側：APL 弁と呼吸バッグ
APX = 800
pipe([(SX - 36, SY), (770, SY)], inner=EXP)
pipe([(APX, SY), (APX, SY + 10)], inner=EXP, w=10)
# APL 弁の断面（2026-11-02）：上の口から入ったガスの圧が、ばねで弁座に押しつけられた弁板（青）を押し下げると開き、
# 横の出口から余剰ガス排出装置へ出る。下のつまみを回すと、ねじでばねの受けが上下し、開く圧（設定圧）が変わる。
# ベローズ式（人工呼吸中）は回路から外れているので閉じた姿
APL_DZ = 0                                   # 弁板が弁座から下がっている量（0 なら閉）
rect(APX - 20, SY + 8, 40, 48, fill=METAL, rx=5)
add(f'<rect x="{APX-3.5}" y="{SY+6.8}" width="7" height="{7.8}" fill="{EXP}"/>')            # 入口
add(f'<rect x="{APX-16}" y="{SY+14}" width="32" height="32" fill="{EXP}"/>')               # 弁の部屋
add(f'<rect x="{APX+15}" y="{SY+26.5}" width="6.2" height="7" fill="{EXP}"/>')            # 出口（右へ）
for _sx in (APX - 9, APX + 3.5):
    add(f'<rect x="{_sx}" y="{SY+14}" width="5.5" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # 弁座
# 用手換気では、呼吸バッグが満杯になる時刻（T_FULL）から呼気の終わりまで弁板が 6 px 下がって開き、ばねが縮む
_fo = T_FULL / CYC
_akt = f"0;{_fo:.4f};{min(_fo + 0.01, 0.98):.4f};0.99;1"
if MANUAL:
    add(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 6;0 6;0 0" keyTimes="{_akt}" dur="{CYC}s" repeatCount="indefinite"/>')
add(f'<rect x="{APX-8.5}" y="{SY+16.5+APL_DZ}" width="17" height="3.5" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')
if MANUAL:
    add('</g>')
_s0, _s1 = SY + 20 + APL_DZ, SY + 44
if MANUAL:
    _sr = (_s1 - _s0 - 6) / (_s1 - _s0)
    add(f'<g transform="translate({APX},{_s1})"><g><animateTransform attributeName="transform" type="scale" '
        f'values="1 1;1 1;1 {_sr:.4f};1 {_sr:.4f};1 1" keyTimes="{_akt}" dur="{CYC}s" repeatCount="indefinite"/>'
        f'<g transform="translate({-APX},{-_s1})">')
add(f'<path d="M {APX},{_s0} ' + " ".join(f"L {APX + (6 if k % 2 else -6)},{_s0 + (_s1 - _s0) * k / 6:.1f}" for k in range(1, 6))
    + f' L {APX},{_s1}" fill="none" stroke="{K}" stroke-width="1.5" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
if MANUAL:
    add('</g></g></g>')
add(f'<rect x="{APX-9}" y="{SY+44}" width="18" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')     # ばねの受け
add(f'<rect x="{APX-2.5}" y="{SY+46.5}" width="5" height="12" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # ねじ
for _k in range(3):
    add(f'<line x1="{APX-2.5}" y1="{SY+50+3.5*_k}" x2="{APX+2.5}" y2="{SY+48+3.5*_k}" stroke="{K}" stroke-width="0.8"/>')
rect(APX - 12, SY + 58, 24, 12, fill=METAL, rx=2, sw=1.8)                                        # つまみ（ぎざぎざ）
for _k in range(1, 6):
    add(f'<line x1="{APX-12+4*_k}" y1="{SY+59}" x2="{APX-12+4*_k}" y2="{SY+69}" stroke="{K}" stroke-width="1"/>')
# 呼吸バッグ：人工呼吸中は切替弁で回路から外れて止まっている。用手換気では手で押してしぼみ、呼気でふくらむ
BG_P = 772                                  # バッグの差し込み口
if MANUAL:
    breathing_bag(BG_P, SY, EXP, BAG_S, BELLOWS_KT)
    squeeze_mark(BG_P, SY, gate_open("insp"))
else:
    breathing_bag(BG_P, SY, EXP)
# 人工呼吸器（上昇式ベローズ）
# 呼気と新鮮ガスがベローズを下から押し上げ、吸気では駆動ガス（O2）がハウジング内で
# ベローズを押し下げて、中のガスを患者へ送る。
# 2026-11-01 配置変更：切替弁からの管は、ベローズ基部（台座）の横面に直接つなぐ。人工呼吸器の箱を
# 切替弁のすぐ右に寄せ、管の容積（粒の数）を実機の接続ホースに近づける（旧：299 px、新：約 170 px）
VX0 = 1022                                  # 箱の左端（切替弁のすぐ右。2026-11-03：60 px 右へ）
HX0, HX1 = VX0 + 12, VX0 + 70               # 透明なハウジングの左右
BASE_T, BASE_B = SY - 7, SY + 7             # ベローズ基部（台座）。管はこの横面に入る
BBOT = BASE_T                               # ベローズの底板
BTOP = BBOT - 64                            # ベローズの上端（満杯）
HY0, HY1 = BTOP - 12, BASE_B + 2            # ハウジングの上下
VY0, VY1 = HY0 - 6, HY1 + 12                # 箱の上下
CONN_Y = SY                                 # 回路側からベローズ基部へ入る管の高さ（切替弁と同じ）
HXc = (HX0 + HX1) / 2
pipe([(SX + 36, SY), (HX0 + 3, SY)], inner=EXP)
# 2026-11-01：人工呼吸器を囲む箱と「人工呼吸器」の文字はやめた（部品の名前「ベローズ」だけを置く）
BX0, BX1 = HX0 + 8, HX1 - 8                                  # ベローズの左右
add(f'<rect x="{HX0}" y="{HY0}" width="{HX1-HX0}" height="{HY1-HY0}" rx="10" fill="#fff" stroke="{K}" stroke-width="2"/>')
_kb = ";".join(f"{k/CYC:.4f}" for k in BELLOWS_KT)
_sc = _BSC                                         # ベローズの縦の伸び（底板を基準。用手換気では止まっている）
_top = [BBOT - v * (BBOT - BTOP) for v in _sc]   # 天板の高さ
_dh = ";".join(f"{max(0.0, t - (HY0 + 2)):.1f}" for t in _top)
add(f'<rect x="{HX0+2}" y="{HY0+2}" width="{HX1-HX0-4}" height="{BTOP-HY0-2}" rx="8" fill="#e6e6e6">'
    + anim("height", _dh, _kb) + '</rect>')
add(f'<defs><clipPath id="bdrv"><rect x="{HX0+2}" y="{HY0+2}" width="{HX1-HX0-4}" height="{BTOP-HY0-2}">'
    + anim("height", _dh, _kb) + '</rect></clipPath></defs>')
# ベローズ：蛇腹の側面（中は回路のガス＝呼気側の色）
left, right = [], []
n = 6
for i in range(n + 1):
    yy = BTOP + 4 + i * (BBOT - BTOP - 4) / n
    dx = 0 if i % 2 == 0 else 5
    left.append((BX0 + dx, yy))
    right.append((BX1 - dx, yy))
poly = left + right[::-1]
add(f'<g transform="translate(0,{BBOT})"><g><animateTransform attributeName="transform" type="scale" '
    f'values="{";".join(f"1 {v:.4f}" for v in _BSC)}" keyTimes="{";".join(f"{k/CYC:.4f}" for k in BELLOWS_KT)}" dur="{CYC}s" repeatCount="indefinite"/>'
    f'<g transform="translate(0,{-BBOT})">')
add('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in poly) + f'" fill="{EXP}" stroke="{K}" stroke-width="1.8" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
add(f'<rect x="{BX0-2}" y="{BTOP}" width="{BX1-BX0+4}" height="5" rx="1.5" fill="{K}"/>')
add('</g></g></g>')
# 台座（マニホールド）：白地に黒枠。横から入ったガスが中の通路を通り、底板の中央の口からベローズへ上がる
add(f'<rect x="{HX0+2}" y="{BASE_T}" width="{HX1-HX0-4}" height="{BASE_B-BASE_T}" fill="#fff" stroke="{K}" stroke-width="2"/>')
add(f'<rect x="{HX0+2}" y="{BASE_T}" width="{HX1-HX0-4}" height="4" fill="{K}"/>')                       # 底板
add(f'<path d="M {HX0+2},{SY} L {HXc},{SY} L {HXc},{BBOT-3}" fill="none" stroke="{K}" stroke-width="{GAS_W-3}" stroke-linecap="butt" stroke-linejoin="miter"/>')
add(f'<path d="M {HX0+1},{SY} L {HXc},{SY} L {HXc},{BBOT-3}" fill="none" stroke="{EXP}" stroke-width="{GAS_W-7}" stroke-linecap="butt" stroke-linejoin="miter"/>')
# 2026-11-02：ベローズの上下の矢印はやめた（動きはベローズのアニメーションと粒で分かる）
# 駆動ガス（O2）の入口：内腔は駆動ガスの色（灰）で、ハウジングの壁を切ってハウジングの中の駆動ガスにつなぐ。
# 2026-11-02：入る・出る向きの矢印はやめた（駆動ガスの粒の動きで分かる）
DRV_C = "#e6e6e6"
DRV_END = VX0 + 84
add(f'<path d="M {HX1 - 1},{HY0 + 7} L {DRV_END},{HY0 + 7}" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="butt"/>')
add(f'<path d="M {HX1 - 7},{HY0 + 7} L {DRV_END},{HY0 + 7}" fill="none" stroke="{DRV_C}" stroke-width="5" stroke-linecap="butt"/>')
text("駆動ガス（O₂）", DRV_END + 18, HY0 + 12, 13, color="#333")
text("ベローズ", HX1 + 12, HY0 + 62, 16, weight=700)
if MANUAL:   # 用手換気で止まっていることの注記。操作ページでは隠して解説に回す（class="svgnote"。コマ撮りでは出す。2026-11-02）
    add('<g class="svgnote">')
    text("（止まっている）", HX1 + 12, HY0 + 82, 13, color="#666")
    add('</g>')
# 余剰ガス排出装置
SC_T = 680
pipe([(APX + 20, SY + 30), (APX + 36, SY + 30), (APX + 36, SC_T)], inner=EXP)   # 2026-11-02：点線から管に（APL 弁の出口 → 余剰ガス排出装置）
# 余剰ガス弁（スピル弁）：ベローズの基部から箱の底を抜けて余剰ガス排出装置へ
# 台座の中の通路から下へ分かれ、底を抜けて余剰ガス弁まで 1 本の通路（2026-11-03：以前は底から別の通路を描いていて、その角張った
# 黒い端が台座の通路にかぶさり、遮られて見えた）
add(f'<path d="M {HXc},{SY} L {HXc},{VY1 - 6}" fill="none" stroke="{K}" stroke-width="{GAS_W-3}" stroke-linecap="butt"/>')
add(f'<path d="M {HXc},{SY} L {HXc},{VY1 - 6}" fill="none" stroke="{EXP}" stroke-width="{GAS_W-7}" stroke-linecap="butt"/>')
# 2026-11-02：逆止弁と同じ構造を下向きにした断面。ベローズが上がりきったあと（呼気の終わり）だけ弁板が開き、
# 回路の余ったガスを余剰ガス排出装置へ逃がす。吸気中は駆動ガスの圧で閉じている
_fo = T_FULL / CYC
check_valve(HXc, VY1, EXP, rot=180, anim=None if MANUAL else ([0, 0, -80, -80, 0], f"0;{_fo:.4f};{min(_fo + 0.01, 0.98):.4f};0.99;1"))
text("余剰ガス弁", HXc + 16, VY1 + 26, 13, color="#333")
pipe([(HXc, VY1 + 9), (HXc, SC_T)], inner=EXP)   # 2026-11-02：点線から管に（余剰ガス弁 → 余剰ガス排出装置）
# 余剰ガス排出装置（2026-11-02）：金属の箱の中に透明なため（リザーバー）。回路から来たガスはためを通って右端の
# 吸引の口（黒：吸引の配管の色）から手術室の外へ吸い出される。ためは上の口で大気に開いていて、吸引が強すぎても
# 弱すぎても回路に陰圧・陽圧がかからない（開放型）
rect(760, SC_T, 556, 44, fill=METAL, rx=8)
_rx0, _rx1 = APX + 26, 1292
add(f'<rect x="{_rx0}" y="{SC_T+11}" width="{_rx1-_rx0}" height="22" rx="5" fill="{GLASS}" stroke="{K}" stroke-width="1.4"/>')
add(f'<line x1="{_rx0+6}" y1="{SC_T+14.5}" x2="{_rx1-6}" y2="{SC_T+14.5}" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>')
add(f'<line x1="{_rx0+6}" y1="{SC_T+29.5}" x2="{_rx1-6}" y2="{SC_T+29.5}" stroke="{GLASS_SHADE}" stroke-width="2.5" stroke-linecap="round"/>')
for _ex in (APX + 36, HXc):                                       # 上から来る管（ホース）の入口
    add(f'<rect x="{_ex-3.5}" y="{SC_T-1.2}" width="7" height="13" fill="{GLASS}"/>')
for _vx in (1150, 1164):                                         # 大気への口（2026-11-03：余剰ガス弁からの管（x = 1063）と重なったので右へ）
    add(f'<rect x="{_vx-3}" y="{SC_T-1.2}" width="6" height="13" fill="{GLASS}"/>')
text("大気", 1157.0, SC_T - 6, 12, "middle", color="#333")
add(f'<rect x="{_rx1}" y="{SC_T+13}" width="18" height="18" rx="2" fill="{K}"/>')   # 吸引の口
text("吸引", _rx1 + 9, SC_T + 26, 9, "middle", 700, "#fff", halo=False)
text("→ 手術室外へ", 1260, SC_T - 7, 16, "middle", color="#333")


# ================= 経路データ（JS シミュレーション用） =================


J_FG = (AX, 230)
VP = (HX0 + 3, SY)                                     # 人工呼吸器の口（ベローズ基部の横面）
LG = HIL                                               # 肺胞の入口（気管分岐部）
TUBES = {
    "A": [J_FG, (AX, MAN_Y)] + valve_detour(IV_X, MAN_Y, 1) + [(IP[0], MAN_Y)] + qpts(IP, C_I, YI)[1:] + [(YX, YY)],     # 回路の入口 → 吸気弁 → 吸気蛇管 → Y
    "B": [(YX, YY), (TR_X, YY), HIL],                                                   # Y → 気管（死腔）→ 気管分岐部
    "C": [(YX, YY), YE] + qpts(YE, C_E, EP)[1:] + valve_detour(EV_X, EXP_Y, -1) + [(SX, EXP_Y)],                      # Y → 呼気蛇管 → 呼気弁 → 合流点
    "D": [(SX, EXP_Y), (AX, EXP_Y), (AX, CB), (AX, CT), J_FG],                          # 合流点 → 吸収装置 → 回路の入口
    "E": [(SX, EXP_Y), (SX, SY), VP],                                                     # 合流点 → 切替弁 → 人工呼吸器の口
    "S": [VP, (HXc, SY), (HXc, VY1), (HXc, SC_T + 22), (1300, SC_T + 22)],              # 台座 → 余剰ガス弁 → 排出装置 → 外
}
if MANUAL:
    # 用手換気：合流点 → 切替弁 → 左へ APL 弁の分岐まで（ここから呼吸バッグへ出入りする）。余ったガスは APL 弁の
    # 弁座と弁板のすき間から弁板のふちを回って余剰ガス排出装置へ（ピストン式の APL 弁と同じ道）
    VP = (APX, SY)
    TUBES["E"] = [(SX, EXP_Y), (SX, SY), VP]
    TUBES["S"] = [VP, (APX, SY + 19.5), (APX + 12, SY + 19.5), (APX + 12, SY + 30), (APX + 36, SY + 30),
                  (APX + 36, SC_T + 22), (1300, SC_T + 22)]
_bc = (BG_P - 44, SY)                              # 呼吸バッグの中心（大きさ 1 のとき）
BAG_SLOTS = [(_bc[0] + dx, _bc[1] + dy) for dy in (-18, -9, 0, 9, 18) for dx in (-18, -9, 0, 9, 18)
             if (dx / 26) ** 2 + (dy / 24) ** 2 <= 1]


_cD = cum(TUBES["D"])
PIN0, POUT0 = VAPS[0] - VW / 2 + 14, VAPS[0] + VW / 2 - 14
by_, cy_ = VT + 13, VT + 26 + 9

def supply_path(gx, chamber):
    seg = [(gx - 30, OUT_Y), (gx - 30, JOIN_Y), (gx, JOIN_Y), (gx, MAN_Y), (PIN0, MAN_Y), (PIN0, by_)]
    seg += ([(PIN0, cy_), (POUT0, cy_), (POUT0, by_)] if chamber else [(POUT0, by_)])
    seg += [(POUT0, MAN_Y), (CGO_X + 10, MAN_Y), (720, MAN_Y), (720, 230), J_FG]
    return seg

# 管ごとの粒の間隔の係数（>1 は粒がまばら）。2026-11-02 に呼気弁と吸収装置を上げて（呼気弁がベローズの
# ハウジングに接していたため）管 C・D が短く、E が長くなった。粒の数と管を通り抜ける時間が変わると、
# 新鮮ガス多めの場面で吸収装置に届く CO2 が 0 になるなど振る舞いまで変わるので、間隔を長さに比例させて
# 配置を変える前の管の長さ（下の値、px）と同じ粒の数に保つ
TUBE_REF_LEN = {"A": 463.721, "C": 371.995, "D": 360.0, "E": 189.0}   # A：2026-11-02 吸気弁の中の回り道を足す前の長さ
TUBE_SPACING = {k: round(plen(TUBES[k]) / v, 4) for k, v in TUBE_REF_LEN.items()}
GEO = {
    "CYC": CYC, "TI": TI, "FG_RATE": FG_RATE, "NB_FULL": NB_FULL, "NB_MIN": NB_MIN,
    "VT_B": VT_B, "VT_P": VT_P, "T_FULL": T_FULL,
    "SP": 40.0, "SUP_V": 88.0, "SCAV_V": 120.0, "LUNG_MIN": LUNG_MIN,
    # 新鮮ガスの粒が回路に届く時刻のずれ（到着の間隔に対する割合）。低流量では到着の間隔（2 秒）が吸気時間と
    # 同じで、ずらさないと毎回ちょうど流れの切り替わりの瞬間に届き、合流点で粒が重なって回路を回り続ける
    "supplyPhase": 0.5 if LOW_FLOW else 0.0,
    "tubeSpacing": TUBE_SPACING,
    "tubes": TUBES,
    "absD": [_cD[2], _cD[3]],                                  # D の弧長のうち吸収装置の範囲
    # 吸収剤の層（入口側から）：D の弧長の範囲。層ごとの容量は CO2 の粒の数（時間を縮めた値）
    "absorber": {
        "rows": [[_cD[2] + (CB - (PT + 7 + r * ABS_PITCH + ABS_PITCH / 2)), _cD[2] + (CB - (PT + 7 + r * ABS_PITCH - ABS_PITCH / 2))]
                 for r in reversed(range(ABS_ROWS))],
        "cap": ABS_CAP, "spread": [0.6, 0.3, 0.1],
        "fresh": "#ffffff", "used": ABS_USED_C,
    },
    # 供給路は 4 本：流量計（O2 は x=420、N2O は x=100）から合流管で混ざった新鮮ガスを、気化室とバイパスに分ける。
    # 粒の番号 k で選ぶ（偶数 O2・奇数 N2O、6 粒のうち 2 粒が気化室）。2026-11-04：O2 だけが気化室・N2O だけがバイパスに固定されていたのを直した
    "supply": [supply_path(420, True), supply_path(100, False), supply_path(420, False), supply_path(100, True)],
    "nodes": {"VP": VP, "JFG": J_FG, "SX": (SX, EXP_Y), "Y": (YX, YY), "LG": LG},
    "bellows": {"HXc": HXc, "BBOT": BBOT, "BTOP": BTOP, "BX0": BX0, "BX1": BX1, "HY0": HY0,
                "keyT": BELLOWS_KT, "keyS": BELLOWS_SC},
    "lung": {"hilum": HIL, "s0": LUNG_S0, "s1": LUNG_S1,
             "slots": [(lx + dx, LOBE_T + 10 + 11.5 * r) for lx in LOBES for r in range(8) for dx in (-6, 6)]},
    "exhale": {"tau": TAU, "tEnd": T_EXH},
}
if MANUAL:                                          # 用手換気：ベローズの代わりに呼吸バッグにためる（sim_bellows.js が見る）
    GEO["bag"] = {"pivot": (BG_P, SY), "slots": BAG_SLOTS, "keyT": BELLOWS_KT, "keyS": BAG_S}
    GEO["nodes"]["BAGM"] = (BG_P - 14, SY)
if len(sys.argv) > 3:
    json.dump(GEO, open(sys.argv[3], "w"), ensure_ascii=False)
add('<g id="particles"></g>')
C_FRESH, C_EXPG, C_DRV = "#2b2b2b", C_CO2_DOT, "#7a7a7a"   # 粒の色（新鮮／CO2 を含む／駆動ガス）

def _plate_top(t):
    """時刻 t の天板の上端（ベローズのアニメーションと同じキー）"""
    ks, vs = BELLOWS_KT, BELLOWS_SC
    for (t0, v0), (t1, v1) in zip(zip(ks, vs), zip(ks[1:], vs[1:])):
        if t0 <= t <= t1:
            v = v0 + (v1 - v0) * (t - t0) / (t1 - t0) if t1 > t0 else v1
            return BBOT - v * (BBOT - BTOP)
    return BTOP


def _along(pts, u):
    """折れ線 pts の上で、全長に対する割合 u の位置"""
    segs = list(zip(pts, pts[1:]))
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    d = u * sum(lens)
    for (a, b), L in zip(segs, lens):
        if d <= L or L == sum(lens):
            r = d / L if L else 0
            return a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r
        d -= L
    return pts[-1]


ND, TRIP, DT = 9, 0.45, 0.05            # 駆動ガスの粒の数＝ベローズから出入りする粒の数（体積の釣り合い）
OUTSIDE, PORT = (DRV_END, HY0 + 7), (HX1 - 3, HY0 + 7)
ts = [i * DT for i in range(int(CYC / DT) + 1)]
for i in (range(ND) if not MANUAL else ()):      # 用手換気では駆動ガスは動かない
    # 横と高さの位置を、互いに関係しない 2 つの数列で決めて、空間全体に散らす
    fx = HX0 + 9 + (HX1 - HX0 - 18) * ((i * 0.618034 + 0.1) % 1.0)
    ff = 0.10 + 0.80 * ((i * 0.754878 + 0.35) % 1.0)
    t_in = 0.05 + i * (TI - 0.55) / ND                                 # 入り始める時刻
    t_out = TI + 0.05 + i * (T_FULL - TI - 0.1 - TRIP) / max(1, ND - 1)  # 出始める時刻（ベローズが満杯になるまで）
    xs, ys, ops = [], [], []
    for t in ts:
        home = (fx, HY0 + 5 + ff * max(0.0, _plate_top(t) - HY0 - 10))
        if t < t_in or t >= t_out + TRIP:
            x, y, o = OUTSIDE[0], OUTSIDE[1], 0
        elif t < t_in + TRIP:
            x, y = _along([OUTSIDE, PORT, home], (t - t_in) / TRIP); o = 1
        elif t < t_out:
            x, y, o = home[0], home[1], 1
        else:
            x, y = _along([home, PORT, OUTSIDE], (t - t_out) / TRIP); o = 1
        xs.append(f"{x:.1f}"); ys.append(f"{y:.1f}"); ops.append(str(o))
    kt = ";".join(f"{t / CYC:.4f}" for t in ts)
    add(f'<circle r="3" fill="{C_DRV}" stroke="#fff" stroke-width="1" cx="{OUTSIDE[0]}" cy="{OUTSIDE[1]}" opacity="0">'
        f'<animate attributeName="cx" values="{";".join(xs)}" keyTimes="{kt}" dur="{CYC}s" repeatCount="indefinite"/>'
        f'<animate attributeName="cy" values="{";".join(ys)}" keyTimes="{kt}" dur="{CYC}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="{";".join(ops)}" keyTimes="{kt}" calcMode="discrete" dur="{CYC}s" repeatCount="indefinite"/>'
        '</circle>')


# ================= 字幕と進行バー =================
add('<g class="svgcap">')
CAP_Y = 830
add(f'<rect x="12" y="{CAP_Y-28}" width="{W-24}" height="44" rx="8" fill="#f4f1fb" stroke="#cbbfe8"/>')
_CAPS = ((("insp", "吸気", "呼吸バッグを手で押すと、ガスは切替弁から吸収装置と吸気弁を通って患者へ送られる"),
          ("exp", "呼気", "呼気と新鮮ガスが呼吸バッグへ戻ってふくらませる。いっぱいになって圧が上がると APL 弁から余剰ガス排出装置へ"))
         if MANUAL else
         (("insp", "吸気", "駆動ガス（O₂）がベローズを押し下げ、ガスは吸収装置と吸気弁を通って患者へ送られる"),
          ("exp", "呼気", "呼気と新鮮ガスがベローズを下から押し上げる。上まで上がると、余ったガスは余剰ガス排出装置へ")))
for ph, label_, msg in _CAPS:
    add(gate_open(ph))
    add(f'<rect x="24" y="{CAP_Y-20}" width="64" height="28" rx="6" fill="{K if ph == "insp" else EXP_ARROW}"/>')
    text(label_, 56, CAP_Y + 1, 18, "middle", 700, "#fff", halo=False)
    text(msg, 100, CAP_Y + 1, 17, halo=False)
    add('</g>')
BX, BW = 1150, 170
add(f'<rect x="{BX}" y="{CAP_Y-8}" width="{BW*TI/CYC:.1f}" height="10" fill="#444"/>')
add(f'<rect x="{BX + BW*TI/CYC:.1f}" y="{CAP_Y-8}" width="{BW*(1-TI/CYC):.1f}" height="10" fill="{EXP_ARROW}"/>')
add(f'<rect x="{BX}" y="{CAP_Y-14}" width="3" height="22" fill="#d33"><animate attributeName="x" values="{BX};{BX+BW}" dur="{CYC}s" repeatCount="indefinite"/></rect>')

add('</g>')

# ================= 部品の名前（記号なし） =================
# ガス供給：右側の列に縦にそろえ、O2 の系統へ引き出し線でつなぐ
LX = 500
label("③", "逆止弁", LX, CHK_Y); leader(463, CHK_Y, LX - 16, CHK_Y)
label("②", "減圧弁", LX, REG_Y); leader(467, REG_Y, LX - 16, REG_Y)
label("①", "ボンベ", LX, 603); leader(476, 603, LX - 16, 603)
label("①", "中央配管", LX, OUT_Y + 14); leader(412, OUT_Y + 14, LX - 16, OUT_Y + 14)
text("亜酸化窒素", 130, CUT_Y - 18, 17); text("遮断弁", 130, CUT_Y + 3, 17)
label("⑤", "流量計", 48, 205, "below")   # 2026-11-04：図の枠の点線にかからないよう右へ
label("⑥", "酸素フラッシュ", 512, FLUSH_Y + 45, "right")
label("⑦", "気化器", 500, VB + 66, "right")
label("⑧", "共通ガス出口", CGO_X + 10, 56, "left")
# 呼吸回路
label("⑨", "吸気弁", IV_X, 62, "right")
text("蛇管・", 1202, 165, 18); text("Yピース", 1202, 189, 18)
text("二酸化炭素", 848, 335, 18); text("吸収装置", 848, 359, 18)
label("⑪", "呼気弁", EV_X, EXP_Y - 58, "left")
text("APL弁", APX + 10, SY - 14, 19, "middle")   # 2026-11-02：APL 弁の真上（管のすぐ上）へ。旧：label(…, SY - 46, "left") で左上に離れていた
text("呼吸バッグ", 734, SY + 46, 15, "middle")
text("切替弁", SX, SY + 50, 17, "middle")
text("余剰ガス排出装置", 848, SC_T - 7, 17)   # 2026-11-02：ためを APL 弁の管まで延ばしたので箱の上へ（APL 弁の管と余剰ガス弁の管の間）

# ================= 凡例 =================
L2 = 770
# 2026-11-02：管の色の凡例（吸気側・呼気側）をやめ、粒の色の凡例にした
add(f'<circle cx="30" cy="{L2-6}" r="6" fill="#2b2b2b" stroke="#fff" stroke-width="1"/>')
text("CO₂ を含まないガス", 44, L2, 17)
add(f'<circle cx="222" cy="{L2-6}" r="6" fill="{C_CO2_DOT}" stroke="#fff" stroke-width="1"/>')
text("CO₂ を含むガス", 236, L2, 17)
# 2026-11-02：流れの矢印の凡例はやめた（流れの矢印をやめたため）

out[PIPE_MARK:PIPE_MARK] = flush_pipes()
add("</svg>")
open(sys.argv[1], "w").write("\n".join(o for o in out if o))
