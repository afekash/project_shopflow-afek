# Distributed System Demo

A distributed task processing system demonstrating microservices architecture with Docker Compose.

## Architecture

```
User → Gateway (FastAPI) → Redis (Queue) → Worker (Python)
                              ↑
                              └─ Results stored here
```

**Services:**
- **Gateway**: FastAPI service that accepts HTTP requests and manages tasks
- **Worker**: Python service that processes tasks from the queue
- **Redis**: Message broker and shared state storage

## Running the System

### Start all services

```bash
docker compose up --build
```

### Submit a task

```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"data": "process this data"}'

# Response:
# {
#   "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
#   "status": "submitted",
#   "message": "Task queued for processing"
# }
```

### Get task result

```bash
# Replace with your task_id
curl http://localhost:8000/result/a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Response when completed:
# {
#   "status": "completed",
#   "task_id": "a1b2c3d4-...",
#   "original_data": "process this data",
#   "processed_data": "PROCESS THIS DATA",
#   "processed_at": 1707476408.123,
#   "worker": "worker-service"
# }
```

### Check system stats

```bash
curl http://localhost:8000/stats

# Response:
# {
#   "pending_tasks": 0,
#   "total_results": 5,
#   "message": "System statistics"
# }
```

### View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f worker
docker compose logs -f gateway
```

## Scaling Workers

Run multiple workers to process tasks in parallel:

```bash
docker compose up -d --scale worker=3
```

Submit multiple tasks to see them distributed:

```bash
for i in {1..10}; do
  curl -X POST http://localhost:8000/task \
    -H "Content-Type: application/json" \
    -d "{\"data\": \"task $i\"}"
done
```

Watch the workers process tasks in parallel:

```bash
docker compose logs -f worker
```

## Stopping the System

```bash
# Stop and remove containers
docker compose down

# Stop, remove containers, and remove volumes
docker compose down --volumes
```

## Endpoints

### Gateway Service

- `GET /` - Service information
- `POST /task` - Submit a task
- `GET /result/{task_id}` - Get task result
- `GET /stats` - System statistics
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Key Concepts Demonstrated

1. **Service Discovery**: Services communicate by name (`redis`, not IP addresses)
2. **Asynchronous Processing**: Gateway responds immediately; Worker processes in background
3. **Horizontal Scalability**: Add more workers to increase throughput
4. **Message Queue Pattern**: Redis acts as a task queue
5. **Microservices Architecture**: Each service has a single responsibility

## Real-World Applications

This pattern is used in:
- ETL pipelines (extract, transform, load data)
- Image/video processing systems
- Machine learning inference services
- Email/notification systems
- Web scraping and data collection
- Report generation systems
