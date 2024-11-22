import os
import subprocess
import time
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def is_redis_running():
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379)
        client.ping()
        return True
    except redis.ConnectionError:
        return False

def wait_for_redis(max_attempts=10):
    import redis
    client = redis.Redis(host='localhost', port=6379)
    
    for attempt in range(max_attempts):
        try:
            client.ping()
            print("Redis is ready!")
            return True
        except redis.ConnectionError:
            print(f"Waiting for Redis (attempt {attempt + 1}/{max_attempts})...")
            time.sleep(1)
    
    return False

def start_services():
    # Check if Redis is already running
    print("Checking Redis server...")
    if is_redis_running():
        print("Redis is already running!")
        redis_process = None
    else:
        # Start Redis
        print("Starting Redis server...")
        redis_process = subprocess.Popen(['redis-server'])
        
        # Wait for Redis to be ready
        if not wait_for_redis():
            print("Redis failed to start!")
            if redis_process:
                redis_process.terminate()
            return
    
    # Start Celery worker
    print("Starting Celery worker...")
    celery_env = {
        **os.environ,
        'PYTHONPATH': str(project_root)
    }
    celery_process = subprocess.Popen([
        'celery',
        '-A',
        'backend.tasks',
        'worker',
        '--loglevel=INFO'
    ], env=celery_env)
    
    # Start FastAPI server
    print("Starting FastAPI server...")
    fastapi_env = {
        **os.environ,
        'PYTHONPATH': str(project_root)
    }
    fastapi_process = subprocess.Popen([
        'uvicorn',
        'backend.main:app',
        '--reload',
        '--port',
        '8000'
    ], env=fastapi_env)
    
    try:
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
    finally:
        # Cleanup
        if redis_process:
            redis_process.terminate()
        celery_process.terminate()
        fastapi_process.terminate()
        
        # Wait for processes to terminate
        if redis_process:
            redis_process.wait(timeout=5)
        celery_process.wait(timeout=5)
        fastapi_process.wait(timeout=5)
        print("All services stopped!")

if __name__ == "__main__":
    start_services() 