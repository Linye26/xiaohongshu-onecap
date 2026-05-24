"""
小红书图片生成模块
使用 Pillow 生成小红书风格封面图和内容卡片
"""

import os
from PIL import Image, ImageDraw, ImageFont
import textwrap


# 配色方案 - 暖色教育风
COLORS = {
    "primary": "#FF6B35",       # 主色-活力橙
    "secondary": "#FFF8F0",     # 背景-米白
    "accent": "#FFB347",        # 强调-暖金
    "text_dark": "#2D2D2D",     # 深色文字
    "text_light": "#FFFFFF",    # 浅色文字
    "border": "#FFD4A8",        # 边框-浅橙
    "tag_bg": "#FF8C5A",        # 标签背景
    "card_bg": "#FFFFFF",       # 卡片白色
}


# 小红书图片标准尺寸
SIZES = {
    "封面": (1080, 1440),      # 3:4 竖版封面
    "内页": (1080, 1440),      # 内页图
    "横版": (1440, 1080),      # 横版封面
    "方图": (1080, 1080),      # 1:1 方图
}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取字体，优先使用系统字体"""
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",      # 微软雅黑粗体
        "C:/Windows/Fonts/simhei.ttf",       # 黑体
        "C:/Windows/Fonts/simfang.ttf",      # 仿宋
        "C:/Windows/Fonts/simsun.ttc",       # 宋体
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # 兜底：使用默认字体
    return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> tuple:
    """十六进制颜色转 RGB"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple,
    radius: int,
    fill: str,
    outline: str = None,
):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def _wrap_text(text: str, max_chars_per_line: int) -> list:
    """中文换行处理"""
    lines = []
    current_line = ""
    for char in text:
        current_line += char
        if len(current_line) >= max_chars_per_line:
            lines.append(current_line)
            current_line = ""
    if current_line:
        lines.append(current_line)
    return lines


def generate_cover(
    title: str,
    content_type: str,
    keyword: str,
    output_path: str,
) -> str:
    """生成小红书封面图"""
    width, height = SIZES["封面"]
    img = Image.new("RGB", (width, height), COLORS["secondary"])
    draw = ImageDraw.Draw(img)

    # 顶部装饰色块
    draw.rectangle([(0, 0), (width, 280)], fill=COLORS["primary"])

    # 顶部装饰圆弧
    draw.ellipse(
        [(width - 200, -80), (width + 80, 200)], fill=COLORS["accent"]
    )

    # 内容类型标签
    tag_w, tag_h = 200, 60
    tag_x, tag_y = 60, 340
    _draw_rounded_rect(
        draw,
        (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h),
        radius=15,
        fill=COLORS["primary"],
    )
    font_tag = _get_font(28, bold=True)
    draw.text(
        (tag_x + tag_w // 2, tag_y + tag_h // 2),
        content_type,
        fill=COLORS["text_light"],
        font=font_tag,
        anchor="mm",
    )

    # 主标题
    title_lines = _wrap_text(title, 14)
    font_title = _get_font(56, bold=True)
    title_y = 460
    for line in title_lines[:3]:
        draw.text((60, title_y), line, fill=COLORS["text_dark"], font=font_title)
        title_y += 80

    # 装饰线
    line_y = title_y + 40
    draw.rectangle([(60, line_y), (220, line_y + 6)], fill=COLORS["primary"])

    # 底部信息
    bottom_y = height - 200
    font_bottom = _get_font(32)
    draw.text(
        (60, bottom_y),
        "一键生成 · 小红书创作助手",
        fill=COLORS["primary"],
        font=font_bottom,
    )

    # 底部装饰色条
    draw.rectangle([(0, height - 60), (width, height)], fill=COLORS["primary"])

    img.save(output_path, quality=95)
    return output_path


def generate_content_card(
    title: str,
    body_section: str,
    card_number: int,
    total_cards: int,
    output_path: str,
) -> str:
    """生成内容卡片"""
    width, height = SIZES["内页"]
    img = Image.new("RGB", (width, height), COLORS["card_bg"])
    draw = ImageDraw.Draw(img)

    # 顶部色条
    draw.rectangle([(0, 0), (width, 8)], fill=COLORS["primary"])

    # 页码
    font_page = _get_font(26)
    draw.text(
        (width - 120, 40),
        f"{card_number}/{total_cards}",
        fill="#999999",
        font=font_page,
    )

    # 小标题
    font_title = _get_font(44, bold=True)
    title_lines = _wrap_text(title, 16)
    title_y = 100
    for line in title_lines[:2]:
        draw.text((80, title_y), line, fill=COLORS["text_dark"], font=font_title)
        title_y += 60

    # 分隔线
    sep_y = title_y + 30
    draw.rectangle([(80, sep_y), (280, sep_y + 4)], fill=COLORS["accent"])

    # 正文内容
    font_body = _get_font(32)
    body_lines = _wrap_text(body_section, 22)
    body_y = sep_y + 60
    for line in body_lines[:15]:
        draw.text((80, body_y), line, fill="#444444", font=font_body)
        body_y += 52

    # 底部
    draw.rectangle([(0, height - 4), (width, height)], fill=COLORS["primary"])

    img.save(output_path, quality=95)
    return output_path


def generate_tag_card(tags: str, output_path: str) -> str:
    """生成标签页卡片"""
    width, height = SIZES["内页"]
    img = Image.new("RGB", (width, height), COLORS["secondary"])
    draw = ImageDraw.Draw(img)

    # 标题区
    draw.rectangle([(0, 0), (width, 200)], fill=COLORS["primary"])
    font_title = _get_font(48, bold=True)
    draw.text(
        (width // 2, 100),
        "话题标签",
        fill=COLORS["text_light"],
        font=font_title,
        anchor="mm",
    )

    # 标签列表
    tag_list = [t.strip() for t in tags.split("#") if t.strip()]
    font_tag = _get_font(36)
    tag_y = 280
    for tag in tag_list:
        tag_text = f"# {tag}"
        tag_w = len(tag_text) * 36 + 60
        tag_h = 70

        if tag_y + tag_h > height - 100:
            break

        _draw_rounded_rect(
            draw,
            (100, tag_y, 100 + tag_w, tag_y + tag_h),
            radius=20,
            fill=COLORS["primary"],
        )
        draw.text(
            (130, tag_y + tag_h // 2),
            tag_text,
            fill=COLORS["text_light"],
            font=font_tag,
            anchor="lm",
        )
        tag_y += 110

    img.save(output_path, quality=95)
    return output_path


def generate_all_images(content: dict, output_dir: str) -> list:
    """根据生成的内容，生成全套小红书图片"""
    os.makedirs(output_dir, exist_ok=True)
    images = []

    # 1. 封面图
    cover_path = os.path.join(output_dir, "01_封面.png")
    generate_cover(
        title=content["标题"],
        content_type=content["类型"],
        keyword=content["关键词"],
        output_path=cover_path,
    )
    images.append(("封面图", cover_path))

    # 2. 内容卡片（将正文分成两段）
    body = content["正文"]
    paragraphs = body.split("\n\n")

    # 合并短段落
    merged = []
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) < 200:
            current += ("\n" if current else "") + p
        else:
            if current:
                merged.append(current)
            current = p
    if current:
        merged.append(current)

    # 至少生成2张内容卡
    if len(merged) == 0:
        merged = [body]
    if len(merged) == 1:
        mid = len(merged[0]) // 2
        merged = [merged[0][:mid], merged[0][mid:]]

    total_cards = len(merged) + 1  # +1 为标签页
    for i, section in enumerate(merged[:4]):  # 最多4张内容卡
        card_path = os.path.join(output_dir, f"0{i+2}_内容卡.png")
        generate_content_card(
            title=content["标题"],
            body_section=section,
            card_number=i + 1,
            total_cards=total_cards,
            output_path=card_path,
        )
        images.append((f"内容卡{i+1}", card_path))

    # 3. 标签页
    tag_path = os.path.join(output_dir, f"0{len(images)+1}_标签页.png")
    generate_tag_card(content["标签"], output_path=tag_path)
    images.append(("标签页", tag_path))

    return images