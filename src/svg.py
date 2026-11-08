# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""SVG を組み立てる道具（図の生成スクリプトで共通）。
図の要素は add() で out に積み、最後に "\n".join(out) で書き出す。管（pipe）は外形を先に全部描いてから内腔を重ねるので、
pipe() はいったん PIPES にためて、flush_pipes() の戻り値を out の決まった位置（PIPE_MARK）に差し込む。
SMIL のアニメーションは 1 周期 CYC 秒（吸気 TI 秒＋呼気）。
使う前に configure(lang, family) を呼ぶ（en なら図の中の文字を labels_en.py で英語に、zh なら labels_zh.py で中国語（簡体字）に置き換える）。"""
import math

import labels_en
import labels_zh
from palette import FONT, FONT_ZH, K, B

CYC = 6.0                  # 1 周期（吸気 2 秒＋呼気 4 秒）
TI = 2.0                   # 吸気時間
GAS_W = 12                 # 管の太さ（外形）。内腔は 5 px 細い

LANG = "ja"                # "ja"・"en"・"zh"
FAMILY = "b"               # 図の方式：b＝上昇式ベローズ、p＝ピストン式（英語の文字の表で、方式ごとに違う文字を選ぶため）

out = []
add = out.append
PIPES = []


def configure(lang="ja", family="b"):
    global LANG, FAMILY
    LANG, FAMILY = lang, family


def text(s, x, y, size=19, anchor="start", weight=400, color=K, halo=True):
    if LANG in ("en", "zh"):
        s, _o = labels_en.en(FAMILY, s) if LANG == "en" else labels_zh.zh(FAMILY, s)
        size, anchor = _o.get("size", size), _o.get("anchor", anchor)
        x, y = x + _o.get("dx", 0), y + _o.get("dy", 0)
    h = ' stroke="#fff" stroke-width="5" stroke-linejoin="round" paint-order="stroke"' if halo else ""
    add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
        f'text-anchor="{anchor}" font-family="{FONT_ZH if LANG == "zh" else FONT}"{h}>{s}</text>')


def pipe(pts, inner="#fff", w=GAS_W):
    PIPES.append((pts, inner, w))


def flush_pipes():
    """外形（黒）を全部描いてから内腔を描く。角は miter、端は square で延ばして継ぎ目を埋める"""
    outer, inner = [], []
    for pts, col, w in PIPES:
        d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
        outer.append(f'<path d="{d}" fill="none" stroke="{K}" stroke-width="{w}" stroke-linejoin="miter" stroke-linecap="square"/>')
        inner.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w-5}" stroke-linejoin="miter" stroke-linecap="square"/>')
    return outer + inner


def dashed(pts, color=K, w=2.2):
    d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-dasharray="8 6"/>')


def arrow(x, y, ang, color=B, size=16):
    a = math.radians(ang)
    p = [(x + size * math.cos(a), y + size * math.sin(a)),
         (x + size * 0.7 * math.cos(a + 2.5), y + size * 0.7 * math.sin(a + 2.5)),
         (x + size * 0.7 * math.cos(a - 2.5), y + size * 0.7 * math.sin(a - 2.5))]
    add('<polygon points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py in p) + f'" fill="{color}"/>')


def anim(attr, values, key_times, calc="linear", extra=""):
    return (f'<animate attributeName="{attr}" values="{values}" keyTimes="{key_times}" calcMode="{calc}" '
            f'dur="{CYC}s" repeatCount="indefinite"{extra}/>')


def gate_open(phase):
    """吸気中だけ／呼気中だけ見えるグループの開始タグ"""
    k = f"{TI/CYC:.4f}"
    v = "1;0" if phase == "insp" else "0;1"
    return f'<g opacity="{v[0]}">' + anim("opacity", v, f"0;{k}", "discrete")


def label(n, name, x, y, where="right"):
    """部品の名前だけを、以前の記号の位置に置く"""
    if where == "right":
        text(name, x - 12, y + 7)
    elif where == "left":
        text(name, x + 12, y + 7, anchor="end")
    elif where == "below":
        text(name, x, y + 8, anchor="middle")
    elif where == "above":
        text(name, x, y - 10, anchor="middle")


def leader(x1, y1, x2, y2):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{B}" stroke-width="2"/>')


def rect(x, y, w, h, fill="#fff", rx=4, sw=2.2):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{K}" stroke-width="{sw}"/>')


def gate_win(a, b):
    """周期のうち a〜b 秒だけ見えるグループの開始タグ"""
    if a <= 0:
        return '<g opacity="1">' + anim("opacity", "1;0", f"0;{b/CYC:.4f}", "discrete")
    if b >= CYC:
        return '<g opacity="0">' + anim("opacity", "0;1", f"0;{a/CYC:.4f}", "discrete")
    return '<g opacity="0">' + anim("opacity", "0;1;0", f"0;{a/CYC:.4f};{b/CYC:.4f}", "discrete")


def win_keys(a, b, v_in, v_out, d=0.1):
    """a〜b 秒は v_in、それ以外は v_out の値をとる、なめらかな切り替えのキー列"""
    pts = [(0.0, v_in if a <= 0 else v_out)]
    if a > 0:
        pts += [(a - d, v_out), (a + d, v_in)]
    if b < CYC:
        pts += [(b - d, v_in), (b + d, v_out)]
    else:
        pts += [(CYC - d, v_in)]
    if a <= 0:
        pts += [(CYC - d, v_out)]
    pts += [(CYC, v_in if a <= 0 else v_out)]
    pts = sorted({round(t, 3): v for t, v in pts}.items())
    return ";".join(str(v) for _, v in pts), ";".join(f"{t/CYC:.4f}" for t, _ in pts)
