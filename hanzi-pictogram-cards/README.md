# 汉字字画联想识字卡 Skill

这是给 Codex 用的本地 Skill。批量生成时**生图由 Codex 的内置 `image_gen` 完成**，本包不调用收费图像 API。

## 安装（Windows / PowerShell 7）

把解压后的整个 `hanzi-pictogram-cards` 目录放进：

`$HOME\.agents\skills\hanzi-pictogram-cards\`

例如将解压目录复制到用户级 Skill 文件夹：

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force ".\hanzi-pictogram-cards" "$HOME\.agents\skills\"
```

在 Codex 中输入 `$hanzi-pictogram-cards` 并交代字表即可。若没有识别新 Skill，重启 Codex。

建议先安装 Pillow：

```powershell
python -m pip install pillow
```

## 可以直接复制给 Codex 的示例指令

> 使用 `$hanzi-pictogram-cards`，先做“鱼、鸟、山、木、火、水、日、月、田、人、雨、门”12 张识字卡。右侧插画优先用物体自然轮廓建立字形联想；鱼必须鱼头朝上、鱼尾朝下，画里不要出现文字。使用内置 image_gen 生图，不要调用付费 API。将结果统一排版，输出逐张 PNG、总览图和 A4 打印拼版。

内置适合 2～3 岁的 156 张词库：`assets/characters.csv`（完整版，84 个单字 + 72 个词语）、`assets/starter_24.csv`（首批 24 张）以及 `assets/characters.json`（同内容 JSON）。默认先试作首批 24 张，完整版按 `batch` 每批 12 张逐批制作。字段 `stage` 表示推荐先后，详细见 `assets/WORD_BANK.md`。

默认词表在 `assets/characters.csv`。修改其中的 `hanzi`、`pinyin`、`slug`、`mode`、`accent`、`visual_brief` 即可添加字或词。`slug` 是独立的英文字母文件名；例如“鱼”是 `yu`，插画必须保存在 `illustrations/yu.png`。

当所有插画就位，也可以手工运行排版脚本：

```powershell
python "$HOME\.agents\skills\hanzi-pictogram-cards\scripts\render_cards.py" `
  --manifest ".\hanzi-card-project\characters.csv" `
  --illustrations ".\hanzi-card-project\illustrations" `
  --output ".\hanzi-card-project\output"
```

如果中文字体无法自动找到，在末尾添加 `--font "C:\Windows\Fonts\msyhbd.ttc"`。

## 输出

- `cards/`：逐张横向 A6 规格 PNG，300 DPI；
- `overview.png`：手机/电脑快速查看的总览；
- `print-sheets/`：每页四张的 A4 横向 PNG，300 DPI。打印时选 A4 横向、100% 比例，注意打印机的边距设置。

生成插画质量仍需肉眼看一遍；这个 Skill 解决的是**设计约束 + 批量流程 + 正确排版**，无法保证每次 AI 绘画都准确。尤其“象形相似”不是汉字字源考证。
