from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DocumentType(str, Enum):
    RENTAL_AGREEMENT = "rental_agreement"
    LOAN_CONTRACT = "loan_contract"
    EMPLOYMENT_CONTRACT = "employment_contract"
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    NDA = "nda"
    OTHER = "other"

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETE = "ocr_complete"
    CLASSIFIED = "classified"
    ANALYZED = "analyzed"
    COMPLETE = "complete"
    FAILED = "failed"

class ClauseType(str, Enum):
    PARTIES_INVOLVED = "parties_involved"
    DEFINITIONS = "definitions"
    PURPOSE_SCOPE = "purpose_scope"
    PAYMENT_TERMS = "payment_terms"
    FEES_CHARGES = "fees_charges"
    PENALTIES = "penalties"
    INTEREST = "interest"
    SECURITY_DEPOSIT = "security_deposit"
    REFUND_POLICY = "refund_policy"
    CONTRACT_DURATION = "contract_duration"
    TERMINATION = "termination"
    AUTO_RENEWAL = "auto_renewal"
    EXIT_FEES = "exit_fees"
    WARRANTIES = "warranties"
    OBLIGATIONS = "obligations"
    LIMITATION_LIABILITY = "limitation_liability"
    INDEMNIFICATION = "indemnification"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    DATA_OWNERSHIP = "data_ownership"
    DATA_SHARING = "data_sharing"
    CONFIDENTIALITY = "confidentiality"
    NON_COMPETE = "non_compete"
    IP_RIGHTS = "ip_rights"
    AMENDMENTS = "amendments"
    SEVERABILITY = "severability"

class Citation(BaseModel):
    source: str
    reference: str
    url: Optional[str] = None

class ClauseAnalysis(BaseModel):
    id: str
    clause_type: ClauseType
    original_text: str
    plain_language: str
    risk_level: RiskLevel
    risk_reason: str
    recommendations: List[str]
    citations: Optional[List[Citation]] = []
    confidence_score: Optional[float] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None

class DocumentMetadata(BaseModel):
    file_name: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    user_id: Optional[str] = None
    original_language: Optional[str] = "en"

class DocumentAnalysisResult(BaseModel):
    document_id: str
    metadata: DocumentMetadata
    document_type: DocumentType
    processing_status: ProcessingStatus
    overall_risk: RiskLevel
    clauses: List[ClauseAnalysis]
    key_findings: List[str]
    summary: str
    raw_text: Optional[str] = None
    processed_at: datetime
    processing_time_seconds: Optional[float] = None
    model_versions: Optional[Dict[str, str]] = None

class QARequest(BaseModel):
    document_id: str
    question: str
    user_id: Optional[str] = None

class QAResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    sources: List[str]
    citations: Optional[List[Citation]] = []
    response_time_ms: Optional[int] = None

class UploadResponse(BaseModel):
    success: bool
    document_id: str
    message: str
    upload_url: Optional[str] = None

class ProcessingRequest(BaseModel):
    document_id: str
    options: Optional[Dict[str, Any]] = {}

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
