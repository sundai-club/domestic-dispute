from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from models import HWInputState, OverreactionInputState
from ai import result, async_result, analyze_overreaction  # You'll implement this in ai.py
from database import SessionLocal, Dispute, init_db  # Updated this line
from tasks import process_dispute, process_overreaction  # Add this import
import os
import shutil
from datetime import datetime
from typing import List
from pathlib import Path
import io
from PIL import Image
from PIL.ExifTags import TAGS
import base64
from image_processor import extract_multiple_text

import uvicorn
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

init_db()

UPLOAD_DIR = "images"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/analyze-dispute")
async def analyze_dispute(request: HWInputState):
    try:
        analysis = await async_result(
            conversation=request.conversation,
            person1=request.name1,
            person2=request.name2,
            context = request.context,
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/store-dispute")
async def analyze_dispute(request: HWInputState):
    # Create DB session
    print(f"Request received")
    db = SessionLocal()
    try:
        # Create dispute record
        dispute = Dispute(
            party_one_name=request.party_one_name,
            party_two_name=request.party_two_name,
            context=request.context,
            #context2=request.context2,
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
    print(f"Getting dispute {dispute_id}")
    db = SessionLocal()
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        print(dispute.result)
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        return {
            "status": dispute.status,
            "result": dispute.result,
            "error": dispute.error if dispute.error else None
        }
    finally:
        db.close()

@app.post("/api/upload-image")
async def upload_image(files: List[UploadFile] = File(...)):
    try:
        image_data = []
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Create PIL Image from bytes
            img = Image.open(io.BytesIO(content))
            
            # Get creation time
            creation_time = None
            exif = img.getexif()
            if exif:
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exif.get(tag_id)
                    if tag == 'DateTime':
                        creation_time = datetime.strptime(data, '%Y:%m:%d %H:%M:%S')
                        break
            
            if not creation_time:
                # If no EXIF timestamp, use current time
                creation_time = datetime.now()
            
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format=img.format)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            image_data.append({
                "timestamp": creation_time,
                "base64": img_base64,
                "original_name": file.filename
            })
        
        # Sort by timestamp
        image_data.sort(key=lambda x: x["timestamp"])
        
        # Extract text from sorted images
        conversation_text = extract_multiple_text([d["base64"] for d in image_data])
        
        return {
            "message": f"Successfully processed {len(image_data)} images",
            "conversation": conversation_text
        }
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-overreaction")
async def analyze_overreaction_endpoint(request: OverreactionInputState):
    try:
        analysis = await analyze_overreaction(
            name=request.name,
            context=request.context,
            conversation=request.conversation
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/store-overreaction")
async def store_overreaction(request: OverreactionInputState):
    db = SessionLocal()
    try:
        # Create overreaction analysis record
        dispute = Dispute(
            party_one_name=request.name,
            party_two_name="N/A",  # Single player mode
            context=request.context,  # Add context here
            conversation=request.conversation,
            status="pending",
            analysis_type="overreaction"
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)
        
        # Start background task
        process_overreaction.delay(dispute.id)
        return {"message": "Analysis started", "dispute_id": dispute.id}
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
