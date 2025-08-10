#!/bin/bash
"""
Ollama Flow CLI Installation Script v2.5.0
Installs the enhanced CLI system-wide with LLM Chooser
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_NAME="ollama-flow"

print_banner() {
    echo -e "${BLUE}"
    echo "🚀 OLLAMA FLOW v2.6.0 - CLI INSTALLATION"
    echo "=========================================="
    echo "Dynamic Role Assignment & Auto-Reset CLI"
    echo -e "${NC}"
}

check_requirements() {
    echo -e "${YELLOW}📋 Checking requirements...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"
    
    # Check Ollama
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}❌ Ollama is required but not installed${NC}"
        echo "Install with: curl -fsSL https://ollama.ai/install.sh | sh"
        exit 1
    fi
    echo -e "${GREEN}✅ Ollama found: $(ollama --version)${NC}"
    
    # Check if running as root for system-wide install
    if [[ $EUID -eq 0 ]]; then
        INSTALL_DIR="/usr/local/bin"
        echo -e "${GREEN}✅ Running as root - system-wide installation${NC}"
    else
        INSTALL_DIR="$HOME/.local/bin"
        echo -e "${YELLOW}⚠️  Running as user - local installation to $INSTALL_DIR${NC}"
        mkdir -p "$INSTALL_DIR"
    fi
}

install_dependencies() {
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    
    # Check if requirements.txt exists
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        python3 -m pip install --user -r "$SCRIPT_DIR/requirements.txt"
    else
        # Install common dependencies
        python3 -m pip install --user requests ollama-python asyncio aiofiles python-dotenv
    fi
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

install_cli() {
    echo -e "${YELLOW}🔧 Installing CLI...${NC}"
    
    # Make CLI executable
    chmod +x "$SCRIPT_DIR/$CLI_NAME"
    
    # Copy or symlink CLI to installation directory
    if [[ -f "$INSTALL_DIR/$CLI_NAME" ]]; then
        echo -e "${YELLOW}⚠️  Existing installation found, backing up...${NC}"
        mv "$INSTALL_DIR/$CLI_NAME" "$INSTALL_DIR/${CLI_NAME}.backup"
    fi
    
    # Create symlink instead of copy to allow updates
    ln -sf "$SCRIPT_DIR/$CLI_NAME" "$INSTALL_DIR/$CLI_NAME"
    
    echo -e "${GREEN}✅ CLI installed to $INSTALL_DIR/$CLI_NAME${NC}"
    
    # Check if install directory is in PATH
    if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
        echo -e "${YELLOW}⚠️  $INSTALL_DIR is not in your PATH${NC}"
        echo "Add this to your ~/.bashrc or ~/.zshrc:"
        echo "export PATH=\"$INSTALL_DIR:\$PATH\""
        
        # Auto-add to bashrc if user confirms
        read -p "Add to ~/.bashrc automatically? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
            echo -e "${GREEN}✅ Added to ~/.bashrc${NC}"
        fi
    fi
}

create_config() {
    echo -e "${YELLOW}⚙️ Creating configuration...${NC}"
    
    # Create config directory
    CONFIG_DIR="$HOME/.config/ollama-flow"
    mkdir -p "$CONFIG_DIR"
    
    # Create default configuration if it doesn't exist
    if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
        cat > "$CONFIG_DIR/config.json" << EOF
{
    "version": "2.6.0",
    "default_model": "auto",
    "default_architecture": "HIERARCHICAL",
    "default_workers": 4,
    "auto_model_selection": true,
    "security_mode": true,
    "llm_chooser_config": "$SCRIPT_DIR/llm_models.json"
}
EOF
        echo -e "${GREEN}✅ Created default configuration${NC}"
    fi
    
    # Copy LLM chooser config if it exists
    if [[ -f "$SCRIPT_DIR/llm_models.json" ]]; then
        cp "$SCRIPT_DIR/llm_models.json" "$CONFIG_DIR/"
        echo -e "${GREEN}✅ LLM Chooser configuration copied${NC}"
    fi
}

test_installation() {
    echo -e "${YELLOW}🧪 Testing installation...${NC}"
    
    # Test CLI execution
    if "$INSTALL_DIR/$CLI_NAME" version &> /dev/null; then
        echo -e "${GREEN}✅ CLI installation successful${NC}"
    else
        echo -e "${RED}❌ CLI installation failed${NC}"
        exit 1
    fi
    
    # Test model listing
    if "$INSTALL_DIR/$CLI_NAME" models list &> /dev/null; then
        echo -e "${GREEN}✅ LLM Chooser integration working${NC}"
    else
        echo -e "${YELLOW}⚠️  LLM Chooser may need configuration${NC}"
    fi
}

show_completion() {
    echo -e "${GREEN}"
    echo "🎉 INSTALLATION COMPLETE!"
    echo "========================="
    echo -e "${NC}"
    echo "Ollama Flow v2.6.0 CLI has been installed successfully!"
    echo
    echo -e "${BLUE}📍 Installation Location:${NC} $INSTALL_DIR/$CLI_NAME"
    echo -e "${BLUE}📁 Configuration:${NC} $HOME/.config/ollama-flow/"
    echo
    echo -e "${BLUE}🚀 Quick Start:${NC}"
    echo "  $CLI_NAME run \"Create a Python web scraper\""
    echo "  $CLI_NAME models list"
    echo "  $CLI_NAME dashboard"
    echo
    echo -e "${BLUE}🆕 New Features in v2.6.0:${NC}"
    echo "  • 🎯 Dynamic Role Assignment: Agents automatically choose best role"
    echo "  • 🔄 Database Auto-Reset: Fresh start on every run"
    echo "  • 🧠 Smart Task Analysis: 90% role assignment accuracy"
    echo "  • ⚡ Zero Configuration: Just run tasks, agents handle the rest"
    echo "  • 🎭 5 Expert Roles: Developer, Analyst, Security, Architect, Data Scientist"
    echo
    echo -e "${YELLOW}💡 Tip:${NC} Use 'ollama-flow --help' for detailed usage information"
    
    if [[ $EUID -ne 0 ]]; then
        echo -e "${YELLOW}⚠️  Don't forget to reload your shell or run: source ~/.bashrc${NC}"
    fi
}

main() {
    print_banner
    check_requirements
    install_dependencies
    install_cli
    create_config
    test_installation
    show_completion
}

# Run installation
main "$@"