# PubMed 文章推送工具

基于 LLM 的智能 PubMed 文献聚合与多平台文案生成工具。

## 功能特性

- 🤖 **AI 智能检索**：自然语言描述兴趣，LLM 自动生成 PubMed 高级检索式
- 📚 **多平台文案**：自动生成小红书（emoji+口语化）和公众号（严肃专业）双版本文案
- 🎨 **多格式输出**：支持 Markdown、HTML 报告、JSON 数据
- 🌐 **Web 管理界面**：可视化配置、历史管理、批量导出
- ⏰ **定时任务**：可选的定时自动抓取（支持 Cron 表达式）
- 🗄️ **智能去重**：SQLite 数据库存储，自动过滤已推送文章

## 快速开始

### 方式一：直接使用可执行文件（推荐非技术用户）

#### Windows 用户
1. 下载 `PubMedPapersFeed-Windows.zip` 并解压
2. 双击运行 `start.bat`
3. 浏览器自动打开 http://localhost:8000

#### macOS 用户
1. 下载 `PubMedPapersFeed-macOS-arm64.zip` (M1/M2/M3) 或 `PubMedPapersFeed-macOS-x86_64.zip` (Intel)
2. 解压后，**右键点击** `start.command` → 选择 "打开"
3. 首次运行需在 **系统设置 > 隐私与安全性** 中点击 "仍要打开"
4. 浏览器自动打开 http://localhost:8000

> ⚠️ **macOS 安全提示**：由于应用未签名，首次运行可能提示无法打开。请前往 **系统设置 > 隐私与安全性**，点击 "仍要打开"。

### 方式二：源码安装（推荐开发者）

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置

复制 `config.yaml.example` 为 `config.yaml`，填写你的配置：

```yaml
llm:
  base_url: "https://api.openai.com/v1"  # 你的 LLM API 地址
  api_key: "your-api-key"                # API 密钥
  model: "gpt-4"                         # 模型名称

pubmed:
  search_days: 7          # 搜索最近 N 天的文章
  max_results: 100        # 每次最多获取 100 篇

interests:
  - "人工智能在医学影像诊断中的应用"
  - "COVID-19 疫苗的长期免疫效果研究"
```

### 3. 启动 Web 界面

```bash
python main.py
```

访问 http://localhost:8000 即可使用。

### 4. 命令行运行（可选）

```bash
python -m core.cli  # 手动触发一次搜索
```

## 项目结构

```
pubmed_papers_feed/
├── main.py                 # FastAPI 应用入口
├── requirements.txt        # Python 依赖
├── config.yaml            # 用户配置文件
├── config.yaml.example    # 配置模板
├── core/                  # 核心模块
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── llm_generator.py   # LLM 检索式生成
│   ├── pubmed_client.py   # PubMed API 客户端
│   ├── database.py        # SQLite 数据库
│   ├── content_generator.py # 文案生成器
│   └── reporter.py        # 报告生成器
├── web/                   # Web 界面
│   ├── __init__.py
│   ├── app.py             # FastAPI 路由
│   ├── static/            # CSS/JS/图片
│   └── templates/         # HTML 模板
├── data/                  # 数据存储
│   ├── reports/           # 生成的报告
│   └── pubmed.db          # SQLite 数据库
└── README.md              # 本文档
```

## 配置说明

### LLM 配置

支持所有兼容 OpenAI API 格式的服务：

```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-xxxxxxxx"
  model: "gpt-4"
```

其他提供商示例：
- **Azure OpenAI**: `base_url: "https://your-resource.openai.azure.com/openai/deployments/your-deployment"`
- **本地 Ollama**: `base_url: "http://localhost:11434/v1"`, `model: "llama2"`

### PubMed 配置

```yaml
pubmed:
  search_days: 7          # 搜索最近 N 天（1-365）
  max_results: 100        # 每次最多 100 篇
  schedule: "0 9 * * *"   # 定时规则（Cron 表达式，可选）
```

Cron 表达式说明：
- `"0 9 * * *"` = 每天上午 9 点
- `"0 */6 * * *"` = 每 6 小时
- `"0 9 * * 1"` = 每周一上午 9 点

### 兴趣配置

```yaml
interests:
  - "人工智能在医学影像诊断中的应用"
  - "COVID-19 疫苗的长期免疫效果研究"
  - "机器学习在药物发现中的应用"
```

每个兴趣点会单独生成检索式并合并搜索。

## 使用指南

### Web 界面功能

1. **仪表盘**：查看系统状态、最近报告、统计信息
2. **配置管理**：在线编辑 LLM、PubMed、兴趣配置
3. **手动搜索**：立即触发一次文献搜索
4. **历史报告**：
   - 查看所有生成的报告
   - 预览 Markdown/HTML/JSON
   - 批量导出（ZIP）
   - 删除旧报告
5. **预览模式**：查看单篇文章的小红书和公众号文案

### 文案生成示例

**小红书文案**（emoji + 口语化）：
```
姐妹们！今天发现了一篇超有意思的医学论文 🤩

📌 标题：AI 诊断乳腺癌准确率超过资深医生！
💡 核心发现：
   • 准确率提升了 15% 📈
   • 诊断时间缩短了 50% ⏱️
   • 假阳性率大幅降低 ✨

👩‍⚕️ 这对我们意味着什么？
以后体检可能会更快更准啦！医学 AI 真的在改变生活～

📖 想了解的姐妹可以看原文：
链接: https://pubmed.ncbi.nlm.nih.gov/xxxxx

#医学前沿 #人工智能 #乳腺癌筛查 #健康生活 #医学科普
```

**公众号文案**（严肃专业）：
```
标题：人工智能在乳腺癌诊断中的应用进展：一项多中心验证研究

【研究背景】
乳腺癌是全球女性最常见的恶性肿瘤之一。近年来，人工智能（AI）技术在医学影像分析领域取得显著进展，但在临床实际应用中的有效性仍需大规模验证。

【研究方法】
本研究为多中心回顾性队列研究，纳入来自 15 家医院的 50,000 例乳腺钼靶影像数据，对比分析了基于深度学习的 AI 诊断系统与资深放射科医师的诊断效能。

【主要发现】
1. AI 系统的诊断准确率达到 92.3%，显著高于医师组的 89.1%（p<0.001）
2. 诊断时间中位数从 15 分钟缩短至 30 秒
3. 假阳性率降低 23%，有望减少不必要的活检

【临床意义】
该研究表明，经过充分验证的 AI 系统可作为乳腺癌筛查的有力辅助工具，有助于提高诊断效率、缓解放射科医师短缺问题。然而，AI 系统的临床部署仍需考虑伦理、法律责任及医师接受度等因素。

【原文链接】
https://pubmed.ncbi.nlm.nih.gov/xxxxx

---
本文选自 PubMed 数据库，由 AI 辅助整理生成。
```

## 批量导出

在历史报告页面，你可以：
- 选择多个报告 → 批量下载 ZIP
- 选择日期范围 → 导出该时段所有报告
- 一键导出全部 → 下载所有历史报告

## 定时任务

启用定时任务后，系统会在后台自动运行：

```bash
# 启动时自动加载定时任务
python main.py

# 查看日志
tail -f data/scheduler.log
```

## 打包分发

### Windows 打包

```bash
python build_exe.py
```

输出目录：`dist/`，包含：
- `PubMedPapersFeed.exe` - 主程序
- `start.bat` - 启动脚本

### macOS 打包

**需要在 macOS 系统上执行**：

```bash
# 赋予执行权限
chmod +x build_macos.sh

# 执行打包（自动检测当前架构）
./build_macos.sh

# 或指定架构（Intel）
TARGET_ARCH=x86_64 ./build_macos.sh

# 或指定架构（Apple Silicon M1/M2/M3）
TARGET_ARCH=arm64 ./build_macos.sh
```

输出目录：`dist/`，包含：
- `PubMedPapersFeed` - 主程序
- `start.command` - macOS 启动脚本

### 使用 GitHub Actions 自动打包

项目已配置 GitHub Actions 工作流，推送标签自动构建：

```bash
# 创建版本标签
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会自动构建：
- Windows x64 版本
- macOS Intel (x86_64) 版本
- macOS Apple Silicon (arm64) 版本

构建完成后，在 Releases 页面下载各平台安装包。

## 注意事项

1. **API 限制**：PubMed E-utilities API 有访问频率限制，建议不要频繁调用
2. **LLM Token 消耗**：生成检索式和文案会消耗 Token，请注意用量
3. **隐私保护**：数据库中存储的文章信息仅本地使用，不会上传到云端
4. **macOS 签名**：分发的 macOS 应用未经过 Apple 签名，用户需要在 "隐私与安全性" 中手动允许运行

## 许可证

MIT License
