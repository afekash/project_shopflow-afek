from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import uuid
import json

app = FastAPI(title="Gateway Service")

# Connect to Redis using service name
r = redis.Redis(host='redis', port=6379, decode_responses=True)

class Task(BaseModel):
    data: str

@app.get("/")
def read_root():
    """Gateway service information"""
    return {
        "service": "Gateway",
        "status": "running",
        "description": "Task submission and result retrieval service",
        "endpoints": {
            "POST /task": "Submit a task for processing",
            "GET /result/{task_id}": "Get task result",
            "GET /stats": "Get system statistics"
        }
    }

@app.post("/task")
def create_task(task: Task):
    """Submit a task for processing"""
    task_id = str(uuid.uuid4())
    task_payload = {
        "id": task_id,
        "data": task.data,
        "status": "pending"
    }
    
    # Push task to Redis list (queue)
    r.lpush("tasks", json.dumps(task_payload))
    
    # Store initial status
    r.set(f"result:{task_id}", json.dumps({"status": "pending"}))
    
    return {
        "task_id": task_id,
        "status": "submitted",
        "message": "Task queued for processing"
    }

@app.get("/result/{task_id}")
def get_result(task_id: str):
    """Get the result of a processed task"""
    result = r.get(f"result:{task_id}")
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return json.loads(result)

@app.get("/stats")
def get_stats():
    """Get system statistics"""
    pending_tasks = r.llen("tasks")
    all_results = list(r.scan_iter("result:*"))
    
    return {
        "pending_tasks": pending_tasks,
        "total_results": len(all_results),
        "message": "System statistics"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {str(e)}")
