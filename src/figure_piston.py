# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
"""麻酔器・呼吸回路の模式図（ピストン式）実行時シミュレーション用の土台 SVG。
弁・ピストン・呼吸バッグ・肺の動きは SMIL、ガスの粒はブラウザ側の JS（sim_piston.js）が描く。
管の経路や部屋の位置は JSON（argv[3]）に書き出す。make_anim_piston.py（SMIL で粒を流す旧版）から作った。

使い方: python3 figure_piston.py out.svg color out_geo.json [low] [manual] [en]
  low を付けると低流量の場面（新鮮ガスを 1/4 に減らす。ピストンの 1 回換気量は変わらない）
"""
import json
import math
import sys

import palette
import svg
from geometry import cum, plen, qpts, unit
from palette import *   # noqa: F401,F403  色と字体（K・B・METAL・GLASS など）
from parts import (FM_W_BOT, FM_W_TOP, alveoli_path, breathing_bag, bronchus, check_valve, collar, hose, one_way_valve, port,
                   squeeze_mark, valve_detour)
from svg import CYC, GAS_W, TI, add, anim, arrow, dashed, flush_pipes, gate_win, label, leader, out, pipe, rect, text


MODE = sys.argv[2] if len(sys.argv) > 2 else "2c"
LUNG_TISSUE, EXP_C, EXP_ARROW, PIPE, CYL, WICK = (palette.by_mode(MODE)[k] for k in ("LUNG_TISSUE", "EXP_C", "EXP_ARROW", "PIPE", "CYL", "WICK"))
W, H = 1340, 860           # 患者（気管・肺胞）を描くため旧版より 40 px 広い
T2 = 3.6                   # 呼気①（2〜3.6 秒：呼気がバッグへ）と呼気②（3.6〜6 秒：ピストンが吸い込む）
T3 = CYC - 0.3             # ピストンが下がりきる時刻（5.7〜6 秒は止まっている）
_FLAGS = set(sys.argv[4:])
LOW_FLOW = "low" in _FLAGS
MANUAL = "manual" in _FLAGS               # 用手換気の場面（ピストンは止まり、呼吸バッグを手で押して換気する。2026-11-02）
LANG = "en" if "en" in _FLAGS else "zh" if "zh" in _FLAGS else "tw" if "tw" in _FLAGS else "ja"       # en：図の中の文字を英語にする（labels_en.py。2026-11-02）
svg.configure(LANG, "p")
FG_RATE = 0.5 if LOW_FLOW else 2.0     # 新鮮ガス（粒/秒）。上昇式ベローズの図と同じ値
VT_P = 13                  # ピストンが送る量＝患者に入る量（粒）。デカップリング弁があるので新鮮ガスの量によらない
NC_FULL, NC_MIN = 15, 2    # シリンダーの中の粒（ピストンが下・上）
NG_FULL = 18               # 呼吸バッグが満杯の粒。これを超える分は余剰ガス排出装置へ
VP_IN = VT_P / TI          # 吸気のピストンの送り出し（粒/秒）
V_DRAW = VT_P / (T3 - T2)  # 呼気②のピストンの吸い込み（粒/秒）
# 呼気は受動的（上昇式ベローズの図と同じ）：時定数 TAU、T_EXH で吐き終える
TAU = 1.2
T_EXH = (CYC - TI) - 0.3
LUNG_MIN = 6


def exh_frac(dt):
    if dt <= 0:
        return 0.0
    if dt >= T_EXH:
        return 1.0
    return (1 - math.exp(-dt / TAU)) / (1 - math.exp(-T_EXH / TAU))


def ex_rate(dt):
    if dt < 0 or dt >= T_EXH:
        return 0.0
    return VT_P * math.exp(-dt / TAU) / (TAU * (1 - math.exp(-T_EXH / TAU)))


def lung_vol(t):
    if t < TI:
        return LUNG_MIN + VT_P * t / TI
    return LUNG_MIN + VT_P * (1 - exh_frac(t - TI))


LUNG_S0, LUNG_S1 = 0.82, 1.0
def lung_scale(t):
    return LUNG_S0 + (LUNG_S1 - LUNG_S0) * (lung_vol(t) - LUNG_MIN) / VT_P


VB_MAN = (VT_P - FG_RATE * TI) / TI    # 用手換気の吸気でバッグから押し出す量（粒/秒）。吸気中の新鮮ガスと合わせて VT_P


def bag_inflow(t):
    """呼吸バッグへ入る量（粒/秒、満杯で逃がす前）。吸気と 5.7 秒以降は新鮮ガスが吸収装置を逆に通って入り、
    呼気では呼気も入る。呼気②はピストンが吸い込む分（新鮮ガスで足りない分）が出ていく。
    用手換気では、吸気で手で押した分が出ていき、呼気で呼気と新鮮ガスが入る"""
    ex = ex_rate(t - TI) if t >= TI else 0.0
    if MANUAL:
        return -VB_MAN if t < TI else ex + FG_RATE
    if t < TI:
        return FG_RATE
    if t < T2:
        return ex + FG_RATE
    if t < T3:
        return ex - (V_DRAW - FG_RATE)
    return ex + FG_RATE


def _bag_cycle(n0, dt=0.001):
    n, out = n0, []
    for k in range(int(CYC / dt) + 1):
        t = k * dt
        out.append((t, n))
        n = min(NG_FULL, n + bag_inflow(t) * dt)
    return out


_n0 = NG_FULL - 6.0
for _ in range(50):                               # 周期的になる始めの量を探す
    _n0 = _bag_cycle(_n0)[-1][1]
_bag = _bag_cycle(_n0)
BAG_KT = [round(k * 0.1, 1) for k in range(int(CYC / 0.1) + 1)]
BAG_N = [_bag[min(len(_bag) - 1, int(round(t / 0.001)))][1] for t in BAG_KT]
BAG_S = [0.75 + 0.42 * n / NG_FULL for n in BAG_N]        # 呼吸バッグの大きさ（満杯で 1.17 倍）
PH_LO, PH_HI = 226, 162                                   # ピストンの頭（下・上）
HEAD_KT = [0.0, TI, T2, T3, CYC]
HEAD_Y = [PH_HI] * 5 if MANUAL else [PH_LO, PH_HI, PH_HI, PH_LO, PH_LO]   # 用手換気ではピストンは上で止まっている
ABS_CAP = 15.0             # 吸収剤 1 層の容量（上昇式ベローズの図と同じ）


    # 2026-11-02：本体の下の流れの向きの矢印はやめた（粒の動きで分かる）。show_arrow は使わない


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
CT, CB = 300, 440
EXP_Y = 480                       # 呼気側の横の管
SX, SY = 900, 580                 # 切替弁
IV_X = 1058                       # 吸気弁（2026-11-02：回路内圧計に近すぎたので 28 px 右へ）
EV_X = 1110                       # 呼気弁
YX, YY = 1190, 290                # Y ピース

# ================= 土台 =================
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add(f'<rect width="{W}" height="{H}" fill="#fff"/>')
add('<defs><pattern id="gasdots" width="11" height="11" patternUnits="userSpaceOnUse">'
    '<circle cx="3" cy="3" r="1.6" fill="#a8a8a8"/><circle cx="8.5" cy="8.5" r="1.6" fill="#a8a8a8"/></pattern></defs>')
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
    fy = FM_B - 14 if name == "Air" else (FM_B - 24 if LOW_FLOW else FM_B - 46)     # Air は流していない。低流量ではフロートが低い
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

# ================= 呼吸回路（ピストン式） =================
# Dräger Fabius 型の構成（Miller's Anesthesia 10th ed., Ch.20 の記述に基づく）。
# 吸収装置 → [新鮮ガスの入口] → 新鮮ガス・デカップリング弁 → ピストン → 吸気弁 → 患者
# → 呼気弁 → PEEP/Pmax 弁 → 呼吸バッグ（換気中もリザーバー）・APL 弁 → 吸収装置
INSP, EXP = INSP_C, EXP_C
FG_Y = 282                                  # 新鮮ガスが回路に入る高さ（吸収装置の出口のすぐ上）
DV_X = 850                                  # 新鮮ガス・デカップリング弁
PS_X = 940                                  # ピストンの取り付け位置
pipe([(CGO_X + 20, MAN_Y), (720, MAN_Y), (720, FG_Y), (AX - 6, FG_Y)], inner=INSP)
pipe([(AX, CT), (AX, MAN_Y), (IV_X - 32, MAN_Y)], inner=INSP)
# 回路内圧計：ピストンと吸気弁のあいだの管から立ち上げる。針は回路内圧（cmH2O）に合わせて回る。
# 目盛は 0〜30 cmH2O を 240°（150°→390°）に割り当てる。
# 波形（従量式・定常流の模式）：吸気の始めに抵抗分だけ跳ね上がり、吸気中は直線的に上がって吸気終末で最高。
# 呼気に入ると急に下がり、呼気終末は PEEP/Pmax 弁の設定値（ここでは 0 相当）まで下がる
# （上昇式ベローズでは余剰ガス弁の開放圧 2〜3 cmH2O が残るのと対照的）
GX, GY = 988, 78
pipe([(GX, MAN_Y), (GX, GY + 18)], inner=INSP, w=9)
add(f'<circle cx="{GX}" cy="{GY}" r="20" fill="#fff" stroke="{K}" stroke-width="2.2"/>')
for k in range(7):
    aa = math.radians(150 + k * 40)
    add(f'<line x1="{GX+14*math.cos(aa):.1f}" y1="{GY+14*math.sin(aa):.1f}" x2="{GX+19*math.cos(aa):.1f}" y2="{GY+19*math.sin(aa):.1f}" stroke="{K}" stroke-width="1.5"/>')
P_KEYS = [(0.0, 0.5), (0.12, 6.0), (TI, 16.0), (TI + 0.12, 3.0), (3.0, 1.0), (T2, 0.5), (CYC, 0.5)]
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
text("回路内圧計", GX, GY - 28, 13, "middle", color="#333")
text("cmH₂O", GX, GY - 42, 10, "middle", color="#555")


IP = (IV_X + 32 + 16, MAN_Y)
EP = (EV_X + 32 + 16, EXP_Y)
C_I = (1140, MAN_Y)
C_E = (1232, EXP_Y)
YL = 36
_ui = unit(C_I[0], C_I[1], YX, YY)
_ue = unit(C_E[0], C_E[1], YX, YY)
YI = (YX - YL * _ui[0], YY - YL * _ui[1])
YE = (YX - YL * _ue[0], YY - YL * _ue[1])
YP = (1218, YY)
# 呼気側：呼気弁 → PEEP/Pmax 弁 → 吸収装置
PV_X = 1010
pipe([(EV_X + 32, EXP_Y), (AX, EXP_Y), (AX, CB)], inner=EXP)
port(IV_X + 32, MAN_Y, IP[0], IP[1])
port(EV_X + 32, EXP_Y, EP[0], EP[1])
hose((IP[0] + 3, IP[1]), C_I, YI, INSP)
hose((EP[0] + 3, EP[1]), C_E, YE, EXP)
# 患者：Y ピースの口から気管（死腔）が右へ、そして下へ降り、気管分岐部で 2 葉の肺胞につながる
TR_X = 1272
HIL = (TR_X, YY + 92)
LOBES = (TR_X - 19, TR_X + 19)
LOBE_W, LOBE_T, LOBE_B = 30, HIL[1] + 24, HIL[1] + 130
LOBE = (LOBE_W, LOBE_T, LOBE_B)
_tr = f"M {YP[0]},{YY} L {TR_X},{YY} L {TR_X},{HIL[1]}"
add(f'<path d="{_tr}" fill="none" stroke="{K}" stroke-width="16" stroke-linecap="butt" stroke-linejoin="round"/>')


for lx in LOBES:
    x0, y0, x1, y1 = bronchus(lx, 0.0, 1.0, HIL, LOBE_T)
    add(f'<path d="M {x0},{y0} L {x1:.1f},{y1:.1f}" stroke="{K}" stroke-width="12" stroke-linecap="butt"/>')
add(f'<circle cx="{HIL[0]}" cy="{HIL[1]}" r="8" fill="{K}"/>')
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
add(f'<path d="{_tr}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="butt" stroke-linejoin="round"/>')
add(f'<circle cx="{HIL[0]}" cy="{HIL[1]}" r="5" fill="#fff"/>')
for lx in LOBES:
    x0, y0, x1, y1 = bronchus(lx, 0.0, 0.62, HIL, LOBE_T)
    add(f'<path d="M {x0},{y0} L {x1:.1f},{y1:.1f}" stroke="#fff" stroke-width="6" stroke-linecap="butt"/>')
    x0, y0, x1, y1 = bronchus(lx, 0.62, 1.22, HIL, LOBE_T)
    add(f'<path d="M {x0:.1f},{y0:.1f} L {x1:.1f},{y1:.1f}" stroke="{B_TINT2}" stroke-width="6" stroke-linecap="butt"/>')
text("患者", TR_X, YY - 20, 15, "middle", 700)
text("気管", TR_X + 10, YY + 52, 12, color="#333")
text("（死腔）", TR_X + 4, YY + 68, 11, color="#333")
if LANG == "en":                                  # 英語は 1 行では図の枠の点線にかかるので、(dead と space) の 2 行に分ける
    text("space)", TR_X + 10, YY + 75, 9, color="#333")
text("肺胞", TR_X, LOBE_B + 22, 13, "middle", color="#333")   # 2026-11-02：輪郭の袋のふくらみの分 4 px 下げた
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
one_way_valve(IV_X, MAN_Y, 1, INSP_FILL, open_win=(0, TI))
one_way_valve(EV_X, EXP_Y, -1, EXP, open_win=(TI, CYC))
# 新鮮ガス・デカップリング弁：吸気中はピストンの圧で閉じ、新鮮ガスをバッグ側へ逃がす
one_way_valve(DV_X, MAN_Y, 1, B_TINT2, open_win=(0, TI) if MANUAL else (T2, T3))   # 用手換気では吸気でバッグのガスが通る
# PEEP/Pmax 弁：呼気終末の圧を保ち、ピストンが肺からガスを引き込まないようにする
# 2026-11-02：ばねで弁板を押さえた一方向弁（ドーム弁）の断面に。呼気の圧がばねの力（設定値）を超えたときだけ開く
one_way_valve(PV_X, EXP_Y, -1, EXP, open_win=(TI, CYC), spring=True)
text("PEEP/Pmax弁", PV_X, EXP_Y + 44, 15, "middle", 700, color="#333")
# ピストン：モーターで動くシリンダー。下がるとき（呼気）にバッグと新鮮ガスを吸い込み、
# 上がるとき（吸気）に患者へ送る
CY0, CY1 = 150, 250
pipe([(PS_X, MAN_Y), (PS_X, CY0 + 2)], inner=INSP)
# シリンダー（2026-11-02）：金属の筒の断面（灰の壁）。上の口から回路のガスが出入りする
rect(PS_X - 26, CY0, 52, CY1 - CY0, fill=METAL, rx=6)
add(f'<rect x="{PS_X-22}" y="{CY0+4}" width="44" height="{CY1-CY0-8}" fill="#fff"/>')
add(f'<rect x="{PS_X-3.5}" y="{CY0-1.2}" width="7" height="6" fill="#fff"/>')
PH = 200                                    # ピストンの頭の位置
_pk = ";".join(f"{k/CYC:.4f}" for k in HEAD_KT)
_ph = ";".join(str(v) for v in HEAD_Y)
_gh = ";".join(str(int(v) - (CY0 + 4)) for v in _ph.split(";"))
add(f'<rect x="{PS_X-22}" y="{CY0+4}" width="44" height="{PH_LO-CY0-4}" fill="#fff">' + anim("height", _gh, _pk) + '</rect>')
add(f'<defs><clipPath id="pgas"><rect x="{PS_X-22}" y="{CY0+2}" width="44" height="{PH_LO-CY0-2}">'
    + anim("height", ";".join(str(int(v) + 2) for v in _gh.split(";")), _pk) + '</rect></clipPath></defs>')
# ピストンの頭（青＝動く部品）と、壁との間をふさぐシール（黒い帯）。ロッドは金属
_pr = ";".join(str(int(v) + 8) for v in _ph.split(";"))
add(f'<line x1="{PS_X}" y1="{PH_LO+8}" x2="{PS_X}" y2="{CY1+16}" stroke="{K}" stroke-width="7">' + anim("y1", _pr, _pk) + '</line>')
add(f'<line x1="{PS_X}" y1="{PH_LO+8}" x2="{PS_X}" y2="{CY1+16}" stroke="{METAL}" stroke-width="3.4">' + anim("y1", _pr, _pk) + '</line>')
add(f'<rect x="{PS_X-22}" y="{PH_LO}" width="44" height="9" rx="1.5" fill="{B}" stroke="{K}" stroke-width="1.5">' + anim("y", _ph, _pk) + '</rect>')
_ps = ";".join(str(int(v) + 3.5) for v in _ph.split(";"))
add(f'<rect x="{PS_X-22}" y="{PH_LO+3.5}" width="44" height="2" fill="{K}">' + anim("y", _ps, _pk) + '</rect>')
# モーター：金属の箱（両端は濃い灰のふた、上に軸受け）。ロッドを上下に動かす
rect(PS_X - 36, CY1 + 16, 72, 26, fill=METAL, rx=4)
for _ex in (PS_X - 36, PS_X + 31):
    add(f'<rect x="{_ex}" y="{CY1+16}" width="5" height="26" rx="1.5" fill="#9a9a9a" stroke="{K}" stroke-width="1.4"/>')
add(f'<rect x="{PS_X-7}" y="{CY1+11}" width="14" height="6" rx="1" fill="{METAL}" stroke="{K}" stroke-width="1.4"/>')
text("モーター", PS_X, CY1 + 34, 14, "middle", 700, halo=False)
if not MANUAL:
    arrow(PS_X + 36, PH - 12, -90, K, 10)
    arrow(PS_X + 36, PH + 18, 90, K, 10)
    add(f'<line x1="{PS_X+36}" y1="{PH-8}" x2="{PS_X+36}" y2="{PH+14}" stroke="{K}" stroke-width="2"/>')
text("ピストン", PS_X, CY1 + 66, 16, "middle", 700)
if MANUAL:   # 用手換気で止まっていることの注記。操作ページでは隠して解説に回す（class="svgnote"。コマ撮りでは出す。2026-11-02）
    add('<g class="svgnote">')
    text("（止まっている）", PS_X + 36, CY1 + 66, 13, color="#666")
    add('</g>')
# 外気取り込み弁（陰圧防止）：新鮮ガスが足りないとき外気を入れ、回路の陰圧を防ぐ
AV_Y = 172
add(f'<line x1="{PS_X+26}" y1="{AV_Y}" x2="{PS_X+46}" y2="{AV_Y}" stroke="{K}" stroke-width="7"/>')
add(f'<line x1="{PS_X+26}" y1="{AV_Y}" x2="{PS_X+46}" y2="{AV_Y}" stroke="#fff" stroke-width="3"/>')
check_valve(PS_X + 58, AV_Y, rot=-90)       # 2026-11-02：逆止弁の断面（右の外気側から左のシリンダーへだけ通す。閉じた姿）
arrow(PS_X + 82, AV_Y, 180, K, 10)
text("外気取り込み弁", PS_X + 88, AV_Y - 2, 14, color="#333")
text("（陰圧防止）", PS_X + 88, AV_Y + 16, 13, color="#333")
# 二酸化炭素吸収装置：下から入った呼気が吸収剤の層を上へ抜ける
# 容器は透明な樹脂：流量計のガラス管と同じ薄い青で「透けて中の吸収剤が見える」ことを示し、
# 左の白い照りと右の青い影（平らな線）で円筒に見せる。上下は回路につながる金属の口金（2026-11-02）
add(f'<rect x="{AX-40}" y="{CT}" width="80" height="{CB-CT}" rx="10" fill="{GLASS}" stroke="{K}" stroke-width="2.2"/>')
add(f'<line x1="{AX-35.5}" y1="{CT+12}" x2="{AX-35.5}" y2="{CB-12}" stroke="#fff" stroke-width="3" stroke-linecap="round"/>')
add(f'<line x1="{AX+35.5}" y1="{CT+12}" x2="{AX+35.5}" y2="{CB-12}" stroke="{GLASS_SHADE}" stroke-width="3" stroke-linecap="round"/>')
PT, PB = CT + 14, CB - 14
ABS_ROWS, ABS_PITCH = 9, 12.6
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
# 呼吸バッグ（人工呼吸中もリザーバーとして回路に残る）と APL 弁
pipe([(SX, EXP_Y), (SX, SY), (782, SY)], inner=EXP)
APX = 812
BYP_X = 878                                  # APL バイパス弁（2026-11-02）
pipe([(SX - 36, SY), (782, SY)], inner=EXP)
pipe([(APX, SY), (APX, SY + 10)], inner=EXP, w=10)
# APL 弁の断面（2026-11-02）：上の口から入ったガスの圧が、ばねで弁座に押しつけられた弁板（青）を押し下げると開き、
# 横の出口から余剰ガス排出装置へ出る。下のつまみを回すと、ねじでばねの受けが上下し、開く圧（設定圧）が変わる。
# 用手換気では、バッグが満杯になると APL 弁から余るガスを逃がすので、開いた姿（弁板を下げた姿）で描き、
# 粒は弁座と弁板のすき間から弁板のふちを回って出口へ出る（GEO の管 S）。
# 人工呼吸中は APL バイパス弁（下）が開いていて、余るガスはそちらから出るので、APL 弁は閉じた姿（2026-11-02。
# Miller 10e 図 20.44：Fabius では人工呼吸中は APL バイパス弁が開き、余ったガスは排気の逆止弁を通って
# 余剰ガス排出装置へ出る。用手・自発呼吸ではバイパス弁が閉じ、APL 弁が働く。旧版は人工呼吸中も APL 弁が開く形だった）
APL_DZ = 6 if MANUAL else 0                  # 弁板が弁座から下がっている量（0 なら閉）
rect(APX - 20, SY + 8, 40, 48, fill=METAL, rx=5)
add(f'<rect x="{APX-3.5}" y="{SY+6.8}" width="7" height="{7.8}" fill="{EXP}"/>')            # 入口
add(f'<rect x="{APX-16}" y="{SY+14}" width="32" height="32" fill="{EXP}"/>')               # 弁の部屋
add(f'<rect x="{APX+15}" y="{SY+26.5}" width="6.2" height="7" fill="{EXP}"/>')            # 出口（右へ）
for _sx in (APX - 9, APX + 3.5):
    add(f'<rect x="{_sx}" y="{SY+14}" width="5.5" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # 弁座
add(f'<rect x="{APX-8.5}" y="{SY+16.5+APL_DZ}" width="17" height="3.5" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')
_s0, _s1 = SY + 20 + APL_DZ, SY + 44
add(f'<path d="M {APX},{_s0} ' + " ".join(f"L {APX + (6 if k % 2 else -6)},{_s0 + (_s1 - _s0) * k / 6:.1f}" for k in range(1, 6))
    + f' L {APX},{_s1}" fill="none" stroke="{K}" stroke-width="1.5" stroke-linejoin="round"/>')
add(f'<rect x="{APX-9}" y="{SY+44}" width="18" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')     # ばねの受け
add(f'<rect x="{APX-2.5}" y="{SY+46.5}" width="5" height="12" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # ねじ
for _k in range(3):
    add(f'<line x1="{APX-2.5}" y1="{SY+50+3.5*_k}" x2="{APX+2.5}" y2="{SY+48+3.5*_k}" stroke="{K}" stroke-width="0.8"/>')
rect(APX - 12, SY + 58, 24, 12, fill=METAL, rx=2, sw=1.8)                                        # つまみ（ぎざぎざ）
for _k in range(1, 6):
    add(f'<line x1="{APX-12+4*_k}" y1="{SY+59}" x2="{APX-12+4*_k}" y2="{SY+69}" stroke="{K}" stroke-width="1"/>')
# APL バイパス弁（2026-11-02）：APL 弁と並んでバッグの管から分かれ、人工呼吸中は開いて、余るガスを APL 弁を通さずに
# 排出へ逃がす。用手換気・自発呼吸では閉じて、APL 弁を働かせる。実機は換気モードに合わせて自動で開閉する
# （図では弁板を下の操作部の棒で動かす形）。断面は APL 弁を左右反転し、ばねとつまみの代わりに操作部を付けた
BYP_DZ = 0 if MANUAL else 6
pipe([(BYP_X, SY), (BYP_X, SY + 10)], inner=EXP, w=10)
rect(BYP_X - 20, SY + 8, 40, 36, fill=METAL, rx=5)
add(f'<rect x="{BYP_X-3.5}" y="{SY+6.8}" width="7" height="7.8" fill="{EXP}"/>')            # 入口
add(f'<rect x="{BYP_X-16}" y="{SY+14}" width="32" height="22" fill="{EXP}"/>')             # 弁の部屋
add(f'<rect x="{BYP_X-21.2}" y="{SY+26.5}" width="6.2" height="7" fill="{EXP}"/>')         # 出口（左へ）
for _sx in (BYP_X - 9, BYP_X + 3.5):
    add(f'<rect x="{_sx}" y="{SY+14}" width="5.5" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # 弁座
add(f'<line x1="{BYP_X}" y1="{SY+20+BYP_DZ}" x2="{BYP_X}" y2="{SY+48}" stroke="{K}" stroke-width="2.2"/>')     # 棒
add(f'<rect x="{BYP_X-8.5}" y="{SY+16.5+BYP_DZ}" width="17" height="3.5" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')
rect(BYP_X - 11, SY + 44, 22, 11, fill=METAL, rx=2, sw=1.8)                                       # 操作部
text("APLバイパス弁", BYP_X + 24, SY + 30, 13, color="#333")
text("（人工呼吸中に開く）", BYP_X + 24, SY + 46, 11, color="#666")
# 呼吸バッグ：人工呼吸中もリザーバーとしてふくらみ・しぼむ。用手換気では手で押してしぼむ
BG_P = 784                                  # バッグの差し込み口
breathing_bag(BG_P, SY, EXP, BAG_S, BAG_KT)
if MANUAL:
    squeeze_mark(BG_P, SY, gate_win(0, TI))
# 図の中の説明文。操作ページでは隠し、呼吸バッグの名前をクリックしたときの解説に回す（class="svgnote"。コマ撮りでは出す）
add('<g class="svgnote">')
for _k, _ln in enumerate(("用手換気ではピストンが止まり、", "呼吸バッグを手で押して", "患者へガスを送る") if MANUAL else
                         ("人工呼吸中も呼吸バッグは", "リザーバーとして回路に残り、", "ふくらみ・しぼむ")):
    text(_ln, 1030, SY - 2 + 22 * _k, 15, color="#333")   # 2026-11-02：APL バイパス弁の名前と重ならないよう右へ
add('</g>')
# 余剰ガス排出装置
SC_T = 680
pipe([(APX + 20, SY + 30), (APX + 36, SY + 30), (APX + 36, SC_T)], inner=EXP)   # 2026-11-02：点線から管に（APL 弁の出口 → 余剰ガス排出装置）
pipe([(BYP_X - 20, SY + 30), (APX + 36, SY + 30)], inner=EXP)                    # APL バイパス弁の出口 → 合流
EXH_Y = SY + 68                                                                  # 排気の逆止弁（合流のあと。下向きにだけ通す）
check_valve(APX + 36, EXH_Y, EXP, is_open=True, rot=180)
text("排気逆止弁", APX + 26, EXH_Y + 26, 13, "end", color="#333")
# 余剰ガス排出装置（2026-11-02）：金属の箱の中に透明なため（リザーバー）。回路から来たガスはためを通って右端の
# 吸引の口（黒：吸引の配管の色）から手術室の外へ吸い出される。ためは上の口で大気に開いていて、吸引が強すぎても
# 弱すぎても回路に陰圧・陽圧がかからない（開放型）
rect(760, SC_T, 520, 44, fill=METAL, rx=8)
_rx0, _rx1 = APX + 26, 1164
add(f'<rect x="{_rx0}" y="{SC_T+11}" width="{_rx1-_rx0}" height="22" rx="5" fill="{GLASS}" stroke="{K}" stroke-width="1.4"/>')
add(f'<line x1="{_rx0+6}" y1="{SC_T+14.5}" x2="{_rx1-6}" y2="{SC_T+14.5}" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>')
add(f'<line x1="{_rx0+6}" y1="{SC_T+29.5}" x2="{_rx1-6}" y2="{SC_T+29.5}" stroke="{GLASS_SHADE}" stroke-width="2.5" stroke-linecap="round"/>')
for _ex in (APX + 36,):                                       # 上から来る管（ホース）の入口
    add(f'<rect x="{_ex-3.5}" y="{SC_T-1.2}" width="7" height="13" fill="{GLASS}"/>')
for _vx in (1100, 1114):                                         # 大気への口
    add(f'<rect x="{_vx-3}" y="{SC_T-1.2}" width="6" height="13" fill="{GLASS}"/>')
text("大気", 1107.0, SC_T - 6, 12, "middle", color="#333")
add(f'<rect x="{_rx1}" y="{SC_T+13}" width="18" height="18" rx="2" fill="{K}"/>')   # 吸引の口
text("吸引", _rx1 + 9, SC_T + 26, 9, "middle", 700, "#fff", halo=False)
text("→ 手術室外へ", 1200, SC_T - 7, 16, "middle", color="#333")

# ================= 経路データ（JS シミュレーション用） =================


J_FG = (AX, FG_Y)                                  # 新鮮ガスの入口（吸収装置の出口のすぐ上）
NP = (PS_X, MAN_Y)                                 # ピストンの口の分岐
NX = (SX, EXP_Y)                                   # 呼気側の分岐（吸収装置へ／呼吸バッグへ）
APL = (APX, SY) if MANUAL else (BYP_X, SY)         # 余るガスの分岐：用手換気は APL 弁、人工呼吸中は APL バイパス弁（満杯ならここから排出へ）
TUBES = {
    "A": [NP] + valve_detour(IV_X, MAN_Y, 1) + [(IP[0], MAN_Y)] + qpts(IP, C_I, YI)[1:] + [(YX, YY)],          # ピストンの口 → 吸気弁 → 蛇管 → Y
    "B": [(YX, YY), (TR_X, YY), HIL],                                         # Y → 気管（死腔）→ 気管分岐部
    "C": [(YX, YY), YE] + qpts(YE, C_E, EP)[1:] + valve_detour(EV_X, EXP_Y, -1) + valve_detour(PV_X, EXP_Y, -1) + [NX],                      # Y → 蛇管 → 呼気弁 → PEEP/Pmax 弁 → 分岐
    "F": [NX, (AX, EXP_Y), (AX, CB), (AX, CT), J_FG],                         # 分岐 → 吸収装置 → 新鮮ガスの入口
    "G": [J_FG, (AX, MAN_Y)] + valve_detour(DV_X, MAN_Y, 1) + [NP],                                             # 新鮮ガスの入口 → デカップリング弁 → ピストンの口
    "P": [NP, (PS_X, CY0)],                                                   # ピストンの口 → シリンダー
    "H": [NX, (SX, SY), APL],                                                 # 分岐 → 呼吸バッグの口
    "S": ([APL, (APX, SY + 19.5), (APX + 12, SY + 19.5), (APX + 12, SY + 30)] if MANUAL else           # APL 弁の中を回る
          [APL, (BYP_X, SY + 19.5), (BYP_X - 12, SY + 19.5), (BYP_X - 12, SY + 30)])                 # APL バイパス弁の中を回る
         + [(APX + 36, SY + 30), (APX + 36, SC_T + 22), (1180, SC_T + 22)],                          # → 排気の逆止弁 → 余剰ガス排出装置 → 外
}
_cF = cum(TUBES["F"])
PIN0, POUT0 = VAPS[0] - VW / 2 + 14, VAPS[0] + VW / 2 - 14
by_, cy_ = VT + 13, VT + 26 + 9


def supply_path(gx, chamber):
    seg = [(gx - 30, OUT_Y), (gx - 30, JOIN_Y), (gx, JOIN_Y), (gx, MAN_Y), (PIN0, MAN_Y), (PIN0, by_)]
    seg += ([(PIN0, cy_), (POUT0, cy_), (POUT0, by_)] if chamber else [(POUT0, by_)])
    seg += [(POUT0, MAN_Y), (CGO_X + 10, MAN_Y), (720, MAN_Y), (720, FG_Y), J_FG]
    return seg


_bc = (BG_P - 44, SY)                              # 呼吸バッグの中心（大きさ 1 のとき）
BAG_SLOTS = [(_bc[0] + dx, _bc[1] + dy) for dy in (-18, -9, 0, 9, 18) for dx in (-18, -9, 0, 9, 18)
             if (dx / 26) ** 2 + (dy / 24) ** 2 <= 1]
# 管ごとの粒の間隔の係数（>1 は粒がまばら）。2026-11-02 に吸気弁を右へ動かして（回路内圧計に近すぎたため）
# 管 A が長くなった。粒の数と通り抜ける時間を変えないよう、間隔を長さに比例させて配置を変える前の
# 管の長さ（下の値、px）と同じ粒の数に保つ
H_REF = plen([NX, (SX, SY), (APX, SY)])           # 管 H の基準の長さ（分岐を APL 弁に置いていたときの長さ）
TUBE_REF_LEN = {"A": 354.179, "C": 477.716, "G": 312.0, "H": H_REF}   # C・G：2026-11-02 一方向弁の中の回り道を足す前の長さ。H：人工呼吸中は分岐を APL バイパス弁へ移した（短くなる）ので、移す前の長さ
TUBE_SPACING = {k: round(plen(TUBES[k]) / v, 4) for k, v in TUBE_REF_LEN.items()}
GEO = {
    "kind": "piston",
    "manual": MANUAL,                              # 用手換気（sim_piston.js が見る）
    "CYC": CYC, "TI": TI, "T2": T2, "T3": T3, "FG_RATE": FG_RATE, "VT_P": VT_P,
    "NC_FULL": NC_FULL, "NC_MIN": NC_MIN, "NG_FULL": NG_FULL, "LUNG_MIN": LUNG_MIN,
    "SP": 40.0, "SUP_V": 88.0, "SCAV_V": 120.0,
    # 新鮮ガスの粒が回路に届く時刻のずれ（到着の間隔に対する割合）。用手換気では、吸気中に届く新鮮ガスが
    # デカップリング弁の手前で吸気の流れに合流するため、ずれによって 1 回換気量の粒の数が呼吸ごとにゆらぐ。
    # 平均が VT_P になり、到着が吸気・呼気の切り替わりの瞬間に重ならない値を選んだ（2026-11-02）
    # 1.3.1：供給路の出発時刻の基準を変えたので走査し直し、1 回換気量が 13 に最も近い値
    "supplyPhase": (0.125 if LOW_FLOW else 0.875) if MANUAL else (0.125 if LOW_FLOW else 0.25),
    "tubeSpacing": TUBE_SPACING,
    "tubes": TUBES,
    "absD": [_cF[2], _cF[3]],
    "absorber": {
        "rows": [[_cF[2] + (CB - (PT + 7 + r * ABS_PITCH + ABS_PITCH / 2)), _cF[2] + (CB - (PT + 7 + r * ABS_PITCH - ABS_PITCH / 2))]
                 for r in reversed(range(ABS_ROWS))],
        "cap": ABS_CAP, "spread": [0.6, 0.3, 0.1], "fresh": "#ffffff", "used": ABS_USED_C,
    },
    # 供給路は 4 本：流量計（O2 は x=420、N2O は x=100）から合流管で混ざった新鮮ガスを、気化室とバイパスに分ける。
    # 粒の番号 k で選ぶ（偶数 O2・奇数 N2O、6 粒のうち 2 粒が気化室）。2026-11-04：O2 だけが気化室・N2O だけがバイパスに固定されていたのを直した
    "supply": [supply_path(420, True), supply_path(100, False), supply_path(420, False), supply_path(100, True)],
    "nodes": {"NP": NP, "JFG": J_FG, "NX": NX, "Y": (YX, YY), "LG": HIL, "APL": APL,
              "CYLM": (PS_X, CY0), "BAGM": (BG_P - 14, SY)},
    "cylinder": {"x": PS_X, "top": CY0 + 4, "keyT": HEAD_KT, "keyY": HEAD_Y},
    "bag": {"pivot": (BG_P, SY), "slots": BAG_SLOTS, "keyT": BAG_KT, "keyS": BAG_S, "keyN": BAG_N},
    "lung": {"hilum": HIL, "s0": LUNG_S0, "s1": LUNG_S1,
             "slots": [(lx + dx, LOBE_T + 10 + 11.5 * r) for lx in LOBES for r in range(8) for dx in (-6, 6)]},
    "exhale": {"tau": TAU, "tEnd": T_EXH},
}
if len(sys.argv) > 3:
    json.dump(GEO, open(sys.argv[3], "w"), ensure_ascii=False)
add('<g id="particles"></g>')

# ================= 字幕と進行バー =================
add('<g class="svgcap">')
CAP_Y = 830
add(f'<rect x="12" y="{CAP_Y-28}" width="{W-24}" height="44" rx="8" fill="#f4f1fb" stroke="#cbbfe8"/>')
_CAPS = ((((0, TI), "吸気", "呼吸バッグを手で押すと、ガスは吸収装置を通り、新鮮ガスと合わさってデカップリング弁と吸気弁から患者へ", K),
          ((TI, CYC), "呼気", "呼気と新鮮ガスが呼吸バッグへ戻ってふくらませる。いっぱいになって圧が上がると APL 弁から余剰ガス排出装置へ", EXP_ARROW))
         if MANUAL else
         (((0, TI), "吸気", "ピストンが押し上がり、ガスを吸気弁から患者へ送る。デカップリング弁は閉じ、新鮮ガスは呼吸バッグへ", K),
          ((TI, T2), "呼気①", "呼気は呼気弁と PEEP/Pmax 弁を通って呼吸バッグへ。人工呼吸中もバッグがふくらむ", EXP_ARROW),
          ((T2, CYC), "呼気②", "ピストンが下がり、バッグのガスと新鮮ガスをデカップリング弁から吸い込む", EXP_ARROW)))
for (a, b), lab, msg, col in _CAPS:
    add(gate_win(a, b))
    add(f'<rect x="24" y="{CAP_Y-20}" width="72" height="28" rx="6" fill="{col}"/>')
    text(lab, 60, CAP_Y + 1, 18, "middle", 700, "#fff", halo=False)
    text(msg, 108, CAP_Y + 1, 17, halo=False)
    add('</g>')
BX, BW = 1110, 170
add(f'<rect x="{BX}" y="{CAP_Y-8}" width="{BW*TI/CYC:.1f}" height="10" fill="#444"/>')
add(f'<rect x="{BX + BW*TI/CYC:.1f}" y="{CAP_Y-8}" width="{BW*(1-TI/CYC):.1f}" height="10" fill="{EXP_ARROW}"/>')
if not MANUAL:
    add(f'<rect x="{BX + BW*T2/CYC:.1f}" y="{CAP_Y-8}" width="2" height="10" fill="#fff"/>')
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
text("蛇管・", 1182, 162, 18); text("Yピース", 1182, 186, 18)
text("二酸化炭素", 848, 349, 18); text("吸収装置", 848, 373, 18)
label("⑪", "呼気弁", EV_X, EXP_Y - 58, "right")
text("APL弁", APX + 10, SY - 14, 19, "middle")   # 2026-11-02：APL 弁の真上（管のすぐ上）へ。旧：label(…, SY - 46, "left") で左上に離れていた
text("呼吸バッグ", 748, SY + 64, 17, "middle")   # 2026-11-02：APL 弁の本体と重ならないよう 8 px 左へ。満杯のバッグの輪郭に近かったので 6 px 下へ
text("新鮮ガス・", DV_X - 40, 58, 16); text("デカップリング弁", DV_X - 40, 80, 16)
label("⑯", "余剰ガス排出装置", 882, SC_T - 14, "right")   # 2026-11-02：粒の通り道と重ならないよう箱の上へ

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
