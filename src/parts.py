# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""部品の描き方（上昇式ベローズ・ピストン式の図で共通）。平らな 2 次元の構造の断面で、色は意味のあるものだけ：
灰＝金属、青＝動く部品、薄い青＝透明な材料、薄い赤＝組織、濃い灰＝ゴム。方針の正本は著者の設計ノート。"""
import math

from geometry import unit
from palette import B, GLASS, GLASS_SHADE, K, METAL, RUBBER
from svg import CYC, TI, add, arrow, rect, text, win_keys

VD_UP, VD_OUT = 19.5, 16.5         # 一方向弁の中の粒の通り道：弁座の上へ上がる高さと、出口側の通路までの横の距離
VD_LIFT = 9                        # 開いたときに弁板が持ち上がる高さ
ALV_N, ALV_BUMP = 16, 4.0          # 肺葉の輪郭の袋の数と、ふくらみの高さ（px）
FM_W_TOP, FM_W_BOT = 14, 9         # 流量計のガラス管の半幅（上・下）


def check_valve(x, y, col="#fff", is_open=False, rot=0, anim=None):
    """逆止弁（スイング式）の断面。2026-11-02 に記号（▲と横棒）から構造に近い図に変えた。
    下の通路から入ったガスが弁板（青＝動く部品）を押し上げて上の部屋へ抜ける。逆向きには弁板が弁座（部屋の床）を
    ふさぐ。弁板は左の軸で回るので、開いても管の中心（粒の通り道）をふさがない。
    ガスが流れている系統（is_open）は開いた姿、ほかは閉じた姿で描く（動かさない）。通路は管の内腔と同じ色（col）。
    rot で向きを回す（-90 で右から入って左へ出る）"""
    if rot:
        add(f'<g transform="rotate({rot} {x} {y})">')
    rect(x - 13, y - 14, 26, 28, fill=METAL, rx=4)
    add(f'<rect x="{x-4}" y="{y+4}" width="8" height="11.2" fill="{col}"/>')       # 入口の通路
    add(f'<rect x="{x-9}" y="{y-10}" width="18" height="14" fill="{col}"/>')      # 弁の部屋
    add(f'<rect x="{x-4}" y="{y-15.2}" width="8" height="5.2" fill="{col}"/>')     # 出口の通路
    ang = -80 if is_open else 0
    if anim:                                     # anim = (角度の列, keyTimes)：弁板を周期に合わせて開閉する
        add(f'<g><animateTransform attributeName="transform" type="rotate" '
            f'values="{";".join(f"{v} {x-7} {y+2.75}" for v in anim[0])}" keyTimes="{anim[1]}" dur="{CYC}s" repeatCount="indefinite"/>')
        ang = 0
    add(f'<rect x="{x-7}" y="{y+1.5}" width="12" height="2.5" rx="0.8" fill="{B}" stroke="{K}" stroke-width="1" '
        f'transform="rotate({ang} {x-7} {y+2.75})"/>')
    if anim:
        add('</g>')
    add(f'<circle cx="{x-7}" cy="{y+2.75}" r="1.6" fill="{K}"/>')
    if rot:
        add('</g>')


def valve_detour(x, y, direction):
    """一方向弁の中の粒の通り道：入口の通路 → 縦の筒（弁座）を上へ → 弁板の下を横へ → 出口側の通路を下りる"""
    s = direction
    return [(x, y), (x, y - VD_UP), (x + s * VD_OUT, y - VD_UP), (x + s * VD_OUT, y)]


def one_way_valve(x, y, direction, fill, open_phase=None, open_win=None, spring=False):
    """一方向弁（ドーム弁）の断面。2026-11-02 に論理的な図（仕切りとフラップ）から実物の構造に近い図に変えた。
    入口の通路から縦の筒を上がり、筒の口（弁座）に載った弁板（青）を押し上げて透明なドームの中へ出て、
    出口側の通路を下りて出る。逆向きの流れでは弁板が弁座に押しつけられて閉じる。
    本体は灰（樹脂・金属の塊）、ガスの通路は fill の色（その側の管の内腔と同じ）、ドームは透明（GLASS）。
    direction = 1 なら左→右、-1 なら右→左。open_phase="insp"／"exp" はその相で、open_win=(a, b) は周期の a〜b 秒で
    弁板が持ち上がる。spring は PEEP/Pmax 弁のばね（弁板が上がると縮む）"""
    s = direction
    hw = 4                                          # 通路の半幅（管の内腔とほぼ同じ太さ）
    xo = x + s * VD_OUT                             # 出口側の縦の通路
    rect(x - 32, y - 12, 64, 28, fill=METAL, rx=4)
    # 通路：端は本体の輪郭を越えて、管の内腔・ドームの中につなぐ
    xa, xb = sorted((x - s * 33.2, x + s * hw))
    add(f'<rect x="{xa}" y="{y-hw}" width="{xb-xa}" height="{2*hw}" fill="{fill}"/>')
    xa, xb = sorted((xo - s * hw, x + s * 33.2))
    add(f'<rect x="{xa}" y="{y-hw}" width="{xb-xa}" height="{2*hw}" fill="{fill}"/>')
    for cx in (x, xo):
        add(f'<rect x="{cx-hw}" y="{y-13.2}" width="{2*hw}" height="{13.2+hw}" fill="{fill}"/>')
    # 透明なドーム：平らな照り（左上）と影（右上）の線で丸みを出す
    DR, DH, b = 25, 24, y - 12
    add(f'<path d="M {x-DR},{b} A {DR},{DH} 0 0 1 {x+DR},{b} Z" fill="{GLASS}"/>')
    def _pt(th, k):
        return x + (DR - k) * math.cos(math.radians(th)), b - (DH - k) * math.sin(math.radians(th))
    (p0, q0), (p1, q1) = _pt(160, 5), _pt(118, 5)
    add(f'<path d="M {p0:.1f},{q0:.1f} A {DR-5},{DH-5} 0 0 1 {p1:.1f},{q1:.1f}" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>')
    (p0, q0), (p1, q1) = _pt(62, 4.5), _pt(22, 4.5)
    add(f'<path d="M {p0:.1f},{q0:.1f} A {DR-4.5},{DH-4.5} 0 0 1 {p1:.1f},{q1:.1f}" fill="none" stroke="{GLASS_SHADE}" stroke-width="3" stroke-linecap="round"/>')
    # ドームの床（本体の上面）：縦の筒と出口側の通路の口だけ開いている
    cuts = sorted([(x - hw, x + hw), (xo - hw, xo + hw)])
    xs = [x - DR] + [v for c in cuts for v in c] + [x + DR]
    for xa, xb in zip(xs[0::2], xs[1::2]):
        add(f'<line x1="{xa}" y1="{b}" x2="{xb}" y2="{b}" stroke="{K}" stroke-width="2.2"/>')
    add(f'<path d="M {x-DR},{b} A {DR},{DH} 0 0 1 {x+DR},{b}" fill="none" stroke="{K}" stroke-width="2.2"/>')
    # 弁座（筒の口の縁）
    for xa in (x - hw - 3.5, x + hw):
        add(f'<rect x="{xa}" y="{b-3}" width="3.5" height="3" fill="{METAL}" stroke="{K}" stroke-width="1.2"/>')
    # 弁板（青＝動く部品）：閉じているときは弁座に載り、開くと持ち上がる
    if open_phase:
        k1, k2 = TI / CYC - 0.012, TI / CYC + 0.018
        vals = f"-{VD_LIFT};-{VD_LIFT};0;0;-{VD_LIFT}" if open_phase == "insp" else f"0;0;-{VD_LIFT};-{VD_LIFT};0"
        add(f'<g><animateTransform attributeName="transform" type="translate" '
            f'values="{";".join("0 " + v for v in vals.split(";"))}" '
            f'keyTimes="0;{k1:.4f};{k2:.4f};0.985;1" dur="{CYC}s" repeatCount="indefinite"/>')
    elif open_win:
        vals, keys = win_keys(open_win[0], open_win[1], -VD_LIFT, 0)
        add(f'<g><animateTransform attributeName="transform" type="translate" '
            f'values="{";".join("0 " + v for v in vals.split(";"))}" keyTimes="{keys}" '
            f'dur="{CYC}s" repeatCount="indefinite"/>')
    add(f'<rect x="{x-11}" y="{b-6.5}" width="22" height="3.5" rx="1" fill="{B}" stroke="{K}" stroke-width="1.2"/>')
    if open_phase or open_win:
        add('</g>')
    if spring:
        # 弁板を上から押さえるばね（PEEP/Pmax 弁）。上端はドームの中の受け、弁板が上がると縮む
        st, sb = b - 22, b - 6.5
        zz = " ".join(f"L {x + (5 if k % 2 else -5)},{st + (sb - st) * k / 4:.1f}" for k in range(1, 4))
        add(f'<line x1="{x-6}" y1="{st}" x2="{x+6}" y2="{st}" stroke="{K}" stroke-width="2"/>')
        if open_win:
            sv, sk = win_keys(open_win[0], open_win[1], round((sb - VD_LIFT - st) / (sb - st), 4), 1)
            add(f'<g transform="translate({x},{st})"><g><animateTransform attributeName="transform" type="scale" '
                f'values="{";".join("1 " + v for v in sv.split(";"))}" keyTimes="{sk}" dur="{CYC}s" repeatCount="indefinite"/>'
                f'<g transform="translate({-x},{-st})">')
        add(f'<path d="M {x},{st} {zz} L {x},{sb}" fill="none" stroke="{K}" stroke-width="1.4" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
        if open_win:
            add('</g></g></g>')


def breathing_bag(bp, sy, fill, scales=None, keys=None):
    """呼吸バッグ（2026-11-02 描き直し）：ゴムの袋の断面。壁（濃い灰の帯。両側に黒い輪郭）の中は回路のガス
    （fill）。首は金属の差し込み口（22 mm の継ぎ手）にかぶせてある。scales・keys（周期内の秒）を渡すと、
    差し込み口を中心にふくらみ・しぼむ。粒の席（GEO の bag.slots）も同じ中心・同じ倍率で動く"""
    d = (f"M {bp-2},{sy-7} L {bp-14},{sy-7} "
         f"C {bp-24},{sy-7} {bp-28},{sy-28} {bp-46},{sy-28} "
         f"C {bp-62},{sy-28} {bp-72},{sy-20} {bp-72},{sy} "
         f"C {bp-72},{sy+20} {bp-62},{sy+28} {bp-46},{sy+28} "
         f"C {bp-28},{sy+28} {bp-24},{sy+7} {bp-14},{sy+7} L {bp-2},{sy+7} Z")
    if scales:
        add(f'<g transform="translate({bp},{sy})"><g><animateTransform attributeName="transform" type="scale" '
            f'values="{";".join(f"{v:.4f}" for v in scales)}" keyTimes="{";".join(f"{t/CYC:.4f}" for t in keys)}" '
            f'calcMode="linear" dur="{CYC}s" repeatCount="indefinite"/><g transform="translate({-bp},{-sy})">')
    add(f'<path d="{d}" fill="{fill}"/>')
    add(f'<path d="{d}" fill="none" stroke="{K}" stroke-width="8" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
    add(f'<path d="{d}" fill="none" stroke="{RUBBER}" stroke-width="5" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
    if scales:
        add('</g></g></g>')
    # 差し込み口：金属の継ぎ手と回路側のつば。中はガスの道
    rect(bp - 18, sy - 9, 20, 18, fill=METAL, rx=2, sw=1.6)
    rect(bp - 3, sy - 13, 7, 26, fill=METAL, rx=1.5, sw=1.8)
    add(f'<rect x="{bp-19.2}" y="{sy-3.5}" width="24.4" height="7" fill="{fill}"/>')


def squeeze_mark(bp, sy, gate):
    """用手換気の吸気：バッグを手で押す印（上から押す矢印と「手で押す」）。gate は表示する時間のグループの開始タグ"""
    add(gate)
    text("手で押す", bp - 44, sy - 64, 14, "middle", 700)
    add(f'<line x1="{bp-44}" y1="{sy-60}" x2="{bp-44}" y2="{sy-46}" stroke="{K}" stroke-width="2.5"/>')
    arrow(bp - 44, sy - 47, 90, K, 12)
    add("</g>")


def channels(paths, col="#fff"):
    ds = ["M " + " L ".join(f"{x},{y}" for x, y in pts) for pts in paths]
    for d in ds:
        add(f'<path d="{d}" fill="none" stroke="{K}" stroke-width="9" stroke-linejoin="miter" stroke-linecap="square"/>')
    for d in ds:
        add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="5" stroke-linejoin="miter" stroke-linecap="square"/>')


def collar(cx, cy, ux, uy):
    """コネクタのつば（管の差し込み口の縁）"""
    ang = math.degrees(math.atan2(uy, ux))
    add(f'<rect x="-3" y="-14" width="7" height="28" rx="1.5" fill="#fff" stroke="{K}" stroke-width="2" transform="translate({cx:.1f},{cy:.1f}) rotate({ang:.1f})"/>')


def port(x0, y0, x1, y1):
    """弁や Y ピースの差し込み口：短い管の先につば"""
    add(f'<path d="M {x0},{y0} L {x1},{y1}" stroke="{K}" stroke-width="20" stroke-linecap="butt"/>')
    add(f'<path d="M {x0},{y0} L {x1},{y1}" stroke="#fff" stroke-width="14" stroke-linecap="butt"/>')
    u = unit(x0, y0, x1, y1)
    collar(x1, y1, *u)


def hose(p0, c, p1, fill, d=22, rib=8.5):
    """蛇管：2 次ベジェ曲線に沿って曲がった管と、等間隔のひだ"""
    pts = []
    for i in range(121):
        t = i / 120
        pts.append(((1-t)**2*p0[0] + 2*(1-t)*t*c[0] + t*t*p1[0],
                    (1-t)**2*p0[1] + 2*(1-t)*t*c[1] + t*t*p1[1]))
    dpath = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    add(f'<path d="{dpath}" fill="none" stroke="{K}" stroke-width="{d+4}" stroke-linecap="butt" stroke-linejoin="round"/>')
    add(f'<path d="{dpath}" fill="none" stroke="{fill}" stroke-width="{d}" stroke-linecap="butt" stroke-linejoin="round"/>')
    acc, nxt = 0.0, rib
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        seg = math.hypot(xb - xa, yb - ya)
        while acc + seg >= nxt:
            t = (nxt - acc) / seg
            x, y = xa + t * (xb - xa), ya + t * (yb - ya)
            nx, ny = -(yb - ya) / seg, (xb - xa) / seg
            add(f'<line x1="{x + nx*d/2:.1f}" y1="{y + ny*d/2:.1f}" x2="{x - nx*d/2:.1f}" y2="{y - ny*d/2:.1f}" stroke="{K}" stroke-width="1.2"/>')
            nxt += rib
        acc += seg


def alveoli_pts(lx, inset, lobe):
    """肺葉の輪郭（両端が半円の縦長の形）の周上に等間隔の点と外向きの法線。inset だけ内側の輪郭も同じ点の数で作る。
    lobe = (幅, 上端 y, 下端 y)"""
    LOBE_W, LOBE_T, LOBE_B = lobe
    R = LOBE_W / 2 - inset
    y1, y2 = LOBE_T + LOBE_W / 2, LOBE_B - LOBE_W / 2
    L = y2 - y1
    P = 2 * L + 2 * math.pi * (LOBE_W / 2 - inset)
    out_ = []
    for i in range(ALV_N):
        s = P * i / ALV_N
        if s < L:                                            # 右の直線（下へ）
            nrm = (1.0, 0.0); c = (lx, y1 + s)
        elif s < L + math.pi * R:                            # 下の半円
            a = (s - L) / R; nrm = (math.cos(a), math.sin(a)); c = (lx, y2)
        elif s < 2 * L + math.pi * R:                        # 左の直線（上へ）
            nrm = (-1.0, 0.0); c = (lx, y2 - (s - L - math.pi * R))
        else:                                                # 上の半円
            a = math.pi + (s - 2 * L - math.pi * R) / R; nrm = (math.cos(a), math.sin(a)); c = (lx, y1)
        out_.append(((c[0] + R * nrm[0], c[1] + R * nrm[1]), nrm))
    return out_


def alveoli_path(lx, inset, lobe):
    """点と点の間を外へふくらませた曲線でつなぎ、小さな袋が並んだ輪郭にする"""
    pts = alveoli_pts(lx, inset, lobe)
    (x0, y0), _ = pts[0]
    d = [f"M {x0:.1f},{y0:.1f}"]
    for k in range(len(pts)):
        (ax, ay), na = pts[k]
        (bx, by), nb = pts[(k + 1) % len(pts)]
        nx, ny = na[0] + nb[0], na[1] + nb[1]
        n = math.hypot(nx, ny) or 1.0
        cx, cy = (ax + bx) / 2 + ALV_BUMP * 2 * nx / n, (ay + by) / 2 + ALV_BUMP * 2 * ny / n
        d.append(f"Q {cx:.1f},{cy:.1f} {bx:.1f},{by:.1f}")
    return " ".join(d) + " Z"


def bronchus(lx, frac0, frac1, hil, lobe_t):
    """気管分岐部から肺葉の入口へ向かう気管支の軸線上の 2 点（frac は軸線の長さに対する割合。1 ＝ 肺葉の壁の少し奥）。hil は気管分岐部、lobe_t は肺葉の上端 y"""
    ex, ey = lx - hil[0], (lobe_t + 3) - hil[1]
    return (hil[0] + ex * frac0, hil[1] + ey * frac0, hil[0] + ex * frac1, hil[1] + ey * frac1)
