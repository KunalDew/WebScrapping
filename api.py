import os
import json
import asyncio
import time
import uuid
from fastapi import FastAPI, Query, Depends, HTTPException, Security, Request, BackgroundTasks
from fastapi.security.api_key import APIKeyQuery
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import redis
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from dotenv import load_dotenv

load_dotenv()

from researcher import run_research_task
from database import get_research_logs

API_KEY = os.getenv("BACKEND_API_KEY", "dev-secret-key")
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

# GCP Cloud Tasks Configuration
GCP_PROJECT = os.getenv("GCP_PROJECT", "your-project-id")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GCP_QUEUE = os.getenv("GCP_QUEUE", "research-queue")
# The URL of this API when deployed (e.g., https://api-xyz.a.run.app)
WORKER_URL = os.getenv("WORKER_URL", "http://localhost:8000")

# Only initialize Cloud Tasks if we have credentials (skip for local if not setup)
try:
    tasks_client = tasks_v2.CloudTasksClient()
    queue_path = tasks_client.queue_path(GCP_PROJECT, GCP_LOCATION, GCP_QUEUE)
except Exception as e:
    print(f"Warning: Cloud Tasks client could not be initialized: {e}")
    tasks_client = None
    queue_path = None

def verify_api_key(api_key: str = Security(api_key_query)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate API key")
    return api_key

app = FastAPI(title="Web Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task_id: str
    question: str

async def redis_task_generator(task_id: str):
    """
    Polls the task state from Redis and streams updates via SSE.
    """
    def emit(payload: dict):
        return json.dumps(payload)
        
    last_message = ""
    last_emit_time = time.time()
    
    yield emit({"status": "Started", "task_id": task_id})
    
    while True:
        task_data_raw = redis_client.get(f"task:{task_id}")
        if not task_data_raw:
            await asyncio.sleep(0.5)
            continue
            
        task_data = json.loads(task_data_raw)
        state = task_data.get("state")
        
        if state == 'PROGRESS':
            current_message = task_data.get("info", {}).get("message", "")
            if current_message != last_message:
                yield emit(task_data.get("info", {}))
                last_message = current_message
                last_emit_time = time.time()
            elif time.time() - last_emit_time > 15:
                yield emit({"status": "Heartbeat", "message": current_message})
                last_emit_time = time.time()
        
        elif state == 'SUCCESS':
            yield emit(task_data.get("result", {}))
            break
            
        elif state == 'FAILURE':
            yield emit(task_data.get("result", {}))
            break
            
        await asyncio.sleep(0.5)

@app.get("/api/research")
async def api_research(
    question: str = Query(..., min_length=3),
    api_key: str = Depends(verify_api_key)
):
    task_id = str(uuid.uuid4())
    
    # Write initial state
    redis_client.setex(f"task:{task_id}", 3600, json.dumps({"state": "PROGRESS", "info": {"message": "Queued for processing..."}}))
    
    payload = {"task_id": task_id, "question": question}
    
    if tasks_client and WORKER_URL != "http://localhost:8000":
        # Create Cloud Task
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{WORKER_URL}/api/internal/worker?api_key={API_KEY}",
                "headers": {"Content-type": "application/json"},
                "body": json.dumps(payload).encode(),
            }
        }
        
        # Add task name for deduplication/cancellation
        task["name"] = tasks_client.task_path(GCP_PROJECT, GCP_LOCATION, GCP_QUEUE, task_id)
        
        try:
            tasks_client.create_task(request={"parent": queue_path, "task": task})
        except Exception as e:
            redis_client.setex(f"task:{task_id}", 3600, json.dumps({"state": "FAILURE", "result": {"status": "error", "error": f"Failed to enqueue task: {e}"}}))
    else:
        # Fallback for local testing if Cloud Tasks is not set up
        print("Cloud Tasks not configured or running locally. Using asyncio.create_task.")
        asyncio.create_task(asyncio.to_thread(run_research_task, task_id, question))
    
    return EventSourceResponse(redis_task_generator(task_id))

@app.post("/api/internal/worker")
def internal_worker(request: TaskRequest, api_key: str = Depends(verify_api_key)):
    """
    Internal endpoint called by Cloud Tasks to execute the background job.
    """
    try:
        run_research_task(request.task_id, request.question)
        return {"status": "ok"}
    except Exception as e:
        # Errors are already written to Redis inside run_research_task
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research/{task_id}/stop")
async def stop_research(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    # Set cancel flag in Redis
    redis_client.setex(f"task:{task_id}:cancel", 3600, "1")
    
    # Try to cancel in Cloud Tasks if it hasn't started yet
    if tasks_client:
        task_name = tasks_client.task_path(GCP_PROJECT, GCP_LOCATION, GCP_QUEUE, task_id)
        try:
            tasks_client.delete_task(name=task_name)
        except Exception:
            pass # Task might already be running or deleted
            
    return {"status": "ok", "message": "Task cancellation requested"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/logs")
async def api_logs(
    limit: int = 50,
    api_key: str = Depends(verify_api_key)
):
    try:
        logs = await get_research_logs(limit=limit)
        return {"status": "ok", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
