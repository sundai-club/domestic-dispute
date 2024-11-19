from database import SessionLocal, Dispute

# Create a database session
db = SessionLocal()

# Query the most recent dispute
dispute = db.query(Dispute).order_by(Dispute.id.desc()).first()

# Print the details
print(f"ID: {dispute.id}")
print(f"Status: {dispute.status}")
print(f"Result: {dispute.result}")
#print(f"Error: {dispute.error if hasattr(dispute, 'error') else 'None'}")