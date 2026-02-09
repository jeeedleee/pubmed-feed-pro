"""Command line interface for PubMed paper feed."""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from core import (
    get_config,
    QueryGenerator,
    PubMedClient,
    ContentGenerator,
    ReportGenerator,
    db,
)


def print_header():
    """Print CLI header."""
    print("=" * 60)
    print("  PubMed Paper Feed - CLI")
    print("  智能 PubMed 文献聚合与文案生成工具")
    print("=" * 60)
    print()


def print_config_info(config):
    """Print current configuration."""
    print("[配置信息]")
    print(f"  LLM Base URL: {config.llm.base_url}")
    print(f"  Model: {config.llm.model}")
    print(f"  搜索天数: {config.pubmed.search_days}")
    print(f"  最大结果: {config.pubmed.max_results}")
    print(f"  兴趣主题数: {len(config.interests)}")
    for i, interest in enumerate(config.interests, 1):
        print(f"    {i}. {interest}")
    print()


async def run_search(
    interest: str = None,
    days: int = None,
    max_results: int = None,
    dry_run: bool = False,
):
    """Run a search with optional filters."""
    config = get_config()
    
    # Use config defaults if not specified
    if days is None:
        days = config.pubmed.search_days
    if max_results is None:
        max_results = config.pubmed.max_results
    
    print(f"[开始搜索]")
    print(f"  日期范围: 最近 {days} 天")
    print(f"  最大结果: {max_results} 篇")
    print()
    
    # Generate query
    print("[1/4] 正在生成检索式...")
    query_gen = QueryGenerator()
    
    if interest:
        interests = [interest]
        print(f"  主题: {interest}")
    else:
        interests = config.interests
        print(f"  使用全部 {len(interests)} 个兴趣主题")
    
    try:
        queries = await query_gen.generate_queries(interests)
        combined_query = await query_gen.combine_queries(queries)
        print(f"  生成检索式: {combined_query[:100]}...")
    except Exception as e:
        print(f"  [错误] 生成检索式失败: {e}")
        return False
    print()
    
    # Search PubMed
    print("[2/4] 正在搜索 PubMed...")
    client = PubMedClient()
    try:
        articles = client.search_and_fetch(combined_query, days, max_results)
        print(f"  找到 {len(articles)} 篇文章")
    except Exception as e:
        print(f"  [错误] 搜索 PubMed 失败: {e}")
        return False
    print()
    
    if not articles:
        print("[结果] 未找到相关文章")
        return True
    
    # Filter and generate content
    print("[3/4] 正在生成文案...")
    new_articles = []
    content_gen = ContentGenerator()
    
    for i, article in enumerate(articles, 1):
        print(f"  处理文章 {i}/{len(articles)}: {article.title[:50]}...", end=" ")
        
        if db.article_exists(article.pmid):
            print("[已存在，跳过]")
            continue
        
        if dry_run:
            print("[模拟模式，跳过生成]")
            new_articles.append({"article": article, "content": None})
        else:
            try:
                content = await content_gen.generate_all(article)
                new_articles.append({"article": article, "content": content})
                db.save_article(article.to_dict())
                print("[完成]")
            except Exception as e:
                print(f"[失败: {e}]")
    print()
    
    if not new_articles:
        print("[结果] 没有新文章需要生成报告")
        return True
    
    # Generate report
    print("[4/4] 正在生成报告...")
    try:
        report_gen = ReportGenerator()
        report = await report_gen.create_report(new_articles)
        
        print(f"  报告 ID: {report['report_id']}")
        print(f"  文章数: {report['article_count']}")
        print(f"  文件数: {len(report['file_paths'])}")
        
        # Also save a summary
        date_str = report['date']
        summary_path = Path("data/reports") / date_str / f"summary_{report['report_id']}.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"PubMed 搜索报告\n")
            f.write(f"报告ID: {report['report_id']}\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write(f"文章数量: {report['article_count']}\n")
            f.write("\n文章列表:\n")
            for item in new_articles:
                article = item['article']
                f.write(f"\n- {article.title}\n")
                f.write(f"  PMID: {article.pmid}\n")
                f.write(f"  期刊: {article.journal}\n")
                f.write(f"  链接: {article.url}\n")
        
        print(f"  摘要文件: {summary_path}")
        
    except Exception as e:
        print(f"  [错误] 生成报告失败: {e}")
        return False
    print()
    
    print("=" * 60)
    print(f"[完成] 共处理 {len(new_articles)} 篇新文章")
    print("=" * 60)
    
    return True


def preview_article(pmid: str):
    """Preview a specific article by PMID."""
    print(f"[预览文章] PMID: {pmid}")
    
    client = PubMedClient()
    articles = client.fetch_articles([pmid])
    
    if not articles:
        print("  [错误] 未找到该文章")
        return False
    
    article = articles[0]
    print(f"\n标题: {article.title}")
    print(f"作者: {', '.join(article.authors[:5])}")
    print(f"期刊: {article.journal}")
    print(f"日期: {article.pub_date}")
    print(f"链接: {article.url}")
    print(f"\n摘要:\n{article.abstract[:500]}...")
    
    return True


def list_history():
    """List search history."""
    print("[搜索历史]")
    # TODO: Implement history listing from database
    print("  功能开发中...")
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PubMed Paper Feed - 智能文献聚合与文案生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m core.cli                    # 使用默认配置搜索所有兴趣主题
  python -m core.cli -i "糖尿病治疗"      # 搜索指定主题
  python -m core.cli -d 14              # 搜索最近14天的文章
  python -m core.cli --preview 123456   # 预览指定PMID的文章
  python -m core.cli --dry-run          # 模拟运行（不调用LLM生成文案）
        """
    )
    
    parser.add_argument(
        "-i", "--interest",
        help="指定单个兴趣主题（覆盖配置文件）"
    )
    parser.add_argument(
        "-d", "--days",
        type=int,
        help="搜索最近N天的文章（覆盖配置文件）"
    )
    parser.add_argument(
        "-m", "--max",
        type=int,
        default=100,
        help="最多获取的文章数量（默认100）"
    )
    parser.add_argument(
        "--preview",
        metavar="PMID",
        help="预览指定PMID的文章"
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="显示搜索历史"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="显示当前配置"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行模式（不保存到数据库，不生成文案）"
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Handle simple info commands
    if args.config:
        print_config_info(get_config())
        return 0
    
    if args.history:
        return 0 if list_history() else 1
    
    if args.preview:
        return 0 if preview_article(args.preview) else 1
    
    # Run search
    print("正在初始化...")
    if args.dry_run:
        print("[模拟模式] 不会保存到数据库，不会消耗LLM Token")
    print()
    
    try:
        success = asyncio.run(run_search(
            interest=args.interest,
            days=args.days,
            max_results=args.max,
            dry_run=args.dry_run,
        ))
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        return 1
    except Exception as e:
        print(f"\n[错误] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
