#!/bin/bash

# Local Development Setup Script for Nayaya.ai

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Node.js and Python are installed
check_local_requirements() {
    log_info "Checking local development requirements..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18 or later."
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11 or later."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        log_error "pip is not installed. Please install pip."
        exit 1
    fi
    
    log_success "Local requirements satisfied"
}

# Setup backend
setup_backend() {
    log_info "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp env_example .env
        log_warning "Created .env file from template. Please update with your Google Cloud configuration."
    fi
    
    log_success "Backend setup complete"
    cd ..
}

# Setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    npm install
    
    # Create .env.local file if it doesn't exist
    if [ ! -f ".env.local" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env.local
            log_success "Created .env.local from env.example template"
        else
            # Create basic .env.local
            cat > .env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
NEXT_PUBLIC_APP_NAME=Nayaya.ai
NEXT_PUBLIC_MAX_FILE_SIZE_MB=10
EOF
            log_success "Created basic .env.local file"
        fi
        log_warning "Please review and update .env.local with your configuration"
    fi
    
    log_success "Frontend setup complete"
    cd ..
}

# Start development servers
start_dev_servers() {
    log_info "Starting development servers..."
    
    # Function to cleanup background processes
    cleanup() {
        log_info "Stopping development servers..."
        jobs -p | xargs -r kill
        exit 0
    }
    
    # Set trap to cleanup on script exit
    trap cleanup SIGINT SIGTERM
    
    # Start backend
    log_info "Starting backend server on port 8000..."
    cd backend
    source venv/bin/activate
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    # Start frontend
    log_info "Starting frontend server on port 3000..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    log_success "Development servers started!"
    log_info "Frontend: http://localhost:3000"
    log_info "Backend API: http://localhost:8000"
    log_info "API Docs: http://localhost:8000/docs"
    
    log_info "Press Ctrl+C to stop all servers"
    
    # Wait for background processes
    wait
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Backend tests
    cd backend
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        if [ -f "test_main.py" ]; then
            python -m pytest test_main.py -v
        else
            log_warning "No backend tests found"
        fi
    fi
    cd ..
    
    # Frontend tests
    cd frontend
    if [ -f "package.json" ]; then
        if npm list --depth=0 | grep -q "jest\|vitest\|@testing-library"; then
            npm test -- --watchAll=false
        else
            log_warning "No frontend tests found"
        fi
    fi
    cd ..
    
    log_success "Tests completed"
}

# Display help
show_help() {
    echo "Nayaya.ai Local Development Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Set up local development environment"
    echo "  start     - Start development servers"
    echo "  test      - Run tests"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup   # Initial setup"
    echo "  $0 start   # Start dev servers"
    echo "  $0 test    # Run tests"
}

# Main function
main() {
    case "${1:-setup}" in
        setup)
            check_local_requirements
            setup_backend
            setup_frontend
            log_success "Local development environment setup complete!"
            log_info "Run '$0 start' to start development servers"
            ;;
        start)
            start_dev_servers
            ;;
        test)
            run_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
