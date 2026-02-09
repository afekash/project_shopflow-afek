from fastapi import FastAPI
from pydantic import BaseModel
import datetime

app = FastAPI(title="Simple API Demo")

# In-memory data storage
items = []

class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the Simple API!",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": {
            "GET /": "This message",
            "GET /health": "Health check",
            "GET /items": "List all items",
            "POST /items": "Create an item",
            "GET /items/{item_id}": "Get specific item",
            "GET /docs": "Interactive API documentation"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "simple-api"
    }

@app.get("/items")
def list_items():
    """List all items"""
    return {
        "items": items,
        "count": len(items),
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/items")
def create_item(item: Item):
    """Create a new item"""
    item_dict = item.model_dump()
    item_dict["id"] = len(items) + 1
    item_dict["created_at"] = datetime.datetime.now().isoformat()
    items.append(item_dict)
    return item_dict

@app.get("/items/{item_id}")
def get_item(item_id: int):
    """Get a specific item by ID"""
    for item in items:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found", "item_id": item_id}

@app.get("/info")
def info():
    """Service information"""
    return {
        "service": "simple-api",
        "description": "A simple FastAPI demo application",
        "features": [
            "RESTful API",
            "In-memory storage",
            "Auto-generated documentation",
            "JSON responses"
        ],
        "tech_stack": {
            "framework": "FastAPI",
            "language": "Python 3.11",
            "server": "Uvicorn"
        }
    }
