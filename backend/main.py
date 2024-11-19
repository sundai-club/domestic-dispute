from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from models import DisputeRequest
from ai import result  # You'll implement this in ai.py
from database import SessionLocal, Dispute, init_db  # Updated this line
from tasks import process_dispute  # Add this import

import uvicorn
app = FastAPI()
init_db()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/analyze-dispute")
async def analyze_dispute(request: DisputeRequest):
    try:
        person1 = {
            "name":request.party_one_name,
            "context":request.context1
        }
        person2 = {
            "name":request.party_two_name,
            "context":request.context2
        }
        analysis = await result(
            conversation=request.text,
            person1=person1,
            person2= person2,
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/store-dispute")
async def analyze_dispute(request: DisputeRequest):
    # Create DB session
    db = SessionLocal()
    try:
        # Create dispute record
        dispute = Dispute(
            party_one_name=request.party_one_name,
            party_two_name=request.party_two_name,
            context1=request.context1,
            context2=request.context2,
            conversation=request.text,
            status="pending"
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)
        # Start background task
        process_dispute.delay(dispute.id)
        print(f"Dispute {dispute.id} started")
        return {"message": "Analysis started", "dispute_id": dispute.id}
    finally:
        db.close()

@app.get("/api/dispute/{dispute_id}")
async def get_dispute(dispute_id: int):
    db = SessionLocal()
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        return {
            "status": dispute.status,
            "result": dispute.result,
            "error": dispute.error if dispute.error else None
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
