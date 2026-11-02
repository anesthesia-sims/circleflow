<a id="japanese"></a>

# CircleFlow：麻酔器と呼吸回路のガスの流れ

**日本語** ｜ [English](#english)

麻酔器の中を流れるガスを、1 粒ずつ動く粒で見せる教育用のシミュレーターです。ガス供給機構・気化器から、循環式の呼吸回路（circle system）、人工呼吸器、患者の死腔・肺胞、二酸化炭素吸収装置、余剰ガス排出装置まで、1 呼吸（6 秒）のあいだのガスの動きを 1 つのページで追えます。臨床工学技士・医学生・研修医などの学習用に作りました。

**ページを開く**：https://anesthesia-sims.github.io/circleflow/ ／ English: https://anesthesia-sims.github.io/circleflow/en/

![上昇式ベローズの吸気中](docs/screenshot-bellows.png)

## できること

- **2 つの方式を比べる**：上昇式ベローズ（駆動ガスがベローズを押し下げる）とピストン式（モーターがピストンを動かす。新鮮ガス・デカップリング弁つき）を、タブで切り替えて比べられます。
- **CO₂ を含むガスを色で見る**：黒い粒は CO₂ を含まないガス、オレンジの粒は CO₂ を含むガス（呼気）です。肺胞で CO₂ を受け取り、二酸化炭素吸収装置を通ると CO₂ が除かれます。
- **粒を追跡する**：粒をクリックすると、その粒の通った道を赤い足跡で表示します。
- **吸収剤の消費を見る**：CO₂ を吸収した吸収剤は、指示薬の色が白から紫へ変わっていきます（時間を縮めて表示。4 倍・16 倍で早送りできます）。使い切ると CO₂ が吸気側へ戻ります。「交換」で新しい吸収剤に戻せます。
- **場面を切り替える**：新鮮ガス（多め／低流量）と換気（人工呼吸／用手換気）を切り替えられます。方式と合わせて 8 つの場面があります。用手換気では、呼吸バッグを手で押して換気し、余ったガスは APL 弁から排出されます。

![用手換気（上昇式ベローズ）：左は吸気でバッグを手で押す、右は呼気でバッグがふくらみ APL 弁が開く](docs/screenshot-manual.png)

![ピストン式の呼気②：ピストンが下がり、呼吸バッグのガスと新鮮ガスを吸い込む](docs/screenshot-piston.png)

## 使い方

`index.html` をブラウザで開くだけで動きます（インターネット接続も、ほかのファイルも要りません）。英語版は `en/index.html` で、見出しの横のリンクで行き来できます。

初めて学ぶ人向けに、画面には図と操作だけを置き、説明は必要なときに重ねて出します。

- **使い方**：「使い方」ボタン（または <kbd>?</kbd> キー）で、画面の上を指が動いて操作を順に見せます。初めて開いたときは自動で出ます
- **部品の名前をクリック**：点線の下線がある名前をクリックすると、その部品を拡大して、はたらきを短く説明します。「前へ・次へ」でガスの流れの順に部品をたどれます
- **時刻のバー**：吸気・呼気のバーを押すとその時刻で止まり、いま起きていることを説明します
- **くわしく**：2 つの方式の比較や、吸収剤の消費のくわしい説明
- スペースキー：再生／一時停止
- ← →：0.1 秒ずつ送る
- Esc：説明を閉じる／粒の追跡をやめる
- `index.html?term=inspValve` のように開くと、その部品の説明を開いた状態になります（教科書やスライドから部品へ直接つなぐ用。名前は `src/make_sim_page.py` の `TERMS`）
- `index.html?type=pistonMan&t=1.5` のように開くと、その場面・時刻で止めた 1 コマになります（動画や図のコマ撮り用）。場面の名前は `bellows`・`bellowsLow`・`bellowsMan`・`bellowsLowMan`・`piston`・`pistonLow`・`pistonMan`・`pistonLowMan` です。

## 作り直し方

図（SVG）と粒の経路データは Python のスクリプトが作り、粒の動きはブラウザの中で JavaScript が計算します。

```sh
./build.sh    # build/ に 8 つの場面の図と経路データを日本語・英語で作り、index.html と en/index.html にまとめる（Python 3、標準ライブラリだけ）
./check.sh    # 8 つの場面の粒の動きを点検する（Node.js）
```

`check.sh` は場面ごとに、粒が管の外にはみ出していないこと、巻き戻しても同じ状態になること、1 回換気量（1 呼吸で肺胞へ入る粒の数）、吸収剤を使い切るまでの呼吸の数を表示します。

| ファイル | 役割 |
|---|---|
| `src/make_anim_bellows3.py` | 上昇式ベローズの図と経路データを作る（`low`：低流量、`manual`：用手換気） |
| `src/make_anim_piston2.py` | ピストン式の図と経路データを作る（同上） |
| `src/sim_bellows.js`・`src/sim_piston.js` | 粒の動きのシミュレーション（ブラウザで動く） |
| `src/make_sim_page.py` | 8 つの場面を 1 つのページ（`index.html`）にまとめる（`--lang en` で英語版） |
| `src/labels_en.py` | 図の中の文字の英語版（日本語との対応表と、文字の大きさ・位置の調整） |
| `src/page_en.py` | ページの英語版の文（画面・部品の解説・場面の説明・使い方） |
| `src/make_text_list.py` | ページに出る解説文をすべて取り出し、確認用の一覧（Markdown）を作る |
| `tests/check.js` | 1 つの場面の粒の動きの点検 |

## 開発（このリポジトリが正本）

CircleFlow の生成スクリプト・シミュレーション・ページの正本は、このリポジトリです（2026-11-02 から）。直すときは次の順に進めます。

1. `src/` を直す（図の文字の英語は `src/labels_en.py`、ページの英語の文は `src/page_en.py`）
2. `./build.sh` で日本語版・英語版を作り直し、`./check.sh` で 8 つの場面を点検する（英語版に訳し残しの日本語があると `build.sh` が止まります）
3. 画面で確かめてから、`index.html`・`en/index.html` と `src/` をいっしょにコミットして送信する。`main` に送ると GitHub Pages の公開ページが更新されます

解説文を直したときは、`python3 src/make_text_list.py index.html 一覧.md` で、画面に出る文を確認用の一覧（Markdown）にできます。

## 模式図としての注意

- 教育用の模式図です。臨床の判断や、実際の麻酔器の操作・点検に用いるものではありません。内容について保証はありません。
- 部品の形・位置・弁の構成は機種によって異なります。ピストン式は Dräger Fabius 型の構成を参考にしていますが、特定のメーカーや機種とは関係ありません。
- ガスの量（粒の数）や時間、吸収剤の容量は、見やすさのために縮めたり整えたりした値です。実際の機種どうしの性能の比較ではありません。
- 配管とボンベの識別色は日本の規格に従っています（配管：O₂ 緑・空気 黄・N₂O 青、ボンベ：O₂ 黒・そのほか灰）。

## ライセンス

- **プログラム**（`src/`・`tests/`・`build.sh`・`check.sh`、`index.html` の中の HTML・CSS・JavaScript）：[MIT ライセンス](LICENSE)
- **図と文章**（スクリプトが描く図そのもの、`docs/` の画像、ページと README の説明文）：[クリエイティブ・コモンズ 表示 4.0 国際（CC BY 4.0）](LICENSE-CONTENT)

図や文章を使うときは、次のように出典を示してください。

> 朝元雅明（Masaaki Asamoto）「CircleFlow：麻酔器と呼吸回路のガスの流れ」CC BY 4.0

## 著作者

朝元雅明（Masaaki Asamoto）、麻酔科医

## 謝辞

帝京大学医学部附属溝口病院 麻酔科の平林剛先生から、呼吸回路と人工呼吸器の方式について助言をいただきました。内容の誤りは著者の責任です。

---

<a id="english"></a>

# CircleFlow: Gas Flow in the Anesthesia Machine and Breathing Circuit

[日本語](#japanese) ｜ **English**

An educational simulator that shows the gas inside an anesthesia machine as individual moving particles. From the gas supply and vaporizers, through the circle breathing system, the ventilator, the patient's dead space and alveoli, the CO₂ absorber and the scavenging system, you can follow how gas moves during one breath (6 s) on a single page. It was made for clinical engineers, medical students and residents.

**Open the simulator**: https://anesthesia-sims.github.io/circleflow/en/ (English) ／ https://anesthesia-sims.github.io/circleflow/ (Japanese)

![English version: ascending bellows during inspiration](docs/screenshot-en.png)

## What you can do

- **Compare two ventilator types**: the ascending bellows (drive gas pushes the bellows down) and the piston type (a motor drives the piston; with a fresh gas decoupling valve). Switch between them with the tabs.
- **See CO₂ by color**: black particles are gas without CO₂, orange particles are gas with CO₂ (exhaled gas). Particles pick up CO₂ in the alveoli and lose it in the CO₂ absorber.
- **Follow a particle**: click a particle to show its path as a red trail.
- **Watch the absorbent being used up**: as the absorbent takes up CO₂, its indicator changes from white to purple (time is compressed; speed up to 4× or 16×). Once it is exhausted, CO₂ returns to the inspiratory side. Press Replace for fresh absorbent.
- **Switch scenes**: fresh gas (High / Low flow) and ventilation (Ventilator / Manual). Together with the two types, there are 8 scenes. In manual ventilation you squeeze the reservoir bag, and excess gas leaves through the APL valve.

## How to use

Just open `en/index.html` (English) or `index.html` (Japanese) in a browser; no internet connection or other files are needed. A link next to the title switches languages. When the Japanese page is opened in a browser whose language is not Japanese, it shows a one-line notice pointing to the English version (it does not redirect).

For beginners, the screen shows only the figure and the controls; explanations appear on top only when you ask for them.

- **How to use**: the How to use button (or the <kbd>?</kbd> key) starts a tour in which a finger moves over the screen and shows each control. It starts automatically the first time.
- **Click a part name**: names with a dotted underline zoom in on that part and explain what it does. Prev / Next follow the parts in the order the gas flows.
- **Time bar**: press the inspiration / expiration bar to stop at that moment and see what is happening.
- **Learn more**: how the two types differ, and details of absorbent use.
- Space: play / pause; ← →: step 0.1 s; Esc: close an explanation or stop following a particle.
- Open `en/index.html?term=inspValve` to start with that part's explanation open (for linking from textbooks or slides; the names are the keys of `TERMS` in `src/make_sim_page.py`).
- Open `en/index.html?type=pistonMan&t=1.5` to get a still frame of that scene at that time (for video or figure capture). Scene names: `bellows`, `bellowsLow`, `bellowsMan`, `bellowsLowMan`, `piston`, `pistonLow`, `pistonMan`, `pistonLowMan`.

## Building

Python scripts draw the figures (SVG) and the particle paths; JavaScript computes the particle motion in the browser.

```sh
./build.sh    # builds the 8 scenes in Japanese and English and writes index.html and en/index.html (Python 3, standard library only)
./check.sh    # checks the particle motion in all 8 scenes (Node.js)
```

For each scene, `check.sh` reports that no particle leaves its tube, that rewinding reproduces the same state, the tidal volume (particles entering the alveoli per breath), and the breath at which the absorbent is used up.

| File | Purpose |
|---|---|
| `src/make_anim_bellows3.py` | Draws the ascending-bellows figure and particle paths (`low`: low flow, `manual`: manual ventilation, `en`: English labels) |
| `src/make_anim_piston2.py` | Same for the piston type |
| `src/sim_bellows.js`, `src/sim_piston.js` | Particle simulation (runs in the browser) |
| `src/make_sim_page.py` | Combines the 8 scenes into one page (`--lang en` for English) |
| `src/labels_en.py` | English labels for the figures (mapping from Japanese, with per-label size and position) |
| `src/page_en.py` | English page text (controls, part explanations, scene narration, tour) |
| `src/make_text_list.py` | Extracts all explanation text from a page into a review list (Markdown) |
| `tests/check.js` | Particle check for one scene |

## Development (this repository is the source of truth)

This repository is the canonical source of the scripts, simulation and pages (since 2026-11-02). To make a change:

1. Edit `src/` (English figure labels in `src/labels_en.py`, English page text in `src/page_en.py`).
2. Run `./build.sh` to rebuild both languages and `./check.sh` to check the 8 scenes (`build.sh` stops if any Japanese text is left untranslated in the English page).
3. Check the result in a browser, then commit `index.html`, `en/index.html` and `src/` together and push. Pushing to `main` updates the GitHub Pages site.

## Notes on the schematic

- This is an educational schematic. It is not for clinical decisions or for operating or checking real anesthesia machines, and comes with no warranty.
- The shape and position of parts and the valve arrangement vary between machines. The piston type is modeled on the Dräger Fabius layout but is not affiliated with any manufacturer or model.
- Gas volumes (number of particles), timing and absorbent capacity are scaled or adjusted for clarity; they do not compare the performance of real machines.
- Gas color codes follow Japanese standards (pipelines: O₂ green, air yellow, N₂O blue; cylinders: O₂ black, others gray).

## License

- **Code** (`src/`, `tests/`, `build.sh`, `check.sh`, and the HTML, CSS and JavaScript in the pages): [MIT License](LICENSE)
- **Figures and text** (the figures drawn by the scripts, the images in `docs/`, and the explanatory text of the pages and this README): [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-CONTENT)

When you use the figures or text, please credit them as:

> Masaaki Asamoto, "CircleFlow: Gas Flow in the Anesthesia Machine and Breathing Circuit", CC BY 4.0

## Author

Masaaki Asamoto (朝元雅明), anesthesiologist

## Acknowledgments

We thank Dr. Go Hirabayashi (Department of Anesthesiology, Teikyo University School of Medicine Hospital Mizonokuchi) for advice on the breathing circuit and ventilator types. Any errors are the author's own.
