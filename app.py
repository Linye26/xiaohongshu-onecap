"""
小红书一键创作助手 - 主程序（AI增强版）
基于 Flask 的 Web 应用，集成 Ollama 本地模型生成高品质小红书内容
"""

import os
import sys
import re
import json
import zipfile
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_generator import generate_all, CONTENT_TYPES
from image_generator import generate_all_images
from content_reviewer import review_content, export_review_report

app = Flask(__name__)

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


@app.route("/")
def index():
    """首页 - 创作表单"""
    content_types = list(CONTENT_TYPES.keys())
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

    # 创建本次输出目录（关键词做安全处理）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = re.sub(r'[^\w\-]', '_', keyword)[:20]
    session_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_keyword}")
    os.makedirs(session_dir, exist_ok=True)
    
    # 生成文案
    content = generate_all(keyword=keyword, content_type=content_type)
    
    # 内容审查
    review_result = review_content(content)
    review_report = export_review_report(content, review_result)
    
    # 保存审查报告
    review_path = os.path.join(session_dir, "审查报告.txt")
    with open(review_path, "w", encoding="utf-8") as f:
        f.write(review_report)
    
    if not review_result["passed"]:
        return jsonify({
            "success": False,
            "error": "内容未通过合规审查",
            "review": review_result,
            "report": review_report
        }), 400

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
            "review": review_result,
            "text_path": text_path,
            "review_path": review_path,
            "images": [{
                "name": name, 
                "path": path,
                "url": f"/api/image?path={os.path.basename(path)}&dir={os.path.basename(session_dir)}"
            } for name, path in images],
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


@app.route("/api/image")
def serve_image():
    """提供生成的图片文件"""
    filename = request.args.get("path", "")
    dirname = request.args.get("dir", "")
    file_path = os.path.join(OUTPUT_DIR, dirname, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="image/png")
    return "Image not found", 404


@app.route("/api/download", methods=["POST"])
def download_all():
    """打包下载所有生成的内容（文案 + 图片）"""
    data = request.json
    session_dir = data.get("output_dir", "").strip()
    
    if not session_dir or not os.path.exists(session_dir):
        return jsonify({"success": False, "error": "输出目录不存在"}), 400
    
    # 创建内存 ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 添加文案文件
        text_path = os.path.join(session_dir, "文案.txt")
        if os.path.exists(text_path):
            zip_file.write(text_path, "文案.txt")
        
        # 添加所有图片
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, session_dir)
                    zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    dir_name = os.path.basename(session_dir)
    response = send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"小红书创作_{dir_name}.zip"
    )
    # 确保 ZIP 文件正确关闭
    response.headers['Content-Length'] = str(zip_buffer.getbuffer().nbytes)
    return response

# ==================== 审查规则管理 API ====================

@app.route("/api/review/rules", methods=["GET"])
def get_review_rules():
    """获取当前审查规则版本"""
    from content_reviewer import get_rules_version
    return jsonify(get_rules_version())


@app.route("/api/review/test", methods=["POST"])
def test_review():
    """测试审查功能"""
    data = request.json
    content = data.get("content", {})
    result = review_content(content)
    return jsonify(result)


@app.route("/api/review/add_keyword", methods=["POST"])
def add_review_keyword():
    """添加敏感词（规则迭代）"""
    from content_reviewer import add_sensitive_word
    data = request.json
    category = data.get("category", "").strip()
    word = data.get("word", "").strip()
    
    if not category or not word:
        return jsonify({"success": False, "error": "缺少 category 或 word 参数"}), 400
    
    success = add_sensitive_word(category, word)
    return jsonify({"success": success, "message": f"已添加敏感词: {category} - {word}"})


@app.route("/api/review/add_pattern", methods=["POST"])
def add_review_pattern():
    """添加禁止模式"""
    from content_reviewer import add_prohibited_pattern
    data = request.json
    pattern_type = data.get("type", "").strip()
    pattern = data.get("pattern", "").strip()
    
    if not pattern_type or not pattern:
        return jsonify({"success": False, "error": "缺少 type 或 pattern 参数"}), 400
    
    success = add_prohibited_pattern(pattern_type, pattern)
    return jsonify({"success": success, "message": f"已添加禁止模式: {pattern_type}"})


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  小红书一键创作助手 已启动")
    print("  打开浏览器访问: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)