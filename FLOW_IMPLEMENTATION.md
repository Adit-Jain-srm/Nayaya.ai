# Nayaya.ai - Flow Implementation Guide

This document explains how the Nayaya.ai application implements the flow diagram you provided, mapping each component to the actual code and Google Cloud services.

## 📊 Flow Diagram Implementation

### 1. User Uploads Document (PDF, DOC, Image)

**Frontend Implementation:**
- `frontend/app/components/DocumentUpload.tsx`
- Uses `react-dropzone` for drag-and-drop upload
- Validates file types and size limits
- Shows upload progress with visual feedback

**Backend Implementation:**
- `backend/api/upload.py` - `/api/upload` endpoint
- Stores files in Google Cloud Storage with CMEK encryption
- Creates document metadata in Firestore
- Returns document ID for tracking

**Google Cloud Services:**
- **Cloud Storage**: Encrypted document storage
- **Firestore**: Document metadata and status tracking

### 2. Google Cloud Services - Cloud Storage (Encrypted with CMEK)

**Implementation:**
- `infra/main.tf` - Terraform configuration for CMEK encryption
- `google_kms_crypto_key.storage_key` - KMS key for encryption
- All uploaded documents automatically encrypted at rest
- Bucket lifecycle policies for cost optimization

**Security Features:**
- Customer-managed encryption keys (CMEK)
- Uniform bucket-level access
- Audit logging enabled
- Versioning for data protection

### 3. Document AI OCR and Layout Analysis

**Backend Implementation:**
- `backend/api/document_ai.py` - `/api/process-ocr` endpoint
- Uses Google Cloud Document AI Form Parser processor
- Extracts text, structure, tables, and entities
- Stores processed data in Firestore

**Processing Pipeline:**
```python
# Document AI integration
docai_client = documentai.DocumentProcessorServiceClient()
raw_document = documentai.RawDocument(content=document_content, mime_type=mime_type)
result = docai_client.process_document(request=request_docai)
```

**Output:**
- Raw text extraction
- Page structure and layout
- Tables and form fields
- Entity recognition
- Confidence scores

### 4. Clause Detection and Classification - Vertex AI Model

**Backend Implementation:**
- `backend/api/vertex_ai.py` - `/api/classify-clauses` endpoint
- Uses Vertex AI Gemini model for classification
- Implements comprehensive clause taxonomy (50+ clause types)
- Generates structured JSON output

**Clause Classification Process:**
```python
model = GenerativeModel(MODEL_NAME)  # gemini-1.5-pro
clauses = await segment_and_classify_clauses(model, raw_text, paragraphs)
```

**Clause Types Supported:**
- Payment Terms, Security Deposit, Termination
- Data Privacy, IP Rights, Non-Compete
- Liability, Indemnification, Dispute Resolution
- And 40+ more legal clause types

### 5. Knowledge Retrieval from Legal Corpus - Vertex AI Search and BigQuery

**Backend Implementation:**
- `backend/api/rag.py` - Knowledge base and search functionality
- Uses Vertex AI Embeddings for semantic search
- Integrates with Vertex AI Search for legal corpus
- BigQuery for analytics and legal knowledge storage

**RAG Implementation:**
```python
# Generate embeddings
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
embeddings = embedding_model.get_embeddings([chunk["text"]])

# Semantic search
similarity = calculate_cosine_similarity(query_vector, stored_vector)
```

**Knowledge Sources:**
- Legal statutes and regulations
- Case law and precedents
- Contract templates and examples
- Jurisdiction-specific rules

### 6. Gemini Pro Generation - Plain Language plus Risk Flag

**Backend Implementation:**
- `backend/api/vertex_ai.py` - `/api/analyze` endpoint
- Uses Gemini Pro for plain language generation
- Implements structured risk assessment
- Generates actionable recommendations

**Risk Assessment Logic:**
```python
# Generate plain language and risk assessment
summary_data = await generate_summary_and_findings(model, clauses, document_type)
overall_risk = calculate_overall_risk(clauses)
```

**Output Format:**
- Plain language explanations (Grade 8 reading level)
- Risk levels: High/Medium/Low with rationale
- Specific recommendations for each clause
- Overall document risk assessment

### 7. Multilingual Translation - Cloud Translation API

**Implementation:**
- Configured in `backend/requirements.txt` - `google-cloud-translate`
- Environment setup in `backend/env_example`
- Ready for Hindi and other language support

**Translation Pipeline:**
```python
# Translate content to user's preferred language
from google.cloud import translate
translate_client = translate.Client()
result = translate_client.translate(text, target_language='hi')
```

### 8. UI Presentation - Clause-by-Clause View with Color Coding

**Frontend Implementation:**
- `frontend/app/components/DocumentAnalysis.tsx` - Main analysis view
- `frontend/app/components/ClauseCard.tsx` - Individual clause display
- Color-coded risk levels with visual indicators

**UI Features:**
- **Red**: High risk clauses with warning icons
- **Yellow**: Medium risk with caution indicators  
- **Green**: Low risk with check marks
- Expandable clause details
- Plain language summaries
- Recommendation lists

**Visual Design:**
```tsx
const riskColors = {
  high: 'border-red-300 bg-red-50',
  medium: 'border-yellow-300 bg-yellow-50', 
  low: 'border-green-300 bg-green-50'
}
```

### 9A. PDF or Report Export

**Frontend Implementation:**
- `frontend/app/components/ExportReport.tsx`
- Uses `jsPDF` for client-side PDF generation
- Comprehensive report with all analysis data

**Export Features:**
- Executive summary and key findings
- Clause-by-clause risk analysis
- Recommendations and action items
- Legal disclaimers
- Professional formatting

### 9B. Interactive Q&A with Gemini and RAG

**Backend Implementation:**
- `backend/api/qa.py` - `/api/qa` endpoint
- RAG-powered question answering
- Context-aware responses with citations

**Q&A Pipeline:**
```python
# Search document knowledge base
document_context = await search_knowledge_base(document_id, question)
legal_context = await search_legal_corpus(question)

# Generate answer with Gemini
answer_data = await generate_answer(model, question, document_context, legal_context)
```

**Frontend Implementation:**
- `frontend/app/components/QASection.tsx`
- Real-time Q&A interface
- Suggested questions based on document type
- Confidence scores and source citations

### Security and Governance Layer

**Implementation Across All Components:**

1. **IAM and VPC-SC:**
   - `infra/main.tf` - Service accounts and IAM roles
   - VPC connectors for secure communication
   - Principle of least privilege

2. **Cloud DLP for PII Redaction:**
   - Configured in backend environment
   - Optional PII detection and masking
   - Compliance with data protection regulations

3. **Audit Logs:**
   - All API calls logged automatically
   - Document processing audit trail
   - User interaction tracking

## 🔄 Complete Processing Flow

### Step-by-Step Execution:

1. **Document Upload**
   ```bash
   POST /api/upload
   → Cloud Storage (CMEK encrypted)
   → Firestore metadata
   ```

2. **OCR Processing**
   ```bash
   POST /api/process-ocr
   → Document AI processing
   → Text extraction and structure analysis
   ```

3. **Clause Classification**
   ```bash
   POST /api/classify-clauses
   → Vertex AI Gemini model
   → Structured clause identification
   ```

4. **Knowledge Base Creation**
   ```bash
   POST /api/create-knowledge-base
   → Vertex AI Embeddings
   → Vector database for RAG
   ```

5. **Risk Analysis**
   ```bash
   POST /api/analyze
   → Gemini Pro generation
   → Risk assessment and recommendations
   ```

6. **Interactive Q&A**
   ```bash
   POST /api/qa
   → RAG search + Gemini generation
   → Context-aware answers
   ```

## 🎯 Key Technical Decisions

### 1. Model Selection
- **Gemini 1.5 Pro**: Best balance of capability and cost
- **Text-Embedding-Gecko**: Optimized for semantic search
- **Document AI Form Parser**: Superior OCR for legal documents

### 2. Architecture Patterns
- **Microservices**: Separate concerns for scalability
- **Event-driven**: Async processing with Pub/Sub ready
- **RAG Pattern**: Grounded AI responses with citations

### 3. Data Flow
- **Stateless APIs**: Easy to scale and maintain
- **Firestore**: Fast document metadata queries
- **Cloud Storage**: Cost-effective file storage
- **BigQuery**: Analytics and reporting

### 4. Security Design
- **Zero-trust**: Every request authenticated and authorized
- **Encryption**: End-to-end data protection
- **Audit**: Complete traceability of all operations

## 🚀 Performance Optimizations

1. **Caching Strategy**
   - Firestore for fast metadata access
   - Cloud CDN for static assets
   - Client-side caching for UI components

2. **Async Processing**
   - Background document processing
   - Non-blocking API responses
   - Progress tracking and notifications

3. **Resource Optimization**
   - Cloud Run auto-scaling
   - Efficient Docker images
   - Optimized AI model usage

## 📊 Monitoring and Analytics

1. **Processing Metrics**
   - Document processing times
   - AI model performance
   - Error rates and types

2. **User Analytics**
   - Document types processed
   - Q&A interaction patterns
   - Feature usage statistics

3. **Business Metrics**
   - User engagement
   - Document complexity trends
   - Risk distribution analysis

This implementation provides a production-ready legal document analysis platform that follows Google Cloud best practices while delivering the functionality outlined in your flow diagram.
