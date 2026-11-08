# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""色と字体（上昇式ベローズ・ピストン式の図で共通）。
色は意味のあるものだけに使う：灰＝金属、青＝動く部品、薄い青＝透明な材料、薄い赤＝組織、濃い灰＝ゴム、黒＝吸引。
管の中（内腔）は吸気側も呼気側も白。ガスに色はないので、CO2 の有無は粒の色（黒／オレンジ）だけで示す。
印刷の 2 色刷り（mode "2c"：青＋墨）で変わる色は by_mode() が返す。"""

FONT = "'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif"
# 中国語（簡体字）版の字体（2026-11-08）。日本語の字体で簡体字を出すと、字形が日本式になったり別の字体に混ざったりするので分ける
FONT_ZH = "'PingFang SC','Hiragino Sans GB','Noto Sans SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
# 繁体字（台湾）版の字体（2026-11-08）
FONT_TW = "'PingFang TC','Hiragino Sans CNS','Noto Sans TC','Noto Sans CJK TC','Microsoft JhengHei',sans-serif"
K = "#1a1a1a"            # 黒（墨）
B = "#1f5fae"            # 2色目（青）：動く部品
B_TINT = "#d6e4f5"       # 青の淡い網
B_TINT2 = "#ffffff"      # 部品の地（色は意味のあるものだけに使うので白）
G_TINT = "#ffffff"       # 同上（モーター・余剰ガス排出装置など）
GLASS = "#e3effa"        # 透明な材料（流量計のガラス管・吸収装置の容器・弁のドーム）
GLASS_SHADE = "#a9c6e6"  # 透明な材料の右側の影
METAL = "#c8c8c8"        # 金属の部品
FLOAT_C = "#8a8a8a"      # 流量計のフロート（ガラスの薄い青の中で高さが読めるよう口金より濃い灰）
RUBBER = "#4a4a4a"       # 呼吸バッグのゴム
INSP_FILL = "#ffffff"    # 管の内腔（吸気側）
INSP_C = "#ffffff"
C_CO2_DOT = "#e8590c"    # CO2 を含むガスの粒（sim_common.js の C_CO2 と同じ）
ABS_USED_C = "#8f6fd0"   # 使い切った吸収剤（エチルバイオレット系の指示薬の紫）
PIPE_NAME = {"O₂": "緑", "N₂O": "青", "Air": "黄"}   # 配管端末器の帯に書く色名（2 色刷りでも識別できる）


def by_mode(mode):
    """印刷の方式で変わる色。mode は "color" か "2c"（青＋墨の 2 色刷り）"""
    color = mode == "color"
    return {
        "LUNG_TISSUE": "#f2bcc2" if color else "#d6d6d6",   # 肺胞の壁（組織と毛細血管）。2 色刷りでは墨の網
        "EXP_C": "#ffffff",                                  # 管の内腔（呼気側）。吸気側と同じ白
        "EXP_ARROW": "#5e3fae" if color else "#1f5fae",   # 呼気の色（字幕の札）
        "PIPE": {"O₂": "#1e9e4a", "N₂O": "#1f6fd1", "Air": "#f2c500"} if color
                else {"O₂": "#ffffff", "N₂O": "#ffffff", "Air": "#ffffff"},   # 配管の識別色。2 色刷りは色名の文字で示す
        "CYL": {"O₂": "#111111", "N₂O": "#8c8c8c", "Air": "#8c8c8c"},        # ボンベの塗色（墨と墨の網で表せる）
        "WICK": "#e3d5b0" if color else "#d0d0d0",           # 気化器の灯心（布）
    }
