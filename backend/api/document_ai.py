from fastapi import APIRouter, HTTPException, Depends
from google.cloud import documentai
from google.cloud import storage
from google.cloud import firestore
import os
from typing import Optional

from models.document import ProcessingRequest, ProcessingStatus
from services.auth import get_current_user_optional

router = APIRouter()

# Initialize clients
docai_client = documentai.DocumentProcessorServiceClient()
storage_client = storage.Client()
firestore_client = firestore.Client()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("DOCUMENT_AI_LOCATION", "us")
PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
BUCKET_NAME = os.getenv("CLOUD_STORAGE_BUCKET", "nayaya-documents")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "documents")

# Build processor path
PROCESSOR_NAME = docai_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)

@router.post("/process-ocr")
async def process_document_ocr(
    request: ProcessingRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Process document with Google Cloud Document AI for OCR and layout analysis.
    """
    
    try:
        # Get document from Firestore
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(request.document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check user access
        if current_user and doc_data.get("metadata", {}).get("user_id"):
            if doc_data["metadata"]["user_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Update status to processing
        doc_ref.update({
            "processing_status": ProcessingStatus.PROCESSING.value,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        # Get document from Cloud Storage
        gcs_path = doc_data.get("gcs_path")
        if not gcs_path:
            raise HTTPException(status_code=400, detail="Document path not found")
        
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(gcs_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Document file not found in storage")
        
        # Download document content
        document_content = blob.download_as_bytes()
        
        # Determine MIME type
        mime_type = doc_data.get("metadata", {}).get("mime_type", "application/pdf")
        
        # Create Document AI request
        raw_document = documentai.RawDocument(
            content=document_content,
            mime_type=mime_type
        )
        
        # Configure processing options
        process_options = documentai.ProcessOptions(
            ocr_config=documentai.OcrConfig(
                enable_native_pdf_parsing=True,
                enable_image_quality_scores=True,
                enable_symbol=True,
                compute_style_info=True,
            )
        )
        
        request_docai = documentai.ProcessRequest(
            name=PROCESSOR_NAME,
            raw_document=raw_document,
            process_options=process_options
        )
        
        # Process document
        result = docai_client.process_document(request=request_docai)
        document = result.document
        
        # Extract text and structure
        extracted_data = {
            "raw_text": document.text,
            "pages": [],
            "entities": [],
            "paragraphs": [],
            "tables": []
        }
        
        # Extract page information
        for page in document.pages:
            page_info = {
                "page_number": page.page_number,
                "dimensions": {
                    "width": page.dimension.width,
                    "height": page.dimension.height,
                    "unit": page.dimension.unit
                },
                "blocks": [],
                "paragraphs": [],
                "lines": [],
                "tokens": []
            }
            
            # Extract blocks
            for block in page.blocks:
                block_text = get_text_from_layout(document.text, block.layout)
                page_info["blocks"].append({
                    "text": block_text,
                    "confidence": block.layout.confidence if block.layout.confidence else 0.0
                })
            
            # Extract paragraphs
            for paragraph in page.paragraphs:
                para_text = get_text_from_layout(document.text, paragraph.layout)
                page_info["paragraphs"].append({
                    "text": para_text,
                    "confidence": paragraph.layout.confidence if paragraph.layout.confidence else 0.0
                })
                
                # Also add to global paragraphs list
                extracted_data["paragraphs"].append({
                    "text": para_text,
                    "page": page.page_number,
                    "confidence": paragraph.layout.confidence if paragraph.layout.confidence else 0.0
                })
            
            extracted_data["pages"].append(page_info)
        
        # Extract entities (if available)
        for entity in document.entities:
            extracted_data["entities"].append({
                "type": entity.type_,
                "mention_text": entity.mention_text,
                "confidence": entity.confidence if entity.confidence else 0.0,
                "normalized_value": entity.normalized_value.text if entity.normalized_value else None
            })
        
        # Extract tables
        for page in document.pages:
            for table in page.tables:
                table_data = {
                    "page": page.page_number,
                    "rows": []
                }
                
                for row in table.body_rows:
                    row_data = []
                    for cell in row.cells:
                        cell_text = get_text_from_layout(document.text, cell.layout)
                        row_data.append(cell_text.strip())
                    table_data["rows"].append(row_data)
                
                extracted_data["tables"].append(table_data)
        
        # Update document in Firestore
        doc_ref.update({
            "processing_status": ProcessingStatus.OCR_COMPLETE.value,
            "extracted_data": extracted_data,
            "ocr_confidence": document.pages[0].blocks[0].layout.confidence if document.pages and document.pages[0].blocks else 0.0,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        return {
            "success": True,
            "document_id": request.document_id,
            "message": "OCR processing completed successfully",
            "extracted_text_length": len(extracted_data["raw_text"]),
            "pages_processed": len(extracted_data["pages"]),
            "entities_found": len(extracted_data["entities"]),
            "tables_found": len(extracted_data["tables"])
        }
        
    except HTTPException:
        # Update status to failed
        doc_ref.update({
            "processing_status": ProcessingStatus.FAILED.value,
            "error_message": "OCR processing failed",
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        raise
    except Exception as e:
        # Update status to failed
        doc_ref.update({
            "processing_status": ProcessingStatus.FAILED.value,
            "error_message": str(e),
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )

def get_text_from_layout(document_text: str, layout) -> str:
    """Extract text from a layout element using text segments."""
    if not layout.text_anchor:
        return ""
    
    text = ""
    for segment in layout.text_anchor.text_segments:
        start_index = int(segment.start_index) if segment.start_index else 0
        end_index = int(segment.end_index) if segment.end_index else len(document_text)
        text += document_text[start_index:end_index]
    
    return text

@router.get("/ocr-result/{document_id}")
async def get_ocr_result(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get the OCR processing result for a document."""
    
    try:
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check user access
        if current_user and doc_data.get("metadata", {}).get("user_id"):
            if doc_data["metadata"]["user_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        extracted_data = doc_data.get("extracted_data")
        if not extracted_data:
            raise HTTPException(status_code=404, detail="OCR data not found. Process the document first.")
        
        return {
            "document_id": document_id,
            "status": doc_data.get("processing_status"),
            "extracted_data": extracted_data,
            "ocr_confidence": doc_data.get("ocr_confidence", 0.0),
            "processed_at": doc_data.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OCR result: {str(e)}"
        )
