# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）。プログラムは MIT ライセンス、図と文章は CC BY 4.0
"""麻酔器・呼吸回路の模式図（ボリュームリフレクタ式。Getinge（Maquet）Flow-i の構成を参考）実行時シミュレーション用の土台 SVG。
弁・肺・電磁弁の動きは SMIL、ガスの粒（リフレクタガスの O2 を含む）はブラウザ側の JS（sim_reflector.js）が描く。
左半分（ガス供給・気化器）は 1.3（2026-11-04）で Flow-i の構成に合わせ、流量計・ニードル弁・可変バイパス式の気化器・インターロックの代わりに、
ガスごとの電子制御のガスモジュール（比例弁と流量センサ）、注入式の気化器（加圧した液の容器・注入器・加熱気化室）、制御部を描く
（Miller 第10版 第20章、Flow-i 4.7 取扱説明書・サービスマニュアル、FDA K102182、PMDA 添付文書。vault の調査・監査ノート 2026-11-04）。
管の経路や部屋の位置は JSON（argv[3]）に書き出す。

使い方: python3 figure_reflector.py out.svg color out_geo.json [low|short] [manual] [en]
  low を付けると低流量の場面（新鮮ガスを 1/4 に減らし、リフレクタガスで押し出す量を増やして患者に入る量はそろえる）
  short を付けると「不足」の場面（1.3、2026-11-04）：新鮮ガスは低流量と同じで、患者の取り込み（肺胞で血液へ消える粒）がそれより多く、
  リフレクタガス（O₂）の境目が呼吸ごとに患者側へ進んで、やがて O₂ が回路に加わる（Getinge の VR balance が負の状態）
B5判の本文幅（約150 mm）に縮小して、本文の文字が約7.5 pt になる大きさで描く。
"""
import json
import math
import sys

import palette
import svg
from geometry import cum, plen, qpts, unit
from palette import *   # noqa: F401,F403  色と字体（K・B・METAL・GLASS など）
from parts import FM_W_BOT, FM_W_TOP, alveoli_path, breathing_bag, bronchus, check_valve, collar, hose, one_way_valve, port, valve_detour
from svg import CYC, GAS_W, TI, add, arrow, dashed, flush_pipes, gate_open, label, leader, out, pipe, rect, text


MODE = sys.argv[2] if len(sys.argv) > 2 else "2c"
LUNG_TISSUE, EXP_C, EXP_ARROW, PIPE, CYL, WICK = (palette.by_mode(MODE)[k] for k in ("LUNG_TISSUE", "EXP_C", "EXP_ARROW", "PIPE", "CYL", "WICK"))
W, H = 1340, 860           # 2026-11-03：ピストン式と同じ幅にそろえた（患者の側を右へ 140 px、蛇管を長く）
_FLAGS = set(sys.argv[4:])
SHORT = "short" in _FLAGS                   # 「不足」の場面：新鮮ガスは低流量と同じ、患者の取り込みがそれより多い（1.3）
LOW_FLOW = "low" in _FLAGS or SHORT
MANUAL = "manual" in _FLAGS                 # 用手換気の場面：呼吸バッグをリフレクタの奥の端につなぎ、リフレクタガスを止める（2026-11-03）
LANG = "en" if "en" in _FLAGS else "ja"       # en：図の中の文字を英語にする（labels_en.py。2026-11-02）
svg.configure(LANG, "r")
# 新鮮ガス。1 呼吸あたりの粒の数はほかの方式と同じ（多め 12 粒、低流量 3 粒）。FG_RATE は平均の流量（粒/秒）。人工呼吸ではガスモジュールが
# 主に吸気中に流し（下の FG_I・FG_E。1.3）、呼気中に届いた分は吸収装置を逆向きに通ってリフレクタへ入る（1.2.9 の著者の判断：新鮮ガスの管には
# ためる場所がなく、回路内圧からはこの向き。1.2.9〜1.2.11 は流量計の図だったので一定に流していた）。用手換気は一定
FG_RATE = 0.5 if LOW_FLOW else 2.0
# 患者に入る量 VT_P は新鮮ガスの量によらず 13 粒（ピストン式と同じ）。リフレクタガス（O2）が押し出す量 VR は、
# 吸気中に加わる新鮮ガスのぶんを引いた残り（多め：4.5 粒/秒、低流量：6.0 粒/秒）
VT_P = 13.0
if MANUAL:
    # 用手換気（2026-11-03）：上昇式ベローズの用手換気と同じ決まり。新鮮ガスは一定で、呼吸バッグが押し出す量 VT_B は
    # 吸気中に加わる新鮮ガスを引いた残り（多め 9 粒、低流量 12 粒）。バッグの粒の数は満杯 NB_FULL、押し切って NB_MIN
    NB_FULL, NB_MIN = (14, 2) if LOW_FLOW else (14, 5)
    VT_B = NB_FULL - NB_MIN
    VR = VT_B / TI
else:
    # 人工呼吸（1.3、2026-11-04 著者の判断）：ガスモジュールは新鮮ガスを主に吸気中に流す（Miller 第10版 第20章、Flow-i 4.7 取扱説明書、
    # FDA K102182「AUTO では動的な流量」）。配分の比率は資料から確定できないので、教材上の近似として 1 呼吸の新鮮ガスの 2/3 を吸気中（2 秒）、
    # 1/3 を呼気中（4 秒）に入れる。瞬時流量は吸気 2×FG_RATE、呼気 0.5×FG_RATE（多め 4.0/1.0、低流量 1.0/0.25 粒/秒。多め 8+4 粒、低流量 2+1 粒）。
    # リフレクタガスが押し出す量は、吸気中に加わる新鮮ガスを引いた残り（多め 2.5、低流量 5.5 粒/秒）
    FG_I, FG_E = 2.0 * FG_RATE, 0.5 * FG_RATE
    VR = VT_P / TI - FG_I
# 患者の取り込み（「不足」の場面）：吸気の終わりに肺胞の粒がこの数だけ血液へ取り込まれて消える。新鮮ガス 3 粒/呼吸より多い 4 粒/呼吸なので、
# 回路のガスは呼吸ごとに 1 粒減り、そのぶんリフレクタガス（O₂）が残って境目が患者側へ進む
UPTAKE = 4 if SHORT else 0
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

if MANUAL:
    def _bag_fill(t):
        """呼気開始 t 秒後に呼吸バッグへ届いた粒の数（呼気＋新鮮ガス）"""
        return VT_P * exh_frac(t) + FG_RATE * t
    T_FULL = TI + next(k * 0.005 for k in range(1, 20000) if _bag_fill(k * 0.005) >= VT_B)   # バッグが満杯になる時刻
    BAG_KT = [0.0, TI] + [TI + k * 0.05 for k in range(1, int((T_FULL - TI) / 0.05))] + [T_FULL, CYC]
    BAG_SC = [1.0, NB_MIN / NB_FULL] + [min(1.0, (NB_MIN + _bag_fill(t - TI)) / NB_FULL) for t in BAG_KT[2:]]
    BAG_S = [0.8 * (0.72 + 0.33 * v) for v in BAG_SC]    # バッグの大きさ（置き場所が狭いので 0.8 倍。満杯で 0.84）

AX = 790                          # 二酸化炭素吸収装置
ABS_CAP = 15.0                    # 吸収剤 1 層が吸える CO2 の粒の数（実際の数時間以上を数分に縮めた値）。
                                  # 低流量では約 22 呼吸で全層を使い切る。多めでは押し出すのが呼気の最後に入った死腔のガス 1 粒だけで、CO2 は届かない
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
    pipe([(x, JOIN_Y), (x, FM_B)])          # 1.3.1：ガスモジュールの底まで（1.3.0 ではニードル弁の本体を外したぶん 20 px 届いていなかった。本人の指摘）
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
    # ガスモジュール（1.3、2026-11-04）：Flow-i では流量計・ニードル弁の代わりに、ガスごとの電子制御のモジュールが流量を作る
    # （Flow-i サービスマニュアル §3.8、FDA K102182）。金属の箱の中に、下から：比例弁（コイルが鉄心＝弁体（青）を引き上げ、ノズルとの
    # すき間で流量を決める。人工呼吸では吸気中に大きく開き、用手換気では一定）、流量センサ（通路を絞るオリフィスの前後の圧の差を膜（青）で
    # 測る）。温度・供給圧のセンサは省く。Air は使っていないので弁は閉じた姿。粒の通り道（管の中心）は変えていない
    rect(x - 28, FM_T, 56, FM_B - FM_T, fill=METAL, rx=4)
    add(f'<rect x="{x-3.5}" y="{FM_T-1.2}" width="7" height="{FM_B-FM_T+2.4}" fill="#fff"/>')              # 通路
    vy = FM_B - 24                                                                                     # 比例弁のノズル（弁座）の高さ
    add(f'<rect x="{x-9}" y="{vy-28}" width="18" height="26" fill="#fff"/>')                             # 弁の部屋
    add(f'<path d="M {x-3.5},{vy+4} L {x-1.6},{vy} L {x-3.5},{vy-4} Z" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # ノズル
    add(f'<path d="M {x+3.5},{vy+4} L {x+1.6},{vy} L {x+3.5},{vy-4} Z" fill="{METAL}" stroke="{K}" stroke-width="1"/>')
    for _sx in (x - 22, x + 13):                                                                       # コイル（左右）
        for _k in range(4):
            add(f'<rect x="{_sx}" y="{vy-27+5.6*_k:.1f}" width="9" height="4" fill="none" stroke="{K}" stroke-width="1"/>')
    _gk = f"0;{TI/CYC-0.012:.4f};{TI/CYC+0.018:.4f};0.985;1"
    if name == "Air":
        add('<g>')                                                                                     # 閉：弁体の先がノズルに入っている
    elif MANUAL:
        add('<g transform="translate(0 -5)">')                                                         # 用手換気：一定の開き
    else:                                                                                              # 人工呼吸：吸気中に大きく開く（新鮮ガスを主に吸気中に）
        add(f'<g><animateTransform attributeName="transform" type="translate" values="0 -8;0 -8;0 -3;0 -3;0 -8" keyTimes="{_gk}" dur="{CYC}s" repeatCount="indefinite"/>')
    add(f'<path d="M {x-4},{vy-24} L {x+4},{vy-24} L {x+4},{vy-7} L {x},{vy+0.5} L {x-4},{vy-7} Z" fill="{B}" stroke="{K}" stroke-width="1.2" stroke-linejoin="round"/>')   # 弁体（先細り）
    add('</g>')
    oy = FM_T + 30                                                                                     # 流量センサ：オリフィスと圧の差を測る膜
    for _sx in (x - 3.5, x + 1.5):
        add(f'<rect x="{_sx}" y="{oy-1.5}" width="2" height="3" fill="{METAL}" stroke="{K}" stroke-width="0.8"/>')   # オリフィス板
    add(f'<rect x="{x+3.5}" y="{oy-10}" width="10" height="2.2" fill="#fff"/>')                        # 絞りの前後から圧を取り出す細い道
    add(f'<rect x="{x+3.5}" y="{oy+7.8}" width="10" height="2.2" fill="#fff"/>')
    add(f'<rect x="{x+13}" y="{oy-13}" width="12" height="26" fill="#fff" stroke="{K}" stroke-width="1"/>')   # センサの部屋
    add(f'<rect x="{x+13}" y="{oy-1.2}" width="12" height="2.4" fill="{B}"/>')                         # 膜（圧の差でたわむ）
    text(name, x - 36, FM_T + 24, 18, "end", 700)
    if name == "Air":
        text("停止", x - 36, FM_T + 48, 15, "end", 700, color="#666")


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

# 制御部（1.3、2026-11-04）：麻酔器の電子制御。設定した流量・酸素濃度・麻酔薬濃度になるよう、ガスモジュールの弁と気化器の注入量を決める。
# 点線は制御の信号（亜酸化窒素遮断弁の「O₂ の圧」の線と同じ描き方。実機の電気配線の形ではない）
CTRL = (84, 78)
rect(CTRL[0] - 40, CTRL[1] - 15, 80, 30, fill=METAL, rx=4)
text("制御部", CTRL[0], CTRL[1] + 6, 15, "middle", 700)
BUS_Y = 108
dashed([(CTRL[0], CTRL[1] + 15), (CTRL[0], BUS_Y), (VAPS[0], BUS_Y)])
for _, _x in GASES:
    dashed([(_x + 20, BUS_Y), (_x + 20, FM_T)])

# 気化器（1.3、2026-11-04）：Flow-i は注入式（Miller 第10版 図 20.28、Flow-i サービスマニュアル §3.10、PMDA 添付文書）。合流管の新鮮ガスは
# 入口ポートから加熱した気化室に入り、注入器が液体の麻酔薬を短いパルスで室内へ噴いて蒸発させ、蒸気と混ざって出口ポートから合流管へ戻る。
# 液は下の容器にあり、新鮮ガスの圧で加圧されて注入器へ送られる。濃度は電子的に設定し（ダイヤルはない）、2 台のうち選んだ 1 台だけが働く
# （機械式のインターロックはない）。灯心・バイパス路・濃度ダイヤルの従来型（上昇式ベローズ・ピストン式の図）とは中身が違う
VW, VT, VB = 70, MAN_Y + 26, MAN_Y + 96
ON = VAPS[0]
PIN, POUT = ON - VW / 2 + 14, ON + VW / 2 - 14
CH_T, CH_B = VT + 18, VT + 40                   # 加熱気化室の上下
pipe([(100, MAN_Y), (PIN, MAN_Y), (PIN, VT + 2)])
pipe([(POUT, VT + 2), (POUT, MAN_Y), (CGO_X, MAN_Y)])
dashed([(ON, BUS_Y), (ON, VT - 2)])             # 制御部 → 注入器


for vx in VAPS:
    on = vx == ON
    x0, x1 = vx - VW / 2, vx + VW / 2
    pin, pout = x0 + 14, x1 - 14
    hw = (GAS_W - 5) / 2
    if not on:
        # 閉じたポート：合流管と気化器の間をふさいだ継ぎ手
        for px in (pin, pout):
            add(f'<rect x="{px-7}" y="{MAN_Y+6}" width="14" height="{VT-MAN_Y-4}" fill="{METAL}" stroke="{K}" stroke-width="1.6"/>')
            add(f'<line x1="{px-7}" y1="{(MAN_Y + 6 + VT + 2) / 2:.1f}" x2="{px+7}" y2="{(MAN_Y + 6 + VT + 2) / 2:.1f}" stroke="{K}" stroke-width="1.2"/>')
    add(f'<rect x="{x0}" y="{VT}" width="{VW}" height="{VB-VT}" rx="7" fill="{METAL}" stroke="{K}" stroke-width="2.2"/>')
    # 加熱気化室：中はガス（白）。床はヒーター（金属の板に斜線）
    add(f'<rect x="{pin-hw}" y="{CH_T}" width="{pout-pin+2*hw}" height="{CH_B-CH_T}" fill="#fff" stroke="{K}" stroke-width="1.2"/>')
    add(f'<rect x="{pin-hw}" y="{CH_B}" width="{pout-pin+2*hw}" height="6" fill="{METAL}" stroke="{K}" stroke-width="1.2"/>')
    for _k in range(int((pout - pin + 2 * hw) // 6)):
        add(f'<line x1="{pin-hw+2+6*_k:.1f}" y1="{CH_B+5}" x2="{pin-hw+5+6*_k:.1f}" y2="{CH_B+1}" stroke="{K}" stroke-width="1"/>')
    # 液の容器（加圧）：液面は高い。上の通路から細い道で新鮮ガスの圧がかかる
    RT, RB = CH_B + 16, VB - 8
    add(f'<rect x="{x0+8}" y="{RT}" width="{VW-16}" height="{RB-RT}" rx="3" fill="#fff" stroke="{K}" stroke-width="1.2"/>')
    add(f'<path d="M {x0+8},{RT+7} q 6,-4 12,0 t 12,0 t 12,0 t 12,0 t 6,0 L {x1-8},{RB} L {x0+8},{RB} Z" fill="{B_TINT}" stroke="none"/>')
    add(f'<path d="M {x0+8},{RT+7} q 6,-4 12,0 t 12,0 t 12,0 t 12,0 t 6,0" fill="none" stroke="{B}" stroke-width="1.8"/>')
    if on:
        add(f'<rect x="{x0+9}" y="{VT+7}" width="{pin-hw-x0-9}" height="2.4" fill="#fff"/>')           # 加圧の道：入口の通路 → 容器の上
        add(f'<rect x="{x0+9}" y="{VT+7}" width="2.4" height="{RT-VT-6}" fill="#fff"/>')
    # 注入器：容器の液を細い道で気化室の床へ。コイルに引かれる鉄心（青）が道を開閉し、短いパルスで液を噴く（使用中だけ動く）
    add(f'<rect x="{vx-1.5}" y="{CH_B+1}" width="3" height="{RT+8-CH_B-1}" fill="#fff"/>')               # 液の道（容器の液の中から気化室の床まで）
    for _sx in (vx - 11, vx + 5):
        add(f'<rect x="{_sx}" y="{CH_B+8}" width="6" height="6" fill="none" stroke="{K}" stroke-width="1"/>')   # コイル
    if on:
        add('<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 -3;0 0;0 0" keyTimes="0;0.08;0.2;0.3;1" dur="0.5s" repeatCount="indefinite"/>')
    add(f'<rect x="{vx-2.5}" y="{CH_B+7}" width="5" height="8" rx="1" fill="{B}" stroke="{K}" stroke-width="1"/>')   # 鉄心（弁体）
    if on:
        add('</g>')
    if on:
        # 通路：入口ポートから気化室へ下り、気化室を通って出口ポートへ上がる（すべての新鮮ガスが気化室を通る）
        for px in (pin, pout):
            add(f'<rect x="{px-hw}" y="{VT-1.2}" width="{2*hw}" height="{CH_T-VT+1.8}" fill="#fff"/>')
        text("使用中", vx, MAN_Y - 24, 15, "middle", 700)
    else:
        text("停止中", vx, MAN_Y - 24, 15, "middle", 700, color="#555")

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
# 呼気に入ると急に下がり、PEEP/APL 弁で設定した PEEP（ここでは 2 cmH2O）まで下がる
GX, GY = AX + 50, 180
P_KEYS = ([(0.0, 2.0), (0.12, 6.0), (TI, 16.0), (TI + 0.12, 3.0), (max(TI + 0.4, T_FULL - 0.15), 1.5), (T_FULL + 0.15, 2.0), (CYC, 2.0)]
          if MANUAL else   # 用手換気：バッグが満杯になって PEEP/APL 弁が開くと、設定圧が残る
          [(0.0, 2.0), (0.12, 6.0), (TI, 16.0), (TI + 0.12, 3.0), (TI + 0.6, 2.0), (CYC, 2.0)])
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
# ボリュームリフレクタ：合流点 J から下りて、とぐろ状に巻いた長い管（約 1.2 L、可動部はない）。
# 患者側の端 J から入ったガスは同じ端から出る（後入れ先出し）。奥の端 K にはリフレクタガス（O2）の入口と
# PEEP/APL 弁がつながる。実機ではプラスチックの管を機械の中にコンパクトに巻いてある
RX0, RX1 = 780, 1170                            # とぐろの左右（2026-11-03：幅をそろえたぶん右へ 110 px 伸ばした）
RYS = [505, 538, 571, 604]                      # 各段の高さ（上から）
RR = (RYS[1] - RYS[0]) / 2                      # 折り返しの半径
def _turn(cx, cy, start_deg, end_deg, n=8):
    """折り返しの半円（中心 cx,cy、半径 RR）を n 分割した点"""
    return [(cx + RR * math.cos(math.radians(start_deg + (end_deg - start_deg) * k / n)),
             cy + RR * math.sin(math.radians(start_deg + (end_deg - start_deg) * k / n))) for k in range(n + 1)]
J = (SX, EXP_Y)
R_PTS = [J, (SX, RYS[0]), (RX0 + RR, RYS[0])]
R_PTS += _turn(RX0 + RR, RYS[0] + RR, -90, -270)[1:]          # 左で折り返して下へ
R_PTS += [(RX1 - RR, RYS[1])]
R_PTS += _turn(RX1 - RR, RYS[1] + RR, -90, 90)[1:]            # 右で折り返して下へ
R_PTS += [(RX0 + RR, RYS[2])]
R_PTS += _turn(RX0 + RR, RYS[2] + RR, -90, -270)[1:]
R_PTS += [(RX1, RYS[3])]
K = (RX1, RYS[3])                                                 # 奥の端
R_PTS = [(round(x, 1), round(y, 1)) for x, y in R_PTS]
pipe(R_PTS, inner=EXP)
text("ボリュームリフレクタ", J[0] + 14, RYS[0] - 3, 15, weight=700)   # 2026-11-04：合流点から下りる管に重ならないよう、管の右へ
# 奥の端 K からの分岐：上はリフレクタガス（O2）の入口、下は PEEP/APL 弁
KX = 1215
APX = 1280                                      # PEEP/APL 弁（右端。2026-11-03：用手換気の呼吸バッグを K の右に置くため右へ寄せ、出口を左向きにした）
pipe([K, (APX, RYS[3])], inner=EXP)
# リフレクタガスモジュール：O2 の配管から電磁弁（コイルで鉄心を引く弁。青＝動く部品）を通してリフレクタの奥へ流す。
# 吸気中だけ弁が開く（SMIL で鉄心が上がる）。実機は電子制御で流量を決める
GM_T = 548
pipe([(KX, RYS[3]), (KX, GM_T + 30)], inner="#e6e6e6")          # 内腔は駆動ガスの色（灰）
rect(KX - 24, GM_T, 48, 32, fill=METAL, rx=4)
add(f'<rect x="{KX-3.5}" y="{GM_T+18}" width="7" height="{14}" fill="#e6e6e6"/>')                     # 出口の通路
add(f'<rect x="{KX-18}" y="{GM_T+10}" width="36" height="9" fill="#e6e6e6"/>')                        # 弁の部屋
add(f'<rect x="{KX+16}" y="{GM_T+10.5}" width="9.2" height="8" fill="#e6e6e6"/>')                     # 右から O2 が入る
for _k in range(4):                                                                                   # コイル
    add(f'<rect x="{KX-14+7*_k}" y="{GM_T+3}" width="4" height="5" fill="none" stroke="{K}" stroke-width="1"/>')
_gk = f"0;{TI/CYC-0.012:.4f};{TI/CYC+0.018:.4f};0.985;1"
if MANUAL:
    add('<g>')                                                                                        # 用手換気：電磁弁は閉じたまま（リフレクタガスを止める）
else:
    add(f'<g><animateTransform attributeName="transform" type="translate" values="0 -5;0 -5;0 0;0 0;0 -5" keyTimes="{_gk}" dur="{CYC}s" repeatCount="indefinite"/>')
add(f'<rect x="{KX-4}" y="{GM_T+8}" width="8" height="11" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')   # 鉄心（下がると出口をふさぐ）
add('</g>')
pipe([(KX + 24, GM_T + 14.5), (KX + 44, GM_T + 14.5)], inner=PIPE["O₂"], w=9)                        # O2 の配管（右から）
text("リフレクタガス", KX - 35, GM_T - 25, 13, color="#333")   # 2026-11-04：1 行ではとぐろの管の壁に重なるので 2 行に
text("モジュール（O₂）", KX - 35, GM_T - 8, 13, color="#333")
text("電磁弁", KX + 52, GM_T + 19, 11, color="#666")
# PEEP/APL 弁：ばねで弁座に押しつけた弁板。呼気では開いて余ったガスを余剰ガス排出装置へ逃がし、呼気の終わりの圧（PEEP）を
# 設定の値に保つ。用手換気では APL 弁として働く（1 つの弁が兼用）。実機は電子制御で、ばねとつまみは模式
APY = RYS[3] + 2
pipe([(APX, RYS[3]), (APX, APY + 10)], inner=EXP, w=10)
APL_DZ = 6                                   # 呼気中は弁板が 6 px 下がって開く（吸気は閉）。用手換気ではバッグが満杯になってから
add(f'<g transform="translate({2*APX},0) scale(-1,1)">')                                        # 左右を裏返し、出口を左向きに
rect(APX - 20, APY + 8, 40, 48, fill=METAL, rx=5)
add(f'<rect x="{APX-3.5}" y="{APY+6.8}" width="7" height="{7.8}" fill="{EXP}"/>')            # 入口
add(f'<rect x="{APX-16}" y="{APY+14}" width="32" height="32" fill="{EXP}"/>')               # 弁の部屋
add(f'<rect x="{APX+15}" y="{APY+26.5}" width="6.2" height="7" fill="{EXP}"/>')            # 出口（右へ）
for _sx in (APX - 9, APX + 3.5):
    add(f'<rect x="{_sx}" y="{APY+14}" width="5.5" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # 弁座
if MANUAL:
    _fo = T_FULL / CYC
    _akt = f"0;{_fo:.4f};{min(_fo + 0.01, 0.98):.4f};0.99;1"
else:
    _akt = f"0;{TI/CYC-0.012:.4f};{TI/CYC+0.018:.4f};0.985;1"
add(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 {APL_DZ};0 {APL_DZ};0 0" keyTimes="{_akt}" dur="{CYC}s" repeatCount="indefinite"/>')
add(f'<rect x="{APX-8.5}" y="{APY+16.5}" width="17" height="3.5" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')
add('</g>')
_s0, _s1 = APY + 20, APY + 44
_sr = (_s1 - _s0 - APL_DZ) / (_s1 - _s0)
add(f'<g transform="translate({APX},{_s1})"><g><animateTransform attributeName="transform" type="scale" '
    f'values="1 1;1 1;1 {_sr:.4f};1 {_sr:.4f};1 1" keyTimes="{_akt}" dur="{CYC}s" repeatCount="indefinite"/>'
    f'<g transform="translate({-APX},{-_s1})">')
add(f'<path d="M {APX},{_s0} ' + " ".join(f"L {APX + (6 if k % 2 else -6)},{_s0 + (_s1 - _s0) * k / 6:.1f}" for k in range(1, 6))
    + f' L {APX},{_s1}" fill="none" stroke="{K}" stroke-width="1.5" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
add('</g></g></g>')
add(f'<rect x="{APX-9}" y="{APY+44}" width="18" height="2.5" fill="{METAL}" stroke="{K}" stroke-width="1"/>')     # ばねの受け
add(f'<rect x="{APX-2.5}" y="{APY+46.5}" width="5" height="12" fill="{METAL}" stroke="{K}" stroke-width="1"/>')   # ねじ
for _k in range(3):
    add(f'<line x1="{APX-2.5}" y1="{APY+50+3.5*_k}" x2="{APX+2.5}" y2="{APY+48+3.5*_k}" stroke="{K}" stroke-width="0.8"/>')
rect(APX - 12, APY + 58, 24, 12, fill=METAL, rx=2, sw=1.8)                                        # つまみ（ぎざぎざ）
for _k in range(1, 6):
    add(f'<line x1="{APX-12+4*_k}" y1="{APY+59}" x2="{APX-12+4*_k}" y2="{APY+69}" stroke="{K}" stroke-width="1"/>')
add('</g>')
# 呼吸バッグと切替弁（2026-11-03）：奥の端 K のすぐ右の分岐から下向きにぶら下げる（差し込み口を上にして 90° 回す）。
# 枝の途中の切替弁は、人工呼吸では閉じてバッグを回路から外し（バッグは止まっている）、用手換気では開く。
# 用手換気では手で押してしぼみ、呼気でふくらむ。粒の席（GEO の bag.slots）も同じ回転と倍率で動く
BT_X, BT_Y = 1182, RYS[3] + 26
pipe([(BT_X, RYS[3]), (BT_X, BT_Y + 2)], inner=EXP)
SV_Y = RYS[3] + 13
rect(BT_X - 9, SV_Y - 7, 18, 14, fill=METAL, rx=2)                                                  # 切替弁の箱
add(f'<rect x="{BT_X-3.5}" y="{SV_Y-7}" width="7" height="14" fill="{EXP}"/>')                         # 通路
if MANUAL:
    add(f'<rect x="{BT_X-1.2}" y="{SV_Y-5}" width="2.4" height="10" fill="{B}" stroke="{K}" stroke-width="0.8"/>')    # 開：板が通路に沿う
else:
    add(f'<rect x="{BT_X-4.5}" y="{SV_Y-1.2}" width="9" height="2.4" fill="{B}" stroke="{K}" stroke-width="0.8"/>')   # 閉：板が通路をふさぐ
text("切替弁", BT_X - 14, SV_Y + 4, 12, "end", 700)
add(f'<g transform="rotate(-90 {BT_X} {BT_Y})">')
if MANUAL:
    breathing_bag(BT_X, BT_Y, EXP, BAG_S, BAG_KT)
else:
    breathing_bag(BT_X, BT_Y, EXP, [0.84, 0.84], [0.0, CYC])                                            # 人工呼吸：満杯の大きさで止まっている
add('</g>')
text("呼吸バッグ", BT_X - 34, BT_Y + 24, 14, "end", 700)   # 2026-11-04：用手換気の「手で押す」に重ならないよう 8 px 上へ
if MANUAL:
    add(gate_open("insp"))
    text("手で押す", BT_X - 44, BT_Y + 51, 14, "end", 700)
    add(f'<line x1="{BT_X-40}" y1="{BT_Y+46}" x2="{BT_X-34}" y2="{BT_Y+46}" stroke="{K}" stroke-width="2.5"/>')
    arrow(BT_X - 35, BT_Y + 46, 0, K, 12)
    add('</g>')
    BAG_SLOTS = [(BT_X + dy, BT_Y + 44 - dx) for dy in (-18, -9, 0, 9, 18) for dx in (-18, -9, 0, 9, 18)
                 if (dx / 26) ** 2 + (dy / 24) ** 2 <= 1]        # 横向きのバッグの席を -90° 回した座標
# 余剰ガス排出装置（2026-11-03：呼吸バッグを置くため 20 px 下げた。2026-11-04：図の枠に収まるよう箱の高さを 44 → 34 px に）
SC_T = 700
SCX = APX - 60                                                                                      # 弁の出口（左向き） → 排出装置へ下りる管（弁の名前と重ならないよう 60 px 左）
pipe([(APX - 20, APY + 30), (SCX, APY + 30), (SCX, SC_T)], inner=EXP)
# 余剰ガス排出装置（2026-11-02）：金属の箱の中に透明なため（リザーバー）。回路から来たガスはためを通って右端の
# 吸引の口（黒：吸引の配管の色）から手術室の外へ吸い出される。ためは上の口で大気に開いていて、吸引が強すぎても
# 弱すぎても回路に陰圧・陽圧がかからない（開放型）
rect(760, SC_T, 556, 34, fill=METAL, rx=8)
_rx0, _rx1 = 800, 1292
add(f'<rect x="{_rx0}" y="{SC_T+6}" width="{_rx1-_rx0}" height="22" rx="5" fill="{GLASS}" stroke="{K}" stroke-width="1.4"/>')
add(f'<line x1="{_rx0+6}" y1="{SC_T+9.5}" x2="{_rx1-6}" y2="{SC_T+9.5}" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>')
add(f'<line x1="{_rx0+6}" y1="{SC_T+24.5}" x2="{_rx1-6}" y2="{SC_T+24.5}" stroke="{GLASS_SHADE}" stroke-width="2.5" stroke-linecap="round"/>')
add(f'<rect x="{SCX-3.5}" y="{SC_T-1.2}" width="7" height="8" fill="{GLASS}"/>')                   # 上から来る管の入口
for _vx in (930, 944):                                                                               # 大気への口
    add(f'<rect x="{_vx-3}" y="{SC_T-1.2}" width="6" height="8" fill="{GLASS}"/>')
text("大気", 937.0, SC_T - 6, 12, "middle", color="#333")
add(f'<rect x="{_rx1}" y="{SC_T+8}" width="18" height="18" rx="2" fill="{K}"/>')   # 吸引の口
text("吸引", _rx1 + 9, SC_T + 21, 9, "middle", 700, "#fff", halo=False)
text("→ 手術室外へ", 1020, SC_T - 7, 16, "middle", color="#333")   # 箱の上、呼吸バッグの左（2026-11-04：吸引の口の下では図の枠の外に出ていた）


# ================= 経路データ（JS シミュレーション用） =================


J_FG = (AX, 230)
LG = HIL                                               # 肺胞の入口（気管分岐部）
TUBES = {
    "A": [J_FG, (AX, MAN_Y)] + valve_detour(IV_X, MAN_Y, 1) + [(IP[0], MAN_Y)] + qpts(IP, C_I, YI)[1:] + [(YX, YY)],     # 回路の入口 → 吸気弁 → 吸気蛇管 → Y
    "B": [(YX, YY), (TR_X, YY), HIL],                                                   # Y → 気管（死腔）→ 気管分岐部
    "C": [(YX, YY), YE] + qpts(YE, C_E, EP)[1:] + valve_detour(EV_X, EXP_Y, -1) + [J],                                # Y → 呼気蛇管 → 呼気弁 → 合流点 J
    "D": [J, (AX, EXP_Y), (AX, CB), (AX, CT), J_FG],                                    # 合流点 → 吸収装置 → 回路の入口
    "R": R_PTS,                                                                         # 合流点 J → ボリュームリフレクタ → 奥の端 K
    # K → PEEP/APL 弁（弁座と弁板のすき間から弁板のふちを回る）→ 余剰ガス排出装置 → 外
    "S": [K, (APX, RYS[3]), (APX, APY + 19.5), (APX - 12, APY + 19.5), (APX - 12, APY + 30), (SCX, APY + 30), (SCX, SC_T + 17), (1300, SC_T + 17)],
}


_cD = cum(TUBES["D"])
PIN0, POUT0 = VAPS[0] - VW / 2 + 14, VAPS[0] + VW / 2 - 14
cy_ = (CH_T + CH_B) / 2

def supply_path(gx, chamber):
    """注入式の気化器では新鮮ガスはすべて加熱気化室を通る（chamber は上昇式ベローズ・ピストン式の図との互換のため受けるだけ）"""
    seg = [(gx - 30, OUT_Y), (gx - 30, JOIN_Y), (gx, JOIN_Y), (gx, MAN_Y), (PIN0, MAN_Y), (PIN0, cy_), (POUT0, cy_)]
    seg += [(POUT0, MAN_Y), (CGO_X + 10, MAN_Y), (720, MAN_Y), (720, 230), J_FG]
    return seg

# 管ごとの粒の間隔の係数（>1 は粒がまばら）。2026-11-02 に呼気弁と吸収装置を上げて（呼気弁がベローズの
# ハウジングに接していたため）管 C・D が短く、E が長くなった。粒の数と管を通り抜ける時間が変わると、
# 新鮮ガス多めの場面で吸収装置に届く CO2 が 0 になるなど振る舞いまで変わるので、間隔を長さに比例させて
# 配置を変える前の管の長さ（下の値、px）と同じ粒の数に保つ
TUBE_REF_LEN = {"A": 463.721, "C": 371.995, "D": 360.0}   # 上昇式ベローズの図と同じ管は同じ粒の数に保つ
TUBE_SPACING = {k: round(plen(TUBES[k]) / v, 4) for k, v in TUBE_REF_LEN.items()}
R_CAP = 30                                                 # リフレクタの容量（粒）：1.2 L ≒ 1 回換気量 13 粒（約 500 mL）の 2.3 倍
TUBE_SPACING["R"] = round(plen(TUBES["R"]) / (40.0 * R_CAP), 4)
GEO = {
    "kind": "reflector",
    "CYC": CYC, "TI": TI, "FG_RATE": FG_RATE, "VT_P": VT_P, "VR": VR, "uptake": UPTAKE,
    **({} if MANUAL else {"FG_I": FG_I, "FG_E": FG_E}),               # 人工呼吸：吸気中・呼気中の新鮮ガスの瞬時流量（粒/秒）
    # 新鮮ガスの到着を流れの切り替わりからずらす（粒の間隔に対する割合）。人工呼吸の多めは 0 だと吸気の終わりに着く粒が毎回 1 つ余分に患者へ入り、
    # 1 回換気量が 14 粒になる（0.5 で 13 粒。2026-11-04）
    # 1.3（2026-11-04）：人工呼吸は吸気 2/3・呼気 1/3 の配分にしたうえで走査し、1 回換気量が 13 に最も近い値を選んだ（多め 13.00 で一定、低流量 13.03、不足 13.00）
    # 1.3.1：供給路の出発時刻の基準を変えたので用手換気も走査し直した（多め 13.00 で一定。以前は 14）
    "supplyPhase": (0.0 if LOW_FLOW else 0.5) if MANUAL else (0.875 if SHORT else 0.625 if LOW_FLOW else 0.375),
    "SP": 40.0, "SUP_V": 88.0, "SCAV_V": 120.0, "LUNG_MIN": LUNG_MIN,
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
    "nodes": {"J": J, "K": K, "JFG": J_FG, "Y": (YX, YY), "LG": LG},
    "lung": {"hilum": HIL, "s0": LUNG_S0, "s1": LUNG_S1,
             "slots": [(lx + dx, LOBE_T + 10 + 11.5 * r) for lx in LOBES for r in range(8) for dx in (-6, 6)]},
    "exhale": {"tau": TAU, "tEnd": T_EXH},
}
if MANUAL:                                          # 用手換気：呼吸バッグの席と大きさ、満杯の時刻（sim_reflector.js が見る）
    GEO["bag"] = {"pivot": (BT_X, BT_Y), "slots": BAG_SLOTS, "keyT": BAG_KT, "keyS": BAG_S}
    GEO["nodes"]["BAGM"] = (BT_X, BT_Y + 14)
    GEO.update({"NB_FULL": NB_FULL, "NB_MIN": NB_MIN, "VT_B": VT_B, "T_FULL": T_FULL})
if len(sys.argv) > 3:
    json.dump(GEO, open(sys.argv[3], "w"), ensure_ascii=False)
add('<g id="particles"></g>')
C_FRESH, C_EXPG, C_DRV = "#2b2b2b", C_CO2_DOT, "#7a7a7a"   # 粒の色（新鮮／CO2 を含む／リフレクタガス。sim_reflector.js と同じ）


# ================= 字幕と進行バー =================
add('<g class="svgcap">')
CAP_Y = 830
add(f'<rect x="12" y="{CAP_Y-28}" width="{W-24}" height="44" rx="8" fill="#f4f1fb" stroke="#cbbfe8"/>')
_CAPS = ((("insp", "吸気", "呼吸バッグを手で押すと、ガスはリフレクタと吸収装置を通り、新鮮ガスと合わさって患者へ送られる"),
          ("exp", "呼気", "呼気と新鮮ガスがリフレクタへ入り、奥の呼吸バッグをふくらませる。いっぱいになって圧が上がると PEEP/APL 弁から排出装置へ"))
         if MANUAL else
         (("insp", "吸気", "リフレクタガス（O₂）がリフレクタのガスを押し出す。新鮮ガスが取り込みより少なく、O₂ の境目が呼吸ごとに患者側へ進む"),
          ("exp", "呼気", "呼気と新鮮ガスがリフレクタへ入る。取り込みのぶん呼気が少なく、奥の O₂ は出た量より多く残る"))
         if SHORT else
         (("insp", "吸気", "リフレクタガス（O₂）が奥からリフレクタのガスを押し出し、吸収装置を通って新鮮ガスと合わさり患者へ"),
          ("exp", "呼気", "呼気と新鮮ガスがリフレクタへ入り、そのぶん奥の O₂ と古いガスが PEEP/APL 弁から排出装置へ")))
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
label("⑤", "ガスモジュール", 180, 264, "below")   # 1.3：N₂O と Air のモジュールの間の下
label("⑥", "酸素フラッシュ", 512, FLUSH_Y + 45, "right")
label("⑦", "気化器", 500, VB + 66, "right")
text("注入式", 488, VB + 94, 14, color="#333")
label("⑧", "共通ガス出口", CGO_X + 10, 56, "left")
# 呼吸回路
label("⑨", "吸気弁", IV_X, 62, "right")
text("蛇管・", 1202, 165, 18); text("Yピース", 1202, 189, 18)
text("二酸化炭素", 848, 335, 18); text("吸収装置", 848, 359, 18)
label("⑪", "呼気弁", EV_X, EXP_Y - 58, "left")
text("PEEP/APL弁", APX, APY + 88, 13, "middle", 700)   # 弁の下（右は図の端、左は排出装置へ下りる管）
text("余剰ガス排出装置", 770, SC_T - 7, 17)

# ================= 凡例 =================
L2 = 770
# 2026-11-02：管の色の凡例（吸気側・呼気側）をやめ、粒の色の凡例にした
add(f'<circle cx="30" cy="{L2-6}" r="6" fill="#2b2b2b" stroke="#fff" stroke-width="1"/>')
text("CO₂ を含まないガス", 44, L2, 17)
add(f'<circle cx="222" cy="{L2-6}" r="6" fill="{C_CO2_DOT}" stroke="#fff" stroke-width="1"/>')
text("CO₂ を含むガス", 236, L2, 17)
add(f'<circle cx="392" cy="{L2-6}" r="6" fill="{C_DRV}" stroke="#fff" stroke-width="1"/>')
text("リフレクタガス（O₂）", 406, L2, 17)
# 2026-11-02：流れの矢印の凡例はやめた（流れの矢印をやめたため）

out[PIPE_MARK:PIPE_MARK] = flush_pipes()
add("</svg>")
open(sys.argv[1], "w").write("\n".join(o for o in out if o))
