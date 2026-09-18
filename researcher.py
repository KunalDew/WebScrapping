import os
import json
import redis
import asyncio

import config
from planner import generate_queries
from search import search
from scraper import scrape_urls
from relevance_filter import filter_relevant
from synthesizer import synthesize
from database import save_research_log

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

def run_research_task(task_id: str, question: str):
    """
    Runs the entire research pipeline synchronously.
    Updates the task state in Redis so the frontend can poll progress.
    """
    def emit(message: str, data: dict = None):
        meta = {"message": message}
        if data:
            meta.update(data)
        
        # Check if the task was cancelled by looking for a cancellation flag
        cancel_flag = redis_client.get(f"task:{task_id}:cancel")
        if cancel_flag:
            redis_client.setex(f"task:{task_id}", 3600, json.dumps({"state": "FAILURE", "result": "Task cancelled by user"}))
            raise Exception("Task cancelled by user")
            
        redis_client.setex(f"task:{task_id}", 3600, json.dumps({"state": "PROGRESS", "info": meta}))

    emit("Initializing research agent...")
    
    # Step 1: Planner
    emit("Generating search queries...")
    queries = generate_queries(question)
    emit("Queries generated", {"queries": queries})
    
    # Step 2: Search
    emit(f"Searching DuckDuckGo ({len(queries)} queries)...")
    all_results = []
    seen_urls = set()
    for q in queries:
        results = search(q)
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_results.append(r)
    emit("Search complete", {"unique_urls": len(all_results)})
    
    # Step 3: Scrape
    emit(f"Scraping {len(all_results)} pages (this may take a moment)...")
    urls = [r.url for r in all_results]
    pages = scrape_urls(urls)
    successful = [p for p in pages if p.success]
    emit("Scraping complete", {"successful": len(successful), "total": len(pages)})
    
    # Step 4: Filter
    emit(f"Filtering {len(successful)} pages for relevance...")
    relevant = filter_relevant(successful, question)
    emit("Filtering complete", {"relevant": len(relevant), "total_scraped": len(successful)})
    
    if not relevant:
        emit("Synthesizing comprehensive research report using deep AI reasoning...")
        report = synthesize(question, [])
    else:
        # Step 5: Synthesize
        emit(f"Synthesizing final report from {len(relevant)} sources...")
        report = synthesize(question, relevant)
    
    # Step 6: Save to DB (Database save is async, so we use asyncio.run)
    try:
        asyncio.run(save_research_log(
            question=question,
            report=report,
            sources_used=len(relevant),
            total_tokens=config.TOTAL_TOKENS_USED
        ))
    except Exception as e:
        print(f"Database save failed: {e}")

    # Return final result which sets the task state to SUCCESS
    result = {
        "status": "Complete",
        "report": report,
        "sources_used": len(relevant),
        "total_tokens_used": config.TOTAL_TOKENS_USED
    }
    redis_client.setex(f"task:{task_id}", 3600, json.dumps({"state": "SUCCESS", "result": result}))
    return result
