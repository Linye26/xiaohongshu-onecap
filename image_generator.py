"""
小红书图片生成模块 - 专业版（v2 优化）
高品质小红书风格封面图和内容卡片
支持：多主题切换 / 参考图配色提取 / 速度优化
"""

import os
import re
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================
# 配色方案
# ============================================================
COLOR_THEMES = {
    "暖色教育": {
        "primary": "#FF6B35", "primary_dark": "#E55A2B", "primary_light": "#FF8C5A",
        "bg": "#FFF8F0", "card_bg": "#FFFFFF",
        "text_dark": "#2D2D2D", "text_medium": "#666666", "text_light": "#999999",
        "accent": "#FFB347", "accent2": "#FFD4A8",
        "tag_bg": "#FF6B35", "tag_text": "#FFFFFF",
        "divider": "#FFD4A8", "highlight": "#FFF0E0",
    },
    "清新薄荷": {
        "primary": "#00B894", "primary_dark": "#00A381", "primary_light": "#55EFC4",
        "bg": "#F5FFFD", "card_bg": "#FFFFFF",
        "text_dark": "#2D3436", "text_medium": "#636E72", "text_light": "#B2BEC3",
        "accent": "#81ECEC", "accent2": "#B2F0E2",
        "tag_bg": "#00B894", "tag_text": "#FFFFFF",
        "divider": "#B2F0E2", "highlight": "#E8FFF8",
    },
    "活力蓝紫": {
        "primary": "#6C5CE7", "primary_dark": "#5A4BD1", "primary_light": "#A29BFE",
        "bg": "#F8F7FF", "card_bg": "#FFFFFF",
        "text_dark": "#2D2D2D", "text_medium": "#666666", "text_light": "#B2BEC3",
        "accent": "#A29BFE", "accent2": "#D0C8FF",
        "tag_bg": "#6C5CE7", "tag_text": "#FFFFFF",
        "divider": "#D0C8FF", "highlight": "#F0EEFF",
    },
    "暗夜黑金": {
        "primary": "#D4AF37", "primary_dark": "#B8960C", "primary_light": "#F0D060",
        "bg": "#1A1A2E", "card_bg": "#16213E",
        "text_dark": "#E0E0E0", "text_medium": "#AAAAAA", "text_light": "#777777",
        "accent": "#C9A84C", "accent2": "#3D2E0A",
        "tag_bg": "#D4AF37", "tag_text": "#1A1A2E",
        "divider": "#3D2E0A", "highlight": "#0F3460",
    },
}

SIZES = {"封面": (1080, 1440), "内页": (1080, 1440)}
QUALITY = 90  # 图片保存质量（90 = 速度与质量最佳平衡）

COLORS = COLOR_THEMES["暖色教育"]  # 默认主题


# ============================================================
# 工具函数
# ============================================================
def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# --- 字体缓存（避免每次创建 ImageFont，提速 2-3x） ---
_font_cache = {}
def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    cache_key = (size, bold)
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    font_paths = [
        ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[cache_key] = font
                return font
            except:
                pass
    font = ImageFont.load_default()
    _font_cache[cache_key] = font
    return font


def _clean_text(text: str) -> str:
    replacements = {
        "🚀": "", "🌟": "", "🌈": "", "✨": "", "💕": "", "🔥": "",
        "❗": "！", "⚠️": "【注意】", "✅": "【对】", "❌": "【错】",
        "💡": "【提示】", "💰": "", "☀️": "", "🌙": "", "📚": "",
        "📸": "", "🧩": "", "💛": "", "🎁": "", "🌿": "", "⚡": "",
        "⭐": "", "🖼️": "", "▎": "|", "▶": "", "◆": "", "▪": "",
        "•": "·",
    }
    for emoji, safe in replacements.items():
        text = text.replace(emoji, safe)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# --- 快速渐变（分块 rectangle 替代逐行 line，提速 3-5x） ---
def _draw_gradient_v(draw, x1, y1, x2, y2, c1, c2):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    height = y2 - y1
    chunk = max(1, height // 4)  # 每 chunk px 一个块
    hh = height
    for i in range(0, hh, chunk):
        t = i / hh
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.rectangle([(x1, y1+i), (x2, min(y1+i+chunk, y2))], fill=(r, g, b))


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _wrap_text(text: str, max_chars: int) -> list:
    """中文换行"""
    lines = []
    current = ""
    for ch in text:
        current += ch
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


# --- 参考图配色提取 ---
def extract_colors_from_ref(ref_path: str, n: int = 3) -> list:
    """从参考图中提取主色调，返回 #RRGGBB 列表"""
    try:
        from collections import Counter
        img = Image.open(ref_path).convert("RGB")
        img = img.resize((200, 200), Image.LANCZOS)
        img = img.quantize(colors=32, method=Image.Quantize.MEDIANCUT).convert("RGB")
        pixels = list(img.getdata())
        color_counts = Counter(pixels)
        dominant = []
        for rgb, _ in color_counts.most_common(50):
            r, g, b = rgb
            brightness = (r + g + b) / 3
            if 30 < brightness < 240:
                dominant.append("#{:02X}{:02X}{:02X}".format(r, g, b))
            if len(dominant) >= n:
                break
        return dominant if dominant else ["#FF6B35", "#FFB347", "#FFF8F0"]
    except Exception:
        return ["#FF6B35", "#FFB347", "#FFF8F0"]


def set_theme(theme_name: str):
    """切换当前全局配色主题"""
    global COLORS
    if theme_name in COLOR_THEMES:
        COLORS = COLOR_THEMES[theme_name]
        return True
    return False


def apply_reference_colors(ref_path: str):
    """从参考图提取颜色并覆盖当前主题的 primary/accent"""
    global COLORS
    try:
        dom = extract_colors_from_ref(ref_path, 3)
        COLORS = dict(COLORS)
        COLORS["primary"] = dom[0]
        COLORS["accent"] = dom[1] if len(dom) > 1 else dom[0]
        bg_rgb = hex_to_rgb(dom[2]) if len(dom) > 2 else (255, 248, 240)
        COLORS["bg"] = "#{:02X}{:02X}{:02X}".format(*bg_rgb)
        if sum(bg_rgb) / 3 < 128:
            COLORS["text_dark"] = "#E0E0E0"
            COLORS["text_medium"] = "#AAAAAA"
            COLORS["card_bg"] = "#2A2A2A"
            COLORS["tag_text"] = "#FFFFFF"
        return True
    except Exception:
        return False


# ============================================================
# 封面图
# ============================================================
def generate_cover(title: str, content_type: str, keyword: str,
                   output_path: str) -> str:
    title = _clean_text(title)
    content_type = _clean_text(content_type)
    W, H = SIZES["封面"]
    M = 60  # 边距

    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # --- 顶部渐变横幅 ---
    _draw_gradient_v(draw, 0, 0, W, 520, COLORS["primary"], COLORS["accent"])

    # --- 装饰圆 ---
    for cx, cy, r, a in [
        (W-100, 80, 200, 0.10),
        (W-60, 280, 120, 0.06),
        (80, 180, 80, 0.08),
    ]:
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255,255,255,int(255*a)))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # --- 顶部品牌区 ---
    font_brand = _get_font(28)
    draw.text((M, 40), "小红书创作助手", fill="#FFFFFF", font=font_brand)
    draw.text((M, 80), "AI 驱动 · 一键出图", fill="#FFD4A8",
              font=_get_font(22))

    # --- 类型标签 ---
    tag_w, tag_h = 200, 64
    tag_x, tag_y = M, 200
    _draw_rounded_rect(draw, [tag_x, tag_y, tag_x+tag_w, tag_y+tag_h],
                       radius=32, fill="#FFFFFF")
    font_tag = _get_font(28, bold=True)
    draw.text((tag_x+tag_w//2, tag_y+tag_h//2), content_type,
              fill=COLORS["primary"], font=font_tag, anchor="mm")

    # --- 主标题 ---
    title_lines = _wrap_text(title, 12)
    if len(title_lines) > 4:
        title_lines = title_lines[:4]

    font_title = _get_font(56, bold=True)
    title_y = 340
    for i, line in enumerate(title_lines):
        draw.text((M, title_y + i*80), line,
                  fill="#FFFFFF", font=font_title)

    # --- 装饰线 ---
    line_y = title_y + len(title_lines)*80 + 30
    draw.line([(M, line_y), (M+180, line_y)], fill="#FFFFFF", width=4)

    # --- 中间卡片区 ---
    card_top = line_y + 60
    card_h = 300
    _draw_rounded_rect(draw, [M, card_top, W-M, card_top+card_h],
                       radius=24, fill=COLORS["card_bg"],
                       outline=COLORS["divider"], width=2)

    # 卡片内图标区
    icon_y = card_top + 50
    icon_size = 80
    icon_colors = [COLORS["primary"], COLORS["accent"], COLORS["primary_light"]]
    icon_labels = ["输入主题", "AI 创作", "导出图文"]
    for idx in range(3):
        cx = M + 60 + idx * ((W-2*M-120)//2)
        cy = icon_y + icon_size//2
        _draw_rounded_rect(draw,
            [cx-icon_size//2, cy-icon_size//2, cx+icon_size//2, cy+icon_size//2],
            radius=20, fill=icon_colors[idx])
        # 序号
        font_num = _get_font(36, bold=True)
        draw.text((cx, cy), str(idx+1), fill="#FFFFFF", font=font_num, anchor="mm")
        # 标签
        font_lbl = _get_font(22)
        draw.text((cx, cy+icon_size//2+20), icon_labels[idx],
                  fill=COLORS["text_medium"], font=font_lbl, anchor="mm")

    # 箭头
    arrow_y = icon_y + icon_size//2
    for idx in range(2):
        ax = M + 60 + icon_size//2 + idx * ((W-2*M-120)//2) + 60
        draw.text((ax, arrow_y), "→", fill=COLORS["divider"],
                  font=_get_font(32), anchor="mm")

    # --- 底部 ---
    footer_h = 100
    draw.rectangle([(0, H-footer_h), (W, H)], fill=COLORS["primary"])
    font_footer = _get_font(26)
    draw.text((W//2, H-footer_h//2), "小红书创作助手 · 本地 AI 驱动",
              fill="#FFFFFF", font=font_footer, anchor="mm")

    img.save(output_path, quality=QUALITY)
    return output_path


# ============================================================
# 内容卡片
# ============================================================
def generate_content_card(title: str, body_section: str, card_number: int,
                          total_cards: int, output_path: str) -> str:
    title = _clean_text(title)
    body_section = _clean_text(body_section)
    W, H = SIZES["内页"]
    M = 60

    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # --- 顶部色条 ---
    draw.rectangle([(0, 0), (W, 8)], fill=COLORS["primary"])

    # --- 白色内容卡片 ---
    card_top = 40
    card_bottom = H - 40
    _draw_rounded_rect(draw, [M, card_top, W-M, card_bottom],
                       radius=28, fill=COLORS["card_bg"])

    # --- 卡片内顶部装饰线 ---
    inner_top = card_top + 30
    draw.line([(M+30, inner_top), (M+30, inner_top+50)],
              fill=COLORS["primary"], width=5)

    # --- 小标题 ---
    short_title = title[:14]
    font_stitle = _get_font(34, bold=True)
    draw.text((M+55, inner_top+5), short_title,
              fill=COLORS["primary"], font=font_stitle)

    # --- 页码 ---
    font_page = _get_font(22)
    page_text = f"{card_number} / {total_cards}"
    bbox = draw.textbbox((0,0), page_text, font=font_page)
    pw = bbox[2] - bbox[0]
    draw.text((W-M-30-pw, inner_top+10), page_text,
              fill=COLORS["text_light"], font=font_page)

    # --- 分隔线 ---
    sep_y = inner_top + 70
    draw.line([(M+30, sep_y), (M+230, sep_y)],
              fill=COLORS["accent"], width=3)

    # --- 正文 ---
    body_y = sep_y + 40
    max_chars = 18
    max_lines = 20

    body_section = body_section.replace("\n\n", "\n").strip()
    all_lines = []
    for paragraph in body_section.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        p_lines = _wrap_text(paragraph, max_chars)
        all_lines.extend(p_lines)
        all_lines.append("")

    font_body = _get_font(30)
    font_bold = _get_font(32, bold=True)
    line_count = 0

    for line in all_lines:
        if line_count >= max_lines:
            break
        if not line.strip():
            body_y += 12
            continue

        # 判断行类型
        is_heading = any(line.startswith(p) for p in [
            "【注意】", "！", "【对】", "【错】", "【提示】",
            "第一步", "第二步", "第三步", "第四步", "第五步",
            "总结", "核心", "关键", "重点"
        ])

        if is_heading:
            # 标题行：加左侧色块
            _draw_rounded_rect(draw,
                [M+30, body_y+4, M+36, body_y+40],
                radius=3, fill=COLORS["primary"])
            draw.text((M+55, body_y), line,
                      fill=COLORS["primary"], font=font_bold)
            body_y += 52
        else:
            # 普通行：加圆点
            dot_x, dot_y = M+35, body_y+18
            draw.ellipse([dot_x-3, dot_y-3, dot_x+3, dot_y+3],
                        fill=COLORS["accent"])
            draw.text((M+55, body_y), line,
                      fill=COLORS["text_dark"], font=font_body)
            body_y += 48

        line_count += 1

    # --- 底部装饰 ---
    draw.rectangle([(0, H-8), (W, H)], fill=COLORS["primary"])

    img.save(output_path, quality=QUALITY)
    return output_path


# ============================================================
# 标签页
# ============================================================
def generate_tag_card(tags: str, output_path: str) -> str:
    tags = _clean_text(tags)
    W, H = SIZES["内页"]
    M = 60

    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # --- 顶部标题区 ---
    header_h = 200
    _draw_gradient_v(draw, 0, 0, W, header_h,
                     COLORS["primary"], COLORS["primary_dark"])

    font_title = _get_font(48, bold=True)
    draw.text((W//2, 80), "话题标签", fill="#FFFFFF",
              font=font_title, anchor="mm")
    font_sub = _get_font(26)
    draw.text((W//2, 140), "让更多人看到你的内容",
              fill="#FFC48C", font=font_sub, anchor="mm")

    # --- 标签网格 ---
    tag_list = [t.strip().lstrip("#") for t in tags.split("#") if t.strip()]

    cols = 2
    rows = math.ceil(len(tag_list) / cols)
    tag_w = (W - 2*M - 30) // cols
    tag_h = 72
    x_start = M
    y_start = header_h + 60

    font_tag = _get_font(30, bold=True)

    for i, tag in enumerate(tag_list):
        col = i % cols
        row = i // cols
        x = x_start + col * (tag_w + 30)
        y = y_start + row * (tag_h + 30)

        # 标签背景
        _draw_rounded_rect(draw, [x, y, x+tag_w, y+tag_h],
                           radius=18, fill=COLORS["tag_bg"])

        tag_text = f"# {tag}"
        draw.text((x+tag_w//2, y+tag_h//2), tag_text,
                  fill=COLORS["tag_text"], font=font_tag, anchor="mm")

    # --- 底部提示 ---
    footer_y = H - 160
    _draw_rounded_rect(draw,
        [M, footer_y, W-M, footer_y+80],
        radius=20, fill=COLORS["highlight"],
        outline=COLORS["divider"], width=2)

    font_tip = _get_font(26)
    draw.text((W//2, footer_y+40),
              "收藏 + 转发，让更多家长看到",
              fill=COLORS["primary"], font=font_tip, anchor="mm")

    # --- 底部色条 ---
    draw.rectangle([(0, H-8), (W, H)], fill=COLORS["primary"])

    img.save(output_path, quality=QUALITY)
    return output_path


# ============================================================
# 批量生成（v2：支持主题、张数、参考图）
# ============================================================
def generate_all_images(content: dict, output_dir: str,
                        theme: str = "暖色教育",
                        image_count: int = 5,
                        reference_image: str = None) -> list:
    global COLORS
    # 先设置主题
    if reference_image and os.path.exists(reference_image):
        apply_reference_colors(reference_image)
    else:
        set_theme(theme)

    os.makedirs(output_dir, exist_ok=True)
    images = []

    # 封面（始终生成）
    cover_path = os.path.join(output_dir, "01_封面.png")
    generate_cover(content["标题"], content["类型"],
                   content["关键词"], cover_path)
    images.append(("封面图", cover_path))

    # 内容卡片（根据 image_count 控制）
    body = content["正文"]
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

    merged = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) < 300:
            current += ("\n\n" if current else "") + p
        else:
            if current:
                merged.append(current)
            current = p
    if current:
        merged.append(current)

    if not merged:
        merged = [body]
    if len(merged) == 1 and len(merged[0]) > 200:
        # 按需求张数均匀拆分
        chunk = max(1, len(merged[0]) // image_count)
        merged = [merged[0][i:i+chunk] for i in range(0, len(merged[0]), chunk)]

    max_cards = min(image_count, 5, len(merged))
    for i, section in enumerate(merged[:max_cards]):
        card_path = os.path.join(output_dir, f"0{i+2}_内容卡.png")
        generate_content_card(content["标题"], section,
                             i+1, max_cards, card_path)
        images.append((f"内容卡{i+1}", card_path))

    # 标签页（仅张数 >= 3 时生成，保证至少封面+1内容+标签）
    if image_count >= 3:
        tag_path = os.path.join(output_dir, f"0{len(images)+1}_标签页.png")
        generate_tag_card(content["标签"], tag_path)
        images.append(("标签页", tag_path))

    return images
