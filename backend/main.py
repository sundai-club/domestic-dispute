from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from models import DisputeRequest
from ai import result  # You'll implement this in ai.py

import uvicorn
app = FastAPI()

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
