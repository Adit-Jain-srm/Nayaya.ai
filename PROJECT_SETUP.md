# Nayaya.ai - Project Setup Guide

This guide will help you set up and deploy the Nayaya.ai legal document analysis platform using Google Cloud's AI tools.

## 🏗️ Architecture Overview

Nayaya.ai follows the flow diagram you provided, implementing:

1. **Document Upload & OCR** - Google Cloud Document AI
2. **Clause Classification** - Vertex AI with Gemini
3. **Knowledge Retrieval** - Vertex AI Matching Engine + RAG
4. **Risk Assessment** - Gemini Pro with structured prompts
5. **Q&A System** - Retrieval-Augmented Generation
6. **Export & Reports** - PDF generation with jsPDF

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Terraform >= 1.0
- Docker installed
- Node.js 18+ and Python 3.11+

### Automated Setup

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo-url>
   cd nayaya-ai
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

2. **The setup script will:**
   - Enable required Google Cloud APIs
   - Deploy infrastructure with Terraform
   - Build and deploy the application to Cloud Run
   - Configure authentication and permissions

### Manual Setup

If you prefer manual setup or need to customize the deployment:

#### 1. Google Cloud Setup

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
    documentai.googleapis.com \
    aiplatform.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com \
    firestore.googleapis.com \
    dlp.googleapis.com \
    translate.googleapis.com \
    discoveryengine.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    cloudkms.googleapis.com \
    secretmanager.googleapis.com \
    vpcaccess.googleapis.com
```

#### 2. Infrastructure Deployment

```bash
cd infra

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id  = "your-project-id"
region      = "us-central1"
environment = "dev"
EOF

# Deploy infrastructure
terraform init
terraform plan
terraform apply
```

#### 3. Application Deployment

```bash
# Build and deploy with Cloud Build
gcloud builds submit --config=cloudbuild.yaml \
    --substitutions=_REGION=us-central1,_ENVIRONMENT=dev
```

## 🛠️ Local Development

### Setup Local Environment

```bash
# Use the local development script
chmod +x scripts/local-dev.sh
./scripts/local-dev.sh setup
```

### Start Development Servers

```bash
# Start both frontend and backend
./scripts/local-dev.sh start
```

This will start:
- Backend API server on `http://localhost:8000`
- Frontend Next.js app on `http://localhost:3000`
- API documentation on `http://localhost:8000/docs`

### Manual Local Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp env_example .env
# Edit .env with your Google Cloud configuration

# Start server
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Document AI
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_LOCATION=us

# Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL_NAME=gemini-1.5-pro
VERTEX_AI_EMBEDDING_MODEL=textembedding-gecko@003

# Storage
CLOUD_STORAGE_BUCKET=nayaya-documents
CLOUD_STORAGE_BUCKET_PROCESSED=nayaya-processed

# Security
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```

#### Frontend Environment Setup

1. **Copy environment template:**
   ```bash
   cd frontend
   cp env.example .env.local
   ```

2. **Update .env.local with your configuration:**
   ```bash
   # For local development
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NODE_ENV=development
   
   # For production (update with your Cloud Run backend URL)
   # NEXT_PUBLIC_API_URL=https://nayaya-ai-backend-dev-xxxxxxxxx-uc.a.run.app
   
   # Optional configurations
   NEXT_PUBLIC_APP_NAME=Nayaya.ai
   NEXT_PUBLIC_MAX_FILE_SIZE_MB=10
   ```

## 📊 Testing the Application

### 1. Upload a Document
- Navigate to the frontend URL
- Upload a PDF, DOC, or DOCX legal document
- Watch the processing pipeline in action

### 2. Document Processing Flow
The application follows this flow:
1. **Upload** → Document stored in Cloud Storage
2. **OCR** → Document AI extracts text and structure
3. **Classification** → Vertex AI identifies and classifies clauses
4. **Analysis** → Gemini generates plain language explanations and risk assessments
5. **Knowledge Base** → Creates embeddings for Q&A
6. **Results** → Display analysis with interactive Q&A and export options

### 3. Test Features
- **Clause Analysis**: Review plain language explanations and risk levels
- **Q&A System**: Ask questions about the document
- **Export**: Generate PDF reports
- **Risk Assessment**: View overall document risk and recommendations

## 🔒 Security Features

The application implements several security measures:

1. **Encryption at Rest**: CMEK encryption for Cloud Storage
2. **Data Privacy**: Optional PII redaction with DLP API
3. **Access Control**: IAM-based permissions and service accounts
4. **Network Security**: VPC connectors for Cloud Run services
5. **Audit Logging**: All operations logged for compliance

## 📈 Monitoring and Analytics

### Cloud Monitoring
- Cloud Run metrics and logs
- Document processing analytics in BigQuery
- Error tracking and alerting

### Application Metrics
- Document processing times
- Q&A response quality
- User interaction patterns

## 🚀 Deployment Environments

### Development
- Single instance Cloud Run services
- Basic monitoring
- Development-grade security

### Production
- Multi-instance with auto-scaling
- Enhanced monitoring and alerting
- Production security hardening
- CDN for frontend assets

## 🛠️ Customization

### Adding New Document Types
1. Update `DocumentType` enum in `backend/models/document.py`
2. Add classification logic in `backend/api/vertex_ai.py`
3. Update frontend components to handle new types

### Extending Clause Types
1. Update `ClauseType` enum in `backend/models/document.py`
2. Modify classification prompts in Vertex AI integration
3. Add new risk assessment rules

### Adding Languages
1. Configure Cloud Translation API
2. Update frontend with language selection
3. Modify prompts for multilingual support

## 📚 API Documentation

Once deployed, visit `/docs` on your backend URL for interactive API documentation.

Key endpoints:
- `POST /api/upload` - Upload documents
- `POST /api/process-ocr` - Process with Document AI
- `POST /api/classify-clauses` - Classify document clauses
- `POST /api/analyze` - Generate analysis and risk assessment
- `POST /api/qa` - Ask questions about documents

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure service account has proper permissions
   - Check GOOGLE_APPLICATION_CREDENTIALS path

2. **API Quota Exceeded**
   - Monitor API usage in Cloud Console
   - Request quota increases if needed

3. **Processing Failures**
   - Check Cloud Run logs: `gcloud run services logs read SERVICE_NAME --region=REGION`
   - Verify Document AI processor is active

4. **Frontend Build Issues**
   - Ensure Node.js version compatibility
   - Clear npm cache: `npm cache clean --force`

### Getting Help

- Check the logs in Google Cloud Console
- Review API documentation at `/docs`
- Monitor Cloud Run service health
- Use Cloud Debugger for production issues

## 🎯 Next Steps

1. **Enhance the Model**: Fine-tune Vertex AI models with domain-specific legal data
2. **Add Features**: Implement clause comparison, contract templates, legal aid routing
3. **Scale**: Add caching, CDN, and performance optimizations
4. **Integrate**: Connect with legal databases, e-signature platforms
5. **Compliance**: Add audit trails, data retention policies, jurisdiction-specific rules

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Disclaimer**: Nayaya.ai is an educational tool that simplifies legal text. It does not provide legal advice. Please consult with a qualified attorney for legal decisions.
