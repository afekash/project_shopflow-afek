import redis
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Connect to Redis using service name
r = redis.Redis(host='redis', port=6379, decode_responses=True)

def process_task(task_data):
    """
    Simulate task processing
    In a real system, this would:
    - Transform data
    - Make API calls
    - Run computations
    - Store results in a database
    """
    logger.info(f"Processing task {task_data['id']}")
    
    # Simulate work (e.g., data transformation, API call, computation)
    time.sleep(2)
    
    # Generate result
    result = {
        "status": "completed",
        "task_id": task_data['id'],
        "original_data": task_data['data'],
        "processed_data": task_data['data'].upper(),  # Simple transformation
        "processed_at": time.time(),
        "worker": "worker-service"
    }
    
    return result

def main():
    """Main worker loop"""
    logger.info("Worker starting... waiting for tasks from Redis")
    
    while True:
        try:
            # Block until a task is available (BRPOP with 1 second timeout)
            task = r.brpop("tasks", timeout=1)
            
            if task:
                # task is a tuple: (key, value)
                task_json = task[1]
                task_data = json.loads(task_json)
                
                logger.info(f"Received task: {task_data['id']}")
                
                # Process the task
                result = process_task(task_data)
                
                # Store result in Redis
                r.set(f"result:{task_data['id']}", json.dumps(result))
                
                logger.info(f"Task {task_data['id']} completed and result stored")
            
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
