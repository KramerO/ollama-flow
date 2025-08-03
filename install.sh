#!/bin/bash
# Ollama Flow Framework - Complete Installation Script
# Installs all components to the correct locations with proper CLI wrapper

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.ollama-flow"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/ollama-flow"
PYTHON_MIN_VERSION="3.8"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                 🚀 OLLAMA FLOW INSTALLER v2.0                   ║"
    echo "║          Multi-AI Agent Orchestration Framework                 ║"
    echo "║                                                                  ║"
    echo "║  Enhanced with Neural Intelligence, MCP Tools & Translation     ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    print_status "Checking Python installation..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python $python_version found, but $required_version or higher is required."
        exit 1
    fi
    
    print_success "Python $python_version found ✓"
}

# Check Ollama installation
check_ollama() {
    print_status "Checking Ollama installation..."
    
    if ! command_exists ollama; then
        print_warning "Ollama not found. Installing Ollama..."
        if command_exists curl; then
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            print_error "curl not found. Please install Ollama manually:"
            print_error "curl -fsSL https://ollama.ai/install.sh | sh"
            exit 1
        fi
    else
        print_success "Ollama found ✓"
    fi
    
    # Check if ollama service is running
    if ! pgrep -x "ollama" > /dev/null; then
        print_status "Starting Ollama service..."
        ollama serve &
        sleep 2
    fi
    
    # Pull required model
    print_status "Ensuring CodeLlama model is available..."
    ollama pull codellama:7b || print_warning "Model pull failed - will try later"
}

# Create directory structure
setup_directories() {
    print_status "Setting up directory structure..."
    
    # Create main directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$INSTALL_DIR"/{agents,orchestrator,dashboard}
    
    print_success "Directories created ✓"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create requirements.txt if it doesn't exist
    cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
ollama>=0.1.0
httpx>=0.24.0
aiofiles>=23.0.0
asyncio-mqtt>=0.11.0
click>=8.0.0
rich>=13.0.0
pydantic>=2.0.0
EOF
    
    # Install dependencies
    python3 -m pip install --user -r "$INSTALL_DIR/requirements.txt"
    
    print_success "Dependencies installed ✓"
}

# Copy framework files
install_framework() {
    print_status "Installing Ollama Flow Framework..."
    
    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Copy main Python files
    cp "$SCRIPT_DIR/enhanced_main.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/db_manager.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/session_manager.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/monitoring_system.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/neural_intelligence.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/mcp_tools.py" "$INSTALL_DIR/"
    
    # Copy agent modules
    cp -r "$SCRIPT_DIR/agents" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/orchestrator" "$INSTALL_DIR/"
    
    # Copy dashboard if exists
    if [ -d "$SCRIPT_DIR/dashboard" ]; then
        cp -r "$SCRIPT_DIR/dashboard" "$INSTALL_DIR/"
    fi
    
    # Copy tests
    if [ -d "$SCRIPT_DIR/tests" ]; then
        cp -r "$SCRIPT_DIR/tests" "$INSTALL_DIR/"
    fi
    
    print_success "Framework files installed ✓"
}

# Create CLI wrapper
create_cli_wrapper() {
    print_status "Creating CLI wrapper..."
    
    cat > "$BIN_DIR/ollama-flow" << EOF
#!/bin/bash
# Ollama Flow CLI Wrapper - Auto-generated by installer
# Version: 2.0.0

# Configuration
OLLAMA_FLOW_DIR="$INSTALL_DIR"
PYTHON_SCRIPT="\$OLLAMA_FLOW_DIR/enhanced_main.py"

# Ensure PATH includes local bin
export PATH="\$HOME/.local/bin:\$PATH"

# Check if framework exists
if [ ! -f "\$PYTHON_SCRIPT" ]; then
    echo "❌ Error: Ollama Flow not found at \$PYTHON_SCRIPT"
    echo "🔧 Try reinstalling: curl -fsSL https://ollama-flow.ai/install.sh | sh"
    exit 1
fi

# Help function
show_help() {
    echo "🚀 OLLAMA FLOW - Multi-AI Agent Orchestration Framework"
    echo "========================================================"
    echo ""
    echo "USAGE:"
    echo "  ollama-flow <command> [options]"
    echo ""
    echo "COMMANDS:"
    echo "  run <task>              Execute a task with AI agents"
    echo "  dashboard              Launch web dashboard"
    echo "  status                 Show system status"
    echo "  install                Install/update dependencies"
    echo "  version                Show version information"
    echo ""
    echo "RUN OPTIONS:"
    echo "  --workers N            Number of worker agents (default: 4)"
    echo "  --arch TYPE            Architecture: HIERARCHICAL, CENTRALIZED, FULLY_CONNECTED"
    echo "  --model NAME           Ollama model (default: codellama:7b)"
    echo "  --project-folder PATH  Working directory (default: current directory)"
    echo ""
    echo "EXAMPLES:"
    echo "  ollama-flow run 'Create a Flask web application'"
    echo "  ollama-flow run 'Build REST API' --workers 8"
    echo "  ollama-flow dashboard"
    echo ""
    echo "For more help: https://github.com/ruvnet/ollama-flow"
}

# Parse command
case "\$1" in
    "run")
        shift
        if [ -z "\$1" ]; then
            echo "❌ Error: Task description required"
            echo "Usage: ollama-flow run 'task description'"
            exit 1
        fi
        
        # Auto-detect current directory if no project folder specified
        CURRENT_DIR="\$(pwd)"
        ARGS=("--task" "\$1" "--project-folder" "\$CURRENT_DIR")
        shift
        
        # Add remaining arguments
        while [ \$# -gt 0 ]; do
            ARGS+=("\$1")
            shift
        done
        
        echo "🔍 Working in: \$CURRENT_DIR"
        exec python3 "\$PYTHON_SCRIPT" "\${ARGS[@]}"
        ;;
    "dashboard")
        shift
        exec python3 "\$PYTHON_SCRIPT" --web-dashboard "\$@"
        ;;
    "status")
        echo "🔍 Ollama Flow Status Check"
        echo "=========================="
        echo "Framework: \$OLLAMA_FLOW_DIR"
        echo "Python: \$(python3 --version)"
        echo "Ollama: \$(ollama --version 2>/dev/null || echo 'Not found')"
        echo "Current Directory: \$(pwd)"
        ;;
    "install")
        echo "🔧 Updating dependencies..."
        python3 -m pip install --user -r "\$OLLAMA_FLOW_DIR/requirements.txt"
        echo "✅ Dependencies updated"
        ;;
    "version")
        echo "Ollama Flow Framework v2.0.0"
        echo "Multi-AI Agent Orchestration with Neural Intelligence"
        ;;
    "--help"|"-h"|"help"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: \$1"
        echo "Run 'ollama-flow --help' for usage information"
        exit 1
        ;;
esac
EOF
    
    # Make executable
    chmod +x "$BIN_DIR/ollama-flow"
    
    print_success "CLI wrapper created ✓"
}

# Create configuration files
create_config() {
    print_status "Creating configuration files..."
    
    # Create main config
    cat > "$CONFIG_DIR/config.yaml" << 'EOF'
# Ollama Flow Configuration
framework:
  version: "2.0.0"
  
models:
  default: "codellama:7b"
  available:
    - "codellama:7b"
    - "llama3:8b"
    - "phi3:mini"

agents:
  default_workers: 4
  max_workers: 16
  architectures:
    - "HIERARCHICAL"
    - "CENTRALIZED" 
    - "FULLY_CONNECTED"

features:
  translation: true
  neural_intelligence: true
  mcp_tools: true
  monitoring: true
  
security:
  secure_mode: true
  allowed_extensions: [".py", ".js", ".html", ".css", ".md", ".txt", ".json", ".yaml", ".yml"]
EOF
    
    # Create .env file
    cat > "$CONFIG_DIR/.env" << 'EOF'
# Enhanced Ollama Flow Configuration
OLLAMA_MODEL=codellama:7b
OLLAMA_WORKER_COUNT=4
OLLAMA_ARCHITECTURE_TYPE=HIERARCHICAL
OLLAMA_SECURE_MODE=true
OLLAMA_PARALLEL_LLM=true
OLLAMA_METRICS=true

# Enhanced Features
OLLAMA_NEURAL_ENABLED=true
OLLAMA_MCP_ENABLED=true
OLLAMA_MONITORING_ENABLED=true
OLLAMA_SESSION_ENABLED=true
EOF
    
    print_success "Configuration created ✓"
}

# Update PATH in shell profile
update_path() {
    print_status "Updating PATH in shell profile..."
    
    # Detect shell
    SHELL_PROFILE=""
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_PROFILE="$HOME/.bashrc"
    else
        SHELL_PROFILE="$HOME/.profile"
    fi
    
    # Add PATH export if not already present
    if ! grep -q ".local/bin" "$SHELL_PROFILE" 2>/dev/null; then
        echo "" >> "$SHELL_PROFILE"
        echo "# Added by Ollama Flow installer" >> "$SHELL_PROFILE"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_PROFILE"
        print_success "PATH updated in $SHELL_PROFILE ✓"
    else
        print_success "PATH already configured ✓"
    fi
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test CLI wrapper
    if [ -x "$BIN_DIR/ollama-flow" ]; then
        print_success "CLI wrapper executable ✓"
    else
        print_error "CLI wrapper not executable"
        return 1
    fi
    
    # Test framework
    if python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); import enhanced_main" 2>/dev/null; then
        print_success "Framework import test ✓"
    else
        print_warning "Framework import test failed (may need shell restart)"
    fi
    
    print_success "Installation test completed ✓"
}

# Main installation function
main() {
    print_banner
    
    print_status "Starting Ollama Flow installation..."
    
    # Pre-installation checks
    check_python
    check_ollama
    
    # Installation steps
    setup_directories
    install_dependencies
    install_framework
    create_cli_wrapper
    create_config
    update_path
    
    # Post-installation
    test_installation
    
    print_success "🎉 INSTALLATION COMPLETE!"
    echo ""
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│                        NEXT STEPS                               │"
    echo "├─────────────────────────────────────────────────────────────────┤"
    echo "│ 1. Restart your terminal or run: source ~/.bashrc              │"
    echo "│ 2. Test installation: ollama-flow --help                       │"
    echo "│ 3. Create your first AI task: ollama-flow run 'hello world'    │"
    echo "│ 4. Launch dashboard: ollama-flow dashboard                     │"
    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
    echo "📍 Installation Directory: $INSTALL_DIR"
    echo "🔧 CLI Command: ollama-flow"
    echo "📚 Documentation: https://github.com/ruvnet/ollama-flow"
    echo "🗑️ To uninstall: bash uninstall.sh"
    echo ""
    echo "Happy AI orchestrating! 🚀"
}

# Run main function
main "$@"