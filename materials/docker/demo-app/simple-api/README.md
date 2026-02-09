# Simple API Demo

A minimal FastAPI application demonstrating Docker basics.

## Features

- RESTful API with GET and POST endpoints
- In-memory storage
- Auto-generated documentation
- Health check endpoint

## Running with Docker

### Build the image

```bash
docker build -t simple-api:latest .
```

### Run the container

```bash
docker run -d -p 8000:8000 --name simple-api simple-api:latest
```

### Test the API

```bash
# Root endpoint
curl http://localhost:8000

# Health check
curl http://localhost:8000/health

# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Docker", "description": "Container platform"}'

# List items
curl http://localhost:8000/items

# Interactive docs
open http://localhost:8000/docs
```

## Stopping the container

```bash
docker stop simple-api
docker rm simple-api
```

## Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /items` - List all items
- `POST /items` - Create a new item
- `GET /items/{item_id}` - Get specific item
- `GET /info` - Service information
- `GET /docs` - Interactive API documentation (Swagger UI)
