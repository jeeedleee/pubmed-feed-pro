"""Content generator for different platforms."""

from typing import Dict, Any, List
from datetime import datetime

from openai import AsyncOpenAI

from core.config import get_config
from core.pubmed_client import PubMedArticle


class ContentGenerator:
    """Generate platform-specific content."""

    def __init__(self):
        config = get_config()
        self.client = AsyncOpenAI(
            base_url=config.llm.base_url, api_key=config.llm.api_key
        )
        self.model = config.llm.model

    async def generate_xiaohongshu_long(self, article: PubMedArticle) -> str:
        """Generate 小红书长文案 (200-300字)."""
        prompt = f"""请为一篇医学AI论文生成小红书文案（技术猎奇角度，200-300字）。

要求：
1. 开头用吸睛标题，带emoji
2. 强调技术突破和创新点
3. 提及关键数字和性能指标
4. 指出技术局限或需要注意的问题
5. 结尾引导互动或查看原文
6. 添加3-5个相关话题标签
7. 口语化，适合技术爱好者阅读

论文信息：
标题：{article.title}
期刊：{article.journal}
摘要：{article.abstract[:1000] if article.abstract else "无摘要"}
关键词：{", ".join(article.keywords[:5]) if article.keywords else "N/A"}

生成格式：
[标题]

[正文内容]

[标签]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是医学AI领域的小红书博主，擅长用技术视角解读最新研究，语言生动活泼，emoji使用恰当。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return self._fallback_xiaohongshu_long(article)

    async def generate_xiaohongshu_short(self, article: PubMedArticle) -> str:
        """Generate 小红书短文案 (80-120字)."""
        prompt = f"""请为一篇医学AI论文生成小红书短文案（快讯式，80-120字）。

要求：
1. 一句话概括核心发现
2. 列出2-3个关键数字
3. 添加2-3个emoji
4. 附原文链接提示
5. 极其简洁，适合快速阅读

论文信息：
标题：{article.title}
期刊：{article.journal}
关键信息：{article.abstract[:500] if article.abstract else "无摘要"}

生成格式：
[一句话总结]

[关键数据]

[链接提示 + 标签]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是医学AI资讯博主，擅长快速提炼论文精华，语言精炼，数字准确。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return self._fallback_xiaohongshu_short(article)

    async def generate_wechat_long(self, article: PubMedArticle) -> str:
        """Generate 公众号长文案 (800-1200字)."""
        prompt = f"""请为一篇医学AI论文生成公众号深度解读文章（专业严谨角度，800-1200字）。

要求：
1. 标题：专业且吸引人，体现研究价值
2. 研究背景：为什么做这个研究（100-150字）
3. 研究方法：技术方案简述（150-200字）
4. 核心结果：保留完整统计学指标，并提供通俗解读（200-250字）
   - 例如：AUC 0.89 (95%CI: 0.86-0.92) 意味着...
5. 临床意义：对医生实践的价值（150-200字）
6. 技术亮点：对AI开发者的启示（150-200字）
7. 局限与展望：研究局限性和未来方向（100-150字）
8. 原文链接和引用格式

论文信息：
标题：{article.title}
作者：{", ".join(article.authors[:5]) if article.authors else "N/A"}
期刊：{article.journal}
发表日期：{article.pub_date}
摘要：{article.abstract}
关键词：{", ".join(article.keywords) if article.keywords else "N/A"}
MeSH词：{", ".join(article.mesh_terms[:10]) if article.mesh_terms else "N/A"}
PMID：{article.pmid}
DOI：{article.doi or "N/A"}

注意：
- 保留所有统计学指标（p值、置信区间、效应量等）
- 每个统计指标后都加上一句话通俗解释
- 语言严肃专业，面向医生和AI研究者
- 结构清晰，使用小标题

生成格式：
标题：[文章标题]

【研究背景】
[内容]

【研究方法】
[内容]

【核心结果】
[内容，包含统计指标和解读]

【临床意义】
[内容]

【技术亮点】
[内容]

【局限与展望】
[内容]

---
原文链接：https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/
本文选自 PubMed 数据库，由 AI 辅助整理生成。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是医学AI领域的专业写手，擅长深度解读最新研究，对统计学和机器学习都有深入理解，写作风格严谨专业，面向医生和AI开发者。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return self._fallback_wechat_long(article)

    async def generate_wechat_short(self, article: PubMedArticle) -> str:
        """Generate 公众号短文案 (300-500字)."""
        prompt = f"""请为一篇医学AI论文生成公众号简报（300-500字）。

要求：
1. 标题：简洁明了
2. 研究背景：简述（50字）
3. 核心数据：保留关键统计指标+解读（100-150字）
4. 实践价值：对临床工作的启示（100-150字）
5. 原文链接

论文信息：
标题：{article.title}
期刊：{article.journal}
摘要：{article.abstract[:1500] if article.abstract else "无摘要"}
PMID：{article.pmid}

注意：保留核心统计指标，并解释其含义。

生成格式：
标题：[文章标题]

【研究简介】
[内容]

【核心发现】
[内容]

【实践价值】
[内容]

---
原文链接：https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是医学AI资讯编辑，擅长提炼研究精华，语言简洁专业，面向忙碌的医学工作者。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return self._fallback_wechat_short(article)

    def _fallback_xiaohongshu_long(self, article: PubMedArticle) -> str:
        """Fallback for xiaohongshu long."""
        return f"""🔥 {article.title[:50]}...

今天发现一篇超有意思的研究！{article.journal}刚发的，关于医学AI的新进展～

💡 核心看点：
• 用上了最新的LLM技术
• 在医疗场景有新突破
• 准确率很能打！

⚠️ 但要注意：
这类研究还在早期阶段，离临床实际应用还有距离，大家理性看待～

📖 想深入了解的可以读原文：
{article.url}

#医学AI #人工智能 #前沿科技 #{article.keywords[0] if article.keywords else "医学前沿"}"""

    def _fallback_xiaohongshu_short(self, article: PubMedArticle) -> str:
        """Fallback for xiaohongshu short."""
        return f"""📢 {article.title[:40]}...

期刊：{article.journal}

🔬 用LLM技术解决医学问题
📊 实验数据看起来不错
⚡ 值得关注的新方向

原文→ {article.url}

#LLM #医疗AI"""

    def _fallback_wechat_long(self, article: PubMedArticle) -> str:
        """Fallback for wechat long."""
        authors = ", ".join(article.authors[:3]) if article.authors else "N/A"
        return f"""标题：{article.title}

【研究背景】
本文探讨了大语言模型在医疗领域的最新应用进展。

【研究方法】
研究团队采用了先进的LLM架构，在医疗数据集上进行训练和验证。

【核心结果】
研究展示了LLM在医疗任务中的潜力，但具体统计指标需要查看原文。

【临床意义】
这类技术有望辅助临床决策，但需谨慎评估其可靠性和安全性。

【技术亮点】
使用了当前最先进的自然语言处理技术。

【局限与展望】
研究存在一定局限性，需要更大规模的临床验证。

---
作者：{authors}
期刊：{article.journal}
发表日期：{article.pub_date}
原文链接：{article.url}
PMID：{article.pmid}"""

    def _fallback_wechat_short(self, article: PubMedArticle) -> str:
        """Fallback for wechat short."""
        return f"""标题：{article.title}

【研究简介】
{article.journal}发表的最新研究，探索LLM在医疗中的应用。

【核心发现】
研究展示了该技术的可行性和潜在价值，具体数据见原文。

【实践价值】
为医疗AI的发展提供了新的思路和参考。

---
原文链接：{article.url}"""

    async def generate_all(self, article: PubMedArticle) -> Dict[str, str]:
        """Generate all content types for an article."""
        return {
            "xiaohongshu_long": await self.generate_xiaohongshu_long(article),
            "xiaohongshu_short": await self.generate_xiaohongshu_short(article),
            "wechat_long": await self.generate_wechat_long(article),
            "wechat_short": await self.generate_wechat_short(article),
        }
