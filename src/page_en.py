# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""操作ページの英語版の文（2026-11-02）。build_page.py に --lang en を付けると使う。
- HTML：日本語版の HTML の文を、下の HTML_PAIRS で順に置き換える（構造は日本語版と同じ）。置き換え残しの日本語があると止まる
- 部品の解説：日本語版の TERMS（拡大する範囲 rect を含む）に、名前・押せる文字・解説だけを上書きする
- 図の中の文字は labels_en.py（押せる文字 words はそれと同じ綴りにする）"""
import json

LANG = "en"
TITLE = "CircleFlow: Gas Flow in the Anesthesia Machine and Breathing Circuit"

HTML_PAIRS = [
    ('<small>方式</small>', '<small>Type</small>'), ('<small>換気</small>', '<small>Ventilation</small>'), ('<small>新鮮ガス</small>', '<small>Fresh gas</small>'),
    ('aria-label="速さ" title="速さ"', 'aria-label="Speed" title="Speed"'),
    ("<span>麻酔器と呼吸回路のガスの流れ</span>", "<span>Gas flow in the anesthesia machine and breathing circuit</span>"),
    ('aria-label="使い方"><span class="q">?</span>使い方', 'aria-label="How to use"><span class="q">?</span>How to use'),
    ('<button id="hlBtn">見どころ</button>', '<button id="hlBtn">Highlights</button>'),
    ('<button id="moreBtn">くわしく</button>', '<button id="moreBtn">Learn more</button>'),
    ('role="tab">上昇式ベローズ</button>', 'role="tab">Ascending bellows</button>'),
    ('role="tab">ピストン式</button><button data-type="reflector" role="tab"><span class="full">ボリュームリフレクタ式</span><span class="short">リフレクタ式</span></button>', 'role="tab">Piston</button><button data-type="reflector" role="tab"><span class="full">Volume reflector</span><span class="short">Reflector</span></button>'),
    ('<span class="lab">換気</span>', '<span class="lab">Ventilation</span>'),
    ('class="on">人工呼吸</button>', 'class="on">Ventilator</button>'),
    ('data-vent="man">用手換気</button>', 'data-vent="man">Manual (bag)</button>'),
    ('<span class="lab">新鮮ガス</span>', '<span class="lab">Fresh gas</span>'),
    ('class="on">多め</button>', 'class="on">High</button>'),
    ('data-flow="low">低流量</button>', 'data-flow="low">Low flow</button>'),
    ('data-flow="short" hidden>不足</button>', 'data-flow="short" hidden>Too low</button>'),
    ('<b>追跡中</b>', '<b>Following</b>'),
    ('aria-label="追跡をやめる"', 'aria-label="Stop following"'),
    ('<button class="x" id="cardX" aria-label="閉じる">', '<button class="x" id="cardX" aria-label="Close">'),
    ('‹ 前へ', '‹ Prev'), ('次へ ›', 'Next ›'),
    ('aria-label="一時停止"', 'aria-label="Pause"'),
    ('aria-label="時刻"', 'aria-label="Time"'),
    ('0.0 秒', '0.0 s'),
    ('<span class="lab">速さ</span>', '<span class="lab">Speed</span>'),
    ('data-term="absorber">吸収剤</button>', 'data-term="absorber">Absorbent</button>'),
    ('aria-label="吸収剤の使用率"', 'aria-label="Absorbent used"'),
    ('>1 呼吸目<', '>Breath 1<'),
    ('<button id="absSwap">交換</button>', '<button id="absSwap">Replace</button>'),
    ("CircleFlow © 2026 朝元雅明（Masaaki Asamoto）。プログラムは", "CircleFlow © 2026 Masaaki Asamoto. Code:"),
    ("rel=\"license\">MIT</a>、図と文章は", "rel=\"license\">MIT</a>; figures and text:"),
    ("deed.ja", "deed.en"),
    ("ソースコード：<a href=\"https://github.com/anesthesia-sims/circleflow\">GitHub（anesthesia-sims/circleflow）</a>",
     "Source code: <a href=\"https://github.com/anesthesia-sims/circleflow\">GitHub (anesthesia-sims/circleflow)</a>"),
    ("rel=\"license\">CC BY 4.0</a>。", "rel=\"license\">CC BY 4.0</a>. "),
    ("</a>。版 @@VERSION@@<br>", "</a>. Version @@VERSION@@<br>"),
    ("教育用の模式図で、臨床の判断や機器の操作に用いるものではありません。特定のメーカーとは関係ありません。",
     "An educational schematic, not for clinical decisions or for operating or checking equipment. Not affiliated with any manufacturer. Gas color codes follow Japanese standards."),
    ("謝辞：帝京大学医学部附属溝口病院 麻酔科の平林剛先生から、呼吸回路と人工呼吸器の方式について助言をいただきました。内容の誤りは著者の責任です。",
     "Acknowledgments: We thank Dr. Go Hirabayashi (Department of Anesthesiology, Teikyo University School of Medicine Hospital Mizonokuchi) for advice on the breathing circuit and ventilator types. Any errors are the author&rsquo;s own."),
    ("もし間違いに気づかれましたら、<a href=\"https://github.com/anesthesia-sims/circleflow/issues/new\">GitHub の Issue</a> へ投稿していただくか、メール（<a href=\"mailto:masaaki.asamoto@gmail.com?subject=CircleFlow\">masaaki.asamoto@gmail.com</a>）でご連絡をお願いします。",
     "If you notice a mistake, please report it on <a href=\"https://github.com/anesthesia-sims/circleflow/issues/new\">GitHub Issues</a> or by email (<a href=\"mailto:masaaki.asamoto@gmail.com?subject=CircleFlow\">masaaki.asamoto@gmail.com</a>)."),
    ('aria-label="くわしい解説"', 'aria-label="Learn more"'),
    ('<button class="x" id="moreX" aria-label="閉じる">', '<button class="x" id="moreX" aria-label="Close">'),
    ("<h2>方式の違い</h2>", "<h2>How the types differ</h2>"),
    ("<tr><th></th><th>上昇式ベローズ</th><th>ピストン式</th><th>ボリュームリフレクタ式</th></tr>", "<tr><th></th><th>Ascending bellows</th><th>Piston</th><th>Volume reflector</th></tr>"),
    ("<tr><td>新鮮ガスの作り方</td><td>流量計とニードル弁、可変バイパス式の気化器</td><td>流量計とニードル弁、可変バイパス式の気化器</td><td>ガスごとの電子制御のガスモジュールと、注入式の気化器</td></tr>",
     "<tr><td>How fresh gas is made</td><td>Flowmeters with needle valves; variable-bypass vaporizer</td><td>Flowmeters with needle valves; variable-bypass vaporizer</td><td>An electronically controlled gas module for each gas; injection vaporizer</td></tr>"),
    ("<tr><td>人工呼吸器を動かす力</td><td>駆動ガス（O₂）がハウジング内でベローズを押し下げる</td><td>モーターがロッドでピストンを押し引きする（駆動ガスを使わない）</td><td>リフレクタガス（O₂）が、リフレクタの中のガスを膜なしで直接押す</td></tr>",
     "<tr><td>What drives the ventilator</td><td>Drive gas (O₂) in the housing pushes the bellows down</td><td>A motor moves the piston through a rod (no drive gas)</td><td>Reflector gas (O₂) pushes directly on the gas in the reflector, with no membrane between them</td></tr>"),
    ("<tr><td>次の吸気ガスのため方</td><td>呼気と新鮮ガスがベローズを下から押し上げてためる</td><td>ピストンが下がって、呼吸バッグのガスと新鮮ガスを吸い込む</td><td>呼気と新鮮ガス（吸収装置を逆に通る）がリフレクタの患者側に入り、奥のガスを押し出してためる</td></tr>",
     "<tr><td>How the next breath is collected</td><td>Exhaled and fresh gas push the bellows up from below</td><td>The piston descends and draws in gas from the reservoir bag and fresh gas</td><td>Exhaled and fresh gas (flowing backward through the absorber) enter the patient end of the reflector, pushing out the gas at the far end</td></tr>"),
    ("<tr><td>吸気中の新鮮ガス</td><td>吸気に加わって患者へ</td><td>新鮮ガス・デカップリング弁が閉じ、呼吸バッグへ向かう</td><td>吸気に加わって患者へ（そのぶんリフレクタガスで押し出す量が減る）。ガスモジュールが新鮮ガスを主に吸気中に流す（この図では 1 呼吸の 2/3 を吸気中、1/3 を呼気中に）</td></tr>",
     "<tr><td>Fresh gas during inspiration</td><td>Joins the inspired gas and goes to the patient</td><td>The fresh gas decoupling valve closes; fresh gas goes to the reservoir bag</td><td>Joins the inspired gas and goes to the patient (the reflector gas pushes out correspondingly less). The gas modules deliver fresh gas mainly during inspiration (in this figure, two thirds of each breath&rsquo;s fresh gas during inspiration and one third during expiration)</td></tr>"),
    ("<tr><td>人工呼吸中の呼吸バッグ</td><td>切替弁で回路から外れ、動かない</td><td>リザーバーとして回路に残り、ふくらみ・しぼむ</td><td>切替弁で回路から外れ、動かない（用手換気では切替弁が開いてリフレクタの奥につながり、リフレクタガスは止まる）</td></tr>",
     "<tr><td>Reservoir bag during ventilation</td><td>Taken out of the circuit by the switch; does not move</td><td>Stays in the circuit as a reservoir; inflates and deflates</td><td>Taken out of the circuit by the switch; does not move (in manual ventilation the switch opens, connecting it at the far end of the reflector, and the reflector gas is stopped)</td></tr>"),
    ("<tr><td>回路の陰圧</td><td>人工呼吸器にガスを吸い込む動きがないので、起こりにくい</td><td>吸い込む動きがあるため、PEEP/Pmax 弁と外気取り込み弁で防ぐ</td><td>押す動きだけで、ガスを吸い込む動きはない</td></tr>",
     "<tr><td>Negative pressure in the circuit</td><td>Unlikely, because the ventilator never draws gas in</td><td>Possible because the piston draws gas in; prevented by the PEEP/Pmax valve and the auxiliary air valve</td><td>Only pushing, no drawing in of gas</td></tr>"),
    ("<tr><td>余ったガスの出口</td><td>ベローズが上がりきると、余剰ガス弁から排出装置へ</td><td>呼吸バッグがいっぱいになって圧が上がると、APL バイパス弁から排気逆止弁を通って排出装置へ（用手換気では APL 弁から）</td><td>リフレクタの奥から、PEEP/APL 弁を通って排出装置へ（出ていくのは O₂ と最も古いガス）</td></tr>",
     "<tr><td>Where excess gas leaves</td><td>Once the bellows is fully up, through the relief valve to the scavenging system</td><td>Once the bag is full and the pressure rises, through the APL bypass valve and exhaust check valve to the scavenging system (through the APL valve in manual ventilation)</td><td>From the far end of the reflector, through the PEEP/APL valve to the scavenging system (what leaves is O₂ and the oldest gas)</td></tr>"),
    ("<tr><td>新鮮ガスを減らしたときの 1 回換気量</td><td>ベローズが押し出す量が同じなら、吸気中に加わる新鮮ガスのぶん減る（現代の機種は補正する。この図でもベローズが押し出す量を増やして同じにしている）</td><td>変わらない（デカップリング弁があり、患者へ送るのはピストンが押し出す量だけ）</td><td>変わらない（リフレクタガスで押し出す量を増やす）</td></tr>",
     "<tr><td>Tidal volume when fresh gas is reduced</td><td>Falls by the fresh gas no longer added during inspiration if the bellows delivers the same volume (modern machines compensate; in this figure the bellows pushes out more to keep it the same)</td><td>Unchanged (the decoupling valve means only the volume pushed by the piston reaches the patient)</td><td>Unchanged (the reflector gas pushes out more)</td></tr>"),
    ("<tr><td>呼気終末の回路内圧</td><td>余剰ガス弁の開放圧（2〜3 cmH₂O）が残る</td><td>PEEP/Pmax 弁の設定値まで下がる（設定 0 なら 0 付近）</td><td>PEEP/APL 弁で設定した PEEP</td></tr>",
     "<tr><td>Circuit pressure at end-expiration</td><td>The opening pressure of the relief valve (2–3 cmH₂O) remains</td><td>Falls to the PEEP setting (near 0 if PEEP is 0)</td><td>The PEEP set on the PEEP/APL valve</td></tr>"),
    ("<h2>設計の考え方</h2>", "<h2>Design philosophy</h2>"),
    ("<p>上昇式ベローズは、ベローズが上がりきらないとそのぶん次の吸気が減る代わりに、ガスを能動的に吸い込む機構がないので人工呼吸器の側から患者の気道を陰圧にすることがなく、離断や大きなリークではベローズが上がらなくなって異常に気づきやすい、安全を優先した設計です。ピストン式は、ガスを吸い込む動きによって陰圧が生じうる構造を、新鮮ガス・デカップリングや弁などの制御で補い、正確な換気量や多様な換気モードを実現しています。ボリュームリフレクタ式は、ピストンの代わりに O₂ の流れでガスを押し、長い管の中で押すガスと患者のガスをほとんど混ざらないまま隣り合わせる設計です。吸い込む動きがないので陰圧は起こりにくく、動く部品もありません。</p>",
     "<p>The ascending bellows delivers a smaller breath if it does not rise fully, but in exchange it has no mechanism that actively draws gas in: the ventilator itself cannot make the patient&rsquo;s airway pressure negative, and a disconnection or a large leak keeps the bellows from rising, so the problem is easy to notice. A design that puts safety first. The piston design can create negative pressure because it draws gas in; it compensates with fresh gas decoupling and valves, and in return achieves accurate tidal volumes and many ventilation modes. The volume reflector design pushes gas with a flow of O₂ instead of a piston, keeping the pushing gas and the patient&rsquo;s gas side by side, almost unmixed, inside a long tube. Nothing draws gas in, so negative pressure is unlikely, and there are no moving parts.</p>"),
    ("<h2>用手換気</h2>", "<h2>Manual ventilation</h2>"),
    ("<p>人工呼吸器を使わず、呼吸バッグを手で押して換気します。上昇式ベローズでは切替弁を「用手」に倒し、栓の L 字の穴が呼気側の合流点と APL 弁・呼吸バッグの側をつなぎます（ベローズは回路から外れて止まります）。ピストン式では切替弁はなく、ピストンが止まり、もともと回路にある呼吸バッグを押します。どちらも吸気では、押されたバッグのガスが吸収装置を通って CO₂ を除かれ、新鮮ガスと合わさって吸気弁から患者へ送られます（ピストン式では新鮮ガス・デカップリング弁を通ります）。呼気では、呼気と新鮮ガスがバッグへ戻ってふくらませ、いっぱいになって回路の圧が APL 弁の設定を超えると、余ったガスは APL 弁から余剰ガス排出装置へ出ていきます。ボリュームリフレクタ式では、切替弁が開いて呼吸バッグがリフレクタの奥の端につながり、リフレクタガスは止まります。手で押したバッグのガスはリフレクタと吸収装置を通って患者へ送られ、呼気はリフレクタを通ってバッグへ戻ります。いっぱいになって圧が設定を超えると、余ったガスは PEEP/APL 弁（APL 弁として働きます）から余剰ガス排出装置へ出ていきます。</p>",
     "<p>The patient is ventilated by squeezing the reservoir bag instead of using the ventilator. With the ascending bellows, the switch is turned to Bag, and the L-shaped channel of the plug connects the expiratory junction to the APL valve and bag (the bellows is taken out of the circuit and stops). The piston machine has no such switch: the piston stops and you squeeze the bag that is always in the circuit. In both, during inspiration the squeezed gas passes through the absorber, loses its CO₂, joins the fresh gas and goes through the inspiratory valve to the patient (through the fresh gas decoupling valve on the piston machine). During expiration, exhaled and fresh gas refill the bag; once it is full and the circuit pressure exceeds the APL setting, excess gas leaves through the APL valve to the scavenging system. With the volume reflector, the switch opens to connect the bag at the far end of the reflector, and the reflector gas is stopped: the squeezed gas passes through the reflector and the absorber to the patient, and exhaled gas returns through the reflector to the bag. Once the bag is full and the pressure exceeds the setting, excess gas leaves through the PEEP/APL valve (acting as the APL valve) to the scavenging system.</p>"),
    ("<h2>新鮮ガスが足りないとき（ボリュームリフレクタ式）</h2>", "<h2>When fresh gas runs short (volume reflector)</h2>"),
    ("<p>場面「不足」では、患者の取り込み（肺胞で血液へ取り込まれて消える粒。1 呼吸に 4 粒）が新鮮ガス（1 呼吸に 3 粒）より多くなっています。回路のガスは呼吸ごとに 1 粒ずつ減り、そのぶんリフレクタガス（O₂）が奥に残って境目が患者側へ進み、数呼吸のうちに O₂ が吸収装置を通って吸気に加わり、肺胞まで届きます。実機でも、新鮮ガスが取り込みとリークの合計より少ないと、不足分をリフレクタガスの O₂ が補います。換気量は保たれますが、吸気の O₂ は設定より高くなり、麻酔薬は薄まります。ほかの場面では、見やすさのために取り込みを 0 としています。</p>",
     "<p>In the Too low scene, the patient&rsquo;s uptake (particles that vanish from the alveoli into the blood, 4 per breath) exceeds the fresh gas (3 per breath). The gas in the circuit falls by one particle each breath; that much reflector gas (O₂) stays at the far end, the boundary moves toward the patient, and within a few breaths O₂ passes through the absorber, joins the inspired gas and reaches the alveoli. On the real machine too, when fresh gas is less than uptake plus leaks, the shortfall is made up by O₂ from the reflector gas module. Tidal volume is maintained, but inspired O₂ rises above the setting and the anesthetic is diluted. In the other scenes, uptake is set to zero for clarity.</p>"),
    ("<h2>二酸化炭素吸収剤の色の変化</h2>", "<h2>Color change of the CO₂ absorbent</h2>"),
    ("<p>呼気は吸収装置の下から入るため、吸収剤は入口側（下）から使われ、紫の帯が出口側（上）へ進みます。実際には数時間以上かけて進む変化を、数分から十数分に縮めて表示しています。</p>",
     "<p>Exhaled gas enters the absorber from below, so the absorbent is used from the inlet (bottom), and the purple band moves toward the outlet (top). A change that takes hours or more in reality is compressed into minutes here.</p>"),
    ("<p>「新鮮ガス：多め」は、新鮮ガス流量が分時換気量に近い場合です。上昇式ベローズでは、呼気の CO₂ は吸収装置に届く前に余剰ガスとして排出されるため、この図では吸収剤はほとんど減りません。ピストン式では、呼気がいったん呼吸バッグにたまり、ピストンが吸収装置を通して吸い込むため、約 35 呼吸で使い切り、使い切ると吸気側に CO₂ がわずかに戻ります。</p>",
     "<p>With Fresh gas: High, the fresh gas flow is close to the minute ventilation. With the ascending bellows, the exhaled CO₂ leaves as excess gas before reaching the absorber, so in this figure the absorbent is hardly used. With the piston, exhaled gas first collects in the bag and the piston draws it through the absorber, so the absorbent is used up in about 35 breaths, after which a little CO₂ returns to the inspiratory side.</p>"),
    ("<p>「新鮮ガス：低流量」は、新鮮ガスをその 4 分の 1 に減らした場合です。呼気のほとんどが吸収装置を通って再び吸われるため、消費が速くなります（約 20〜25 呼吸）。使い切るとオレンジの粒が吸気側の管を通って患者へ戻り、吸気の CO₂ が上がります（カプノグラムの基線が 0 に戻らなくなる）。</p>",
     "<p>With Fresh gas: Low flow, the fresh gas is cut to one quarter. Almost all exhaled gas passes through the absorber and is breathed again, so the absorbent is used up faster (about 20–25 breaths). Once it is exhausted, orange particles return to the patient through the inspiratory limb and inspired CO₂ rises (the capnogram baseline no longer returns to zero).</p>"),
    ("<p>ボリュームリフレクタ式では、呼気と新鮮ガスはリフレクタへ入り、次の吸気で後から入った順に押し出されます。多めの場面では、押し出されるのは呼気のあとに入った新鮮ガスで、呼気の CO₂ はリフレクタの奥から PEEP/APL 弁を通って出ていくため、吸収剤の色は変わりません。低流量では押し出す量が増え、約 23 呼吸で使い切ります。</p>\n  <p>方式ごとの呼吸数の違いは、実際の機種どうしの比較ではありません。指示薬の色は、使用後にしばらく置くと白に戻ることがあります。交換の判断は色だけでなく、吸気の CO₂ も合わせて行います。</p>",
     "<p>With the volume reflector, exhaled and fresh gas enter the reflector and are pushed out on the next breath in reverse order. In the High scene what is pushed out is the fresh gas that entered after the exhaled gas, and the exhaled CO₂ leaves from the far end of the reflector through the PEEP/APL valve, so the absorbent color does not change. In the Low flow scene the reflector pushes out more, and the absorbent is used up in about 23 breaths.</p>\n  <p>The difference in breaths between the types is not a comparison of real machines. The indicator color can fade back to white after the absorbent rests, so decide when to replace it from inspired CO₂ as well as the color.</p>"),
    ("<p class=\"small\">本図は模式図です。部品の形・位置・弁の構成は機種によって異なります（ピストン式は Dräger Fabius 型、ボリュームリフレクタ式は Getinge（Maquet）Flow-i 型の構成を参考にしています）。1 呼吸は 6 秒（吸気 2 秒・呼気 4 秒）で表示しています。ガスの量や時間、吸収剤の容量は見やすさのために整えた値です。</p>",
     "<p class=\"small\">This is a schematic. The shape and position of parts and the valve arrangement vary between machines (the piston machine is modeled on the Dräger Fabius layout, and the volume reflector machine on the Getinge (Maquet) Flow-i). Each breath is shown as 6 s (2 s inspiration, 4 s expiration). Gas volumes, timing and absorbent capacity are adjusted for clarity.</p>"),
    ('<div class="keys"><kbd>→</kbd> <kbd>Enter</kbd> 進む　<kbd>←</kbd> <kbd>BS</kbd> 戻る　<kbd>Esc</kbd> 閉じる</div>', '<div class="keys"><kbd>→</kbd> <kbd>Enter</kbd> next&ensp;<kbd>←</kbd> <kbd>BS</kbd> back&ensp;<kbd>Esc</kbd> close</div>'),
    ('<button id="tourSkip">閉じる</button><button id="tourPrev">戻る</button><button id="tourNext" class="pri">次へ</button>',
     '<button id="tourSkip">Close</button><button id="tourPrev">Back</button><button id="tourNext" class="pri">Next</button>'),
]

# 部品の解説（日本語版の TERMS に上書き。拡大する範囲 rect は日本語版のものを使い、英語の文字がはみ出すものだけ RECT で広げる）
TERMS = {
    "supply": ("Gas supply & vaporizers", ["Gas supply & vaporizers"], {
        "bellows": "Gases from the hospital pipelines or cylinders (O₂, air, N₂O) are metered by the flowmeters and mixed, and the vaporizer adds anesthetic vapor. The resulting fresh gas leaves through the common gas outlet to the breathing circuit.",
        "piston": "Gases from the hospital pipelines or cylinders (O₂, air, N₂O) are metered by the flowmeters and mixed, and the vaporizer adds anesthetic vapor. The resulting fresh gas leaves through the common gas outlet to the breathing circuit.",
        "reflector": "Gases from the hospital pipelines or cylinders (O₂, air, N₂O) are metered and mixed by an electronically controlled gas module for each gas, and the injection vaporizer adds anesthetic vapor. The resulting fresh gas leaves through the common gas outlet to the breathing circuit."}),
    "pipeline": ("Pipeline", ["Pipeline"],
                 "O₂, air and N₂O arrive through pipes in the wall. To prevent mix-ups, each gas has its own color (in Japan: O₂ green, air yellow, N₂O blue) and its own connector shape."),
    "cylinder": ("Cylinder", ["Cylinder"],
                 "A backup for when the pipeline is unavailable. Gas is stored at high pressure. In Japan, O₂ cylinders are black and the others gray."),
    "regulator": ("Pressure regulator", ["Regulator"],
                  "Reduces the high cylinder pressure. It is set slightly below pipeline pressure, so pipeline gas is used first whenever the pipeline is connected."),
    "check": ("Check valve", ["Check valve"],
              "Lets gas flow only one way (upward), so pipeline and cylinder gas cannot flow back into each other. In the figure, the flap is open only for the gases that are flowing."),
    "n2ocut": ("N₂O shut-off valve", ["N₂O shut-off", "valve", "O₂ pressure signal"],
               "Held open by O₂ pressure. If the O₂ supply fails and its pressure drops, a spring closes the valve and stops N₂O: a safety device so that N₂O is not delivered without O₂."),
    "flowmeter": ("Flowmeter", ["Flowmeters"],
                  "Opening the knob below (a needle valve) lifts the float in the glass tube. The tube widens toward the top, so the higher the flow, the higher the float. Read the scale at the top of the float."),
    "gasModule": ("Gas module", ["Gas modules"],
                  "One electronically controlled flow regulator per gas, replacing the flowmeter and needle valve. A coil lifts the valve plunger (blue) to change the gap at the nozzle, and the control unit adjusts it so that the flow measured by the flow sensor (a diaphragm senses the pressure difference across a restriction) matches the setting. During mechanical ventilation the valve opens wider during inspiration, so fresh gas is delivered mainly during inspiration. In this figure the particles upstream of the valve flow steadily, and those waiting just before the valve stand for the pressurized supply; the real flow in the supply line varies with the valve opening."),
    "controller": ("Control unit", ["Control unit"],
                   "The machine's electronic control. It adjusts the gas module valves and the vaporizer's injection so that the set fresh gas flow, O₂ concentration and anesthetic concentration are delivered (the dashed lines are control signals)."),
    "vaporizer": ("Vaporizer", ["Vaporizers", "In use", "injection type"], {
        "bellows": "Turns liquid anesthetic into vapor. Part of the gas passes through the vaporizing chamber and picks up vapor; the dial sets how it is mixed with the rest (the bypass), which sets the concentration.",
        "piston": "Turns liquid anesthetic into vapor. Part of the gas passes through the vaporizing chamber and picks up vapor; the dial sets how it is mixed with the rest (the bypass), which sets the concentration.",
        "reflector": "An injector sprays liquid anesthetic in short pulses into a heated vaporizing chamber, where it evaporates and mixes with the fresh gas passing through (injection type). The liquid sits in a reservoir below, pressurized by fresh gas so that it is pushed to the injector. The concentration is set electronically rather than by a dial, and the injected amount follows the fresh gas flow. Only the selected one of the two vaporizers works."}),
    "interlock": ("Interlock", ["Interlock"],
                  "Prevents two vaporizers from being used at once. Turning one dial makes the blue bar lock the other dial."),
    "flush": ("O₂ flush", ["O₂ flush"],
              "Pressing the button sends a large flow of O₂ (about 35–75 L/min) into the circuit, bypassing the flowmeters and vaporizer. It contains no anesthetic. (It is not pressed in this simulator.)"),
    "cgo": ("Common gas outlet", ["Common gas outlet"], {
        "bellows": "The outlet where the fresh gas made by the flowmeters and vaporizer leaves the machine for the breathing circuit.",
        "piston": "The outlet where the fresh gas made by the flowmeters and vaporizer leaves the machine for the breathing circuit.",
        "reflector": "The outlet where the fresh gas made by the gas modules and vaporizer leaves the machine for the breathing circuit."}),
    "circuit": ("Breathing circuit", ["Breathing circuit"],
                "The loop the patient breathes in and out of (circle system). One-way valves set the direction of flow, and the absorber removes exhaled CO₂ so the gas can be breathed again."),
    "decouple": ("Fresh gas decoupling valve", ["Fresh gas", "decoupling valve"],
                 "Closes during inspiration so that fresh gas goes to the reservoir bag instead of the patient. As a result, changing the fresh gas flow does not change the tidal volume."),
    "inspValve": ("Inspiratory valve", ["Inspiratory valve"],
                  "A one-way valve that opens only toward the patient. Flow lifts the blue disc under the dome; reverse flow presses the disc onto its seat and closes it."),
    "gauge": ("Pressure gauge", ["Pressure gauge", "cmH₂O"],
              "Shows the pressure in the breathing circuit (cmH₂O). It rises during inspiration and falls during expiration."),
    "hose": ("Breathing tubes & Y-piece", ["Breathing", "tubes, Y-piece"],
             "The inspiratory and expiratory tubes join at the Y-piece, which connects to the mask or tracheal tube. Beyond the Y-piece, inspired and expired gas share the same path."),
    "patient": ("Patient & trachea (dead space)", ["Patient", "Trachea", "(dead", "space)"],
                "Gas in the trachea never reaches the alveoli, so it picks up no CO₂ (dead space). At the start of inspiration, the exhaled gas left in the trachea goes back to the alveoli first."),
    "alveoli": ("Alveoli", ["Alveoli"],
                "Where CO₂ moves from the blood into the gas. Black particles turn orange (gas with CO₂) here. The lungs expand during inspiration and shrink during expiration."),
    "expValve": ("Expiratory valve", ["Expiratory valve"],
                 "A one-way valve that opens only for gas returning from the patient. It closes during inspiration so inspired gas cannot flow into the expiratory limb."),
    "peep": ("PEEP/Pmax valve", ["PEEP/Pmax valve"],
             "A valve in the expiratory limb that works together with the piston. During inspiration it is closed, so the gas pushed by the piston goes to the patient rather than to the bag (it opens only if circuit pressure exceeds the limit, Pmax). During expiration it lets exhaled gas pass to the bag but keeps lung pressure at PEEP, so the descending piston cannot pull gas out of the lungs."),
    "absorber": ("CO₂ absorber", ["CO₂", "absorber"],
                 "The absorbent removes exhaled CO₂ by a chemical reaction; orange particles turn black as they pass through. Used absorbent turns from white to purple because of an indicator dye (time is compressed here; speed up to see it)."),
    "apl": ("APL valve", ["APL valve"], {
        "bellows": "Opens when circuit pressure exceeds the value set by the knob, releasing excess gas to the scavenging system. It limits the pressure when you squeeze the bag. During mechanical ventilation, the bag/vent switch takes it out of the circuit.",
        "piston": "Opens when circuit pressure exceeds the value set by the knob, releasing excess gas to the scavenging system. It limits the pressure when you squeeze the bag. During mechanical ventilation the APL bypass valve is open, so the APL valve stays closed."}),
    "bypass": ("APL bypass valve", ["APL bypass valve", "(open in vent mode)"],
               "Branches from the bag line next to the APL valve. During mechanical ventilation it is open, and once the bag is full and the pressure rises, excess gas leaves through it without passing the APL valve. In manual ventilation it closes so that the APL valve can control the pressure."),
    "exhaust": ("Exhaust check valve", ["Exhaust check valve"],
                "A check valve that opens only toward the scavenging system. Gas from the APL valve and the APL bypass valve passes through it to the scavenging system and cannot come back."),
    "bag": ("Reservoir bag", ["Reservoir bag", "Squeeze"], {
        "bellows": "In manual ventilation, squeeze this bag to send gas to the patient. It refills during expiration; once it is full and the pressure exceeds the APL setting, excess gas leaves through the APL valve. During mechanical ventilation the bag/vent switch takes it out of the circuit and it does not move.",
        "piston": "Even during mechanical ventilation it stays in the circuit as a reservoir: it collects exhaled and fresh gas, then deflates as the piston draws gas in. In manual ventilation the piston stops and you squeeze this bag to ventilate the patient.",
        "reflector": "During mechanical ventilation the switch takes it out of the circuit and it does not move. In manual ventilation the switch opens and connects it at the far end of the reflector. Squeezing it sends gas through the reflector and the absorber to the patient; during expiration it refills through the reflector. Once it is full and the pressure exceeds the setting, excess gas leaves through the PEEP/APL valve."}),
    "selector": ("Bag/vent switch", ["Bag/vent switch", "Bag", "Vent"], {
        "bellows": "Switches between manual ventilation (bag) and mechanical ventilation (bellows). The blue plug turns, and its L-shaped channel changes which paths are connected.",
        "reflector": "Switches between manual ventilation (bag) and mechanical ventilation. During mechanical ventilation it is closed and takes the bag out of the circuit; in manual ventilation it opens and connects the bag at the far end of the reflector (the reflector gas is stopped)."}),
    "bellows": ("Bellows", ["Bellows"],
                "A folded bag. During inspiration, drive gas around it pushes it down and sends the gas inside to the patient. During expiration, exhaled and fresh gas push it back up (ascending bellows). A leak keeps it from rising fully, which makes leaks easy to notice. In manual ventilation it is taken out of the circuit and stops."),
    "drive": ("Drive gas", ["Drive gas (O₂)"],
              "O₂ that enters the housing around the bellows and pushes on it from outside. The bellows wall keeps it separate from the gas the patient breathes."),
    "spill": ("Ventilator relief valve", ["Relief valve"],
              "Once the bellows has risen fully, it releases excess gas to the scavenging system. During inspiration, drive gas pressure holds it closed. It takes 2–3 cmH₂O to open, so this pressure remains in the circuit at the end of expiration."),
    "piston": ("Piston", ["Piston", "Motor"],
               "The motor pushes the piston up, sending gas from the cylinder to the patient. The volume pushed out is the tidal volume. No drive gas is used. The piston descends in late expiration to draw in the next breath. In manual ventilation it stops at the top."),
    "ambient": ("Auxiliary air valve", ["Aux. air valve", "(vacuum relief)"],
                "If the circuit runs short of gas while the piston descends, this valve lets in room air so that the circuit does not reach negative pressure. (It does not open in this simulator.)"),
    "scav": ("Scavenging system", ["Scavenging system", "→ Out of OR", "To room", "Vac"],
             "Removes excess anesthetic gas from the operating room by suction. Openings to the room keep the suction, or any back-pressure, from reaching the breathing circuit."),
    "particles": ("Gas particles", ["Gas without CO₂", "Gas with CO₂", "Reflector gas (O₂)"],
                  "Each particle is a small amount of gas: black is gas without CO₂, orange is gas with CO₂. Particles turn orange in the alveoli and black again in the absorber. Gray squares are the reflector gas (O₂) of the volume reflector type (and the drive gas of the bellows type): gas that pushes, not gas the patient breathes. Click a particle to follow it."),
    "reflector": ("Volume reflector", ["Volume reflector"],
                  "A long tube of about 1.2 L, coiled, with no moving parts. Exhaled gas enters at the patient end and leaves from the same end (last in, first out). Because the tube is long, the gas at the two ends hardly mixes. The light gray part is where the reflector gas (O₂) is; its edge is the boundary with the patient's gas (there is no membrane). As long as enough fresh gas is supplied, the reflector gas (O₂) at the far end does not reach the patient end."),
    "reflGas": ("Reflector gas module (O₂)", ["Reflector gas module (O₂)"],
                "The O₂ that powers ventilation. During inspiration a solenoid valve opens and O₂ enters at the far end, pushing the gas in the reflector toward the patient. There is no membrane between it and the patient's gas, but as long as the fresh gas exceeds the patient's uptake and any leak, the boundary moves back toward the far end every breath, so it does not reach the patient. (If fresh gas falls short, O₂ makes up the difference and enters the circuit.)"),
    "peepApl": ("PEEP/APL valve", ["PEEP/APL valve"],
                "The valve at the far end of the reflector. It is closed during inspiration and opens during expiration, letting excess gas (the O₂ and the oldest gas at the far end) out to the scavenging system while keeping end-expiratory pressure at the set PEEP. In manual ventilation it works as the APL valve: one valve with two roles."),
    "exhausted": ("Absorbent exhausted", [], ""),
}
RECT = {   # 英語の文字がはみ出す部品だけ、拡大する範囲を広げる（{部品: {方式: [x0, y0, x1, y1]}}。ブラウザで文字の枠を測って決めた）
    "check": {"bellows": [50, 455, 610, 503], "piston": [50, 455, 610, 503]},
    "regulator": {"bellows": [100, 497, 590, 545], "piston": [100, 497, 590, 545]},
    "cylinder": {"bellows": [95, 535, 572, 650], "piston": [95, 535, 572, 650]},
    "cgo": {"bellows": [490, 40, 700, 140], "piston": [490, 40, 700, 140]},
    "gauge": {"bellows": [810, 150, 990, 212], "piston": [925, 22, 1050, 100]},
    "inspValve": {"bellows": [835, 50, 1002, 142], "piston": [1010, 45, 1180, 142]},
    "hose": {"bellows": [915, 95, 1178, 485], "piston": [1090, 100, 1298, 497]},
    "expValve": {"bellows": [865, 385, 1015, 482], "piston": [1000, 405, 1158, 500]},
    "peep": {"piston": [935, 435, 1084, 530]},
    "exhaust": {"piston": [714, 630, 866, 680]},
    "decouple": {"piston": [795, 35, 956, 140]},
}

PHASES = {
    "bellows": [["Insp", 0, 2, "insp", "Drive gas (O₂) pushes the bellows down, sending gas through the absorber and the inspiratory valve to the patient. Fresh gas joins the inspired gas."],
                ["Exp", 2, 6, "exp", "Exhaled and fresh gas push the bellows up from below. Once it reaches the top, excess gas flows through the relief valve to the scavenging system."]],
    "piston": [["Insp", 0, 2, "insp", "The piston rises and sends gas through the inspiratory valve to the patient. The fresh gas decoupling valve is closed, so fresh gas flows backward through the absorber to the reservoir bag."],
               ["Exp 1", 2, 3.6, "exp", "Exhaled gas passes the expiratory and PEEP/Pmax valves into the reservoir bag, which inflates even during mechanical ventilation. Once it is full and the pressure rises, excess gas flows through the APL bypass valve to the scavenging system."],
               ["Exp 2", 3.6, 6, "exp", "The piston descends and draws gas from the bag (through the absorber) and fresh gas through the decoupling valve into the cylinder. It reaches the bottom at 5.7 s and stops; for the rest of the breath, fresh gas goes to the bag."]],
    "bellowsMan": [["Insp", 0, 2, "insp", "Squeezing the bag sends gas through the switch (set to Bag), the absorber and the inspiratory valve to the patient. Fresh gas joins it. The bellows is stopped."],
                   ["Exp", 2, 6, "exp", "Exhaled and fresh gas return to the bag and inflate it. Once the bag is full and the pressure exceeds the APL setting, excess gas leaves through the APL valve to the scavenging system."]],
    "reflectorMan": [["Insp", 0, 2, "insp", "The reflector gas is stopped. Squeezing the bag sends gas through the reflector and the absorber; it joins the fresh gas and goes through the inspiratory valve to the patient."],
                     ["Exp", 2, 6, "exp", "Exhaled and fresh gas enter the reflector and return to the bag at the far end, inflating it. Once the bag is full and the pressure exceeds the setting, excess gas leaves through the PEEP/APL valve to the scavenging system."]],
    "reflectorShort": [["Insp", 0, 2, "insp", "Reflector gas (O₂) enters at the far end and pushes out the gas in the reflector. In this scene the patient's uptake (particles that vanish from the alveoli into the blood) exceeds the fresh gas, so the O₂ boundary moves toward the patient each breath, and eventually O₂ passes through the absorber and joins the inspired gas."],
                       ["Exp", 2, 6, "exp", "Exhaled gas enters the reflector, and fresh gas also flows backward through the absorber into the reflector. Exhalation is smaller by the uptake, so less O₂ leaves the far end through the PEEP/APL valve than entered, and O₂ accumulates in the reflector."]],
    "reflector": [["Insp", 0, 2, "insp", "Reflector gas (O₂) enters at the far end and pushes out the gas stored in the reflector. The gas passes through the absorber, joins the fresh gas and goes through the inspiratory valve to the patient. The PEEP/APL valve is closed."],
                  ["Exp", 2, 6, "exp", "Exhaled gas enters the reflector directly, and fresh gas also flows backward through the absorber into the reflector. In exchange the O₂ and the oldest gas at the far end are pushed out through the PEEP/APL valve to the scavenging system."]],
    "pistonMan": [["Insp", 0, 2, "insp", "The piston is stopped. Squeezing the bag sends gas through the absorber; it joins the fresh gas and passes the decoupling and inspiratory valves to the patient."],
                  ["Exp", 2, 6, "exp", "Exhaled gas passes the expiratory and PEEP/Pmax valves back to the bag, and fresh gas flows backward through the absorber to the bag. Once the bag is full and the pressure exceeds the APL setting, excess gas leaves through the APL valve to the scavenging system."]],
}
UI = {
    "now": "What is happening now", "usedUp": "Exhausted", "pause": "Pause", "play": "Play", "start": "Start", "next": "Next", "hlEnd": "Finish",
    "hl": [["The relief valve creates PEEP", "Ascending bellows", "At the end of expiration, once the bellows is fully up, the relief valve opens and lets the excess gas out. The valve needs a little pressure to open, so the gauge does not return to zero but stops at 2 to 3 cmH₂O. Next, the same gauge on the piston machine."], ["The relief valve creates PEEP", "Piston", "The piston machine has no relief valve; the end-expiratory pressure is set by the PEEP/Pmax valve. With it set to zero, the needle returns almost to zero."], ["The relief valve creates PEEP", "Volume reflector", "On the volume reflector machine the PEEP/APL valve setting is the end-expiratory pressure. Here it is set to 2 cmH₂O, so the needle stops there. Each type decides the end-expiratory pressure differently."], ["The first gas back into the alveoli is the previous breath", "Same on every type", "The trachea (dead space) still holds exhaled gas (orange). When inspiration starts, this leftover is pushed back into the alveoli first, and only then does new gas (black) arrive. The particles show that the dead-space volume is ventilated without renewing the alveolar gas (half speed)."], ["Where fresh gas goes during expiration", "Ascending bellows", "The fresh gas inlet sits between the absorber and the inspiratory valve. During expiration the inspiratory valve is closed, so the fresh gas has nowhere else to go and flows backward through the absorber toward the bellows."], ["Where fresh gas goes during expiration", "Piston", "On the piston machine too, fresh gas during expiration flows backward through the absorber toward the reservoir bag. The fresh gas decoupling valve is closed, so it cannot go to the patient."], ["Where fresh gas goes during expiration", "Volume reflector", "On the volume reflector machine the gas module valves throttle the flow during expiration, so the particles from the pipeline queue before the modules. The little fresh gas that passes flows backward through the absorber into the reflector; on inspiration the valves pass more."], ["Fresh gas during inspiration and tidal volume", "Ascending bellows", "During inspiration the fresh gas simply joins the gas the bellows pushes out, so more fresh gas means a larger tidal volume."], ["Fresh gas during inspiration and tidal volume", "Piston", "During inspiration the fresh gas decoupling valve closes, so fresh gas goes into the reservoir bag instead of to the patient and inflates it. In the second half of expiration the piston draws it back from the bag. That is why the bag moves even during mechanical ventilation, and why fresh gas during inspiration does not change the tidal volume."], ["Fresh gas during inspiration and tidal volume", "Volume reflector", "On the volume reflector machine the reflector gas (O₂) pushes out correspondingly less when fresh gas enters during inspiration. The tidal volume stays the same whatever the fresh gas flow, and with high fresh gas flow very little O₂ enters from the module."], ["How the absorbent is used up", "High fresh gas flow", "With plenty of fresh gas, exhaled gas leaves through the relief valve as soon as the bellows is full, and little CO₂ reaches the absorber. Even at 16× speed the purple band hardly moves."], ["How the absorbent is used up", "Low flow", "With low flow almost all exhaled gas passes through the absorber and is breathed again, so the purple band advances from the inlet (16× speed). Once exhausted, orange particles return to the inspiratory side."], ["The APL valve opens only after the bag is full", "Ascending bellows", "During expiration in manual ventilation, exhaled and fresh gas first inflate the reservoir bag. The APL valve stays closed until the bag is full and the circuit pressure reaches its setting; then the plate drops and the excess gas leaves to the scavenging system."], ["The APL valve opens only after the bag is full", "Piston", "Manual ventilation on the piston machine follows the same order. Back in mechanical ventilation, the APL bypass valve opens instead of the APL valve to vent the excess."], ["The APL valve opens only after the bag is full", "Volume reflector", "On the volume reflector machine the reservoir bag connects at the far end of the reflector, and the PEEP/APL valve acts as the APL valve. The order is the same: the bag fills first, then the valve opens."], ["How the vaporizers differ", "Ascending bellows and piston", "The fresh gas set by the flowmeters enters the vaporizer; part of it passes through the vaporizing chamber and picks up anesthetic vapor, the rest bypasses it, and the two rejoin. The dial sets that split and so the concentration: a variable-bypass vaporizer."], ["How the vaporizers differ", "Volume reflector", "The volume reflector machine has neither flowmeters nor a variable-bypass vaporizer. The control unit sets the flow through the gas modules and the amount of anesthetic through an injection vaporizer."], ["When fresh gas is too low, O₂ reaches the patient", "Volume reflector only", "The light gray part is where the reflector gas (O₂) is. When uptake exceeds the fresh gas, the boundary advances one particle per breath, and eventually O₂ (gray squares) passes through the absorber and reaches the alveoli. Tidal volume is maintained, so this is easy to miss; inspired O₂ rises and the anesthetic is diluted. On the ascending bellows the bellows would fail to rise fully, and on the piston machine the air intake valve would open, so both make it noticeable."]],
    "exhausted": [
        "The absorbent is purple all the way through and no longer removes CO₂. Orange particles are returning to the patient through the inspiratory limb (rebreathing). Press Replace for fresh absorbent.",
        "The absorbent is purple all the way through and no longer removes CO₂. In this scene most CO₂ leaves as excess gas, so little returns to the inspiratory side. Press Replace for fresh absorbent."],
    "steps": [
        'Each moving particle in the figure is gas: <b>black</b> is gas without CO₂, <b style="color:#e8590c">orange</b> is gas with CO₂. Watch the particles to see how the gas flows.',
        "Play or pause (or press <kbd>Space</kbd>).",
        "Switch between the two ventilator types.",
        "Switch the scene: <b>manual</b> ventilation by squeezing the bag, or <b>low</b> fresh gas flow.",
        "The inspiration and expiration bar. Press it to stop at that moment and see what is happening (<kbd>←</kbd> <kbd>→</kbd> step 0.1 s).",
        "Click a particle to follow it with a red ring and trail (<kbd>Esc</kbd> to stop).",
        "Click a part name with a dotted underline to zoom in on that part and read about it.",
        "How much of the CO₂ absorbent has been used. Set the speed to 4× or 16× to watch it turn purple.",
        "More detailed explanations, such as how the types differ, are here. To see this guide again, use How to use."],
}
SIM_TEXT = {
    "inAbs": "inside the CO₂ absorber", "A": "inspiratory limb", "B": "trachea (dead space)", "C": "expiratory limb",
    "D": "absorber line", "Ebag": "bag line", "Event": "ventilator line", "F": "absorber line", "G": "decoupling valve line",
    "P": "piston port", "H": "bag line", "R": "volume reflector", "M": "gas module line", "reflGas": "reflector gas (O₂)", "sup": "supply line", "scav": "excess gas", "bag": "in the reservoir bag",
    "bellows": "in the bellows", "lung": "in the alveoli", "cyl": "in the piston cylinder", "trans": "moving",
}


def terms_js():
    """日本語版の TERMS に英語の名前・押せる文字・解説を上書きする JavaScript"""
    over = {k: {"name": n, "words": w, "text": t} for k, (n, w, t) in TERMS.items()}
    return ("for (const [k, v] of Object.entries(" + json.dumps(over, ensure_ascii=False) + ")) Object.assign(TERMS[k], v);\n"
            "for (const [k, v] of Object.entries(" + json.dumps(RECT) + ")) Object.assign(TERMS[k].rect, v);\n")


def l_js():
    d = dict(UI, phases=PHASES)
    return ("const L = Object.assign(" + json.dumps(d, ensure_ascii=False) + ", {\n"
            "  breath: n => `Breath ${n}`, sec: c => c.toFixed(1) + ' s' });\n")


def sim_text_js():
    return ("window.SIM_TEXT = Object.assign(" + json.dumps(SIM_TEXT, ensure_ascii=False) + ", {\n"
            "  fmt: (gas, id, co2, where) => `Particle #${id} supplied as ${gas} (${co2 ? 'with CO₂' : 'no CO₂'}, ${where})` });\n")
