"""
小红书一键创作助手 - 主程序（AI增强版 v2）
基于 Flask 的 Web 应用，集成 Ollama 本地模型生成高品质小红书内容
新增：主题选择 / 张数控制 / 参考图上传 / 审查规则实时更新
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
from image_generator import generate_all_images, COLOR_THEMES
from content_reviewer import review_content, export_review_report

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 上传限制

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    """首页 - 创作表单"""
    content_types = list(CONTENT_TYPES.keys())
    return render_template("index.html", content_types=content_types)


@app.route("/api/generate", methods=["POST"])
def generate():
    """生成内容 API（v2：支持主题/张数/参考图）"""
    data = request.json
    keyword = data.get("keyword", "").strip()
    content_type = data.get("content_type", "教程攻略")
    generate_images = data.get("generate_images", True)
    theme = data.get("theme", "暖色教育")
    image_count = data.get("image_count", 5)
    reference_image = data.get("reference_image", "").strip()

    if not keyword:
        return jsonify({"success": False, "error": "请输入关键词"}), 400
    if image_count < 1 or image_count > 5:
        image_count = 5

    # 验证参考图路径安全
    if reference_image and not os.path.exists(reference_image):
        reference_image = ""

    # 创建本次输出目录
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

    # 生成图片（传入主题/张数/参考图）
    images = []
    if generate_images:
        try:
            images = generate_all_images(
                content, session_dir,
                theme=theme,
                image_count=image_count,
                reference_image=reference_image if reference_image else None
            )
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


# ==================== 新增 API（v2） ====================

@app.route("/api/themes", methods=["GET"])
def get_themes():
    """获取所有可用配色主题"""
    return jsonify({"success": True, "themes": list(COLOR_THEMES.keys())})


@app.route("/api/upload_reference", methods=["POST"])
def upload_reference():
    """上传参考图，提取主色并返回配色信息"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "未上传文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "文件名为空"}), 400

    # 安全的文件名
    safe_name = re.sub(r'[^\w\.\-]', '_', file.filename)
    save_path = os.path.join(UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}")
    file.save(save_path)

    # 提取配色
    from image_generator import extract_colors_from_ref
    colors = extract_colors_from_ref(save_path, 3)
    
    return jsonify({
        "success": True,
        "path": save_path,
        "colors": colors,
        "primary": colors[0],
        "accent": colors[1] if len(colors) > 1 else colors[0],
        "bg": colors[2] if len(colors) > 2 else "#FFF8F0",
    })


@app.route("/api/review/remote_update", methods=["POST"])
def remote_update_rules():
    """从小红书官方渠道或自定义URL拉取最新审查规则"""
    data = request.json
    url = data.get("url", "").strip()
    
    # 默认使用项目内置的规则更新源（可替换为真实URL）
    if not url:
        url = data.get("source", "")
    
    result = {"success": False, "message": "", "added": []}
    
    if not url:
        # 本地刷新：重新加载 review_rules.json
        from content_reviewer import reload_rules
        try:
            reload_rules()
            result["success"] = True
            result["message"] = "已重新加载本地审查规则"
        except Exception as e:
            result["message"] = f"重新加载失败: {e}"
    else:
        # 远程规则拉取
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "XHS-Creator/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                remote_data = json.loads(resp.read().decode("utf-8"))
            
            from content_reviewer import merge_remote_rules
            added = merge_remote_rules(remote_data)
            result["success"] = True
            result["message"] = f"远程规则合并完成"
            result["added"] = added
        except Exception as e:
            result["message"] = f"远程拉取失败: {e}"
    
    return jsonify(result)


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  小红书一键创作助手 已启动")
    print("  打开浏览器访问: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)