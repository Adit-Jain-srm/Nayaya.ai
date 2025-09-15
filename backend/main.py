from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from dotenv import load_dotenv

from api.upload import router as upload_router
from api.document_ai import router as docai_router
from api.vertex_ai import router as vertex_router
from api.rag import router as rag_router
from api.qa import router as qa_router
from services.auth import get_current_user

load_dotenv()

app = FastAPI(
    title="Nayaya.ai Backend API",
    description="AI-powered legal document analysis using Google Cloud",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(docai_router, prefix="/api", tags=["document-ai"])
app.include_router(vertex_router, prefix="/api", tags=["vertex-ai"])
app.include_router(rag_router, prefix="/api", tags=["rag"])
app.include_router(qa_router, prefix="/api", tags=["qa"])

@app.get("/")
async def root():
    return {
        "message": "Nayaya.ai Backend API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nayaya-backend"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )
