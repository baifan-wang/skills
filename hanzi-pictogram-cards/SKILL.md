---
name: hanzi-pictogram-cards
description: 为宝宝批量制作中文汉字和词语识字卡。调用 Codex 内置 image_gen 绘制字形联想插画，左侧汉字和带声调拼音、右侧可爱图形，支持象形启发、避免生硬把字贴到图上，最后批量输出可打印 PNG 和拼版。适用于中文启蒙识字卡、字画同源卡片、儿童字卡制作。
---

# 汉字字画联想识字卡

目标：让宝宝先看清左侧**标准汉字**，再从右侧**自然的物体轮廓、姿态或动作**建立字形联想。图里不再直接写一遍汉字。象形是设计启发，不能把现代汉字或随意编造的图形说成真实字源。

## 工作流程

1. 获取用户要做的字或词列表。没有给定列表时，**默认选 `assets/starter_24.csv` 首批 24 张**；需要更多字时再使用 `assets/characters.csv` 完整 156 张。将选定 CSV 复制为当前工作目录的 `hanzi-card-project/characters.csv`。词库说明见 `assets/WORD_BANK.md`；`stage` 是内容建议顺序，`batch` 为每批 12 张的制作顺序，二者不影响排版脚本。单字优先，词语也支持；为每行补充准确的**常用读音及带声调拼音**，多音字按此处表达的意思确定读音，不盲信自动注音。每行唯一 `slug` 对应文件名。
2. **先想画面，再生图**。逐字判断 CSV 的 `mode` 和 `visual_brief`：
   - `shape`：可通过物体的**方向、主体轮廓、数量与空间结构**自然联想字形。用几何构图，不把字当贴纸。例如“鱼”要一条**鱼头朝上、鱼尾朝下、身体竖直**的小鱼；“山”三座连续起伏的山峰，中峰较高；“木”树干向上、枝干向左右舒展。
   - `scene`：现代字形和实物不太像，直接画可爱、好认的物体或场景。例如“车”画小汽车，“花”画一朵花；**不强迫藏字**。
   - 即使是 `shape`，只要刻意扭曲后不像物体，就退回自然插画。不能为了字形而牺牲孩子对事物的理解。
3. 每张右侧插画用 Codex **内置 `image_gen`** 单独生成，使用下方统一提示词框架，并将每张选定的最终插画复制到当前项目 `hanzi-card-project/illustrations/<slug>.png`。不要把整张识字卡交给生图模型；插画中禁止出现汉字、拼音、英文字母和水印。若有透明背景能力，优先真实透明背景，保留 PNG alpha。插画应为**一幅主体居中、留有呼吸空间的图**，不要生成多宫格或同一画面中的重复物体。
4. 不得因用户说“批量”就自动改走 API/CLI。内置 `image_gen` 按**每个不同字分别调用一次**，只在用户明确选择 API/CLI 时才采用其他方法。如果本机 Codex 内置生图不可用，明确说明，不要凭空宣称已制作图片，也不要私自切换收费 API。内置图像文件通常位于 `$CODEX_HOME/generated_images/...`，取得实际输出后复制到当前项目目录；不要依赖生图调用参数指定最终路径。
5. 用 `scripts/render_cards.py` 生成统一排版的字卡。Python 环境需要 Pillow。运行：

   ```powershell
   python -m pip install pillow
   python <skill目录>/scripts/render_cards.py --manifest ./hanzi-card-project/characters.csv --illustrations ./hanzi-card-project/illustrations --output ./hanzi-card-project/output
   ```

   如果找不到合适的汉字字体，在命令末尾补 `--font "C:\Windows\Fonts\msyhbd.ttc"`（或用户自己的中文字体路径）。
6. 输出逐张高清 PNG、`overview.png` 总览图、`print-sheets/` A4 横向四张拼版 PNG。检查每张文字/声调、插画主体、图片与字形的自然关联和版面一致性。只针对问题卡片重新生成，其他已完成卡片直接复用。

## 插画提示词模板

根据每行 `visual_brief` 改写主体段落；不要用完全相同的笼统提示词生成不同汉字的图。

```text
Create ONE adorable, instantly recognizable visual illustration for a Chinese preschool literacy flashcard. Subject: {visual_brief}.
Composition: {mode-specific orientation / silhouette / posture}. Use the real, natural object shape to evoke the Chinese character's structure where genuinely possible. DO NOT draw, paste, trace, emboss, hide, spell, or overlay any Chinese character or other symbol inside the illustration. Do not distort anatomy or objects to imitate a glyph. If the resemblance is weak, prefer a charming accurate illustration.
Style: premium children's picture-book illustration, gentle watercolor texture with clean rounded silhouettes, warm happy personality, harmonious pastel-but-vivid colors, simple coherent lighting, visually appealing to 2–5-year-olds, one dominant subject, a few meaningful details only. Consistent style across the whole series.
Layout: isolated central illustration for the RIGHT PANEL of a landscape flashcard, ample clear margins all around, occupy approximately 75-85% of canvas, no outer border, no card frame, no typography, no captions, no pinyin, no letters, no logos, no watermark. Transparent background (real alpha) preferred.
```

如有用户选定的前一张卡或插画，可作为**画风参考**（非修改目标）；保持系列风格一致，但物体构图按各字单独设计。批量工作先做 3–4 张视觉样稿检查设计，再连续完成余下项目；156 张完整版按 `batch` 每 12 张分批执行，优先复用已存在的插画。用户明确要求直接做全套时不要逐张征求确认。

## 排版约定

- 固定横向 A6 比例（1748×1240 px，300 DPI），左约 42% 为文字，右约 58% 为插画；圆角奶油白底，细彩色边框。
- 左侧大号黑色简体字，下方是清晰带调拼音（例如 `yú`，不是 `yu2`），文字由 Pillow 生成，避免 AI 误画、错拼音或字体风格飘移。
- 右侧**不重复印字**。`shape` 模式的对应依赖自然轮廓，不是把字描在鱼肚子、树干、太阳、花瓣上。
- 保持一张卡仅一个核心对象；图形对宝宝来说要先“像真的鱼/鸟/山”，再谈“像字”。
- 对词语，左侧显示完整词与拼音（拼音音节之间用空格），右侧可画一个好认的场景；不要硬把每个字分别变成图案。

## 交付与质量检查

- 默认文件：`illustrations/*.png` 原始插画、`output/cards/*.png` 成品卡、`output/overview.png`、`output/print-sheets/*.png`。
- 可分批执行；已有插画不重复生成。重新做某一字时只替换该字的图片（明确用户允许覆盖后才覆盖），然后重新排版。
- 查看拼版图，优先检查是否有生硬贴字、鱼方向错误、对象主体过小/裁切、字音错误、图像风格不一。没有问题就不制造问题。
- 告诉用户哪些字卡成功生成、哪些没有生成，以及文件路径。内置生图不可用时，可先做好词表/脚本，但不要把排版测试图冒充最终插画。
