"""FastAPI web application."""

import os
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core import (
    get_config,
    QueryGenerator,
    PubMedClient,
    ContentGenerator,
    ReportGenerator,
    db,
)
from core.scheduler import JobScheduler

app = FastAPI(title="PubMed Papers Feed")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Initialize components
report_generator = ReportGenerator()
scheduler = JobScheduler()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard."""
    config = get_config()
    stats = db.get_stats()
    recent_reports = db.get_reports(5)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "config": config,
            "stats": stats,
            "recent_reports": recent_reports,
        },
    )


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page."""
    config = get_config()
    return templates.TemplateResponse(
        "config.html", {"request": request, "config": config}
    )


@app.get("/llm-config", response_class=HTMLResponse)
async def llm_config_page(request: Request):
    """LLM Configuration page."""
    config = get_config()
    return templates.TemplateResponse(
        "llm_config.html", {"request": request, "config": config}
    )


@app.post("/api/llm-config")
async def update_llm_config(
    api_key: str = Form(...),
    model: str = Form(...),
):
    """Update only LLM configuration (base_url is fixed)."""
    from core.config import config_manager
    
    config = get_config()
    
    # Update only LLM config, keep other settings
    # base_url is fixed to https://537-ai.net/v1
    config.llm.base_url = "https://537-ai.net/v1"
    config.llm.api_key = api_key
    config.llm.model = model
    
    # Save config
    config_manager.save(config)
    
    return {"status": "success", "message": "LLM 配置已保存"}


@app.post("/api/test-llm")
async def test_llm_connection(request: Request):
    """Test LLM API connection."""
    import httpx
    from openai import AsyncOpenAI
    
    try:
        data = await request.json()
        base_url = data.get("base_url")
        api_key = data.get("api_key")
        model = data.get("model")
        
        if not base_url or not api_key:
            return {"status": "error", "message": "API 地址和密钥不能为空"}
        
        # Create temporary client
        client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=httpx.AsyncClient(verify=False, timeout=30.0)
        )
        
        # Test with a simple completion
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            await client.close()
            return {
                "status": "success", 
                "message": "连接成功",
                "model": response.model
            }
        except Exception as e:
            await client.close()
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "auth" in error_msg.lower():
                return {"status": "error", "message": "API Key 无效，请检查密钥是否正确"}
            elif "model" in error_msg.lower():
                return {"status": "error", "message": f"模型 '{model}' 不存在或无法访问"}
            else:
                return {"status": "error", "message": f"连接失败: {error_msg[:200]}"}
                
    except Exception as e:
        return {"status": "error", "message": f"请求处理失败: {str(e)[:200]}"}


@app.post("/config")
async def update_config(
    api_key: str = Form(...),
    model: str = Form(...),
    search_days: int = Form(...),
    max_results: int = Form(...),
    schedule: str = Form(None),
    interests: str = Form(...),
):
    """Update configuration (base_url is fixed)."""
    from core.config import AppConfig, LLMConfig, PubMedConfig, config_manager

    # Parse interests (one per line)
    interests_list = [i.strip() for i in interests.split("\n") if i.strip()]

    # Create new config with fixed base_url
    config = AppConfig(
        llm=LLMConfig(base_url="https://537-ai.net/v1", api_key=api_key, model=model),
        pubmed=PubMedConfig(
            search_days=search_days,
            max_results=max_results,
            schedule=schedule if schedule else None,
        ),
        interests=interests_list,
    )

    # Save config
    config_manager.save(config)

    # Update scheduler if needed
    if schedule:
        scheduler.update_schedule(schedule)

    return {"status": "success", "message": "配置已保存"}


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Search page."""
    config = get_config()
    return templates.TemplateResponse(
        "search.html", {"request": request, "interests": config.interests}
    )


@app.post("/search")
async def do_search(
    natural_language: str = Form(None),
    interest_index: int = Form(0), 
    custom_query: str = Form(None)
):
    """Perform search and return preview.
    
    Priority:
    1. natural_language: 直接输入自然语言描述，LLM生成检索式
    2. custom_query: 手动输入PubMed检索式
    3. interest_index: 选择预设的兴趣主题
    """
    config = get_config()

    # Generate query
    query_gen = QueryGenerator()

    if natural_language and natural_language.strip():
        # 自然语言描述优先
        query = await query_gen.generate_query(natural_language.strip())
    elif custom_query and custom_query.strip():
        # 手动检索式
        query = custom_query.strip()
    else:
        # 预设主题
        if interest_index >= len(config.interests):
            raise HTTPException(status_code=400, detail="Invalid interest index")
        interest = config.interests[interest_index]
        query = await query_gen.generate_query(interest)
    
    # 保存原始输入用于历史记录
    original_input = natural_language if natural_language and natural_language.strip() else None

    # Search PubMed
    client = PubMedClient()
    articles = client.search_and_fetch(
        query, config.pubmed.search_days, config.pubmed.max_results
    )

    # Filter out existing articles
    new_articles = [a for a in articles if not db.article_exists(a.pmid)]

    # Calculate quality scores (simplified)
    scored_articles = []
    for article in new_articles:
        score = 50.0  # Base score
        # Higher score for recent articles
        score += 20.0
        scored_articles.append({"article": article, "score": score, "is_new": True})

    # Sort by score
    scored_articles.sort(key=lambda x: x["score"], reverse=True)

    # 保存搜索历史
    db.save_search_history(
        query=query,
        natural_language=original_input,
        total_found=len(articles),
        new_articles=len(new_articles),
    )

    return {
        "status": "success",
        "query": query,
        "total_found": len(articles),
        "new_articles": len(new_articles),
        "articles": [
            {
                "pmid": a["article"].pmid,
                "title": a["article"].title,
                "journal": a["article"].journal,
                "pub_date": a["article"].pub_date,
                "score": a["score"],
                "url": a["article"].url,
            }
            for a in scored_articles[:20]  # Return top 20
        ],
    }


@app.post("/generate")
async def generate_content(
    pmids: str = Form(...),
    xiaohongshu_long: int = Form(0),
    xiaohongshu_short_1: int = Form(1),
    xiaohongshu_short_2: int = Form(2),
    wechat_long: int = Form(0),
    wechat_short_1: int = Form(1),
    wechat_short_2: int = Form(2),
):
    """Generate content for selected articles."""
    pmid_list = [p.strip() for p in pmids.split(",") if p.strip()]

    # Fetch articles
    client = PubMedClient()
    articles = client.fetch_articles(pmid_list)

    if not articles:
        raise HTTPException(status_code=400, detail="No articles found")

    # Generate content
    content_gen = ContentGenerator()
    articles_with_content = []

    for article in articles:
        content = await content_gen.generate_all(article)
        articles_with_content.append({"article": article, "content": content})

        # Save to database
        db.save_article(article.to_dict())

    # Create report
    selected_indices = {
        "xiaohongshu_long": [xiaohongshu_long],
        "xiaohongshu_short": [xiaohongshu_short_1, xiaohongshu_short_2],
        "wechat_long": [wechat_long],
        "wechat_short": [wechat_short_1, wechat_short_2],
    }

    report = await report_generator.create_report(
        articles_with_content, selected_indices
    )

    return {"status": "success", "report": report}


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports list page."""
    reports = db.get_reports(50)
    return templates.TemplateResponse(
        "reports.html", {"request": request, "reports": reports}
    )


@app.get("/report/{report_id}", response_class=HTMLResponse)
async def view_report(request: Request, report_id: str, file: str = None):
    """View specific report."""
    report = db.get_report_by_id(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if file and file in report["file_paths"]:
        # Read specific file
        content = report_generator.read_report(report["file_paths"][file])
        return templates.TemplateResponse(
            "view_report.html",
            {
                "request": request,
                "report": report,
                "filename": file,
                "content": content,
            },
        )

    # Show file list
    return templates.TemplateResponse(
        "view_report.html",
        {"request": request, "report": report, "filename": None, "content": None},
    )


@app.get("/download/{report_id}")
async def download_report(report_id: str, file: str = None):
    """Download report file or zip."""
    report = db.get_report_by_id(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if file and file in report["file_paths"]:
        # Download single file
        file_path = report["file_paths"][file]
        if os.path.exists(file_path):
            return FileResponse(
                file_path, filename=f"{file}.md", media_type="text/markdown"
            )

    # Download all as zip
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for name, path in report["file_paths"].items():
            if os.path.exists(path):
                zip_file.write(path, f"{name}.md")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.zip"},
    )


@app.post("/export")
async def export_reports(report_ids: str = Form(...)):
    """Export multiple reports as zip."""
    ids = [i.strip() for i in report_ids.split(",") if i.strip()]

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for report_id in ids:
            report = db.get_report_by_id(report_id)
            if report:
                date_folder = report["date"]
                for name, path in report["file_paths"].items():
                    if os.path.exists(path):
                        arcname = f"{date_folder}/{name}.md"
                        zip_file.write(path, arcname)

    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=reports_export_{timestamp}.zip"
        },
    )


@app.get("/preview/{pmid}", response_class=HTMLResponse)
async def preview_article(request: Request, pmid: str):
    """Preview content for single article."""
    # Fetch article
    client = PubMedClient()
    articles = client.fetch_articles([pmid])

    if not articles:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles[0]

    # Generate content
    content_gen = ContentGenerator()
    content = await content_gen.generate_all(article)

    return templates.TemplateResponse(
        "preview.html", {"request": request, "article": article, "content": content}
    )


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    return db.get_stats()


@app.get("/search-history", response_class=HTMLResponse)
async def search_history_page(request: Request):
    """Search history page."""
    history = db.get_search_history(100)
    return templates.TemplateResponse(
        "search_history.html", {"request": request, "history": history}
    )


@app.get("/api/search-history")
async def get_search_history_api(limit: int = 50):
    """Get search history as JSON."""
    return {"status": "success", "history": db.get_search_history(limit)}


@app.delete("/api/search-history/{history_id}")
async def delete_search_history(history_id: int):
    """Delete a search history record."""
    success = db.delete_search_history(history_id)
    if success:
        return {"status": "success", "message": "已删除"}
    raise HTTPException(status_code=404, detail="记录不存在")
