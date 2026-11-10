# 2～3 岁宝宝识字卡词库

本词库面向亲子游戏、看图认物和初步识字，不是必须按进度完成的识字任务。家里常见的物品、孩子喜欢的主题可以优先制作；不常见的条目可以跳过。

## 文件

- `characters.csv`：**156 张完整版**，其中单字 84、词语 72。UTF-8 with BOM，可直接交给排版脚本。
- `starter_24.csv`：**首批 24 张**，适合先试画风、检查文字和印刷效果。
- `characters.json`：与完整版 CSV 同内容，方便 Agent 检索、筛选、规划批次；实际排版仍读 CSV。

## CSV 字段

| 字段 | 说明 |
|---|---|
| `hanzi` | 左侧显示的单字或词语 |
| `pinyin` | 带声调拼音；轻声音节不标调，词语音节之间以空格分隔 |
| `slug` | 唯一的英文文件名：`illustrations/<slug>.png` |
| `mode` | `shape`：物体本来的姿态/轮廓可联想字形；`scene`：直接画可爱、好认的图，不强凑字形 |
| `accent` | 字卡边框、拼音用的主题色 |
| `visual_brief` | 右侧插画的具体画面说明，不是生硬描绘汉字 |
| `kind` | 单字 / 词语 |
| `category` | 主题分组 |
| `stage` | 1：先试；2：常见扩展；3：兴趣延伸；不是孩子能力评级 |
| `batch` | `01`～`13`，每批 12 张，按制作优先级排序 |

## 使用建议

1. 默认先用 `starter_24.csv` 制作 24 张，不要一上来制作全部 156 张。
2. 扩展到完整版时，每批 12 张生图并校验；已完成插画根据 `slug` 复用。
3. 图画里不要重复写汉字。只有适合的少数字才做轮廓联想：如鱼竖着画、山三峰、木树形、田四格。其余以清晰可爱为先。
4. 对比类（上/下、大/小、多/少）可在孩子已经理解对应物品后再制作，用两张卡呼应，不必把文字画进插图。
5. `mode`、`visual_brief` 不是汉字字源考据；尤其不应把现代简化字的轮廓误说成真实的古文字结构。

## 直接调用

```powershell
# 只做首批 24 张时，将此 CSV 复制到当前制作项目里
Copy-Item "$HOME\.agents\skills\hanzi-pictogram-cards\assets\starter_24.csv" ".\hanzi-card-project\characters.csv"
```

后续让 Codex 使用 `$hanzi-pictogram-cards`，按项目 `characters.csv` 中的条目生成右侧插画，再运行原 Skill 的 `render_cards.py` 统一排版。无需改变原脚本。
