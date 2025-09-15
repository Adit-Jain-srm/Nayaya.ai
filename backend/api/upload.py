from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from google.cloud import storage
from google.cloud import firestore
import uuid
import os
from datetime import datetime
from typing import Optional
import aiofiles

from models.document import UploadResponse, DocumentMetadata, ProcessingStatus
from services.auth import get_current_user_optional

router = APIRouter()

# Initialize Google Cloud clients
storage_client = storage.Client()
firestore_client = firestore.Client()

BUCKET_NAME = os.getenv("CLOUD_STORAGE_BUCKET", "nayaya-documents")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "documents")

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    document: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Upload a legal document for processing.
    Supports PDF, DOC, DOCX files up to 10MB.
    """
    
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    if document.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOC, or DOCX files."
        )
    
    # Validate file size (10MB limit)
    content = await document.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB in bytes
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit."
        )
    
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Create file path in Cloud Storage
        file_extension = document.filename.split('.')[-1].lower()
        blob_name = f"uploads/{document_id}.{file_extension}"
        
        # Upload to Cloud Storage
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        # Reset file pointer
        await document.seek(0)
        content = await document.read()
        
        blob.upload_from_string(
            content,
            content_type=document.content_type
        )
        
        # Create document metadata
        metadata = DocumentMetadata(
            file_name=document.filename,
            file_size=len(content),
            mime_type=document.content_type,
            upload_timestamp=datetime.utcnow(),
            user_id=current_user.get("user_id") if current_user else None
        )
        
        # Store metadata in Firestore
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(document_id)
        doc_data = {
            "document_id": document_id,
            "metadata": metadata.dict(),
            "processing_status": ProcessingStatus.UPLOADED.value,
            "gcs_path": blob_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        doc_ref.set(doc_data)
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            message="Document uploaded successfully and queued for processing."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/upload/{document_id}/status")
async def get_upload_status(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get the processing status of an uploaded document."""
    
    try:
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check user access (if auth is enabled)
        if current_user and doc_data.get("metadata", {}).get("user_id"):
            if doc_data["metadata"]["user_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "document_id": document_id,
            "status": doc_data.get("processing_status"),
            "uploaded_at": doc_data.get("created_at"),
            "last_updated": doc_data.get("updated_at"),
            "file_name": doc_data.get("metadata", {}).get("file_name")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
        )
