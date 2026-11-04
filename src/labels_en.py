# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""図の中の文字の英語版（2026-11-02）。figure_bellows.py・figure_piston.py に en を付けると、text() がこの表で
日本語を英語に置き換える。値は文字列、または {"t": 文字列, "size": 大きさ, "dx": 横のずれ, "dy": 縦のずれ, "anchor": 揃え}。
方式ごとに変えたいときは ("b", 日本語)・("p", 日本語) をキーにする（b：上昇式ベローズ、p：ピストン式）。
英語は日本語より横に長いので、大きさと位置をここで調整する。表にない日本語が残ったら生成スクリプトが止まる"""

EN = {
    # 見出し・凡例
    "ガス供給機構・気化器": "Gas supply & vaporizers",
    "呼吸回路": "Breathing circuit",
    ("p", "呼吸回路"): {"t": "Breathing circuit", "size": 20},
    "CO₂ を含まないガス": "Gas without CO₂",
    "CO₂ を含むガス": {"t": "Gas with CO₂", "dx": 10},
    # ガス供給機構
    "青": {"t": "N₂O", "size": 13},
    "黄": {"t": "Air", "size": 13},
    "緑": {"t": "O₂", "size": 14},
    "中央配管": "Pipeline",
    "ボンベ": "Cylinder",
    "減圧弁": "Regulator",
    "逆止弁": "Check valve",
    "亜酸化窒素": {"t": "N₂O shut-off", "size": 16},           # 1 行目だけで「N₂O」にすると流量計の「N₂O」と区別できない（押せる文字のため）
    "遮断弁": {"t": "valve", "size": 16},
    "O₂の圧で開閉": {"t": "O₂ pressure signal", "size": 14},
    "流量計": {"t": "Flowmeters", "size": 11, "anchor": "start", "dx": -31},
    "停止": {"t": "Off", "size": 14},
    "使用中": {"t": "In use", "size": 14},
    "停止中": {"t": "Off", "size": 14},
    "インターロック": {"t": "Interlock", "size": 16},
    "気化器": "Vaporizers",
    "酸素フラッシュ": "O₂ flush",
    "共通ガス出口": {"t": "Common gas outlet", "size": 17, "dx": -8},
    # 呼吸回路
    "吸気弁": {"t": "Inspiratory valve", "size": 16},
    "呼気弁": {"t": "Expiratory valve", "size": 16},
    ("p", "呼気弁"): {"t": "Expiratory valve", "size": 15, "anchor": "end", "dx": 24},
    "蛇管・": {"t": "Breathing", "size": 16},
    "Yピース": {"t": "tubes, Y-piece", "size": 16},
    "回路内圧計": {"t": "Pressure gauge", "size": 15},
    "患者": "Patient",
    "気管": {"t": "Trachea", "size": 9, "anchor": "end"},
    ("p", "気管"): {"t": "Trachea", "size": 10},
    "(死腔)": {"t": "(dead", "size": 9, "anchor": "end", "dy": -5},
    ("p", "（死腔）"): {"t": "(dead", "size": 9, "dx": 6, "dy": -4},
    "肺胞": {"t": "Alveoli", "size": 12, "dy": -3},
    ("p", "肺胞"): {"t": "Alveoli", "size": 12},
    "二酸化炭素": {"t": "CO₂", "size": 17},
    "吸収装置": {"t": "absorber", "size": 17},
    "APL弁": {"t": "APL valve", "size": 15, "dx": -4},
    "呼吸バッグ": {"t": "Reservoir bag", "size": 11, "dx": 2},
    ("p", "呼吸バッグ"): {"t": "Reservoir bag", "size": 13, "dx": 3},
    "手で押す": {"t": "Squeeze", "size": 14},
    ("r", "呼吸バッグ"): {"t": "Reservoir bag", "size": 13},
    "切替弁": {"t": "Bag/vent switch", "size": 15, "dx": 10},
    ("r", "切替弁"): {"t": "Bag/vent switch", "size": 10},
    "用手": {"t": "Bag", "size": 14},
    "人工呼吸": {"t": "Vent", "size": 13},
    "ベローズ": "Bellows",
    "駆動ガス（O₂）": {"t": "Drive gas (O₂)", "size": 13},
    "余剰ガス弁": {"t": "Relief valve", "size": 13},
    "余剰ガス排出装置": {"t": "Scavenging system", "size": 15},
    ("r", "余剰ガス排出装置"): {"t": "Scavenging system", "size": 14},
    "大気": {"t": "To room", "size": 11},
    "吸引": {"t": "Vac", "size": 9},
    "→ 手術室外へ": {"t": "→ Out of OR", "size": 14, "dx": 6},
    "（止まっている）": {"t": "(stopped)", "size": 13},
    # ピストン式
    "モーター": "Motor",
    "ピストン": "Piston",
    "新鮮ガス・": {"t": "Fresh gas", "size": 15, "dx": 18},
    "デカップリング弁": {"t": "decoupling valve", "size": 15, "dx": 18},
    "PEEP/Pmax弁": {"t": "PEEP/Pmax valve", "size": 15},
    "外気取り込み弁": {"t": "Aux. air valve", "size": 12},
    "（陰圧防止）": {"t": "(vacuum relief)", "size": 10},
    "APLバイパス弁": {"t": "APL bypass valve", "size": 13},
    "（人工呼吸中に開く）": {"t": "(open in vent mode)", "size": 11},
    "排気逆止弁": {"t": "Exhaust check valve", "size": 12},
    # ボリュームリフレクタ式（figure_reflector.py）
    "ボリュームリフレクタ": {"t": "Volume reflector", "size": 15},
    "リフレクタガス（O₂）": {"t": "Reflector gas (O₂)", "size": 13},                    # 凡例
    "リフレクタガス": {"t": "Reflector gas", "size": 12},
    "モジュール（O₂）": {"t": "module (O₂)", "size": 12},
    "電磁弁": {"t": "solenoid", "size": 10},
    "PEEP/APL弁": {"t": "PEEP/APL valve", "size": 10, "dx": -3},
    "リフレクタガス（O₂）が奥からリフレクタのガスを押し出し、吸収装置を通って新鮮ガスと合わさり患者へ":
        {"t": "Reflector gas (O₂) pushes gas out of the reflector; it flows through the absorber, joins the fresh gas and goes to the patient", "size": 14},
    "呼吸バッグを手で押すと、ガスはリフレクタと吸収装置を通り、新鮮ガスと合わさって患者へ送られる":
        {"t": "Squeezing the bag pushes gas through the reflector and absorber; it joins the fresh gas and goes to the patient", "size": 14},
    "呼気と新鮮ガスがリフレクタへ入り、奥の呼吸バッグをふくらませる。満杯になると PEEP/APL 弁から排出装置へ":
        {"t": "Exhaled and fresh gas enter the reflector and refill the bag at the far end; once full, excess leaves through the PEEP/APL valve", "size": 14},
    "呼気と新鮮ガスがリフレクタへ入り、そのぶん奥の O₂ と古いガスが PEEP/APL 弁から排出装置へ":
        {"t": "Exhaled and fresh gas enter the reflector; O₂ and the oldest gas at the far end leave through the PEEP/APL valve", "size": 14},
    # 図の中の説明文（コマ撮りだけに出る）
    "人工呼吸中も呼吸バッグは": "During ventilation, the bag",
    "リザーバーとして回路に残り、": "stays in the circuit as a",
    "ふくらみ・しぼむ": "reservoir and inflates/deflates",
    "用手換気ではピストンが止まり、": "In manual ventilation, the",
    "呼吸バッグを手で押して": "piston stops and the bag is",
    "患者へガスを送る": "squeezed to ventilate",
    # 字幕（コマ撮りだけに出る）
    "吸気": "Insp",
    "呼気": "Exp",
    "呼気①": "Exp 1",
    "呼気②": "Exp 2",
    "駆動ガス（O₂）がベローズを押し下げ、ガスは吸収装置と吸気弁を通って患者へ送られる":
        {"t": "Drive gas (O₂) pushes the bellows down; gas flows through the absorber and inspiratory valve to the patient", "size": 15},
    "呼気と新鮮ガスがベローズを下から押し上げる。上まで上がると、余ったガスは余剰ガス排出装置へ":
        {"t": "Exhaled and fresh gas push the bellows up; once it is full, excess gas goes to the scavenging system", "size": 15},
    "呼吸バッグを手で押すと、ガスは切替弁から吸収装置と吸気弁を通って患者へ送られる":
        {"t": "Squeezing the bag sends gas through the switch, absorber and inspiratory valve to the patient", "size": 15},
    "呼気と新鮮ガスが呼吸バッグへ戻ってふくらませる。満杯になると APL 弁から余剰ガス排出装置へ":
        {"t": "Exhaled and fresh gas refill the bag; once it is full, excess gas leaves via the APL valve", "size": 15},
    "ピストンが押し上がり、ガスを吸気弁から患者へ送る。デカップリング弁は閉じ、新鮮ガスは呼吸バッグへ":
        {"t": "The piston rises and sends gas to the patient; the decoupling valve closes and fresh gas goes to the bag", "size": 15},
    "呼気は呼気弁と PEEP/Pmax 弁を通って呼吸バッグへ。人工呼吸中もバッグがふくらむ":
        {"t": "Exhaled gas passes the expiratory and PEEP/Pmax valves into the bag, which inflates", "size": 15},
    "ピストンが下がり、バッグのガスと新鮮ガスをデカップリング弁から吸い込む":
        {"t": "The piston descends and draws bag gas and fresh gas through the decoupling valve", "size": 15},
    "呼吸バッグを手で押すと、ガスは吸収装置を通り、新鮮ガスと合わさってデカップリング弁と吸気弁から患者へ":
        {"t": "Squeezing the bag sends gas through the absorber, then with fresh gas through the decoupling and inspiratory valves", "size": 15},
}


def en(family, s):
    """日本語 s の英語版を (文字列, 上書きする引数) で返す。日本語を含まない文字はそのまま"""
    if not any("　" <= ch <= "鿿" or "＀" <= ch <= "￯" for ch in s):
        return s, {}
    v = EN.get((family, s), EN.get(s))
    if v is None:
        raise KeyError(f"labels_en.py に英語がない：{s!r}")
    t, o = (v, {}) if isinstance(v, str) else (v["t"], {k: v[k] for k in ("size", "dx", "dy", "anchor") if k in v})
    return t.replace("&", "&amp;").replace("<", "&lt;"), o                 # SVG（XML）の中に入れるので
