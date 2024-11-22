import os
import subprocess
import time
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

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

def wait_for_server(max_attempts=10):
    import requests
    for attempt in range(max_attempts):
        try:
            requests.get('http://localhost:8000')
            print("FastAPI server is ready!")
            return True
        except requests.ConnectionError:
            print(f"Waiting for FastAPI server (attempt {attempt + 1}/{max_attempts})...")
            time.sleep(1)
    return False

def run_all():
    # Start Redis
    print("Starting Redis server...")
    redis_process = subprocess.Popen(['redis-server'])
    
    # Wait for Redis to be ready
    if not wait_for_redis():
        print("Redis failed to start!")
        redis_process.terminate()
        return
    
    # Start FastAPI server
    print("Starting FastAPI server...")
    fastapi_env = {
        **os.environ,
        'PYTHONPATH': str(project_root)
    }
    fastapi_process = subprocess.Popen([
        'uvicorn',
        'backend.main:app',
        '--port',
        '8000'
    ], env=fastapi_env)
    
    # Wait for FastAPI to be ready
    if not wait_for_server():
        print("FastAPI server failed to start!")
        fastapi_process.terminate()
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
        'tasks',
        'worker',
        '--loglevel=INFO'
    ], env=celery_env)
    
    try:
        # Run the test task
        print("\nRunning test task...")
        test_env = {
            **os.environ,
            'PYTHONPATH': str(project_root)
        }
        subprocess.run([
            'python',
            '-m',
            'backend.test_api'
        ], env=test_env, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Test failed with exit code: {e.returncode}")
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    finally:
        # Cleanup
        print("\nCleaning up processes...")
        fastapi_process.terminate()
        celery_process.terminate()
        redis_process.terminate()
        
        # Wait for processes to terminate
        fastapi_process.wait(timeout=5)
        celery_process.wait(timeout=5)
        redis_process.wait(timeout=5)
        print("Cleanup complete!")

if __name__ == "__main__":
    run_all()