#!/bin/bash
# Docker Setup Script for Ollama Flow
# Automates the setup and deployment of containerized AI agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
DEV_COMPOSE_FILE="docker-compose.dev.yml"
IMAGE_NAME="ollama-flow"
NETWORK_NAME="ollama-flow-net"

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

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    log_success "All requirements met"
}

check_ollama() {
    log_info "Checking Ollama availability..."
    
    # Check if Ollama is running on default port
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        log_success "Ollama is running and accessible"
    else
        log_warning "Ollama not detected on localhost:11434"
        log_info "Please ensure Ollama is running before starting agents"
        log_info "Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build main image
    docker build -t ${IMAGE_NAME}:latest .
    if [ $? -eq 0 ]; then
        log_success "Main image built successfully"
    else
        log_error "Failed to build main image"
        exit 1
    fi
    
    # Build development image
    docker build -t ${IMAGE_NAME}-dev:latest -f Dockerfile.dev .
    if [ $? -eq 0 ]; then
        log_success "Development image built successfully"
    else
        log_error "Failed to build development image"
        exit 1
    fi
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data logs output monitoring
    chmod 755 data logs output monitoring
    
    log_success "Directories created"
}

start_services() {
    local compose_file=$1
    local env_mode=$2
    
    log_info "Starting services with $env_mode configuration..."
    
    # Start services
    docker compose -f $compose_file up -d
    
    if [ $? -eq 0 ]; then
        log_success "Services started successfully"
        
        # Show service status
        log_info "Service status:"
        docker compose -f $compose_file ps
        
        # Show important URLs
        if [ "$env_mode" = "development" ]; then
            echo
            log_info "🌐 Development URLs:"
            echo "  Dashboard: http://localhost:8081"
            echo "  Redis: localhost:6380"
            echo "  Debug Port: 5678"
        else
            echo
            log_info "🌐 Production URLs:"
            echo "  Dashboard: http://localhost:8080"
            echo "  Monitoring: http://localhost:9090"
            echo "  Redis: localhost:6379"
        fi
    else
        log_error "Failed to start services"
        exit 1
    fi
}

stop_services() {
    local compose_file=$1
    
    log_info "Stopping services..."
    
    docker compose -f $compose_file down
    
    if [ $? -eq 0 ]; then
        log_success "Services stopped successfully"
    else
        log_error "Failed to stop services"
    fi
}

cleanup() {
    log_info "Cleaning up Docker resources..."
    
    # Stop all containers
    docker compose -f $COMPOSE_FILE down 2>/dev/null || true
    docker compose -f $DEV_COMPOSE_FILE down 2>/dev/null || true
    
    # Remove images
    docker rmi ${IMAGE_NAME}:latest ${IMAGE_NAME}-dev:latest 2>/dev/null || true
    
    # Remove network
    docker network rm $NETWORK_NAME 2>/dev/null || true
    
    # Remove volumes (with confirmation)
    read -p "Remove persistent data volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume rm ollama-flow-redis-data ollama-flow-data ollama-flow-logs 2>/dev/null || true
        log_success "Volumes removed"
    fi
    
    log_success "Cleanup completed"
}

show_logs() {
    local service=$1
    local compose_file=$2
    
    if [ -z "$service" ]; then
        log_info "Available services:"
        docker compose -f $compose_file ps --services
        return
    fi
    
    log_info "Showing logs for service: $service"
    docker compose -f $compose_file logs -f $service
}

scale_drones() {
    local count=$1
    local compose_file=$2
    
    if [ -z "$count" ] || ! [[ "$count" =~ ^[0-9]+$ ]]; then
        log_error "Please provide a valid drone count"
        exit 1
    fi
    
    log_info "Scaling agent drones to $count instances..."
    
    # Use docker compose to scale drones
    # Note: This creates additional drone services dynamically
    for i in $(seq 1 $count); do
        service_name="agent-drone-$i"
        if [ $i -gt 2 ]; then
            # Create additional drones beyond the default 2
            log_info "Starting additional drone: $service_name"
            docker run -d \
                --name "ollama-flow-drone-$i" \
                --network $NETWORK_NAME \
                -e PYTHONUNBUFFERED=1 \
                -e REDIS_HOST=redis \
                -e REDIS_PORT=6379 \
                -e OLLAMA_HOST=host.docker.internal:11434 \
                -e DOCKER_MODE=true \
                -e AGENT_MODE=drone \
                -e DRONE_ID=$i \
                -v ollama-flow-data:/app/data \
                -v ollama-flow-logs:/app/logs \
                ${IMAGE_NAME}:latest \
                python3 agents/docker_drone_agent.py
        fi
    done
    
    log_success "Scaled to $count drones"
}

health_check() {
    local compose_file=$1
    
    log_info "Performing health check..."
    
    services=($(docker compose -f $compose_file ps --services))
    
    for service in "${services[@]}"; do
        log_info "Checking $service..."
        
        container_id=$(docker compose -f $compose_file ps -q $service)
        if [ -n "$container_id" ]; then
            status=$(docker inspect --format='{{.State.Status}}' $container_id)
            health=$(docker inspect --format='{{.State.Health.Status}}' $container_id 2>/dev/null || echo "no-healthcheck")
            
            if [ "$status" = "running" ]; then
                if [ "$health" = "healthy" ] || [ "$health" = "no-healthcheck" ]; then
                    log_success "$service: Running and healthy"
                else
                    log_warning "$service: Running but health check failed ($health)"
                fi
            else
                log_error "$service: Not running ($status)"
            fi
        else
            log_error "$service: Container not found"
        fi
    done
}

show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  setup          - Full setup: check requirements, build images, create directories"
    echo "  build          - Build Docker images only"
    echo "  start          - Start production services"
    echo "  start-dev      - Start development services"
    echo "  stop           - Stop services"
    echo "  restart        - Restart services"
    echo "  logs [service] - Show logs for a service (or list services if none specified)"
    echo "  scale <count>  - Scale agent drones to specified count"
    echo "  health         - Check service health status"
    echo "  cleanup        - Clean up all Docker resources"
    echo "  test           - Run Docker integration tests"
    echo
    echo "Examples:"
    echo "  $0 setup                 # Complete setup"
    echo "  $0 start                 # Start production environment"
    echo "  $0 start-dev            # Start development environment"
    echo "  $0 logs ollama-flow     # Show main app logs"
    echo "  $0 scale 8              # Scale to 8 agent drones"
    echo "  $0 health               # Check all service health"
}

# Main script logic
case "$1" in
    setup)
        check_requirements
        check_ollama
        create_directories
        build_images
        log_success "Setup completed! Use '$0 start' to launch services."
        ;;
    build)
        check_requirements
        build_images
        ;;
    start)
        check_requirements
        start_services $COMPOSE_FILE "production"
        ;;
    start-dev)
        check_requirements
        start_services $DEV_COMPOSE_FILE "development"
        ;;
    stop)
        stop_services $COMPOSE_FILE
        stop_services $DEV_COMPOSE_FILE
        ;;
    restart)
        stop_services $COMPOSE_FILE
        stop_services $DEV_COMPOSE_FILE
        sleep 2
        start_services $COMPOSE_FILE "production"
        ;;
    logs)
        show_logs "$2" $COMPOSE_FILE
        ;;
    scale)
        scale_drones "$2" $COMPOSE_FILE
        ;;
    health)
        health_check $COMPOSE_FILE
        ;;
    cleanup)
        cleanup
        ;;
    test)
        check_requirements
        log_info "Running Docker integration tests..."
        python3 -m pytest tests/test_docker_integration.py -v
        ;;
    *)
        show_usage
        exit 1
        ;;
esac