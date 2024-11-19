import requests
import json
import time
from pathlib import Path

def test_store_dispute():
    # API endpoint
    url = "http://localhost:8000/api/store-dispute"
    
    # Read sample argument
    conversation = open(Path(__file__).parent / "sample_argument.txt", "r", encoding="utf-8").read()
    
    # Prepare payload
    payload = {
        "text": conversation,
        "party_one_name": "Maya",
        "party_two_name": "Arjun",
        "context1": "my boyfriend doesn't appreciate my achievements",
        "context2": "I'm just so tired all the time"
    }
    
    # Make POST request
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        dispute_id = response.json()['dispute_id']
        print(f"Dispute ID: {dispute_id}")
        
        # Wait for processing
        time.sleep(30)
        
        # Check result
        check_url = f"http://localhost:8000/api/dispute/{dispute_id}"
        result = requests.get(check_url)
        print(f"Result: {result.json()}")

if __name__ == "__main__":
    test_store_dispute() 