# 小红书一键创作助手（AI 增强版）

输入一个关键词，自动生成小红书完整内容：标题、正文、话题标签、精美配图和合规审查报告。

> 基于 **Ollama 本地大模型**（qwen2.5:3b）驱动，无需付费 API，数据完全本地处理。

---

## 环境要求

| 依赖 | 说明 | 安装方式 |
|------|------|---------|
| Python 3.10+ | 运行环境 | [python.org](https://www.python.org/downloads/) |
| Ollama | 本地大模型框架 | [ollama.com/download](https://ollama.com/download) |
| 模型：qwen2.5:3b | 轻量中文模型（~2GB） | `ollama pull qwen2.5:3b` |
| NVIDIA 显卡 8GB+ | 推荐配置（RTX 3070 Ti 可用） | — |

---

## 快速开始

### 第一步：安装 Ollama 并下载模型

1. 访问 [ollama.com/download](https://ollama.com/download) 下载安装 Ollama
2. 安装完成后，打开终端输入：

```bash
ollama pull qwen2.5:3b
```

3. 验证模型安装成功：

```bash
ollama list
```

看到 `qwen2.5:3b` 即表示成功。

### 第二步：安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 第三步：启动程序

```bash
python app.py
```

### 第四步：打开浏览器

访问 **http://127.0.0.1:5000** 即可使用。

---

## AI 模型说明

| 项目 | 详情 |
|------|------|
| 模型框架 | [Ollama](https://ollama.com) 本地部署 |
| 使用模型 | qwen2.5:3b（通义千问 2.5，3B 参数） |
| 显存占用 | 约 2-3GB（适配 RTX 3070 Ti 8GB） |
| 模型大小 | ~1.9GB |
| 是否联网 | 否，完全本地运行，数据不出电脑 |
| 是否付费 | 完全免费 |

**为什么选 qwen2.5:3b？**
- 中文能力优秀，适合生成小红书风格文案
- 模型体量小，8GB 显存轻松运行
- Ollama 一键安装，零配置

---

## 功能说明

| 功能 | 说明 |
|------|------|
| AI 文案生成 | Ollama 本地模型驱动，支持 5 种内容类型 |
| 图片生成 | 自动生成封面图、内容卡片、标签页（暖色教育风 #FF6B35） |
| 内容审查 | 内置合规审查引擎，检测敏感词、违规模式，生成审查报告 |
| ZIP 打包下载 | 一键下载文案 + 图片 + 审查报告 |
| 规则迭代 | 支持在线添加敏感词和审查规则，动态更新 |

---

## 项目结构

```
xiaohongshu-creator/
├── app.py                 # 主程序 + API 路由
├── content_generator.py   # AI 文案生成（Ollama 集成）
├── image_generator.py     # 图片生成（Pillow）
├── content_reviewer.py    # 内容合规审查引擎
├── review_rules.json      # 可迭代审查规则配置
├── requirements.txt       # Python 依赖列表
├── templates/
│   └── index.html         # Web 界面
├── static/
│   └── style.css          # 样式文件
├── output/                # 生成结果（文案/图片/审查报告）
└── README.md              # 本文件
```

---

## API 接口

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web 创作界面 |
| `/api/generate` | POST | 生成文案 + 图片 + 审查 |
| `/api/preview` | POST | 仅预览文案 |
| `/api/download` | POST | ZIP 打包下载 |
| `/api/image` | GET | 查看生成的图片 |
| `/api/review/test` | POST | 测试审查功能 |
| `/api/review/rules` | GET | 查看审查规则版本 |
| `/api/review/add_keyword` | POST | 添加敏感词（规则迭代） |
| `/api/review/add_pattern` | POST | 添加禁止模式 |

---

## 使用流程

```
输入主题关键词 → 选择内容类型 → 点击生成
    → AI 生成文案 → 自动合规审查 → 生成配图
    → 查看结果 → 一键下载 ZIP（含文案+图片+审查报告）
```

---

## 常见问题

**Q: 图片生成失败？**
A: 确保系统安装了中文字体（微软雅黑），程序会自动检测。

**Q: Ollama 连接失败？**
A: 确保 Ollama 正在运行（右下角托盘图标），模型已下载（`ollama pull qwen2.5:3b`）。

**Q: 显存不够？**
A: qwen2.5:3b 仅需 2-3GB 显存，8GB 显卡完全够用。若仍不足可换 `qwen2.5:1.5b`。

**Q: 如何修改配色？**
A: 编辑 `image_generator.py` 中的 `COLORS` 字典。

**Q: 端口被占用？**
A: 修改 `app.py` 最后一行 `port=5000` 为其他端口号。

**Q: 如何更新审查规则？**
A: 调用 `/api/review/add_keyword` 接口，或直接编辑 `review_rules.json`。

---

## 开发者文档

### 审查规则配置

`review_rules.json` 包含以下可配置项：

- `sensitive_keywords` — 敏感词库（医疗/金融/虚假宣传等分类）
- `prohibited_patterns` — 正则禁止模式（联系方式/外链/价格诱导）
- `compliance_scores` — 评分权重和阈值
- `positive_indicators` — 正面加分词（干货/教程/实测等）
- `category_constraints` — 各内容类型的专项约束

修改后重启服务即可生效，也支持通过 API 在线更新。

### 模型切换

编辑 `content_generator.py` 顶部的 `MODEL` 变量：

```python
MODEL = "qwen2.5:3b"  # 可改为 qwen2.5:7b / llama3.1:8b 等
```

### 本地项目路径

默认路径：`D:\lscs\GitHub\xiaohongshu-creator\`

GitHub：`https://github.com/Linye26/xiaohongshu-onecap`