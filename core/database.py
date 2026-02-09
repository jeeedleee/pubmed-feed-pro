"""Database models and operations using SQLAlchemy."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Integer,
    JSON,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class Article(Base):
    """Article model for deduplication and storage."""

    __tablename__ = "articles"

    pmid = Column(String(20), primary_key=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    authors = Column(JSON)
    journal = Column(String(500))
    pub_date = Column(String(100))
    doi = Column(String(200))
    keywords = Column(JSON)
    mesh_terms = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    quality_score = Column(Float, default=0.0)


class Report(Base):
    """Report model for generated content."""

    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    article_ids = Column(JSON)  # List of PMIDs
    file_paths = Column(JSON)  # Dict of platform -> file path
    created_at = Column(DateTime, default=datetime.utcnow)
    article_count = Column(Integer, default=0)


class SearchHistory(Base):
    """Search history model."""

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)  # 实际使用的检索式
    natural_language = Column(Text)  # 用户输入的自然语言（如果有）
    total_found = Column(Integer, default=0)  # 找到的文章总数
    new_articles = Column(Integer, default=0)  # 新文章数量
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    """Database manager."""

    def __init__(self, db_path: str = "data/pubmed.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def save_article(
        self, article_data: Dict[str, Any], quality_score: float = 0.0
    ) -> bool:
        """Save article to database. Returns True if new, False if exists."""
        session = self.get_session()
        try:
            # Check if exists
            existing = (
                session.query(Article).filter_by(pmid=article_data["pmid"]).first()
            )
            if existing:
                return False

            # Create new article
            article = Article(
                pmid=article_data["pmid"],
                title=article_data["title"],
                abstract=article_data.get("abstract", ""),
                authors=article_data.get("authors", []),
                journal=article_data.get("journal", ""),
                pub_date=article_data.get("pub_date", ""),
                doi=article_data.get("doi"),
                keywords=article_data.get("keywords", []),
                mesh_terms=article_data.get("mesh_terms", []),
                quality_score=quality_score,
            )
            session.add(article)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error saving article: {e}")
            return False
        finally:
            session.close()

    def article_exists(self, pmid: str) -> bool:
        """Check if article already exists."""
        session = self.get_session()
        try:
            return session.query(Article).filter_by(pmid=pmid).first() is not None
        finally:
            session.close()

    def get_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent articles."""
        session = self.get_session()
        try:
            articles = (
                session.query(Article)
                .order_by(Article.fetched_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "pmid": a.pmid,
                    "title": a.title,
                    "abstract": a.abstract,
                    "authors": a.authors,
                    "journal": a.journal,
                    "pub_date": a.pub_date,
                    "doi": a.doi,
                    "quality_score": a.quality_score,
                    "fetched_at": a.fetched_at.isoformat() if a.fetched_at else None,
                }
                for a in articles
            ]
        finally:
            session.close()

    def save_report(
        self,
        report_id: str,
        date: str,
        article_ids: List[str],
        file_paths: Dict[str, str],
    ) -> None:
        """Save report record."""
        session = self.get_session()
        try:
            report = Report(
                id=report_id,
                date=date,
                article_ids=article_ids,
                file_paths=file_paths,
                article_count=len(article_ids),
            )
            session.add(report)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error saving report: {e}")
        finally:
            session.close()

    def get_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent reports."""
        session = self.get_session()
        try:
            reports = (
                session.query(Report)
                .order_by(Report.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "date": r.date,
                    "article_count": r.article_count,
                    "file_paths": r.file_paths,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in reports
            ]
        finally:
            session.close()

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get specific report."""
        session = self.get_session()
        try:
            report = session.query(Report).filter_by(id=report_id).first()
            if report:
                return {
                    "id": report.id,
                    "date": report.date,
                    "article_count": report.article_count,
                    "file_paths": report.file_paths,
                    "article_ids": report.article_ids,
                    "created_at": report.created_at.isoformat()
                    if report.created_at
                    else None,
                }
            return None
        finally:
            session.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self.get_session()
        try:
            article_count = session.query(Article).count()
            report_count = session.query(Report).count()
            search_count = session.query(SearchHistory).count()

            # Get articles by date
            from sqlalchemy import func

            articles_by_date = (
                session.query(
                    func.date(Article.fetched_at).label("date"),
                    func.count(Article.pmid).label("count"),
                )
                .group_by(func.date(Article.fetched_at))
                .order_by(func.date(Article.fetched_at).desc())
                .limit(30)
                .all()
            )

            return {
                "total_articles": article_count,
                "total_reports": report_count,
                "total_searches": search_count,
                "articles_by_date": [
                    {"date": str(d.date), "count": d.count} for d in articles_by_date
                ],
            }
        finally:
            session.close()

    def save_search_history(
        self,
        query: str,
        natural_language: Optional[str] = None,
        total_found: int = 0,
        new_articles: int = 0,
    ) -> int:
        """Save search history. Returns the history ID."""
        session = self.get_session()
        try:
            history = SearchHistory(
                query=query,
                natural_language=natural_language,
                total_found=total_found,
                new_articles=new_articles,
            )
            session.add(history)
            session.commit()
            return history.id
        except Exception as e:
            session.rollback()
            print(f"Error saving search history: {e}")
            return -1
        finally:
            session.close()

    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search history."""
        session = self.get_session()
        try:
            histories = (
                session.query(SearchHistory)
                .order_by(SearchHistory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": h.id,
                    "query": h.query,
                    "natural_language": h.natural_language,
                    "total_found": h.total_found,
                    "new_articles": h.new_articles,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in histories
            ]
        finally:
            session.close()

    def delete_search_history(self, history_id: int) -> bool:
        """Delete a search history record."""
        session = self.get_session()
        try:
            history = session.query(SearchHistory).filter_by(id=history_id).first()
            if history:
                session.delete(history)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error deleting search history: {e}")
            return False
        finally:
            session.close()


# Global database instance
db = Database()
