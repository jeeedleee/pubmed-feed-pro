"""Job scheduler for automatic PubMed searches."""

import asyncio
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core import (
    get_config,
    QueryGenerator,
    PubMedClient,
    ContentGenerator,
    ReportGenerator,
    db,
)


class JobScheduler:
    """Schedule and manage periodic PubMed searches."""

    def __init__(self):
        self.scheduler = None
        self.config = get_config()

    def start(self):
        """Start the scheduler."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self.scheduler = AsyncIOScheduler(event_loop=loop)
        
        if self.config.pubmed.schedule:
            self._add_job(self.config.pubmed.schedule)
        self.scheduler.start()
        print(f"[Scheduler] Started at {datetime.now()}")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            print(f"[Scheduler] Stopped at {datetime.now()}")

    def update_schedule(self, cron_expression: str):
        """Update the schedule with a new cron expression."""
        if not self.scheduler:
            print("[Scheduler] Scheduler not started")
            return
            
        # Remove existing jobs
        self.scheduler.remove_all_jobs()

        # Add new job
        if cron_expression:
            self._add_job(cron_expression)
            print(f"[Scheduler] Updated schedule: {cron_expression}")

    def _add_job(self, cron_expression: str):
        """Add a scheduled job."""
        if not self.scheduler:
            print("[Scheduler] Scheduler not initialized")
            return
            
        try:
            self.scheduler.add_job(
                self._run_search,
                trigger=CronTrigger.from_crontab(cron_expression),
                id="pubmed_search",
                replace_existing=True,
            )
            print(f"[Scheduler] Added job with schedule: {cron_expression}")
        except Exception as e:
            print(f"[Scheduler] Error adding job: {e}")

    async def _run_search(self):
        """Execute the scheduled search."""
        print(f"[Scheduler] Running scheduled search at {datetime.now()}")

        try:
            config = get_config()

            # Generate queries
            query_gen = QueryGenerator()
            queries = await query_gen.generate_queries(config.interests)
            combined_query = await query_gen.combine_queries(queries)

            # Search PubMed
            client = PubMedClient()
            articles = client.search_and_fetch(
                combined_query, config.pubmed.search_days, config.pubmed.max_results
            )

            # Filter and generate content
            new_articles = []
            content_gen = ContentGenerator()

            for article in articles:
                if not db.article_exists(article.pmid):
                    content = await content_gen.generate_all(article)
                    new_articles.append({"article": article, "content": content})
                    db.save_article(article.to_dict())

            # Generate report if we have articles
            if new_articles:
                report_gen = ReportGenerator()
                report = await report_gen.create_report(new_articles)
                print(
                    f"[Scheduler] Generated report with {report['article_count']} articles"
                )
            else:
                print("[Scheduler] No new articles found")

        except Exception as e:
            print(f"[Scheduler] Error running search: {e}")
