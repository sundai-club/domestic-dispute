from database import SessionLocal, Dispute
from tasks import process_dispute
from pathlib import Path
from backend.database import init_db

# Initialize the database before running tests
init_db()
db = SessionLocal()
try:
    dispute = Dispute(
        party_one_name="Maya",
        party_two_name="Arjun",
        context1="my boyfriend doesn't appreciate my achievements",
        context2="I'm just so tired all the time",
        conversation=open(Path(__file__).parent /"sample_arguments" /"sample_argument.txt", "r", encoding="utf-8").read(),
        status="pending"
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    
    # Get the ID and trigger the task
    dispute_id = dispute.id
    print(f"Created dispute with ID: {dispute_id}")
    
    # Trigger the Celery task
    process_dispute.delay(dispute_id)
    
    print("Task triggered - check worker logs")
    print("Wait a few moments then check the database...")
    
    # Wait a bit and check the result
    import time
    time.sleep(30)  # Wait 30 seconds
    
    # Check the result
    updated_dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    print(f"Status: {updated_dispute.status}")
    print(f"Result: {updated_dispute.result}")
    
finally:
    db.close() 