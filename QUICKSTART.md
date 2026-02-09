# 快速开始指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置

1. 复制配置文件模板：
```bash
cp config.yaml.example config.yaml
```

2. 编辑 `config.yaml`，填写你的 LLM API 信息：
```yaml
llm:
  base_url: "https://api.openai.com/v1"  # 或你的 API 地址
  api_key: "your-api-key-here"
  model: "gpt-4"

pubmed:
  search_days: 1          # 搜索最近1天的文献
  max_results: 100        # 最多100篇

interests:
  - "LLM在医疗影像诊断中的应用"
  - "大语言模型在药物发现中的研究"
```

## 3. 启动 Web 界面

```bash
python main.py
```

访问 http://localhost:8000

## 4. 使用流程

1. **配置页面**：检查和修改 LLM、PubMed 和兴趣主题配置
2. **搜索页面**：选择兴趣主题或输入自定义检索式，点击搜索
3. **预览文案**：点击文章旁边的"预览文案"查看生成的内容
4. **生成报告**：选择要生成的文章，系统会自动创建 6 份文案（小红书长/短、公众号长/短）
5. **报告页面**：查看历史报告，下载 Markdown 文件

## 5. 每日工作流（30分钟）

1. 打开 http://localhost:8000
2. 点击"开始搜索"，等待 30-60 秒
3. 查看搜索结果，浏览 Top 10-20 篇文献
4. 点击"预览文案"查看感兴趣的文章
5. 选择 3-5 篇文章生成报告
6. 下载 Markdown 文件
7. 复制到小红书/公众号发布

## 6. 文件说明

- `data/pubmed.db` - SQLite 数据库（自动去重）
- `data/reports/YYYY-MM-DD/` - 每日生成的报告
- `config.yaml` - 配置文件

## 7. 注意事项

- **首次使用**：需要先配置好 LLM API
- **API 限制**：PubMed API 有频率限制，不要频繁搜索
- **定时任务**：如需自动搜索，在 config.yaml 中配置 schedule 字段
- **数据备份**：定期备份 data/ 目录

## 8. 常见问题

**Q: LLM 调用失败怎么办？**
A: 检查 base_url 和 api_key 是否正确，测试 API 连通性

**Q: 搜索不到新文章？**
A: 尝试扩大 search_days 或调整兴趣主题描述

**Q: 如何导出所有报告？**
A: 在报告页面选择多个报告，点击"批量导出"

**Q: 如何停止定时任务？**
A: 删除 config.yaml 中的 schedule 字段或重启服务

## 9. 目录结构

```
pubmed_papers_feed/
├── main.py              # 入口文件
├── config.yaml          # 配置文件（需创建）
├── requirements.txt     # 依赖
├── core/               # 核心模块
│   ├── config.py       # 配置管理
│   ├── llm_generator.py # LLM 检索式生成
│   ├── pubmed_client.py # PubMed API
│   ├── database.py     # SQLite 数据库
│   ├── content_generator.py # 文案生成
│   ├── reporter.py     # 报告生成
│   └── scheduler.py    # 定时任务
├── web/                # Web 界面
│   ├── app.py          # FastAPI 路由
│   └── templates/      # HTML 模板
└── data/               # 数据存储
    ├── pubmed.db       # 数据库
    └── reports/        # 生成的报告
```

---

**祝你使用愉快！如有问题请查看 README.md 或提交 Issue。**
