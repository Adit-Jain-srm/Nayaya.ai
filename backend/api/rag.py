from fastapi import APIRouter, HTTPException, Depends
from google.cloud import aiplatform
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from google.cloud import discoveryengine_v1alpha as discoveryengine
import os
import numpy as np
from typing import List, Dict, Any, Optional
import json

from models.document import ProcessingRequest
from services.auth import get_current_user_optional

router = APIRouter()

# Initialize clients
firestore_client = firestore.Client()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_AI_MODEL_NAME", "gemini-1.5-pro")
EMBEDDING_MODEL_NAME = os.getenv("VERTEX_AI_EMBEDDING_MODEL", "textembedding-gecko@003")
SEARCH_ENGINE_ID = os.getenv("VERTEX_SEARCH_ENGINE_ID")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "documents")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize embedding model
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)

@router.post("/create-knowledge-base")
async def create_knowledge_base(
    request: ProcessingRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Create embeddings for document content and store in vector database.
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
        
        # Get document content
        extracted_data = doc_data.get("extracted_data", {})
        raw_text = extracted_data.get("raw_text", "")
        paragraphs = extracted_data.get("paragraphs", [])
        clauses = doc_data.get("clauses", [])
        
        if not raw_text:
            raise HTTPException(status_code=400, detail="No text found in document")
        
        # Create chunks for embedding
        chunks = create_text_chunks(raw_text, paragraphs, clauses)
        
        # Generate embeddings
        embeddings_data = []
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embeddings = embedding_model.get_embeddings([chunk["text"]])
                embedding_vector = embeddings[0].values
                
                embedding_data = {
                    "chunk_id": f"{request.document_id}_chunk_{i}",
                    "document_id": request.document_id,
                    "text": chunk["text"],
                    "chunk_type": chunk["type"],
                    "metadata": chunk["metadata"],
                    "embedding": embedding_vector,
                    "created_at": firestore.SERVER_TIMESTAMP
                }
                
                embeddings_data.append(embedding_data)
                
            except Exception as e:
                print(f"Error generating embedding for chunk {i}: {str(e)}")
                continue
        
        # Store embeddings in Firestore collection
        embeddings_collection = firestore_client.collection("embeddings")
        batch = firestore_client.batch()
        
        for embedding_data in embeddings_data:
            doc_ref = embeddings_collection.document(embedding_data["chunk_id"])
            batch.set(doc_ref, embedding_data)
        
        batch.commit()
        
        # Update main document with knowledge base status
        doc_ref.update({
            "knowledge_base_created": True,
            "embeddings_count": len(embeddings_data),
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        return {
            "success": True,
            "document_id": request.document_id,
            "message": "Knowledge base created successfully",
            "chunks_created": len(embeddings_data),
            "embeddings_generated": len(embeddings_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create knowledge base: {str(e)}"
        )

def create_text_chunks(
    raw_text: str, 
    paragraphs: List[Dict], 
    clauses: List[Dict]
) -> List[Dict[str, Any]]:
    """Create text chunks for embedding generation."""
    
    chunks = []
    
    # Add full document chunk
    chunks.append({
        "text": raw_text[:2000],  # Limit to first 2000 chars
        "type": "document",
        "metadata": {
            "chunk_type": "full_document",
            "length": len(raw_text)
        }
    })
    
    # Add clause chunks
    for clause in clauses:
        chunks.append({
            "text": f"Clause Type: {clause.get('clause_type', '')}\n\nOriginal Text: {clause.get('original_text', '')}\n\nPlain Language: {clause.get('plain_language', '')}\n\nRisk: {clause.get('risk_level', '')} - {clause.get('risk_reason', '')}",
            "type": "clause",
            "metadata": {
                "chunk_type": "clause",
                "clause_type": clause.get("clause_type", ""),
                "risk_level": clause.get("risk_level", ""),
                "clause_id": clause.get("id", "")
            }
        })
    
    # Add paragraph chunks (for longer documents)
    if len(paragraphs) > 0:
        for i, paragraph in enumerate(paragraphs[:10]):  # Limit to first 10 paragraphs
            if len(paragraph.get("text", "")) > 100:  # Only include substantial paragraphs
                chunks.append({
                    "text": paragraph["text"],
                    "type": "paragraph",
                    "metadata": {
                        "chunk_type": "paragraph",
                        "paragraph_index": i,
                        "page": paragraph.get("page", 1),
                        "confidence": paragraph.get("confidence", 0.0)
                    }
                })
    
    return chunks

@router.post("/search-knowledge")
async def search_knowledge_base(
    document_id: str,
    query: str,
    limit: int = 5,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Search the document's knowledge base using semantic similarity.
    """
    
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
        
        if not doc_data.get("knowledge_base_created"):
            raise HTTPException(status_code=400, detail="Knowledge base not created for this document")
        
        # Generate query embedding
        query_embeddings = embedding_model.get_embeddings([query])
        query_vector = query_embeddings[0].values
        
        # Search for similar chunks
        embeddings_collection = firestore_client.collection("embeddings")
        embeddings_query = embeddings_collection.where("document_id", "==", document_id)
        
        results = []
        for doc in embeddings_query.stream():
            embedding_data = doc.to_dict()
            stored_vector = embedding_data.get("embedding", [])
            
            if stored_vector:
                # Calculate cosine similarity
                similarity = calculate_cosine_similarity(query_vector, stored_vector)
                
                results.append({
                    "chunk_id": embedding_data["chunk_id"],
                    "text": embedding_data["text"],
                    "chunk_type": embedding_data["chunk_type"],
                    "metadata": embedding_data["metadata"],
                    "similarity": similarity
                })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results[:limit]
        
        return {
            "query": query,
            "results": top_results,
            "total_searched": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge base search failed: {str(e)}"
        )

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except:
        return 0.0

@router.get("/legal-knowledge/search")
async def search_legal_corpus(
    query: str,
    limit: int = 5
):
    """
    Search general legal knowledge corpus using Vertex AI Search.
    This would be populated with legal statutes, regulations, and case law.
    """
    
    try:
        # This is a placeholder for Vertex AI Search integration
        # In production, you would:
        # 1. Set up a Vertex AI Search engine with legal corpus
        # 2. Use the Discovery Engine API to search
        
        if not SEARCH_ENGINE_ID:
            # Return mock legal knowledge for development
            mock_results = get_mock_legal_knowledge(query)
            return {
                "query": query,
                "results": mock_results,
                "source": "mock_legal_corpus"
            }
        
        # Initialize Discovery Engine client
        client = discoveryengine.SearchServiceClient()
        
        # Configure search request
        serving_config = client.serving_config_path(
            project=PROJECT_ID,
            location="global",
            data_store=SEARCH_ENGINE_ID,
            serving_config="default_config"
        )
        
        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=limit,
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )
        
        # Execute search
        response = client.search(search_request)
        
        # Process results
        results = []
        for result in response.results:
            document = result.document
            results.append({
                "title": document.derived_struct_data.get("title", ""),
                "snippet": document.derived_struct_data.get("snippet", ""),
                "link": document.derived_struct_data.get("link", ""),
                "source": document.derived_struct_data.get("source", "legal_corpus"),
                "relevance_score": getattr(result, 'relevance_score', 0.0)
            })
        
        return {
            "query": query,
            "results": results,
            "source": "vertex_ai_search"
        }
        
    except Exception as e:
        # Fallback to mock results
        mock_results = get_mock_legal_knowledge(query)
        return {
            "query": query,
            "results": mock_results,
            "source": "mock_legal_corpus",
            "error": f"Search service unavailable: {str(e)}"
        }

def get_mock_legal_knowledge(query: str) -> List[Dict[str, Any]]:
    """Return mock legal knowledge for development."""
    
    query_lower = query.lower()
    
    mock_knowledge = [
        {
            "title": "Tenant Rights - Security Deposits",
            "snippet": "Landlords must return security deposits within 30 days of lease termination, minus legitimate deductions for damages beyond normal wear and tear.",
            "link": "https://example.gov/tenant-rights#security-deposits",
            "source": "State Housing Law",
            "relevance_score": 0.95 if "security deposit" in query_lower else 0.3
        },
        {
            "title": "Contract Termination Rights",
            "snippet": "Parties may terminate contracts early only if specific conditions are met, including material breach or mutual agreement. Early termination fees must be reasonable.",
            "link": "https://example.gov/contract-law#termination",
            "source": "Contract Law Statute",
            "relevance_score": 0.9 if "termination" in query_lower else 0.4
        },
        {
            "title": "Limitation of Liability Clauses",
            "snippet": "Courts may void limitation of liability clauses that are unconscionable or attempt to limit liability for gross negligence or willful misconduct.",
            "link": "https://example.gov/contract-law#liability",
            "source": "Civil Code Section 1668",
            "relevance_score": 0.85 if "liability" in query_lower else 0.2
        },
        {
            "title": "Data Privacy Requirements",
            "snippet": "Companies must obtain explicit consent before collecting personal data and provide clear notice of data usage practices.",
            "link": "https://example.gov/privacy-law",
            "source": "Privacy Protection Act",
            "relevance_score": 0.9 if "data" in query_lower or "privacy" in query_lower else 0.3
        },
        {
            "title": "Employment Contract Standards",
            "snippet": "Non-compete clauses must be reasonable in scope, duration, and geographic area to be enforceable. They cannot prevent reasonable employment opportunities.",
            "link": "https://example.gov/employment-law#non-compete",
            "source": "Labor Code",
            "relevance_score": 0.8 if "employment" in query_lower or "non-compete" in query_lower else 0.25
        }
    ]
    
    # Sort by relevance and return top results
    mock_knowledge.sort(key=lambda x: x["relevance_score"], reverse=True)
    return mock_knowledge[:3]
