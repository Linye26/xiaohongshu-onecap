"""
小红书一键创作助手 - 主程序
基于 Flask 的 Web 应用，输入关键词即可生成完整小红书内容
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_generator import generate_all, TEMPLATES
from image_generator import generate_all_images

app = Flask(__name__)

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


@app.route("/")
def index():
    """首页 - 创作表单"""
    content_types = list(TEMPLATES.keys())
    return render_template("index.html", content_types=content_types)


@app.route("/api/generate", methods=["POST"])
def generate():
    """生成内容 API"""
    data = request.json
    keyword = data.get("keyword", "").strip()
    content_type = data.get("content_type", "教程攻略")
    generate_images = data.get("generate_images", True)

    if not keyword:
        return jsonify({"success": False, "error": "请输入关键词"}), 400

    # 生成文案
    content = generate_all(keyword=keyword, content_type=content_type)

    # 创建本次输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_{keyword}")
    os.makedirs(session_dir, exist_ok=True)

    # 保存文案
    text_path = os.path.join(session_dir, "文案.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(f"【{content['类型']}】{content['关键词']}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"📌 标题：\n{content['标题']}\n\n")
        f.write(f"📝 正文：\n{content['正文']}\n\n")
        f.write(f"🏷️ 标签：\n{content['标签']}\n")

    # 生成图片
    images = []
    if generate_images:
        try:
            images = generate_all_images(content, session_dir)
        except Exception as e:
            print(f"图片生成失败: {e}")

    return jsonify(
        {
            "success": True,
            "content": content,
            "text_path": text_path,
            "images": [{"name": name, "path": path} for name, path in images],
            "output_dir": session_dir,
        }
    )


@app.route("/api/preview", methods=["POST"])
def preview():
    """仅预览文案，不生成图片"""
    data = request.json
    keyword = data.get("keyword", "").strip()
    content_type = data.get("content_type", "教程攻略")

    if not keyword:
        return jsonify({"success": False, "error": "请输入关键词"}), 400

    content = generate_all(keyword=keyword, content_type=content_type)
    return jsonify({"success": True, "content": content})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  小红书一键创作助手 已启动")
    print("  打开浏览器访问: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)