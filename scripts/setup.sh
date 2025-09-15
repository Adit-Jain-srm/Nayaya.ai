#!/bin/bash

# Nayaya.ai Setup Script
# This script sets up the development environment and deploys the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    log_success "All requirements satisfied"
}

# Get user input
get_user_input() {
    log_info "Getting project configuration..."
    
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    read -p "Enter region (default: us-central1): " REGION
    REGION=${REGION:-us-central1}
    
    read -p "Enter environment (dev/staging/prod, default: dev): " ENVIRONMENT
    ENVIRONMENT=${ENVIRONMENT:-dev}
    
    log_info "Configuration:"
    log_info "  Project ID: $PROJECT_ID"
    log_info "  Region: $REGION"
    log_info "  Environment: $ENVIRONMENT"
    
    read -p "Continue with this configuration? (y/N): " CONFIRM
    if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
        log_error "Setup cancelled"
        exit 1
    fi
}

# Setup Google Cloud
setup_gcloud() {
    log_info "Setting up Google Cloud..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log_info "Enabling Google Cloud APIs..."
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
    
    log_success "Google Cloud setup complete"
}

# Setup Terraform
setup_terraform() {
    log_info "Setting up Terraform infrastructure..."
    
    cd infra
    
    # Create terraform.tfvars from template
    cat > terraform.tfvars <<EOF
project_id  = "$PROJECT_ID"
region      = "$REGION"
environment = "$ENVIRONMENT"
EOF
    
    # Initialize Terraform
    terraform init
    
    # Plan infrastructure
    log_info "Planning infrastructure..."
    terraform plan
    
    # Apply infrastructure
    read -p "Apply infrastructure? (y/N): " APPLY_CONFIRM
    if [[ $APPLY_CONFIRM == "y" || $APPLY_CONFIRM == "Y" ]]; then
        terraform apply -auto-approve
        log_success "Infrastructure deployed successfully"
    else
        log_warning "Infrastructure deployment skipped"
    fi
    
    cd ..
}

# Setup backend environment
setup_backend() {
    log_info "Setting up backend environment..."
    
    cd backend
    
    # Create .env file
    cp env_example .env
    
    # Update .env with actual values
    sed -i "s/your-project-id/$PROJECT_ID/g" .env
    sed -i "s/us-central1/$REGION/g" .env
    sed -i "s/development/$ENVIRONMENT/g" .env
    
    log_success "Backend environment configured"
    cd ..
}

# Build and deploy application
deploy_application() {
    log_info "Building and deploying application..."
    
    # Submit build to Cloud Build
    gcloud builds submit --config=cloudbuild.yaml \
        --substitutions=_REGION=$REGION,_ENVIRONMENT=$ENVIRONMENT
    
    log_success "Application deployed successfully"
}

# Generate service account key (for local development)
setup_local_auth() {
    log_info "Setting up local authentication..."
    
    SERVICE_ACCOUNT="nayaya-ai-sa-$ENVIRONMENT@$PROJECT_ID.iam.gserviceaccount.com"
    
    # Create service account key
    gcloud iam service-accounts keys create \
        service-account-key.json \
        --iam-account=$SERVICE_ACCOUNT
    
    # Set environment variable
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service-account-key.json"
    
    log_success "Local authentication configured"
    log_warning "Service account key saved to: $(pwd)/service-account-key.json"
    log_warning "Add this to your .env file: GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/service-account-key.json"
}

# Display deployment information
show_deployment_info() {
    log_success "Deployment complete!"
    
    # Get Cloud Run URLs
    BACKEND_URL=$(gcloud run services describe nayaya-ai-backend-$ENVIRONMENT --region=$REGION --format="value(status.url)")
    FRONTEND_URL=$(gcloud run services describe nayaya-ai-frontend-$ENVIRONMENT --region=$REGION --format="value(status.url)")
    
    log_info "Application URLs:"
    log_info "  Frontend: $FRONTEND_URL"
    log_info "  Backend API: $BACKEND_URL"
    
    log_info "Next steps:"
    log_info "1. Test the application at: $FRONTEND_URL"
    log_info "2. Check logs: gcloud run services logs read nayaya-ai-backend-$ENVIRONMENT --region=$REGION"
    log_info "3. Monitor usage in Google Cloud Console"
}

# Main execution
main() {
    log_info "Starting Nayaya.ai setup..."
    
    check_requirements
    get_user_input
    setup_gcloud
    setup_terraform
    setup_backend
    deploy_application
    setup_local_auth
    show_deployment_info
    
    log_success "Setup completed successfully!"
}

# Run main function
main "$@"
