"""
小红书内容审查模块 - 自适应迭代版
审查生成内容是否符合平台规范，支持规则动态更新和迭代反馈
"""

import os
import re
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, "review_rules.json")


def _save_rules(rules):
    """保存规则更新"""
    rules["_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


# ==================== 核心审查引擎 ====================

def review_content(content: dict) -> dict:
    """
    审查生成的小红书内容
    
    Args:
        content: generate_all 返回的字典 {类型, 关键词, 标题, 正文, 副标题, 标签}
    
    Returns:
        {
            "score": int,           # 合规评分 (0-100)
            "passed": bool,         # 是否通过
            "level": str,           # "pass" / "warning" / "fail"
            "issues": [str],        # 问题列表
            "suggestions": [str],   # 修改建议
            "details": {            # 详细审查结果
                "keyword_hits": [],
                "pattern_hits": [],
                "positive_hits": [],
                "category_check": {}
            }
        }
    """
    rules = _load_rules()
    score = 100
    issues = []
    suggestions = []
    keyword_hits = []
    pattern_hits = []
    positive_hits = []

    text = f"{content.get('标题','')} {content.get('正文','')} {content.get('副标题','')} {content.get('标签','')}"
    content_type = content.get("类型", "")

    # 1. 敏感词检测
    for category, words in rules.get("sensitive_keywords", {}).items():
        for word in words:
            if word in text:
                keyword_hits.append({"category": category, "word": word})
                score += rules["compliance_scores"]["sensitive_keyword_hit"]
                issues.append(f"[敏感词-{category}] 包含违规词「{word}」")
                suggestions.append(f"建议删除或替换「{word}」，可使用中性表达")

    # 2. 禁止模式检测（正则）
    for pattern_type, patterns in rules.get("prohibited_patterns", {}).items():
        for pat in patterns:
            matches = re.findall(pat, text)
            if matches:
                pattern_hits.append({"type": pattern_type, "matches": matches})
                score += rules["compliance_scores"]["prohibited_pattern_hit"]
                issues.append(f"[禁止模式-{pattern_type}] 匹配到违规内容")

    # 3. 正面指标加分
    for indicator in rules.get("positive_indicators", []):
        if indicator in text:
            positive_hits.append(indicator)
            score += rules["compliance_scores"]["positive_score"]

    # 4. 分类专项检查
    category_check = {}
    constraints = rules.get("category_constraints", {}).get(content_type, {})
    required = constraints.get("require", [])
    forbidden = constraints.get("forbid", [])

    for r in required:
        found = r in text
        category_check[f"require_{r}"] = found
        if not found:
            issues.append(f"[分类要求] {content_type} 类内容建议包含「{r}」相关内容")
            score -= 5

    for f in forbidden:
        if f in text:
            category_check[f"forbid_{f}"] = True
            issues.append(f"[分类禁止] {content_type} 类内容禁止使用「{f}」")
            score -= 10
        else:
            category_check[f"forbid_{f}"] = False

    # 5. 评分归一化
    score = max(0, min(100, score))
    threshold = rules["compliance_scores"]["pass_threshold"]
    warning_th = rules["compliance_scores"]["warning_threshold"]

    if score >= threshold:
        level = "pass"
        passed = True
    elif score >= warning_th:
        level = "warning"
        passed = True
    else:
        level = "fail"
        passed = False

    return {
        "score": score,
        "passed": passed,
        "level": level,
        "issues": issues,
        "suggestions": suggestions,
        "details": {
            "keyword_hits": keyword_hits,
            "pattern_hits": pattern_hits,
            "positive_hits": positive_hits,
            "category_check": category_check
        }
    }


# ==================== 自适应迭代机制 ====================

def add_sensitive_word(category: str, word: str) -> bool:
    """添加新敏感词（规则迭代）"""
    rules = _load_rules()
    if category not in rules["sensitive_keywords"]:
        rules["sensitive_keywords"][category] = []
    if word not in rules["sensitive_keywords"][category]:
        rules["sensitive_keywords"][category].append(word)
        rules["iteration"]["rule_version_history"].append(
            f"{datetime.now():%Y%m%d_%H%M%S}_add_{category}_{word}"
        )
        _save_rules(rules)
        return True
    return False


def add_prohibited_pattern(pattern_type: str, pattern: str) -> bool:
    """添加禁止正则模式"""
    rules = _load_rules()
    if pattern_type not in rules["prohibited_patterns"]:
        rules["prohibited_patterns"][pattern_type] = []
    if pattern not in rules["prohibited_patterns"][pattern_type]:
        rules["prohibited_patterns"][pattern_type].append(pattern)
        rules["iteration"]["rule_version_history"].append(
            f"{datetime.now():%Y%m%d_%H%M%S}_add_pattern_{pattern_type}"
        )
        _save_rules(rules)
        return True
    return False


def update_compliance_threshold(pass_threshold: int = None, warning_threshold: int = None):
    """更新合规阈值"""
    rules = _load_rules()
    if pass_threshold is not None:
        rules["compliance_scores"]["pass_threshold"] = pass_threshold
    if warning_threshold is not None:
        rules["compliance_scores"]["warning_threshold"] = warning_threshold
    rules["iteration"]["rule_version_history"].append(
        f"{datetime.now():%Y%m%d_%H%M%S}_update_threshold"
    )
    _save_rules(rules)


def get_rules_version() -> dict:
    """获取当前规则版本信息"""
    rules = _load_rules()
    return {
        "version": rules["_version"],
        "updated": rules["_updated"],
        "history_count": len(rules["iteration"]["rule_version_history"])
    }


def export_review_report(content: dict, result: dict) -> str:
    """生成审查报告文本"""
    lines = [
        "=" * 50,
        "  小红书内容合规审查报告",
        "=" * 50,
        f"审查时间: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"规则版本: {get_rules_version()['version']}",
        f"内容类型: {content.get('类型', '未知')}",
        f"审查评分: {result['score']}/100 ({result['level']})",
        f"审查结果: {'✅ 通过' if result['passed'] else '❌ 未通过'}",
        "",
        f"关键词: {content.get('关键词','')}",
        f"标题: {content.get('标题','')[:50]}...",
        "",
    ]

    if result["details"]["positive_hits"]:
        lines.append(f"正面指标: {', '.join(result['details']['positive_hits'])}")
        lines.append("")

    if result["issues"]:
        lines.append(f"发现 {len(result['issues'])} 个问题:")
        for i, issue in enumerate(result["issues"], 1):
            lines.append(f"  {i}. {issue}")
        lines.append("")

    if result["suggestions"]:
        lines.append("修改建议:")
        for i, s in enumerate(result["suggestions"], 1):
            lines.append(f"  {i}. {s}")
        lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)


# ==================== 远程规则更新 ====================

# 模块级缓存，支持热重载
_rules_cache = None
_rules_cache_time = None


def reload_rules():
    """强制重新加载审查规则（清除缓存）"""
    global _rules_cache, _rules_cache_time
    _rules_cache = None
    _rules_cache_time = None
    return _load_rules()


def _load_rules():
    """加载审查规则（带缓存）"""
    global _rules_cache, _rules_cache_time
    mtime = os.path.getmtime(RULES_PATH)
    if _rules_cache is not None and _rules_cache_time == mtime:
        return _rules_cache
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        _rules_cache = json.load(f)
        _rules_cache_time = mtime
    return _rules_cache


def merge_remote_rules(remote_data: dict) -> list:
    """合并远程规则到本地 review_rules.json，返回新增条目列表"""
    rules = _load_rules()
    added = []

    # 合并敏感词
    remote_keywords = remote_data.get("sensitive_keywords", {})
    for category, words in remote_keywords.items():
        if category not in rules["sensitive_keywords"]:
            rules["sensitive_keywords"][category] = []
        for word in words:
            if word not in rules["sensitive_keywords"][category]:
                rules["sensitive_keywords"][category].append(word)
                added.append(f"敏感词:{category}:{word}")

    # 合并禁止模式
    remote_patterns = remote_data.get("prohibited_patterns", {})
    for ptype, patterns in remote_patterns.items():
        if ptype not in rules["prohibited_patterns"]:
            rules["prohibited_patterns"][ptype] = []
        for pat in patterns:
            if pat not in rules["prohibited_patterns"][ptype]:
                rules["prohibited_patterns"][ptype].append(pat)
                added.append(f"禁止模式:{ptype}")

    # 合并合规分数
    remote_scores = remote_data.get("compliance_scores", {})
    for key, val in remote_scores.items():
        if key in rules["compliance_scores"]:
            rules["compliance_scores"][key] = val

    # 合并分类约束
    remote_constraints = remote_data.get("category_constraints", {})
    for ct, constraints in remote_constraints.items():
        rules["category_constraints"][ct] = constraints

    # 记录版本
    rules["iteration"]["rule_version_history"].append(
        f"{datetime.now():%Y%m%d_%H%M%S}_remote_merge_{len(added)}_items"
    )
    _save_rules(rules)
    reload_rules()
    return added


# ==================== 自检入口 ====================

if __name__ == "__main__":
    test_content = {
        "类型": "教程攻略",
        "关键词": "理财入门",
        "标题": "稳赚不赔的理财方法，日赚1000不是梦",
        "正文": "加我微信：abc123，告诉你独家秘方，绝对有效！",
        "副标题": "全网最低，仅需99元",
        "标签": "#理财 #赚钱 #教程"
    }

    result = review_content(test_content)
    print(export_review_report(test_content, result))