"""
小红书文案生成模块 - AI 增强版
使用 Ollama 本地模型生成高质量文案
"""

import json
import requests
import random
import re
from typing import Dict, List

# Ollama 配置
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:3b"

# 内容类型配置
CONTENT_TYPES = {
    "教程攻略": {
        "description": "教学类内容，步骤清晰、实用性强",
        "tags": ["教程", "干货分享", "新手入门", "保姆级教程", "经验分享"]
    },
    "好物测评": {
        "description": "产品评测，客观分析优缺点",
        "tags": ["测评", "好物分享", "真实体验", "购物分享", "种草"]
    },
    "种草推荐": {
        "description": "推荐好物，分享使用体验",
        "tags": ["种草", "爱用分享", "宝藏好物", "按头安利", "好物推荐"]
    },
    "日常Vlog": {
        "description": "生活记录，真实自然",
        "tags": ["日常", "生活碎片", "PLOG", "记录生活", "治愈"]
    },
    "清单合集": {
        "description": "资源整理，系统全面",
        "tags": ["合集", "清单", "整理", "干货", "收藏"]
    }
}

def call_ollama(prompt: str, system_prompt: str = "") -> str:
    """调用 Ollama 生成内容"""
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500
            }
        }
        response = requests.post(f"{OLLAMA_HOST}/api/generate", 
                                json=payload, 
                                timeout=120)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            print(f"Ollama API 错误: {response.status_code}")
            return ""
    except Exception as e:
        print(f"调用 Ollama 失败: {e}")
        return ""

def generate_title(keyword: str, content_type: str) -> str:
    """生成吸引人的小红书标题"""
    system_prompt = "你是一个擅长写小红书标题的专家。标题要吸引人、有网感、有情绪价值。不要使用emoji和特殊符号。"
    
    prompt = f"""请为以下主题生成一个小红书风格的标题：
主题：{keyword}
内容类型：{content_type}

要求：
1. 标题要吸引人点击，有网感
2. 不要使用emoji和特殊符号
3. 体现价值感或情绪价值
4. 长度在15-25字之间

请直接输出标题，不要加引号或其他说明。"""

    title = call_ollama(prompt, system_prompt)
    if not title:
        # 备用模板
        templates = [
            f"保姆级教程 | {keyword}，看这一篇就够了",
            f"手把手教你{keyword}，新手也能轻松搞定",
            f"用了3个月，真实测评{keyword}到底值不值得买",
            f"按头安利 | {keyword}真的太好用了",
            f"记录{keyword}的一天，平淡但充实",
            f"收藏这篇就够了 | {keyword}大全"
        ]
        title = random.choice(templates)
    
    return title

def generate_body(keyword: str, content_type: str) -> str:
    """生成小红书正文内容"""
    system_prompt = "你是一个擅长写小红书内容的高手。内容要有亲和力、实用性强，使用小红书特有的语言风格。不要使用emoji和特殊符号。"
    
    type_config = CONTENT_TYPES[content_type]
    
    prompt = f"""请为以下主题生成一篇小红书风格的正文：
主题：{keyword}
内容类型：{content_type}（{type_config['description']}）

要求：
1. 使用小红书特有的语言风格（亲切、有网感）
2. 结构清晰，有开头、主体、结尾
3. 内容要实用、有价值，避免空洞
4. 适当使用分段增强可读性
5. 不要使用emoji和特殊符号
6. 字数在300-500字之间

请直接输出完整的正文内容。"""

    body = call_ollama(prompt, system_prompt)
    if not body:
        # 备用内容
        steps = [
            f"第一步：先了解{keyword}的基础知识，做好准备工作",
            f"第二步：按照正确的方法开始操作{keyword}",
            f"第三步：检查关键环节，确保{keyword}不出错",
            f"第四步：完成{keyword}后进行复盘优化",
            f"第五步：坚持练习，{keyword}会越来越熟练",
        ]
        selected_steps = random.sample(steps, random.randint(3, 5))
        
        body = f"""作为一个踩过无数坑的人，今天必须把{keyword}的正确方法告诉大家。

{chr(10).join(selected_steps)}

注意事项：
1. 使用{keyword}前一定要做好准备工作
2. 过程中遇到问题不要慌，多查资料
3. 记得定期检查和维护{keyword}
4. 安全第一，不要为了效率忽视风险

总结一下：
{keyword}总体来说是个很值得投入的事情，
只要掌握了正确的方法，坚持下去，
一定会有收获的！一起加油！

觉得有用记得点赞收藏，下次就不怕找不到啦！"""
    
    return body

def generate_tags(keyword: str, content_type: str) -> str:
    """生成话题标签"""
    type_config = CONTENT_TYPES[content_type]
    base_tags = type_config["tags"][:4]
    
    # 生成一些相关标签
    related_tags = []
    if "教程" in content_type or "攻略" in content_type:
        related_tags.extend(["学习打卡", "技能提升", "成长记录"])
    elif "测评" in content_type or "推荐" in content_type:
        related_tags.extend(["购物车", "拔草", "性价比"])
    elif "日常" in content_type:
        related_tags.extend(["vlog", "治愈系", "生活美学"])
    elif "清单" in content_type:
        related_tags.extend(["资源分享", "效率工具", "整理收纳"])
    
    # 添加关键词相关标签
    all_tags = base_tags + related_tags[:2] + [keyword]
    
    # 去重并格式化为 #标签
    unique_tags = []
    for tag in all_tags:
        clean_tag = re.sub(r'[^\w\u4e00-\u9fff]', '', str(tag))
        if clean_tag and clean_tag not in unique_tags:
            unique_tags.append(clean_tag)
    
    return "  ".join([f"#{tag}" for tag in unique_tags[:6]])

def generate_all(keyword: str, content_type: str = "教程攻略") -> Dict:
    """一键生成完整的小红书内容"""
    if content_type not in CONTENT_TYPES:
        content_type = "教程攻略"
    
    return {
        "标题": generate_title(keyword, content_type),
        "正文": generate_body(keyword, content_type),
        "标签": generate_tags(keyword, content_type),
        "类型": content_type,
        "关键词": keyword,
    }

# 保持向后兼容
TEMPLATES = CONTENT_TYPES