<div align="center">

# Nayaya.ai

**AI-Powered Legal Research and Analysis Platform**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?logo=langchain)](https://langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?logo=google)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Adit-Jain-srm/Nayaya.ai)](https://github.com/Adit-Jain-srm/Nayaya.ai)

*Democratizing legal assistance through AI — making Indian law accessible to everyone.*

</div>

---


<div align="center">

# Nayaya.ai

**AI-Powered Legal Research and Analysis Platform**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?logo=langchain)](https://langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Adit-Jain-srm/Nayaya.ai)](https://github.com/Adit-Jain-srm/Nayaya.ai)

*Democratizing legal assistance through AI — making Indian law accessible to everyone.*

</div>

---

## 🚀 Vision

Nayaya.ai makes complex legal documents — rental agreements, loan contracts, employment offers, and online Terms of Service — easy to understand. Built on **Google Cloud AI (Document AI, Vertex AI, Gemini, Matching Engine)**, it converts dense clauses into plain-language explanations, highlights hidden risks, and answers "what-if" questions.

⚠️ **Disclaimer:** Nayaya.ai is an educational tool to simplify legal text. It does *not* provide legal advice. Please consult a qualified lawyer for decisions with legal consequences.

---

## ✨ Features (MVP)

* 📂 **Upload & OCR**: PDF/DOC → text via Document AI
* 📝 **Clause Detection**: Classify into Payment/Termination/Privacy/etc.
* 🔍 **Plain-language Summaries**: Grade 8 reading level per clause
* 🚦 **Risk Flags**: High/Medium/Low with rationale
* ❓ **Interactive Q&A**: Ask contract-specific questions with RAG
* 📑 **PDF Export**: Comprehensive summary & risk report
* 🔒 **Privacy-first**: CMEK encryption, no training on user data, optional PII redaction
* 🌐 **Multilingual**: Ready for Hindi and other languages

---

## 🏗️ Architecture (Production-Ready)

* **Frontend**: Next.js app → Cloud Run with auto-scaling
* **Backend**: FastAPI microservices → Cloud Run
* **Storage**: Cloud Storage with CMEK encryption
* **OCR**: Document AI Form Parser processors
* **AI**: Vertex AI Gemini 1.5 Pro for classification and generation
* **RAG**: Vertex AI Embeddings + Matching Engine for legal knowledge retrieval
* **Database**: Firestore (metadata), BigQuery (analytics)
* **Security**: IAM, VPC-SC, CMEK, DLP API, Audit Logs
* **Infrastructure**: Terraform for reproducible deployments

---

## 📦 Project Structure

```
nayaya-ai/
├─ README.md                    # This file
├─ PROJECT_SETUP.md            # Detailed setup guide
├─ FLOW_IMPLEMENTATION.md      # Technical implementation details
├─ frontend/                   # Next.js frontend application
│  ├─ app/                    # Next.js 13+ app directory
│  │  ├─ components/          # React components
│  │  ├─ globals.css          # Global styles
│  │  ├─ layout.tsx           # Root layout
│  │  ├─ page.tsx             # Home page
│  │  └─ types.ts             # TypeScript types
│  ├─ package.json            # Dependencies
│  ├─ tailwind.config.js      # Tailwind CSS config
│  └─ Dockerfile              # Container config
├─ backend/                    # FastAPI backend services
│  ├─ api/                    # API route handlers
│  │  ├─ upload.py            # Document upload
│  │  ├─ document_ai.py       # OCR processing
│  │  ├─ vertex_ai.py         # AI classification & analysis
│  │  ├─ rag.py               # Knowledge retrieval
│  │  └─ qa.py                # Q&A system
│  ├─ models/                 # Data models
│  │  └─ document.py          # Document schemas
│  ├─ services/               # Business logic
│  │  └─ auth.py              # Authentication
│  ├─ main.py                 # FastAPI application
│  ├─ requirements.txt        # Python dependencies
│  ├─ env_example             # Environment template
│  └─ Dockerfile              # Container config
├─ infra/                      # Infrastructure as Code
│  ├─ main.tf                 # Terraform configuration
│  └─ terraform.tfvars.example # Variables template
├─ scripts/                    # Automation scripts
│  ├─ setup.sh                # Automated deployment
│  └─ local-dev.sh            # Local development
├─ samples/                    # Test documents
│  └─ rental-agreement.md     # Sample contract
├─ cloudbuild.yaml            # CI/CD configuration
└─ Flwo.jpg                   # Architecture diagram
```

---

## ⚡ Quick Start

### Automated Setup (Recommended)

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Adit-Jain-srm/Nayaya.ai.git
   cd Nayaya.ai
   
   # On Unix/macOS:
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   
   # On Windows:
   bash scripts/setup.sh
   ```

2. **The setup script will:**
   - Enable required Google Cloud APIs
   - Deploy infrastructure with Terraform
   - Build and deploy applications to Cloud Run
   - Configure authentication and permissions

### Local Development

1. **Setup local environment:**
   ```bash
   # On Unix/macOS:
   chmod +x scripts/local-dev.sh
   ./scripts/local-dev.sh setup
   
   # On Windows:
   bash scripts/local-dev.sh setup
   ```

2. **Start development servers:**
   ```bash
   ./scripts/local-dev.sh start
   ```

   This starts:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

### Manual Setup

See [PROJECT_SETUP.md](./PROJECT_SETUP.md) for detailed manual setup instructions.

---

## ☁️ Google Cloud Integration

### Services Used

1. **Document AI**: OCR and layout analysis
2. **Vertex AI**: Gemini models for classification and generation
3. **Cloud Storage**: Encrypted document storage with CMEK
4. **Firestore**: Document metadata and real-time updates
5. **Cloud Run**: Serverless container hosting with auto-scaling
6. **BigQuery**: Analytics and legal knowledge corpus
7. **Cloud Translation**: Multilingual support
8. **DLP API**: PII detection and redaction
9. **Cloud KMS**: Customer-managed encryption keys
10. **IAM & VPC**: Security and access control

### Deployment Architecture

```
Internet → Cloud CDN → Cloud Run (Frontend)
                    ↓
              Cloud Run (Backend) → Document AI
                    ↓                    ↓
              Firestore ←→ Vertex AI → Cloud Storage (CMEK)
                    ↓                    ↓
              BigQuery ←→ Cloud DLP → Audit Logs
```

---

## 🧪 Testing the Application

### Sample Documents

Use the provided sample in `samples/rental-agreement.md` to test the system:

1. Convert the markdown to PDF
2. Upload through the web interface
3. Watch the processing pipeline:
   - Document AI extracts text and structure
   - Vertex AI classifies clauses and assesses risks
   - Gemini generates plain-language explanations
   - RAG system enables Q&A functionality

### Expected Results

The sample rental agreement contains several high-risk clauses that should be flagged:
- Excessive security deposit forfeiture
- Unlimited rent increases
- Broad indemnification clauses
- Restrictive termination penalties

---

## 📊 Performance & Evaluation

### Technical Metrics
* **Processing Speed**: ~30-60 seconds per document
* **Classification Accuracy**: F1 ≥ 0.85 on legal clause taxonomy
* **Readability**: Flesch-Kincaid Grade 8 for explanations
* **Availability**: 99.9% uptime with Cloud Run auto-scaling

### Security & Compliance
* **Encryption**: CMEK for all data at rest
* **Privacy**: Zero training on user data, optional PII redaction
* **Audit**: Complete processing trail in Cloud Logging
* **Access**: IAM-based permissions with least privilege

---

## 🛣️ Implementation Roadmap

### ✅ Phase 1 (Complete - MVP)
- Document upload and OCR processing
- Clause classification with 50+ legal clause types
- Risk assessment and plain language generation
- Interactive Q&A with RAG
- PDF export functionality
- Production-ready Google Cloud deployment

### 🔄 Phase 2 (Next Steps)
- Hindi language support with Cloud Translation
- Enhanced legal knowledge corpus
- Citation tracking and legal source linking
- Advanced analytics dashboard
- Mobile-responsive optimizations

### 🎯 Phase 3 (Future)
- Fine-tuning models with annotated legal datasets
- Multi-jurisdiction support (US states, international)
- Integration APIs for fintech/proptech platforms
- Advanced contract comparison features

### 🌟 Phase 4 (Scale)
- Legal aid organization partnerships
- Enterprise features and admin dashboard
- Compliance certifications (SOC 2, GDPR)
- White-label solutions for legal tech companies

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the existing code style
4. Test your changes thoroughly
5. Submit a pull request with a clear description

### Development Guidelines

- Follow TypeScript best practices for frontend
- Use FastAPI patterns for backend APIs
- Include comprehensive error handling
- Add tests for new functionality
- Update documentation for API changes

---

## 📚 Documentation

- **[PROJECT_SETUP.md](./PROJECT_SETUP.md)**: Comprehensive setup guide
- **[FLOW_IMPLEMENTATION.md](./FLOW_IMPLEMENTATION.md)**: Technical implementation details
- **API Documentation**: Available at `/docs` endpoint when backend is running
- **Architecture**: See the flow diagram (`Flwo.jpg`) for visual overview

---

## 🆘 Support & Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure service account has proper IAM permissions
2. **API Quota Limits**: Monitor usage in Google Cloud Console
3. **Processing Failures**: Check Cloud Run logs for detailed error messages
4. **Local Development**: Verify Python/Node.js versions and dependencies

### Getting Help

- Check the troubleshooting section in [PROJECT_SETUP.md](./PROJECT_SETUP.md)
- Review Cloud Run service logs in Google Cloud Console
- Open an issue on GitHub with detailed error information
- Consult the API documentation at `/docs` endpoint

---

## 📜 License

MIT License - See LICENSE file for details.

Free to use, fork, and modify for educational and commercial purposes.

---

## ⚠️ Legal Disclaimer

**Important**: Nayaya.ai is an educational tool designed to help users understand legal documents in plain language. It does NOT provide legal advice and should not be used as a substitute for consultation with a qualified attorney.

Users should always:
- Consult with licensed legal professionals for important decisions
- Verify AI-generated analysis with expert review
- Understand that laws vary by jurisdiction
- Recognize that contract interpretation can be complex and context-dependent

---

**Built with ❤️ using Google Cloud AI** | **Team Nayaya.ai** ✨

