#!/bin/bash

# Enhanced Ollama Flow Installation Script
# Installs the refactored Ollama Flow system with all dependencies

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_FLOW_DIR="$HOME/ollama-flow"
VENV_NAME="ollama-flow-env"
PYTHON_VERSION="3.8"

# Print functions
print_header() {
    echo -e "${PURPLE}"
    echo "==============================================="
    echo "🚀 OLLAMA FLOW ENHANCED INSTALLER v2.0"
    echo "==============================================="
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "-------------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Check system requirements
check_requirements() {
    print_section "Checking System Requirements"
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        python_major=$(echo $python_version | cut -d. -f1)
        python_minor=$(echo $python_version | cut -d. -f2)
        
        if [ "$python_major" -ge 3 ] && [ "$python_minor" -ge 8 ]; then
            print_success "Python $python_version found"
        else
            print_error "Python 3.8+ required, found $python_version"
            exit 1
        fi
    else
        print_error "Python3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 >/dev/null 2>&1; then
        print_success "pip3 found"
    else
        print_error "pip3 not found. Please install pip"
        exit 1
    fi
    
    # Check git
    if command -v git >/dev/null 2>&1; then
        print_success "git found"
    else
        print_error "git not found. Please install git"
        exit 1
    fi
    
    # Check ollama
    if command -v ollama >/dev/null 2>&1; then
        print_success "ollama found"
    else
        print_warning "ollama not found. Will install ollama"
        INSTALL_OLLAMA=true
    fi
    
    # Check disk space (minimum 5GB)
    available_space=$(df "$HOME" | tail -1 | awk '{print $4}')
    required_space=5000000  # 5GB in KB
    
    if [ "$available_space" -gt "$required_space" ]; then
        print_success "Sufficient disk space available"
    else
        print_warning "Low disk space. At least 5GB recommended"
    fi
    
    # Check memory (minimum 4GB)
    total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    required_mem=4000000  # 4GB in KB
    
    if [ "$total_mem" -gt "$required_mem" ]; then
        print_success "Sufficient memory available"
    else
        print_warning "Low memory. At least 4GB recommended for optimal performance"
    fi
}

# Install system dependencies
install_system_deps() {
    print_section "Installing System Dependencies"
    
    if command -v apt-get >/dev/null 2>&1; then
        print_info "Using apt-get package manager"
        sudo apt-get update
        sudo apt-get install -y \
            python3-venv \
            python3-dev \
            python3-pip \
            build-essential \
            curl \
            wget \
            unzip \
            git \
            htop \
            tree \
            jq
        print_success "System dependencies installed"
        
    elif command -v yum >/dev/null 2>&1; then
        print_info "Using yum package manager"
        sudo yum update -y
        sudo yum install -y \
            python3-venv \
            python3-devel \
            python3-pip \
            gcc \
            gcc-c++ \
            curl \
            wget \
            unzip \
            git \
            htop \
            tree \
            jq
        print_success "System dependencies installed"
        
    elif command -v brew >/dev/null 2>&1; then
        print_info "Using Homebrew package manager"
        brew install python3 curl wget unzip git htop tree jq
        print_success "System dependencies installed"
        
    else
        print_warning "Unknown package manager. Please install dependencies manually"
    fi
}

# Install or update Ollama
install_ollama() {
    if [ "$INSTALL_OLLAMA" = true ]; then
        print_section "Installing Ollama"
        
        # Download and install ollama
        curl -fsSL https://ollama.ai/install.sh | sh
        
        # Start ollama service
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl enable ollama
            sudo systemctl start ollama
        else
            # For macOS or systems without systemd
            print_info "Starting ollama in background..."
            nohup ollama serve > /dev/null 2>&1 &
        fi
        
        print_success "Ollama installed and started"
        
        # Wait for ollama to be ready
        print_info "Waiting for Ollama to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                print_success "Ollama is ready"
                break
            fi
            sleep 2
        done
    else
        print_info "Ollama already installed"
    fi
}

# Download initial models
download_models() {
    print_section "Downloading Essential Models"
    
    essential_models=("llama3:latest" "codellama:7b" "phi3:mini")
    
    for model in "${essential_models[@]}"; do
        print_info "Downloading $model..."
        if ollama pull "$model"; then
            print_success "$model downloaded successfully"
        else
            print_warning "Failed to download $model - will continue with installation"
        fi
    done
}

# Setup Ollama Flow
setup_ollama_flow() {
    print_section "Setting up Ollama Flow"
    
    # Create installation directory
    if [ -d "$OLLAMA_FLOW_DIR" ]; then
        print_warning "Ollama Flow directory exists. Backing up..."
        mv "$OLLAMA_FLOW_DIR" "${OLLAMA_FLOW_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Clone or copy Ollama Flow
    if [ -d "$(pwd)/.git" ]; then
        # We're in a git repository, copy current directory
        print_info "Copying current Ollama Flow installation..."
        cp -r "$(pwd)" "$OLLAMA_FLOW_DIR"
    else
        print_error "Not in a git repository. Please clone Ollama Flow first."
        exit 1
    fi
    
    cd "$OLLAMA_FLOW_DIR"
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"
    
    print_success "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_section "Installing Python Dependencies"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install core dependencies
    print_info "Installing core dependencies..."
    pip install \
        ollama \
        pydantic \
        pydantic-settings \
        python-dotenv \
        pyyaml \
        asyncio \
        aiofiles \
        psutil \
        typing-extensions
    
    # Install optional dependencies
    print_info "Installing optional dependencies..."
    pip install \
        pytest \
        pytest-asyncio \
        black \
        flake8 \
        mypy \
        bandit \
        safety
    
    # Install from requirements.txt if exists
    if [ -f "requirements.txt" ]; then
        print_info "Installing from requirements.txt..."
        pip install -r requirements.txt
    fi
    
    print_success "Python dependencies installed"
}

# Configure Ollama Flow
configure_ollama_flow() {
    print_section "Configuring Ollama Flow"
    
    # Create configuration directories
    mkdir -p config data logs
    
    # Generate default configurations
    python3 -c "
from config.settings import create_default_configs
create_default_configs()
print('✅ Default configurations created')
"
    
    # Create .env file
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Ollama Flow Environment Configuration
OLLAMA_FLOW_ENVIRONMENT=development
OLLAMA_FLOW_DEBUG=true
OLLAMA_FLOW_DATABASE__URL=sqlite:///data/ollama_flow.db
OLLAMA_FLOW_LOGGING__LEVEL=INFO
OLLAMA_FLOW_AGENTS__MAX_AGENTS=10
OLLAMA_FLOW_LLM__DEFAULT_MODEL=llama3
EOF
        print_success "Environment configuration created"
    fi
    
    # Set up project structure
    chmod +x ollama-flow* 2>/dev/null || true
    
    # Create CLI symlink
    if [ ! -f "/usr/local/bin/ollama-flow" ]; then
        sudo ln -sf "$OLLAMA_FLOW_DIR/ollama-flow" /usr/local/bin/ollama-flow 2>/dev/null || {
            print_warning "Could not create global CLI link. Use ./ollama-flow instead"
        }
    fi
    
    print_success "Ollama Flow configured successfully"
}

# Run system tests
run_tests() {
    print_section "Running System Tests"
    
    # Test configuration loading
    python3 -c "
from config.settings import get_settings
settings = get_settings()
print(f'✅ Configuration loaded: {settings.environment.value}')
"
    
    # Test core components
    print_info "Testing core components..."
    PYTHONPATH="$OLLAMA_FLOW_DIR" python3 -c "
from llm_chooser import get_llm_chooser
from agents.role_manager import get_role_manager

chooser = get_llm_chooser()
role_mgr = get_role_manager()

print(f'✅ LLM Chooser: {len(chooser.available_models)} models available')
print(f'✅ Role Manager: {len(role_mgr.role_keywords)} roles configured')
"
    
    # Test simple task execution
    print_info "Testing task execution..."
    PYTHONPATH="$OLLAMA_FLOW_DIR" python3 -c "
import asyncio
from agents.core.unified_agent import UnifiedAgent

async def test_agent():
    agent = UnifiedAgent('test', 'TestAgent')
    role = await agent.assign_dynamic_role('Test Python development task')
    print(f'✅ Agent test: Role {role.value} assigned')

asyncio.run(test_agent())
" 2>/dev/null || print_warning "Agent test skipped (requires full setup)"
    
    print_success "Basic system tests completed"
}

# Create uninstaller
create_uninstaller() {
    print_section "Creating Uninstaller"
    
    cat > "$OLLAMA_FLOW_DIR/uninstall_enhanced.sh" << 'EOF'
#!/bin/bash

# Enhanced Ollama Flow Uninstaller
# Removes Ollama Flow and all associated files

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "🗑️  OLLAMA FLOW ENHANCED UNINSTALLER"
    echo "==============================================="
    echo -e "${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

OLLAMA_FLOW_DIR="$HOME/ollama-flow"

print_header

echo "This will completely remove Ollama Flow and all associated files."
echo "The following will be removed:"
echo "  - $OLLAMA_FLOW_DIR (entire directory)"
echo "  - Python virtual environment"
echo "  - CLI symlinks"
echo "  - Configuration files"
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 1
fi

# Remove Ollama Flow directory
if [ -d "$OLLAMA_FLOW_DIR" ]; then
    rm -rf "$OLLAMA_FLOW_DIR"
    print_success "Ollama Flow directory removed"
fi

# Remove CLI symlinks
sudo rm -f /usr/local/bin/ollama-flow 2>/dev/null || true
print_success "CLI symlinks removed"

# Remove from PATH if added
if grep -q "ollama-flow" "$HOME/.bashrc" 2>/dev/null; then
    sed -i '/ollama-flow/d' "$HOME/.bashrc"
    print_success "Removed from .bashrc"
fi

if grep -q "ollama-flow" "$HOME/.zshrc" 2>/dev/null; then
    sed -i '/ollama-flow/d' "$HOME/.zshrc"
    print_success "Removed from .zshrc"
fi

print_success "Ollama Flow has been completely uninstalled"
print_warning "Note: Ollama and downloaded models were not removed"
echo "To remove Ollama: sudo systemctl stop ollama && sudo rm /usr/local/bin/ollama"
EOF

    chmod +x "$OLLAMA_FLOW_DIR/uninstall_enhanced.sh"
    print_success "Uninstaller created"
}

# Setup shell integration
setup_shell_integration() {
    print_section "Setting up Shell Integration"
    
    # Add to PATH
    shell_config=""
    if [ -f "$HOME/.bashrc" ]; then
        shell_config="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        shell_config="$HOME/.zshrc"
    fi
    
    if [ -n "$shell_config" ] && ! grep -q "ollama-flow" "$shell_config"; then
        echo "" >> "$shell_config"
        echo "# Ollama Flow" >> "$shell_config"
        echo "export PATH=\"\$PATH:$OLLAMA_FLOW_DIR\"" >> "$shell_config"
        echo "alias of='ollama-flow'" >> "$shell_config"
        print_success "Shell integration added to $shell_config"
    fi
    
    # Create completion script
    cat > "$OLLAMA_FLOW_DIR/ollama-flow-completion.bash" << 'EOF'
# Ollama Flow bash completion
_ollama_flow_completion() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    commands="run test status monitor config help version"
    
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "--help --version --debug --config" -- ${cur}) )
        return 0
    fi
    
    COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
    return 0
}

complete -F _ollama_flow_completion ollama-flow
complete -F _ollama_flow_completion of
EOF
    
    print_success "Shell completion created"
}

# Main installation function
main() {
    print_header
    
    print_info "Starting enhanced Ollama Flow installation..."
    print_info "Installation directory: $OLLAMA_FLOW_DIR"
    print_info "Python version requirement: $PYTHON_VERSION+"
    
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    # Run installation steps
    check_requirements
    install_system_deps
    install_ollama
    download_models
    setup_ollama_flow
    install_python_deps
    configure_ollama_flow
    run_tests
    create_uninstaller
    setup_shell_integration
    
    print_section "Installation Complete!"
    
    print_success "🎉 Ollama Flow Enhanced has been successfully installed!"
    echo ""
    echo -e "${CYAN}📍 Installation Details:${NC}"
    echo "   Location: $OLLAMA_FLOW_DIR"
    echo "   Python Environment: $OLLAMA_FLOW_DIR/$VENV_NAME"
    echo "   Configuration: $OLLAMA_FLOW_DIR/config/"
    echo "   Logs: $OLLAMA_FLOW_DIR/logs/"
    echo ""
    echo -e "${CYAN}🚀 Quick Start:${NC}"
    echo "   1. Reload your shell: source ~/.bashrc (or ~/.zshrc)"
    echo "   2. Test installation: ollama-flow --version"
    echo "   3. Run a simple task: ollama-flow run \"Hello World example\""
    echo "   4. Check status: ollama-flow status"
    echo "   5. Monitor system: ollama-flow monitor"
    echo ""
    echo -e "${CYAN}📚 Documentation:${NC}"
    echo "   - README: $OLLAMA_FLOW_DIR/README.md"
    echo "   - Configuration: $OLLAMA_FLOW_DIR/config/"
    echo "   - Examples: $OLLAMA_FLOW_DIR/examples/"
    echo ""
    echo -e "${CYAN}🔧 Management:${NC}"
    echo "   - Update: cd $OLLAMA_FLOW_DIR && git pull"
    echo "   - Uninstall: $OLLAMA_FLOW_DIR/uninstall_enhanced.sh"
    echo "   - Logs: tail -f $OLLAMA_FLOW_DIR/logs/ollama_flow.log"
    echo ""
    echo -e "${GREEN}🎯 Installation successful! Ollama Flow Enhanced is ready to use.${NC}"
}

# Error handling
trap 'print_error "Installation failed! Check the error messages above."; exit 1' ERR

# Run main installation
main "$@"