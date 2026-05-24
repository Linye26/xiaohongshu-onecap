"""
小红书文案生成模块
根据主题和内容类型，自动生成标题、正文、话题标签
"""

import random
import re


# ============ 内容类型模板库 ============

TEMPLATES = {
    "教程攻略": {
        "标题模板": [
            "保姆级教程❗{keyword}，看这一篇就够了🔥",
            "手把手教你{keyword}，新手也能轻松搞定✨",
            "别再走弯路了！{keyword}正确方法来了💡",
            "超详细{keyword}指南，建议收藏🌟",
            "零基础学会{keyword}，真的不难！",
        ],
        "正文结构": [
            "开头引入段",
            "分步骤（3~5步）",
            "注意事项段",
            "总结鼓励段",
        ],
        "开头模板": [
            "很多姐妹问我{keyword}到底怎么做，今天就把我的经验毫无保留地分享出来！",
            "作为一个踩过无数坑的人，今天必须把{keyword}的正确方法告诉大家～",
            "最近发现好多小伙伴都在问{keyword}，整理了一份超全攻略！",
        ],
        "结尾模板": [
            "学会了吗？快动手试试吧，有问题评论区问我～",
            "有什么不懂的欢迎留言，看到都会回复哒💕",
            "觉得有用记得点赞收藏，下次就不怕找不到啦！",
        ],
        "标签库": ["教程", "干货分享", "新手入门", "保姆级教程", "经验分享", "学习打卡"],
    },
    "好物测评": {
        "标题模板": [
            "用了3个月，真实测评{keyword}到底值不值得买🤔",
            "{keyword}深度测评！优缺点一次性说清楚⚡",
            "后悔没早入！{keyword}测评分享🌟",
            "测评| {keyword}到底是神器还是智商税？",
            "亲测{keyword}，这些细节没人告诉你！",
        ],
        "正文结构": [
            "入手原因/背景",
            "外观/第一印象",
            "使用体验（优点+缺点）",
            "性价比分析",
            "总结推荐",
        ],
        "开头模板": [
            "入手{keyword}已经有一段时间了，今天来交作业，给大家做个真实测评！",
            "最近{keyword}的风很大，忍不住入手了，来说说真实感受～",
            "观望了很久的{keyword}终于到手，用了一段时间来分享！",
        ],
        "结尾模板": [
            "总体来说还是不错的，推荐给预算合适的姐妹～",
            "总结：优点大于缺点，值得入手！",
            "如果预算有限可以等等活动，不急的话可以蹲个大促～",
        ],
        "标签库": ["测评", "好物分享", "真实体验", "购物分享", "种草", "避坑指南"],
    },
    "种草推荐": {
        "标题模板": [
            "按头安利！{keyword}真的太好用了💕",
            "不允许还有人不知道{keyword}！按头种草🌿",
            "年度爱用| {keyword}必须拥有姓名✨",
            "姐妹们冲！{keyword}简直就是宝藏🎁",
            "私藏{keyword}分享，每一个都超好用！",
        ],
        "正文结构": [
            "引入推荐理由",
            "单品/方法详细介绍",
            "使用感受/效果",
            "购买/获取方式",
            "总结安利",
        ],
        "开头模板": [
            "今天必须来安利一下{keyword}，用了之后真的爱不释手！",
            "发现了一个宝藏——{keyword}，必须分享给我的电子姐妹们！",
            "如果你也在找{keyword}，那一定要看看这个！",
        ],
        "结尾模板": [
            "真的强烈推荐，谁用谁知道！",
            "快冲！真的不会后悔的宝藏～",
            "信我，入手不亏！",
        ],
        "标签库": ["种草", "爱用分享", "宝藏好物", "按头安利", "好物推荐", "私藏"],
    },
    "日常Vlog": {
        "标题模板": [
            "记录{keyword}的一天☀️ 平淡但充实",
            "{keyword}日常 | 和我一起过一天吧📸",
            "今日份{keyword}，治愈系日常分享💛",
            "PLOG | {keyword}的小确幸时刻✨",
            "生活碎片 | {keyword}带来的快乐🧩",
        ],
        "正文结构": [
            "时间线引入",
            "分时段记录（早中晚）",
            "心情/感悟",
            "互动结尾",
        ],
        "开头模板": [
            "今天的{keyword}真的太美好了，忍不住记录下来分享给你们～",
            "平凡的一天因为{keyword}变得特别，来看看吧！",
            "最近爱上了记录{keyword}，慢慢发现生活中的小美好💛",
        ],
        "结尾模板": [
            "今天的分享就到这里啦，晚安🌙",
            "希望你们也度过了美好的一天～",
            "明天见！记得好好生活哦💕",
        ],
        "标签库": ["日常", "生活碎片", "PLOG", "记录生活", "治愈", "vlog"],
    },
    "清单合集": {
        "标题模板": [
            "收藏这篇就够了！{keyword}大全📚",
            "吐血整理！{keyword}超全清单🧾",
            "一定要知道的{keyword}，少走弯路❗",
            "{keyword}合集 | 建议直接收藏⭐",
            "全网最全{keyword}，错过会后悔！",
        ],
        "正文结构": [
            "总述背景",
            "列表/分类展示",
            "每项简要说明",
            "总结/建议",
        ],
        "开头模板": [
            "花了整整一周整理这份{keyword}清单，每一个都反复确认过！",
            "作为{keyword}的重度用户，整理了这份超全合集，拿去直接用！",
            "经常有姐妹问我{keyword}相关的问题，索性整理成合集啦！",
        ],
        "结尾模板": [
            "建议先收藏慢慢看，后续还会更新～",
            "整理不易，点个赞支持一下吧💕",
            "如果还有遗漏的，评论区补充呀！",
        ],
        "标签库": ["合集", "清单", "整理", "干货", "收藏", "资源分享"],
    },
}


def generate_title(keyword: str, content_type: str) -> str:
    """根据关键词和内容类型生成标题"""
    type_config = TEMPLATES.get(content_type, TEMPLATES["教程攻略"])
    template = random.choice(type_config["标题模板"])
    return template.format(keyword=keyword)


def generate_body(keyword: str, content_type: str, tone: str = "亲和") -> str:
    """根据关键词和内容类型生成正文"""
    type_config = TEMPLATES.get(content_type, TEMPLATES["教程攻略"])

    # 选择开头
    opening = random.choice(type_config["开头模板"]).format(keyword=keyword)

    # 生成中间段落（根据类型不同）
    structure = type_config["正文结构"]
    middle_parts = []
    for i, part in enumerate(structure, 1):
        if "步骤" in part:
            middle_parts.append(f"\n{part}：")
            steps = _generate_steps(keyword)
            middle_parts.append(steps)
        elif "优缺点" in part or "优点" in part:
            middle_parts.append(_generate_pros_cons(keyword))
        elif "体验" in part or "感受" in part:
            middle_parts.append(_generate_experience(keyword))
        elif "性价比" in part:
            middle_parts.append(_generate_value_analysis(keyword))
        elif "列表" in part or "分类" in part:
            middle_parts.append(_generate_checklist(keyword))
        elif "推荐" in part or "安利" in part:
            middle_parts.append(_generate_recommendation(keyword))
        elif "时间" in part or "时段" in part:
            middle_parts.append(_generate_timeline(keyword))
        elif "心情" in part or "感悟" in part:
            middle_parts.append(_generate_reflection(keyword))
        elif "注意" in part:
            middle_parts.append(_generate_tips(keyword))
        elif "总结" in part:
            middle_parts.append(_generate_summary(keyword))
        elif "背景" in part or "原因" in part:
            middle_parts.append(_generate_background(keyword))
        elif "外观" in part or "印象" in part:
            middle_parts.append(_generate_first_impression(keyword))
        elif "说明" in part:
            middle_parts.append(_generate_brief_explanations(keyword))
        elif "建议" in part:
            middle_parts.append(_generate_suggestions(keyword))
        else:
            middle_parts.append(f"\n{part}：这里围绕「{keyword}」展开相关内容～")

    middle = "\n".join(middle_parts)

    # 选择结尾
    closing = random.choice(type_config["结尾模板"])

    # 组装正文
    body = f"{opening}\n\n{middle}\n\n{closing}"
    return body


def generate_tags(keyword: str, content_type: str) -> str:
    """生成话题标签"""
    type_config = TEMPLATES.get(content_type, TEMPLATES["教程攻略"])
    tags = type_config["标签库"][:4]
    # 添加关键词相关标签
    tags.append(keyword)
    return "  ".join([f"#{tag}" for tag in tags])


def _generate_steps(keyword: str) -> str:
    steps = [
        f"第一步：先了解{keyword}的基础知识，做好准备工作",
        f"第二步：按照正确的方法开始操作{keyword}",
        f"第三步：检查关键环节，确保{keyword}不出错",
        f"第四步：完成{keyword}后进行复盘优化",
        f"第五步：坚持练习，{keyword}会越来越熟练",
    ]
    return "\n".join(steps[: random.randint(3, 5)])


def _generate_pros_cons(keyword: str) -> str:
    return f"""✅ 优点：
1. {keyword}的核心功能很实用
2. 使用体验整体不错
3. 性价比在同类产品中算高的

❌ 缺点：
1. 初次使用{keyword}需要一定学习成本
2. 部分细节还可以优化
3. 价格对新用户不太友好"""


def _generate_experience(keyword: str) -> str:
    return f"""实际使用{keyword}的感受：
- 日常使用：很方便，能解决大部分需求
- 稳定性：目前没有遇到明显问题
- 上手难度：中等，熟悉后就很顺手
- 推荐指数：⭐⭐⭐⭐（4星）"""


def _generate_value_analysis(keyword: str) -> str:
    return f"""💰 性价比分析：
对比了同类型的几款产品，{keyword}的价格在中等偏上水平，
但考虑到它的功能和使用体验，整体性价比还是不错的。
如果是新手入门，建议先从基础款入手，
等需求提升了再考虑升级～"""


def _generate_checklist(keyword: str) -> str:
    items = [
        f"{keyword}入门必读指南",
        f"{keyword}进阶技巧汇总",
        f"{keyword}常见问题解答",
        f"{keyword}必备工具推荐",
        f"{keyword}学习路线图",
        f"{keyword}实用模板合集",
    ]
    return "\n".join([f"  {i+1}. {item}" for i, item in enumerate(items[:5])])


def _generate_recommendation(keyword: str) -> str:
    return f"""💕 我的{keyword}推荐：
✨ 首推这款，功能全面又好用
✨ 如果预算有限可以选平替版本
✨ 追求品质的话选旗舰款不会错
✨ 新手入门建议从基础版开始"""


def _generate_timeline(keyword: str) -> str:
    return f"""☀️ 早上：用{keyword}开启元气满满的一天
🌤️ 上午：沉浸在{keyword}的世界里
🌞 中午：休息一下，记录{keyword}的灵感
🌅 下午：继续探索{keyword}的更多可能
🌙 晚上：回顾今天的{keyword}收获"""


def _generate_reflection(keyword: str) -> str:
    return f"""关于{keyword}的一些感悟：
生活因为{keyword}变得更加有趣了，
每天花一点时间在{keyword}上，
慢慢积累下来，真的能看到自己的进步。
这大概就是坚持的意义吧💛"""


def _generate_tips(keyword: str) -> str:
    return f"""⚠️ 注意事项：
1. 使用{keyword}前一定要做好准备工作
2. 过程中遇到问题不要慌，多查资料
3. 记得定期检查和维护{keyword}
4. 安全第一，不要为了效率忽视风险"""


def _generate_summary(keyword: str) -> str:
    return f"""总结一下：
{keyword}总体来说是个很值得投入的事情，
只要掌握了正确的方法，坚持下去，
一定会有收获的！一起加油～"""


def _generate_background(keyword: str) -> str:
    return f"""为什么关注{keyword}？
最近{keyword}这个话题越来越火，
身边很多朋友都在讨论，
作为一个深度用户/爱好者，
今天来分享一下我的视角和体验～"""


def _generate_first_impression(keyword: str) -> str:
    return f"""第一印象：
刚接触{keyword}的时候，
外观/界面很吸引人，
整体给人的感觉很舒服，
让人迫不及待想深入了解～"""


def _generate_brief_explanations(keyword: str) -> str:
    items = [
        f"{keyword}类型A：适合新手入门",
        f"{keyword}类型B：功能更全面",
        f"{keyword}类型C：性价比最高",
        f"{keyword}类型D：专业级选择",
    ]
    return "\n".join([f"  • {item}" for item in items])


def _generate_suggestions(keyword: str) -> str:
    return f"""💡 一些建议：
1. 新手建议先从{keyword}的基础开始
2. 多参考别人的经验可以少走弯路
3. 坚持比天赋更重要
4. 享受{keyword}带来的乐趣才是关键"""


def generate_all(keyword: str, content_type: str = "教程攻略") -> dict:
    """一键生成完整的小红书内容"""
    return {
        "标题": generate_title(keyword, content_type),
        "正文": generate_body(keyword, content_type),
        "标签": generate_tags(keyword, content_type),
        "类型": content_type,
        "关键词": keyword,
    }