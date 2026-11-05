# SPDX-License-Identifier: MIT
# CircleFlow © 2026 Masaaki Asamoto（朝元雅明）
"""操作ページの HTML（図の前と後）。BODY_TOP の @@LANGNOTE@@・@@LANG@@ は build_page.py が埋める"""

BODY_TOP = r"""
<body><div class="wrap">
@@LANGNOTE@@<header class="top chrome">
  <h1>CircleFlow<span>麻酔器と呼吸回路のガスの流れ</span></h1>
  @@LANG@@
  <button id="helpBtn" aria-label="使い方"><span class="q">?</span>使い方</button>
  <button id="hlBtn">見どころ</button>
  <button id="moreBtn">くわしく</button>
  <button class="fsBtn" id="fsBtnTop" aria-pressed="false">全画面</button>
</header>
<div class="bar chrome">
  <div class="cyc" id="cycRow"><button id="typeCycle"><small>方式</small><b></b></button><button id="ventCycle"><small>換気</small><b></b></button><button id="flowCycle"><small>新鮮ガス</small><b></b></button></div>
  <div class="seg big" role="tablist" id="typeSeg">
    <button class="on" data-type="bellows" role="tab"><span class="full">ベローズ式（上昇式）</span><span class="short">ベローズ式</span></button><button data-type="piston" role="tab">ピストン式</button><button data-type="reflector" role="tab"><span class="full">ボリュームリフレクタ式</span><span class="short">リフレクタ式</span></button>
  </div>
  <div class="grp" id="ventGrp"><span class="lab">換気</span><div class="seg">
    <button data-vent="auto" class="on">人工呼吸</button><button data-vent="man">用手換気</button></div></div>
  <div class="grp" id="flowGrp"><span class="lab">新鮮ガス</span><div class="seg">
    <button data-flow="high" class="on">多め</button><button data-flow="low">低流量</button><button data-flow="short" hidden>不足</button></div></div>
</div>
<div class="rng chrome" id="rngRow"><div class="seg" id="rangeSeg"><button data-range="all">全体</button><button data-range="supply">ガス供給</button><button data-range="circuit">呼吸回路</button></div><button class="fsBtn" id="fsBtnRow" aria-pressed="false">全画面</button></div>
<div class="hint chrome" id="rotHint" hidden><span>横向きにすると図が大きく見えます。図は 2 本指で拡大、指でずらせます。</span><button id="rotHintX" aria-label="案内を閉じる">✕</button></div>
<div class="stage" id="stage">
"""

BODY_MID = r"""
  <div class="chip chrome" id="chip" hidden><b>追跡中</b><span id="chipMsg"></span><button id="chipX" aria-label="追跡をやめる">✕</button></div>
  <div class="card chrome" id="card" role="dialog" aria-live="polite">
    <button class="x" id="cardX" aria-label="閉じる">✕</button>
    <h3 id="cardTtl"></h3><p id="cardTxt"></p>
    <nav id="cardNav"><button id="cardPrev">‹ 前へ</button><button id="cardNext">次へ ›</button></nav>
  </div>
</div>
<div class="under chrome">
  <button id="play" aria-label="一時停止"></button>
  <div class="tl"><div class="tl-bar" id="tlBar" role="slider" aria-label="時刻" aria-valuemin="0" aria-valuemax="6"></div><output id="tout">0.0 秒</output></div>
  <button id="speedCycle" aria-label="速さ" title="速さ">1×</button>
  <div class="grp" id="speedGrp"><span class="lab">速さ</span><div class="seg">
    <button data-speed="0.25">¼</button><button data-speed="0.5">½</button><button data-speed="1" class="on">1×</button><button data-speed="4">4×</button><button data-speed="16">16×</button></div></div>
  <div class="abs" id="absbox">
    <button class="lk" data-term="absorber">吸収剤</button>
    <button class="meter" id="absMeter" aria-label="吸収剤の使用率"><i id="absBar"></i><output id="absPct">0%</output></button>
    <span class="el" id="absEl">1 呼吸目</span>
    <button id="absSwap">交換</button>
  </div>
</div>
<footer class="foot chrome">
  CircleFlow © 2026 朝元雅明（Masaaki Asamoto）。プログラムは <a href="https://opensource.org/license/mit" rel="license">MIT</a>、図と文章は <a href="https://creativecommons.org/licenses/by/4.0/deed.ja" rel="license">CC BY 4.0</a>。ソースコード：<a href="https://github.com/anesthesia-sims/circleflow">GitHub（anesthesia-sims/circleflow）</a>。版 @@VERSION@@<br>
  教育用の模式図で、臨床の判断や機器の操作に用いるものではありません。特定のメーカーとは関係ありません。<br>
  謝辞：帝京大学医学部附属溝口病院 麻酔科の平林剛先生から、呼吸回路と人工呼吸器の方式について助言をいただきました。内容の誤りは著者の責任です。<br>
  もし間違いに気づかれましたら、<a href="https://github.com/anesthesia-sims/circleflow/issues/new">GitHub の Issue</a> へ投稿していただくか、メール（<a href="mailto:masaaki.asamoto@gmail.com?subject=CircleFlow">masaaki.asamoto@gmail.com</a>）でご連絡をお願いします。
</footer>
</div>
<div class="modal chrome" id="more" role="dialog" aria-label="くわしい解説"><div class="sheet">
  <button class="x" id="moreX" aria-label="閉じる">✕</button>
  <h2>人工呼吸器の分類</h2>
  <p>麻酔器の人工呼吸器は、患者のガスをためる場所と、それを押す力で分けられます。<b>ベローズ式</b>は、硬い箱の中のベローズにためたガスを駆動ガス（O₂ か空気）で押す方式で、駆動ガスの通り道が患者のガスの回路と別にある双回路です。呼気のときにベローズが上がる上昇式と下がる下降式があり、下降式は回路が外れてもベローズが動き続けて気づきにくいため、現在の機種はほぼ上昇式です。<b>ピストン式</b>は、シリンダーの中のピストンをモーターで動かす方式で、駆動ガスの回路がない単回路です。ためる場所は呼吸バッグになります。<b>ブロワ（タービン）式</b>は、回路の中に置いた小さなファンを高速で回して流れと圧を作る単回路の方式で、ためる場所はピストン式と同じく呼吸バッグです。ためたガスを押し出す部品がなく、ピストンのように吸い込み直す動きもいりません（Dräger Perseus・Atlan など）。<b>ボリュームリフレクタ式</b>は、長い管（リフレクタ）にためたガスをリフレクタガス（O₂）の流れで押し出す方式で、動く部品がありません。この図では、ベローズ式（上昇式）・ピストン式・ボリュームリフレクタ式の 3 つを扱います。</p>
  <h2>方式の違い</h2>
  <table>
    <tr><th></th><th>ベローズ式（上昇式）</th><th>ピストン式</th><th>ボリュームリフレクタ式</th></tr>
    <tr><td>新鮮ガスの作り方</td><td>流量計とニードル弁、可変バイパス式の気化器</td><td>流量計とニードル弁、可変バイパス式の気化器</td><td>ガスごとの電子制御のガスモジュールと、注入式の気化器</td></tr>
    <tr><td>人工呼吸器を動かす力</td><td>駆動ガス（O₂）がハウジング内でベローズを押し下げる</td><td>モーターがロッドでピストンを押し引きする（駆動ガスを使わない）</td><td>リフレクタガス（O₂）が、リフレクタの中のガスを膜なしで直接押す</td></tr>
    <tr><td>次の吸気ガスのため方</td><td>呼気と新鮮ガスがベローズを下から押し上げてためる</td><td>ピストンが下がって、呼吸バッグのガスと新鮮ガスを吸い込む</td><td>呼気と新鮮ガス（吸収装置を逆に通る）がリフレクタの患者側に入り、奥のガスを押し出してためる</td></tr>
    <tr><td>吸気中の新鮮ガス</td><td>吸気に加わって患者へ</td><td>新鮮ガス・デカップリング弁が閉じ、呼吸バッグへ向かう</td><td>吸気に加わって患者へ（そのぶんリフレクタガスで押し出す量が減る）。ガスモジュールが新鮮ガスを主に吸気中に流す（この図では 1 呼吸の 2/3 を吸気中、1/3 を呼気中に）</td></tr>
    <tr><td>人工呼吸中の呼吸バッグ</td><td>切替弁で回路から外れ、動かない</td><td>リザーバーとして回路に残り、ふくらみ・しぼむ</td><td>切替弁で回路から外れ、動かない（用手換気では切替弁が開いてリフレクタの奥につながり、リフレクタガスは止まる）</td></tr>
    <tr><td>回路の陰圧</td><td>人工呼吸器にガスを吸い込む動きがないので、起こりにくい</td><td>吸い込む動きがあるため、PEEP/Pmax 弁と外気取り込み弁で防ぐ</td><td>押す動きだけで、ガスを吸い込む動きはない</td></tr>
    <tr><td>余ったガスの出口</td><td>ベローズが上がりきると、余剰ガス弁から排出装置へ</td><td>呼吸バッグがいっぱいになって圧が上がると、APL バイパス弁から排気逆止弁を通って排出装置へ（用手換気では APL 弁から）</td><td>リフレクタの奥から、PEEP/APL 弁を通って排出装置へ（出ていくのは O₂ と最も古いガス）</td></tr>
    <tr><td>新鮮ガスを減らしたときの 1 回換気量</td><td>ベローズが押し出す量が同じなら、吸気中に加わる新鮮ガスのぶん減る（現代の機種は補正する。この図でもベローズが押し出す量を増やして同じにしている）</td><td>変わらない（デカップリング弁があり、患者へ送るのはピストンが押し出す量だけ）</td><td>変わらない（リフレクタガスで押し出す量を増やす）</td></tr>
    <tr><td>呼気終末の回路内圧</td><td>余剰ガス弁の開放圧（2〜3 cmH₂O）が残る</td><td>PEEP/Pmax 弁の設定値まで下がる（設定 0 なら 0 付近）</td><td>PEEP/APL 弁で設定した PEEP</td></tr>
  </table>
  <h2>設計の考え方</h2>
  <p>ベローズ式（上昇式）は、ベローズが上がりきらないとそのぶん次の吸気が減る代わりに、ガスを能動的に吸い込む機構がないので人工呼吸器の側から患者の気道を陰圧にすることがなく、離断や大きなリークではベローズが上がらなくなって異常に気づきやすい、安全を優先した設計です。ピストン式は、ガスを吸い込む動きによって陰圧が生じうる構造を、新鮮ガス・デカップリングや弁などの制御で補い、正確な換気量や多様な換気モードを実現しています。ボリュームリフレクタ式は、ピストンの代わりに O₂ の流れでガスを押し、長い管の中で押すガスと患者のガスをほとんど混ざらないまま隣り合わせる設計です。吸い込む動きがないので陰圧は起こりにくく、動く部品もありません。</p>
  <h2>用手換気</h2>
  <p>人工呼吸器を使わず、呼吸バッグを手で押して換気します。ベローズ式（上昇式）では切替弁を「用手」に倒し、栓の L 字の穴が呼気側の合流点と APL 弁・呼吸バッグの側をつなぎます（ベローズは回路から外れて止まります）。ピストン式では切替弁はなく、ピストンが止まり、もともと回路にある呼吸バッグを押します。どちらも吸気では、押されたバッグのガスが吸収装置を通って CO₂ を除かれ、新鮮ガスと合わさって吸気弁から患者へ送られます（ピストン式では新鮮ガス・デカップリング弁を通ります）。呼気では、呼気と新鮮ガスがバッグへ戻ってふくらませ、いっぱいになって回路の圧が APL 弁の設定を超えると、余ったガスは APL 弁から余剰ガス排出装置へ出ていきます。ボリュームリフレクタ式では、切替弁が開いて呼吸バッグがリフレクタの奥の端につながり、リフレクタガスは止まります。手で押したバッグのガスはリフレクタと吸収装置を通って患者へ送られ、呼気はリフレクタを通ってバッグへ戻ります。いっぱいになって圧が設定を超えると、余ったガスは PEEP/APL 弁（APL 弁として働きます）から余剰ガス排出装置へ出ていきます。</p>
  <h2>新鮮ガスが足りないとき（ボリュームリフレクタ式）</h2>
  <p>場面「不足」では、患者の取り込み（肺胞で血液へ取り込まれて消える粒。1 呼吸に 4 粒）が新鮮ガス（1 呼吸に 3 粒）より多くなっています。回路のガスは呼吸ごとに 1 粒ずつ減り、そのぶんリフレクタガス（O₂）が奥に残って境目が患者側へ進み、数呼吸のうちに O₂ が吸収装置を通って吸気に加わり、肺胞まで届きます。実機でも、新鮮ガスが取り込みとリークの合計より少ないと、不足分をリフレクタガスの O₂ が補います。換気量は保たれますが、吸気の O₂ は設定より高くなり、麻酔薬は薄まります。ほかの場面では、見やすさのために取り込みを 0 としています。</p>
  <h2>二酸化炭素吸収剤の色の変化</h2>
  <p>呼気は吸収装置の下から入るため、吸収剤は入口側（下）から使われ、紫の帯が出口側（上）へ進みます。実際には数時間以上かけて進む変化を、数分から十数分に縮めて表示しています。</p>
  <p>「新鮮ガス：多め」は、新鮮ガス流量が分時換気量に近い場合です。ベローズ式（上昇式）では、呼気の CO₂ は吸収装置に届く前に余剰ガスとして排出されるため、この図では吸収剤はほとんど減りません。ピストン式では、呼気がいったん呼吸バッグにたまり、ピストンが吸収装置を通して吸い込むため、約 35 呼吸で使い切り、使い切ると吸気側に CO₂ がわずかに戻ります。</p>
  <p>「新鮮ガス：低流量」は、新鮮ガスをその 4 分の 1 に減らした場合です。呼気のほとんどが吸収装置を通って再び吸われるため、消費が速くなります（約 20〜25 呼吸）。使い切るとオレンジの粒が吸気側の管を通って患者へ戻り、吸気の CO₂ が上がります（カプノグラムの基線が 0 に戻らなくなる）。</p>
  <p>ボリュームリフレクタ式では、呼気と新鮮ガスはリフレクタへ入り、次の吸気で後から入った順に押し出されます。多めの場面では、押し出されるのは呼気のあとに入った新鮮ガスで、呼気の CO₂ はリフレクタの奥から PEEP/APL 弁を通って出ていくため、吸収剤の色は変わりません。低流量では押し出す量が増え、約 23 呼吸で使い切ります。</p>
  <p>方式ごとの呼吸数の違いは、実際の機種どうしの比較ではありません。指示薬の色は、使用後にしばらく置くと白に戻ることがあります。交換の判断は色だけでなく、吸気の CO₂ も合わせて行います。</p>
  <p class="small">本図は模式図です。部品の形・位置・弁の構成は機種によって異なります（ピストン式は Dräger Fabius 型、ボリュームリフレクタ式は Getinge（Maquet）Flow-i 型の構成を参考にしています）。1 呼吸は 6 秒（吸気 2 秒・呼気 4 秒）で表示しています。ガスの量や時間、吸収剤の容量は見やすさのために整えた値です。</p>
</div></div>
<div class="tour chrome" id="tour" aria-live="polite">
  <svg id="tourSvg"><path id="tourDim" fill="rgba(0,0,0,0.55)" fill-rule="evenodd"/></svg>
  <div class="hand" id="hand"><svg viewBox="-3 -3 42 52" width="44" height="53" aria-hidden="true">
    <g stroke="#1a1a1a" stroke-width="4.4" stroke-linejoin="round">
      <rect x="8" y="0" width="9" height="26" rx="4.5"/><rect x="15.5" y="14" width="8" height="14" rx="4"/>
      <rect x="22.5" y="16" width="8" height="13" rx="4"/><rect x="29" y="19" width="7" height="12" rx="3.5"/>
      <rect x="6" y="20" width="30" height="20" rx="8"/><rect x="0" y="23" width="9" height="15" rx="4.5" transform="rotate(-28 4.5 30)"/>
      <rect x="10" y="38" width="22" height="9" rx="2"/></g>
    <g fill="#fff">
      <rect x="8" y="0" width="9" height="26" rx="4.5"/><rect x="15.5" y="14" width="8" height="14" rx="4"/>
      <rect x="22.5" y="16" width="8" height="13" rx="4"/><rect x="29" y="19" width="7" height="12" rx="3.5"/>
      <rect x="6" y="20" width="30" height="20" rx="8"/><rect x="0" y="23" width="9" height="15" rx="4.5" transform="rotate(-28 4.5 30)"/></g>
    <rect x="10" y="38" width="22" height="9" rx="2" fill="#c8c8c8"/>
    <path d="M19.5 20 v6 M26.5 22 v5" stroke="#1a1a1a" stroke-width="1.6" stroke-linecap="round"/></svg></div>
  <div class="bubble" id="bubble"><div id="bubbleTxt"></div><div class="dots" id="bubbleDots"></div>
    <div class="bb"><button id="tourSkip">閉じる</button><button id="tourPrev">戻る</button><button id="tourNext" class="pri">次へ</button></div>
    <div class="keys"><kbd>Esc</kbd> 閉じる　<kbd>←</kbd> <kbd>BS</kbd> 戻る　<kbd>→</kbd> <kbd>Enter</kbd> 進む</div></div>
</div>
"""
