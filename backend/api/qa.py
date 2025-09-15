from fastapi import APIRouter, HTTPException, Depends
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from typing import List, Dict, Any, Optional
import json
import time

from models.document import QARequest, QAResponse, Citation
from services.auth import get_current_user_optional
from api.rag import search_knowledge_base, search_legal_corpus

router = APIRouter()

# Initialize clients
firestore_client = firestore.Client()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_AI_MODEL_NAME", "gemini-1.5-pro")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "documents")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

@router.post("/qa", response_model=QAResponse)
async def answer_question(
    request: QARequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Answer questions about a specific document using RAG (Retrieval-Augmented Generation).
    """
    
    start_time = time.time()
    
    try:
        # Verify document exists and user has access
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(request.document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check user access
        if current_user and doc_data.get("metadata", {}).get("user_id"):
            if doc_data["metadata"]["user_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Search document knowledge base
        document_context = []
        if doc_data.get("knowledge_base_created"):
            try:
                search_result = await search_knowledge_base(
                    document_id=request.document_id,
                    query=request.question,
                    limit=3,
                    current_user=current_user
                )
                document_context = search_result.get("results", [])
            except:
                # Continue without document context if search fails
                pass
        
        # Search legal corpus for additional context
        legal_context = []
        try:
            legal_search = await search_legal_corpus(query=request.question, limit=2)
            legal_context = legal_search.get("results", [])
        except:
            # Continue without legal context if search fails
            pass
        
        # Get document metadata for context
        document_type = doc_data.get("document_type", "legal document")
        clauses = doc_data.get("clauses", [])
        
        # Generate answer using Gemini
        model = GenerativeModel(MODEL_NAME)
        answer_data = await generate_answer(
            model=model,
            question=request.question,
            document_type=document_type,
            document_context=document_context,
            legal_context=legal_context,
            clauses=clauses
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        response = QAResponse(
            question=request.question,
            answer=answer_data["answer"],
            confidence=answer_data["confidence"],
            sources=answer_data["sources"],
            citations=answer_data.get("citations", []),
            response_time_ms=response_time_ms
        )
        
        # Store Q&A in Firestore for analytics
        qa_collection = firestore_client.collection("qa_history")
        qa_doc = {
            "document_id": request.document_id,
            "user_id": request.user_id,
            "question": request.question,
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "sources": answer_data["sources"],
            "response_time_ms": response_time_ms,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        qa_collection.add(qa_doc)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )

async def generate_answer(
    model: GenerativeModel,
    question: str,
    document_type: str,
    document_context: List[Dict],
    legal_context: List[Dict],
    clauses: List[Dict]
) -> Dict[str, Any]:
    """Generate an answer using retrieved context and Gemini model."""
    
    # Build context from retrieved information
    context_parts = []
    sources = []
    
    # Add document context
    if document_context:
        context_parts.append("=== DOCUMENT CONTEXT ===")
        for i, ctx in enumerate(document_context):
            context_parts.append(f"Context {i+1}: {ctx['text'][:500]}...")
            if ctx['chunk_type'] == 'clause':
                sources.append(f"Clause: {ctx['metadata'].get('clause_type', 'Unknown')}")
            else:
                sources.append(f"Document section (similarity: {ctx['similarity']:.2f})")
    
    # Add legal context
    if legal_context:
        context_parts.append("\n=== LEGAL REFERENCES ===")
        for i, ctx in enumerate(legal_context):
            context_parts.append(f"Legal Reference {i+1}: {ctx['snippet']}")
            sources.append(f"Legal: {ctx['title']}")
    
    # Add clause summaries for additional context
    if clauses:
        context_parts.append("\n=== DOCUMENT CLAUSES SUMMARY ===")
        for clause in clauses[:5]:  # Limit to first 5 clauses
            clause_summary = f"- {clause.get('clause_type', 'Unknown')}: {clause.get('plain_language', '')[:200]}..."
            context_parts.append(clause_summary)
    
    context_text = "\n".join(context_parts)
    
    # Create prompt for answer generation
    prompt = f"""
    You are a legal document analysis assistant. Answer the user's question based on the provided context from their {document_type.replace('_', ' ')}.

    IMPORTANT GUIDELINES:
    1. Base your answer primarily on the document context provided
    2. If the document doesn't contain relevant information, say so clearly
    3. Use plain language (Grade 8 reading level)
    4. Include specific references to clauses or sections when applicable
    5. Always include the disclaimer that this is not legal advice
    6. Be helpful but conservative in your interpretation
    7. If uncertain, recommend consulting a legal professional

    CONTEXT:
    {context_text}

    USER QUESTION: {question}

    Provide your response in this JSON format:
    {{
        "answer": "Your detailed answer here",
        "confidence": 0.85,
        "reasoning": "Brief explanation of how you arrived at this answer",
        "limitations": "Any limitations or uncertainties in your answer"
    }}

    Make sure your confidence score (0.0-1.0) reflects how well the available context addresses the question.
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # Build final answer with disclaimer
        answer = result.get("answer", "I couldn't find relevant information in the document to answer your question.")
        confidence = float(result.get("confidence", 0.5))
        
        # Add disclaimer
        answer += "\n\n⚠️ This analysis is for educational purposes only and does not constitute legal advice. Please consult with a qualified attorney for legal decisions."
        
        return {
            "answer": answer,
            "confidence": min(max(confidence, 0.0), 1.0),  # Ensure confidence is between 0 and 1
            "sources": sources[:5],  # Limit sources
            "citations": create_citations(legal_context)
        }
        
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "answer": "I found some relevant information in your document, but I'm having trouble providing a detailed analysis right now. Please try rephrasing your question or consult the document clauses directly.\n\n⚠️ This analysis is for educational purposes only and does not constitute legal advice.",
            "confidence": 0.3,
            "sources": sources[:3],
            "citations": []
        }
    except Exception as e:
        # Fallback for any other errors
        return {
            "answer": f"I encountered an issue while analyzing your question. The document appears to be a {document_type.replace('_', ' ')}, but I cannot provide a specific answer at this time. Please review the document directly or consult with a legal professional.\n\n⚠️ This analysis is for educational purposes only and does not constitute legal advice.",
            "confidence": 0.2,
            "sources": [],
            "citations": []
        }

def create_citations(legal_context: List[Dict]) -> List[Citation]:
    """Create citation objects from legal context."""
    
    citations = []
    for ctx in legal_context:
        citation = Citation(
            source=ctx.get("source", "Legal Reference"),
            reference=ctx.get("title", "Unknown Reference"),
            url=ctx.get("link")
        )
        citations.append(citation)
    
    return citations

@router.get("/qa/history/{document_id}")
async def get_qa_history(
    document_id: str,
    limit: int = 10,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get Q&A history for a document."""
    
    try:
        # Verify document access
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check user access
        if current_user and doc_data.get("metadata", {}).get("user_id"):
            if doc_data["metadata"]["user_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get Q&A history
        qa_collection = firestore_client.collection("qa_history")
        query = qa_collection.where("document_id", "==", document_id).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        
        history = []
        for doc in query.stream():
            qa_data = doc.to_dict()
            history.append({
                "question": qa_data.get("question", ""),
                "answer": qa_data.get("answer", ""),
                "confidence": qa_data.get("confidence", 0.0),
                "sources": qa_data.get("sources", []),
                "timestamp": qa_data.get("timestamp"),
                "response_time_ms": qa_data.get("response_time_ms", 0)
            })
        
        return {
            "document_id": document_id,
            "history": history,
            "total_questions": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Q&A history: {str(e)}"
        )

@router.get("/qa/suggested/{document_id}")
async def get_suggested_questions(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get suggested questions based on document type and content."""
    
    try:
        # Verify document access
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check user access
        if current_user and doc_data.get("metadata", {}).get("user_id"):
            if doc_data["metadata"]["user_id"] != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        document_type = doc_data.get("document_type", "other")
        clauses = doc_data.get("clauses", [])
        
        # Generate suggested questions based on document type and clauses
        suggested = generate_suggested_questions(document_type, clauses)
        
        return {
            "document_id": document_id,
            "document_type": document_type,
            "suggested_questions": suggested
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggested questions: {str(e)}"
        )

def generate_suggested_questions(document_type: str, clauses: List[Dict]) -> List[str]:
    """Generate suggested questions based on document type and content."""
    
    base_questions = [
        "What are my main obligations under this contract?",
        "What happens if I want to terminate this agreement early?",
        "What fees or penalties might I be charged?",
        "What are the biggest risks I should be aware of?",
        "How can I protect myself when signing this?"
    ]
    
    # Document type specific questions
    type_questions = {
        "rental_agreement": [
            "What happens if I miss a rent payment?",
            "Can my landlord increase the rent?",
            "What is my security deposit used for?",
            "Who is responsible for repairs and maintenance?",
            "How much notice do I need to give before moving out?"
        ],
        "loan_contract": [
            "What is my total cost of borrowing?",
            "What happens if I miss a payment?",
            "Can I pay off the loan early?",
            "What collateral am I putting at risk?",
            "What are the default consequences?"
        ],
        "employment_contract": [
            "What are my working hours and overtime rules?",
            "What benefits am I entitled to?",
            "Can I work for competitors after leaving?",
            "What intellectual property rights do I retain?",
            "How can my employment be terminated?"
        ],
        "terms_of_service": [
            "What data do you collect about me?",
            "Can you change these terms without notice?",
            "What happens if I violate the terms?",
            "How do I delete my account and data?",
            "What are my rights in disputes?"
        ]
    }
    
    # Get document-specific questions
    questions = base_questions + type_questions.get(document_type, [])
    
    # Add clause-specific questions
    clause_types = [clause.get("clause_type", "") for clause in clauses]
    
    if "security_deposit" in clause_types:
        questions.append("When and how will I get my security deposit back?")
    
    if "non_compete" in clause_types:
        questions.append("What jobs am I restricted from taking after this ends?")
    
    if "data_sharing" in clause_types:
        questions.append("Who else will have access to my personal information?")
    
    if "limitation_liability" in clause_types:
        questions.append("What damages can I recover if something goes wrong?")
    
    # Remove duplicates and limit to 8 questions
    unique_questions = list(dict.fromkeys(questions))
    return unique_questions[:8]
