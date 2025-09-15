from fastapi import APIRouter, HTTPException, Depends
from google.cloud import aiplatform
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.language_models import TextEmbeddingModel
import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.document import ProcessingRequest, ProcessingStatus, ClauseType, RiskLevel, ClauseAnalysis, Citation
from services.auth import get_current_user_optional

router = APIRouter()

# Initialize clients
firestore_client = firestore.Client()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_AI_MODEL_NAME", "gemini-1.5-pro")
EMBEDDING_MODEL_NAME = os.getenv("VERTEX_AI_EMBEDDING_MODEL", "textembedding-gecko@003")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "documents")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

@router.post("/classify-clauses")
async def classify_document_clauses(
    request: ProcessingRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Classify document clauses using Vertex AI Gemini model.
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
        
        # Check if OCR is complete
        if doc_data.get("processing_status") != ProcessingStatus.OCR_COMPLETE.value:
            raise HTTPException(
                status_code=400, 
                detail="Document must complete OCR processing first"
            )
        
        # Update status
        doc_ref.update({
            "processing_status": ProcessingStatus.PROCESSING.value,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        # Get extracted text
        extracted_data = doc_data.get("extracted_data", {})
        raw_text = extracted_data.get("raw_text", "")
        paragraphs = extracted_data.get("paragraphs", [])
        
        if not raw_text:
            raise HTTPException(status_code=400, detail="No text found in document")
        
        # Initialize Gemini model
        model = GenerativeModel(MODEL_NAME)
        
        # Classify document type first
        document_type = await classify_document_type(model, raw_text)
        
        # Segment and classify clauses
        clauses = await segment_and_classify_clauses(model, raw_text, paragraphs)
        
        # Update document with classification results
        doc_ref.update({
            "processing_status": ProcessingStatus.CLASSIFIED.value,
            "document_type": document_type,
            "clauses": [clause.dict() for clause in clauses],
            "classification_timestamp": datetime.utcnow(),
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        return {
            "success": True,
            "document_id": request.document_id,
            "message": "Clause classification completed successfully",
            "document_type": document_type,
            "clauses_found": len(clauses),
            "clause_types": list(set([clause.clause_type.value for clause in clauses]))
        }
        
    except HTTPException:
        # Update status to failed
        doc_ref.update({
            "processing_status": ProcessingStatus.FAILED.value,
            "error_message": "Clause classification failed",
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
            detail=f"Clause classification failed: {str(e)}"
        )

async def classify_document_type(model: GenerativeModel, text: str) -> str:
    """Classify the type of legal document."""
    
    prompt = f"""
    Analyze this legal document and classify it into one of these categories:
    - rental_agreement
    - loan_contract
    - employment_contract
    - terms_of_service
    - privacy_policy
    - nda
    - other
    
    Document text (first 2000 characters):
    {text[:2000]}
    
    Respond with ONLY the category name, nothing else.
    """
    
    response = model.generate_content(prompt)
    document_type = response.text.strip().lower()
    
    # Validate response
    valid_types = ["rental_agreement", "loan_contract", "employment_contract", 
                   "terms_of_service", "privacy_policy", "nda", "other"]
    
    if document_type not in valid_types:
        document_type = "other"
    
    return document_type

async def segment_and_classify_clauses(
    model: GenerativeModel, 
    text: str, 
    paragraphs: List[Dict]
) -> List[ClauseAnalysis]:
    """Segment document into clauses and classify each one."""
    
    # Create clause taxonomy for the prompt
    clause_types = [ct.value for ct in ClauseType]
    
    prompt = f"""
    You are a legal document analysis expert. Analyze this document and identify distinct legal clauses.
    
    For each clause you identify, provide:
    1. The exact text of the clause
    2. The clause type from this list: {', '.join(clause_types)}
    3. A plain-language explanation (Grade 8 reading level, max 120 words)
    4. Risk level: high, medium, or low
    5. Explanation of why this risk level was assigned
    6. 2-3 specific recommendations for the reader
    
    Document text:
    {text}
    
    Respond in this JSON format:
    {{
        "clauses": [
            {{
                "original_text": "exact clause text here",
                "clause_type": "clause_type_from_list",
                "plain_language": "simple explanation here",
                "risk_level": "high|medium|low",
                "risk_reason": "why this risk level",
                "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
            }}
        ]
    }}
    
    Only include substantive legal clauses, not headers or signatures.
    """
    
    response = model.generate_content(prompt)
    
    try:
        # Parse JSON response
        result = json.loads(response.text)
        clauses = []
        
        for i, clause_data in enumerate(result.get("clauses", [])):
            # Validate clause type
            clause_type = clause_data.get("clause_type", "other")
            if clause_type not in [ct.value for ct in ClauseType]:
                clause_type = "other"
            
            # Validate risk level
            risk_level = clause_data.get("risk_level", "medium")
            if risk_level not in [rl.value for rl in RiskLevel]:
                risk_level = "medium"
            
            clause = ClauseAnalysis(
                id=f"clause_{i+1}",
                clause_type=ClauseType(clause_type),
                original_text=clause_data.get("original_text", "")[:2000],  # Limit length
                plain_language=clause_data.get("plain_language", "")[:500],  # Limit length
                risk_level=RiskLevel(risk_level),
                risk_reason=clause_data.get("risk_reason", "")[:300],  # Limit length
                recommendations=clause_data.get("recommendations", [])[:3],  # Limit to 3
                confidence_score=0.8  # Default confidence
            )
            
            clauses.append(clause)
        
        return clauses
        
    except json.JSONDecodeError as e:
        # Fallback: create a single clause with the full document
        return [
            ClauseAnalysis(
                id="clause_1",
                clause_type=ClauseType.OTHER,
                original_text=text[:2000],
                plain_language="This document contains legal terms that require careful review. Please consult with a legal professional for detailed analysis.",
                risk_level=RiskLevel.MEDIUM,
                risk_reason="Unable to automatically parse document structure.",
                recommendations=[
                    "Review the entire document carefully",
                    "Consult with a qualified attorney",
                    "Ask questions about unclear terms"
                ],
                confidence_score=0.3
            )
        ]

@router.post("/analyze")
async def analyze_document(
    request: ProcessingRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Generate comprehensive analysis including risk assessment and summary.
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
        
        # Check if classification is complete
        if doc_data.get("processing_status") != ProcessingStatus.CLASSIFIED.value:
            raise HTTPException(
                status_code=400, 
                detail="Document must complete clause classification first"
            )
        
        # Update status
        doc_ref.update({
            "processing_status": ProcessingStatus.PROCESSING.value,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        # Get clauses
        clauses_data = doc_data.get("clauses", [])
        clauses = [ClauseAnalysis(**clause) for clause in clauses_data]
        
        if not clauses:
            raise HTTPException(status_code=400, detail="No clauses found in document")
        
        # Initialize Gemini model
        model = GenerativeModel(MODEL_NAME)
        
        # Generate overall summary and key findings
        summary_data = await generate_summary_and_findings(model, clauses, doc_data.get("document_type", "other"))
        
        # Calculate overall risk
        overall_risk = calculate_overall_risk(clauses)
        
        # Update document with final analysis
        analysis_result = {
            "processing_status": ProcessingStatus.ANALYZED.value,
            "overall_risk": overall_risk,
            "summary": summary_data["summary"],
            "key_findings": summary_data["key_findings"],
            "analysis_timestamp": datetime.utcnow(),
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.update(analysis_result)
        
        return {
            "success": True,
            "document_id": request.document_id,
            "message": "Document analysis completed successfully",
            "overall_risk": overall_risk,
            "summary": summary_data["summary"],
            "key_findings": summary_data["key_findings"],
            "clauses_analyzed": len(clauses)
        }
        
    except HTTPException:
        # Update status to failed
        doc_ref.update({
            "processing_status": ProcessingStatus.FAILED.value,
            "error_message": "Document analysis failed",
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
            detail=f"Document analysis failed: {str(e)}"
        )

async def generate_summary_and_findings(
    model: GenerativeModel, 
    clauses: List[ClauseAnalysis], 
    document_type: str
) -> Dict[str, Any]:
    """Generate overall summary and key findings."""
    
    # Prepare clause summaries for the prompt
    clause_summaries = []
    for clause in clauses:
        clause_summaries.append(f"- {clause.clause_type.value}: {clause.plain_language} (Risk: {clause.risk_level.value})")
    
    prompt = f"""
    Analyze this {document_type.replace('_', ' ')} document and provide:
    
    1. A comprehensive summary (2-3 sentences) of what this document is about and its main purpose
    2. 3-5 key findings that highlight the most important things the reader should know
    
    Clause Analysis:
    {chr(10).join(clause_summaries)}
    
    Respond in this JSON format:
    {{
        "summary": "comprehensive summary here",
        "key_findings": [
            "key finding 1",
            "key finding 2", 
            "key finding 3"
        ]
    }}
    
    Focus on practical implications for the person signing this document.
    """
    
    response = model.generate_content(prompt)
    
    try:
        result = json.loads(response.text)
        return {
            "summary": result.get("summary", "This document contains legal terms that require review."),
            "key_findings": result.get("key_findings", ["Document requires legal review"])
        }
    except json.JSONDecodeError:
        # Fallback
        return {
            "summary": f"This {document_type.replace('_', ' ')} contains multiple clauses with varying risk levels that require careful consideration.",
            "key_findings": [
                f"Document contains {len(clauses)} distinct clauses",
                f"Risk levels range from {min(c.risk_level.value for c in clauses)} to {max(c.risk_level.value for c in clauses)}",
                "Professional legal review recommended"
            ]
        }

def calculate_overall_risk(clauses: List[ClauseAnalysis]) -> str:
    """Calculate overall document risk based on clause risk levels."""
    
    if not clauses:
        return "medium"
    
    risk_scores = {"high": 3, "medium": 2, "low": 1}
    total_score = sum(risk_scores[clause.risk_level.value] for clause in clauses)
    average_score = total_score / len(clauses)
    
    # Determine overall risk
    if average_score >= 2.5:
        return "high"
    elif average_score >= 1.5:
        return "medium"
    else:
        return "low"

@router.get("/analysis/{document_id}")
async def get_analysis_result(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get the complete analysis result for a document."""
    
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
        
        if doc_data.get("processing_status") not in [ProcessingStatus.ANALYZED.value, ProcessingStatus.COMPLETE.value]:
            raise HTTPException(status_code=404, detail="Analysis not complete. Process the document first.")
        
        # Build response
        clauses_data = doc_data.get("clauses", [])
        clauses = [ClauseAnalysis(**clause) for clause in clauses_data]
        
        return {
            "document_id": document_id,
            "file_name": doc_data.get("metadata", {}).get("file_name", ""),
            "document_type": doc_data.get("document_type", "other"),
            "overall_risk": doc_data.get("overall_risk", "medium"),
            "summary": doc_data.get("summary", ""),
            "key_findings": doc_data.get("key_findings", []),
            "clauses": [clause.dict() for clause in clauses],
            "processed_at": doc_data.get("analysis_timestamp"),
            "status": doc_data.get("processing_status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis result: {str(e)}"
        )
