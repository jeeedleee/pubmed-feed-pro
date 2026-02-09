"""PubMed API client using direct HTTP requests."""

import json
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree as ET

import httpx

from core.config import get_config


# Create a global client with SSL verification disabled for problematic environments
httpx_client = httpx.Client(verify=False, timeout=30.0)


class PubMedArticle:
    """Represents a PubMed article."""

    def __init__(
        self,
        pmid: str,
        title: str,
        abstract: str,
        authors: List[str],
        journal: str,
        pub_date: str,
        doi: Optional[str] = None,
        keywords: List[str] = None,
        mesh_terms: List[str] = None,
    ):
        self.pmid = pmid
        self.title = title
        self.abstract = abstract
        self.authors = authors
        self.journal = journal
        self.pub_date = pub_date
        self.doi = doi
        self.keywords = keywords or []
        self.mesh_terms = mesh_terms or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "journal": self.journal,
            "pub_date": self.pub_date,
            "doi": self.doi,
            "keywords": self.keywords,
            "mesh_terms": self.mesh_terms,
        }

    @property
    def url(self) -> str:
        """Get PubMed URL."""
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"


class PubMedClient:
    """Client for PubMed E-utilities API."""

    def __init__(self, email: str = "user@example.com"):
        self.email = email
        self.config = get_config()
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def _make_request(self, url: str) -> str:
        """Make HTTP request with proper headers."""
        headers = {
            "User-Agent": f"PubMedFeed/1.0 ({self.email})",
        }
        response = httpx_client.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def search(self, query: str, days: int = 7, max_results: int = 100) -> List[str]:
        """Search PubMed and return PMIDs."""
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Format dates for PubMed
        date_filter = (
            f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[PDAT]"
        )

        # Combine query with date filter
        full_query = f"({query}) AND {date_filter}"

        try:
            # Build search URL
            params = urllib.parse.urlencode({
                "db": "pubmed",
                "term": full_query,
                "retmax": max_results,
                "sort": "date",
                "retmode": "json",
            })
            url = f"{self.base_url}/esearch.fcgi?{params}"
            
            response = self._make_request(url)
            data = json.loads(response)
            
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []

    def fetch_articles(self, pmids: List[str]) -> List[PubMedArticle]:
        """Fetch article details by PMIDs."""
        if not pmids:
            return []

        articles = []

        try:
            # Fetch in batches to avoid API limits
            batch_size = 100
            for i in range(0, len(pmids), batch_size):
                batch = pmids[i : i + batch_size]

                # Build fetch URL
                params = urllib.parse.urlencode({
                    "db": "pubmed",
                    "id": ",".join(batch),
                    "rettype": "xml",
                    "retmode": "text",
                })
                url = f"{self.base_url}/efetch.fcgi?{params}"

                xml_data = self._make_request(url)

                # Parse XML
                root = ET.fromstring(xml_data)

                for article in root.findall(".//PubmedArticle"):
                    try:
                        pmid_elem = article.find(".//PMID")
                        pmid = pmid_elem.text if pmid_elem is not None else ""

                        # Title
                        title_elem = article.find(".//ArticleTitle")
                        title = title_elem.text if title_elem is not None else ""

                        # Abstract
                        abstract_parts = article.findall(".//AbstractText")
                        abstract = " ".join(
                            [part.text for part in abstract_parts if part.text]
                        )

                        # Authors
                        authors = []
                        author_list = article.findall(".//Author")
                        for author in author_list[:10]:  # Limit to first 10 authors
                            lastname = author.find("LastName")
                            firstname = author.find("ForeName")
                            if lastname is not None:
                                name = lastname.text or ""
                                if firstname is not None:
                                    name = f"{firstname.text} {name}"
                                authors.append(name)

                        # Journal
                        journal_elem = article.find(".//Journal/Title")
                        journal = journal_elem.text if journal_elem is not None else ""

                        # Publication date
                        pub_date_elem = article.find(".//PubDate")
                        pub_date = ""
                        if pub_date_elem is not None:
                            year = pub_date_elem.find("Year")
                            month = pub_date_elem.find("Month")
                            day = pub_date_elem.find("Day")
                            parts = []
                            if year is not None:
                                parts.append(year.text)
                            if month is not None:
                                parts.append(month.text)
                            if day is not None:
                                parts.append(day.text)
                            pub_date = " ".join(parts)

                        # DOI
                        doi_elem = article.find(".//ArticleId[@IdType='doi']")
                        doi = doi_elem.text if doi_elem is not None else None

                        # Keywords
                        keywords = []
                        keyword_list = article.findall(".//Keyword")
                        for kw in keyword_list:
                            if kw.text:
                                keywords.append(kw.text)

                        # MeSH terms
                        mesh_terms = []
                        mesh_list = article.findall(".//MeshHeading/DescriptorName")
                        for mesh in mesh_list:
                            if mesh.text:
                                mesh_terms.append(mesh.text)

                        if pmid and title:  # Only add if we have minimum data
                            articles.append(
                                PubMedArticle(
                                    pmid=pmid,
                                    title=title,
                                    abstract=abstract,
                                    authors=authors,
                                    journal=journal,
                                    pub_date=pub_date,
                                    doi=doi,
                                    keywords=keywords,
                                    mesh_terms=mesh_terms,
                                )
                            )
                    except Exception as e:
                        print(f"Error parsing article: {e}")
                        continue

        except Exception as e:
            print(f"Error fetching articles: {e}")

        return articles

    def search_and_fetch(
        self, query: str, days: int = None, max_results: int = None
    ) -> List[PubMedArticle]:
        """Search and fetch in one call."""
        if days is None:
            days = self.config.pubmed.search_days
        if max_results is None:
            max_results = self.config.pubmed.max_results

        pmids = self.search(query, days, max_results)
        return self.fetch_articles(pmids)
