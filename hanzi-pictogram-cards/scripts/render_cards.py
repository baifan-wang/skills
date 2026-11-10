"""Compose AI-generated flashcard illustrations with deterministic Chinese typography.

Requires: Pillow. Does not call any image generation API.
"""

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

WIDTH, HEIGHT = 1748, 1240  # A6 landscape at ~300 DPI
DPI = (300, 300)
BG = "#FFFCF6"
INK = "#27231E"


def find_font(explicit):
    if explicit:
        return str(Path(explicit)), 0
    candidates = [
        ("C:/Windows/Fonts/msyhbd.ttc", 0),
        ("C:/Windows/Fonts/msyh.ttc", 0),
        ("C:/Windows/Fonts/simhei.ttf", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 2),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 2),
        ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
    ]
    for path, index in candidates:
        if Path(path).exists():
            return path, index
    raise SystemExit("找不到中文字体，请通过 --font 指定微软雅黑或思源黑体等字体文件。")


def fit_font(font_path, index, label, target, max_size):
    for size in range(max_size, 39, -4):
        font = ImageFont.truetype(font_path, size, index=index)
        if font.getlength(label) <= target:
            return font
    return ImageFont.truetype(font_path, 40, index=index)


def render_card(row, art_path, font_path, font_index):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    accent = row["accent"].strip()
    draw.rounded_rectangle((17, 17, WIDTH - 18, HEIGHT - 18), radius=76, fill=BG, outline=accent, width=12)

    # Image area is deliberately larger than the text area; no glyph is drawn here.
    with Image.open(art_path) as src:
        art = src.convert("RGBA")
    alpha_bbox = art.getchannel("A").getbbox()
    if alpha_bbox:
        art = art.crop(alpha_bbox)
    area = (720, 105, 1675, 1132)
    resized = ImageOps.contain(art, (area[2] - area[0], area[3] - area[1]), Image.Resampling.LANCZOS)
    xy = (area[0] + (area[2] - area[0] - resized.width) // 2,
          area[1] + (area[3] - area[1] - resized.height) // 2)
    layer.alpha_composite(resized, xy)

    text_draw = ImageDraw.Draw(layer)
    hanzi = row["hanzi"].strip()
    pinyin = row["pinyin"].strip()
    hanzi_font = fit_font(font_path, font_index, hanzi, 625, 390 if len(hanzi) == 1 else 290)
    pinyin_font = fit_font(font_path, font_index, pinyin, 640, 125)
    center_x = 366
    text_draw.text((center_x, 500), hanzi, anchor="mm", font=hanzi_font, fill=INK)
    text_draw.text((center_x, 853), pinyin, anchor="mm", font=pinyin_font, fill=accent)
    canvas.paste(layer, (0, 0), layer)
    return canvas


def make_overview(cards, output):
    cols = 3
    thumb_w, thumb_h, pad = 540, 383, 24
    rows = (len(cards) + cols - 1) // cols
    board = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad,
                               rows * thumb_h + (rows + 1) * pad), "#F7F6F2")
    for i, path in enumerate(cards):
        with Image.open(path) as img:
            thumb = ImageOps.contain(img.convert("RGB"), (thumb_w, thumb_h))
        x = pad + (i % cols) * (thumb_w + pad)
        y = pad + (i // cols) * (thumb_h + pad)
        board.paste(thumb, (x, y))
    board.save(output)


def make_print_sheets(cards, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    # A4 landscape at 300 DPI, four cards, modest whitespace for home printing.
    page_w, page_h = 3508, 2480
    cell_w, cell_h = page_w // 2, page_h // 2
    target_w, target_h = 1640, 1140
    for page_idx in range((len(cards) + 3) // 4):
        page = Image.new("RGB", (page_w, page_h), "white")
        for n, path in enumerate(cards[page_idx * 4:page_idx * 4 + 4]):
            with Image.open(path) as img:
                card = ImageOps.contain(img.convert("RGB"), (target_w, target_h), Image.Resampling.LANCZOS)
            x = (n % 2) * cell_w + (cell_w - card.width) // 2
            y = (n // 2) * cell_h + (cell_h - card.height) // 2
            page.paste(card, (x, y))
        page.save(output_dir / f"page-{page_idx + 1:02d}.png", dpi=DPI)


def main():
    parser = argparse.ArgumentParser(description="将汉字和拼音排版到儿童识字卡（不负责 AI 生图）。")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--illustrations", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--font", help="中文字体文件路径，例如 C:\\Windows\\Fonts\\msyhbd.ttc")
    args = parser.parse_args()
    font_path, font_index = find_font(args.font)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as f:
        entries = list(csv.DictReader(f))
    cards_dir = args.output / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    cards, missing = [], []
    for entry in entries:
        slug = entry["slug"].strip()
        art = args.illustrations / f"{slug}.png"
        if not art.is_file():
            missing.append(f'{entry["hanzi"]} ({slug}.png)')
            continue
        card = render_card(entry, art, font_path, font_index)
        target = cards_dir / f"{slug}.png"
        card.save(target, dpi=DPI)
        cards.append(target)
        print(f"生成 {entry['hanzi']}：{target}")
    if not cards:
        raise SystemExit("没有发现可排版的插画。请先让 Codex 将内置生图结果保存到插画目录。")
    args.output.mkdir(parents=True, exist_ok=True)
    make_overview(cards, args.output / "overview.png")
    make_print_sheets(cards, args.output / "print-sheets")
    print(f"完成 {len(cards)}/{len(entries)} 张；总览：{args.output / 'overview.png'}")
    if missing:
        print("缺少插画（已跳过）：" + "、".join(missing))


if __name__ == "__main__":
    main()
