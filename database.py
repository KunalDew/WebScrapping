import os
import datetime
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

# Fallback to local MongoDB if not provided (useful for local dev)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Global client for persistent FastAPI event loop
client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
logs_collection = client.research_agent.research_logs

async def save_research_log(question: str, report: str, sources_used: int, total_tokens: int):
    """Save the full research input, output, and metrics to the database."""
    log_entry = {
        "timestamp": datetime.datetime.utcnow(),
        "question": question,
        "report": report,
        "sources_used": sources_used,
        "total_tokens_used": total_tokens,
    }
    
    # Create an isolated client for this task so it binds to Cloud Tasks's temporary asyncio loop
    temp_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
    try:
        await temp_client.research_agent.research_logs.insert_one(log_entry)
        print(f"💾 Saved log to database for question: {question}")
    except Exception as e:
        print(f"⚠ Failed to save log to database: {e}")
    finally:
        # We MUST close the client so its background threads stop before asyncio.run() closes the loop!
        temp_client.close()

async def get_research_logs(limit: int = 50):
    """Fetch the most recent research logs from the database."""
    cursor = logs_collection.find().sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    # Convert ObjectId and datetime to JSON serializable strings
    for log in logs:
        log["_id"] = str(log["_id"])
        log["timestamp"] = log["timestamp"].isoformat()
        
    return logs
