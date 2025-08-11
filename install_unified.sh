#!/bin/bash
"""
Ollama Flow Unified Installation Script v3.0.0
Installs everything to ~/ollama_flow and sets up proper CLI links
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BASE="$HOME/ollama_flow"
CLI_NAME="ollama-flow"
BIN_DIR="$HOME/.local/bin"

print_banner() {
    echo -e "${BLUE}"
    echo "🚀 OLLAMA FLOW v3.0.0 - UNIFIED INSTALLATION"
    echo "============================================"
    echo "All files to ~/ollama_flow with proper CLI links"
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
    
    # Create directories
    mkdir -p "$INSTALL_BASE"
    mkdir -p "$BIN_DIR"
    echo -e "${GREEN}✅ Directories created${NC}"
}

install_dependencies() {
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    
    # Check if requirements.txt exists
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        python3 -m pip install --user -r "$SCRIPT_DIR/requirements.txt"
    else
        # Install common dependencies
        python3 -m pip install --user requests ollama-python asyncio aiofiles python-dotenv psutil httpx beautifulsoup4 jinja2 netaddr
    fi
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

copy_files() {
    echo -e "${YELLOW}📁 Copying files to ~/ollama_flow...${NC}"
    
    # Backup existing installation
    if [[ -d "$INSTALL_BASE" ]]; then
        echo -e "${YELLOW}⚠️ Existing installation found, creating backup...${NC}"
        mv "$INSTALL_BASE" "${INSTALL_BASE}.backup.$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$INSTALL_BASE"
    fi
    
    # Copy all necessary files
    echo -e "${BLUE}Copying Python modules...${NC}"
    cp -r "$SCRIPT_DIR/agents" "$INSTALL_BASE/"
    cp -r "$SCRIPT_DIR/orchestrator" "$INSTALL_BASE/"
    
    # Copy main Python files
    echo -e "${BLUE}Copying main files...${NC}"
    cp "$SCRIPT_DIR/enhanced_main.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/main.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/db_manager.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/neural_intelligence.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/mcp_tools.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/monitoring_system.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/session_manager.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/gpu_autoscaler.py" "$INSTALL_BASE/"
    
    # Copy configuration files
    echo -e "${BLUE}Copying configuration files...${NC}"
    cp "$SCRIPT_DIR/llm_chooser.py" "$INSTALL_BASE/"
    cp "$SCRIPT_DIR/llm_models.json" "$INSTALL_BASE/"
    
    # Copy config directory if it exists
    if [[ -d "$SCRIPT_DIR/config" ]]; then
        cp -r "$SCRIPT_DIR/config" "$INSTALL_BASE/"
    fi
    
    # Copy any additional files
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_BASE/"
    fi
    
    echo -e "${GREEN}✅ Files copied successfully${NC}"
}

create_cli_wrapper() {
    echo -e "${YELLOW}🔧 Creating CLI wrapper...${NC}"
    
    # Create the main CLI wrapper script
    cat > "$INSTALL_BASE/ollama-flow" << 'EOF'
#!/usr/bin/env python3
"""
Ollama Flow CLI Wrapper
Unified entry point for all ollama-flow functionality
"""

import sys
import os
import subprocess
import argparse

# Add the ollama_flow directory to Python path
OLLAMA_FLOW_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OLLAMA_FLOW_DIR)

def main():
    parser = argparse.ArgumentParser(
        description="Ollama Flow - Multi-Agent Task Processing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command (main functionality)
    run_parser = subparsers.add_parser('run', help='Execute a task with agents')
    run_parser.add_argument('task', help='Task description')
    run_parser.add_argument('--drones', type=int, help='Number of drone agents')
    run_parser.add_argument('--sub-queens', type=int, help='Number of sub-queen agents')
    run_parser.add_argument('--arch', choices=['HIERARCHICAL', 'CENTRALIZED', 'FULLY_CONNECTED'], help='Architecture type')
    run_parser.add_argument('--model', help='Ollama model to use')
    run_parser.add_argument('--secure', action='store_true', help='Secure mode')
    run_parser.add_argument('--project-folder', help='Project folder path')
    run_parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    run_parser.add_argument('--metrics', action='store_true', help='Enable metrics')
    run_parser.add_argument('--benchmark', action='store_true', help='Benchmark mode')
    run_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Log level')
    run_parser.add_argument('--auto-scaling', action='store_true', help='Enable auto-scaling')
    run_parser.add_argument('--strategy', choices=['GPU_MEMORY_BASED', 'WORKLOAD_BASED', 'HYBRID', 'CONSERVATIVE', 'AGGRESSIVE'], help='Auto-scaling strategy')
    run_parser.add_argument('--min-agents', type=int, help='Minimum agents')
    run_parser.add_argument('--max-agents', type=int, help='Maximum agents')
    run_parser.add_argument('--docker', action='store_true', help='Docker mode')
    
    # Dashboard commands
    subparsers.add_parser('dashboard', help='Launch web dashboard')
    subparsers.add_parser('cli-dash', help='Launch CLI dashboard')
    
    # Session management
    subparsers.add_parser('sessions', help='Manage sessions')
    
    # Models command
    models_parser = subparsers.add_parser('models', help='Model management')
    models_subparsers = models_parser.add_subparsers(dest='models_action')
    models_subparsers.add_parser('list', help='List available models')
    models_subparsers.add_parser('show', help='Show model details')
    
    # Neural intelligence
    subparsers.add_parser('neural', help='Neural intelligence features')
    
    # Monitoring
    subparsers.add_parser('monitoring', help='System monitoring')
    
    # Utility commands
    subparsers.add_parser('cleanup', help='Cleanup database and files')
    subparsers.add_parser('stop', help='Stop all agents')
    subparsers.add_parser('install', help='Installation utilities')
    subparsers.add_parser('version', help='Show version information')
    
    # Help command
    subparsers.add_parser('help', help='Show help information')
    
    # Parse arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Handle --help and -h at top level
    if '--help' in sys.argv or '-h' in sys.argv:
        parser.print_help()
        return
        
    args, unknown = parser.parse_known_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle commands
    if args.command == 'run':
        # Use enhanced_main.py for run command
        cmd = [sys.executable, os.path.join(OLLAMA_FLOW_DIR, 'enhanced_main.py')]
        cmd.extend(['--task', args.task])
        
        if args.drones:
            cmd.extend(['--workers', str(args.drones)])
        if args.sub_queens:
            cmd.extend(['--sub-queens', str(args.sub_queens)])
        if args.arch:
            cmd.extend(['--arch', args.arch])
        if args.model:
            cmd.extend(['--model', args.model])
        if args.secure:
            cmd.append('--secure')
        if args.project_folder:
            cmd.extend(['--project-folder', args.project_folder])
        if args.interactive:
            cmd.append('--interactive')
        if args.metrics:
            cmd.append('--metrics')
        if args.benchmark:
            cmd.append('--benchmark')
        if args.log_level:
            cmd.extend(['--log-level', args.log_level])
        if args.auto_scaling:
            cmd.append('--auto-scaling')
        if args.strategy:
            cmd.extend(['--strategy', args.strategy])
        if args.min_agents:
            cmd.extend(['--min-agents', str(args.min_agents)])
        if args.max_agents:
            cmd.extend(['--max-agents', str(args.max_agents)])
        if args.docker:
            cmd.append('--docker')
        
        # Add any unknown arguments
        cmd.extend(unknown)
        
        # Execute
        os.chdir(OLLAMA_FLOW_DIR)
        subprocess.run(cmd)
        
    elif args.command == 'models':
        if args.models_action == 'list':
            # Use llm_chooser for model listing
            cmd = [sys.executable, os.path.join(OLLAMA_FLOW_DIR, 'llm_chooser.py'), '--list']
            os.chdir(OLLAMA_FLOW_DIR)
            subprocess.run(cmd)
        elif args.models_action == 'show':
            cmd = [sys.executable, os.path.join(OLLAMA_FLOW_DIR, 'llm_chooser.py'), '--show']
            os.chdir(OLLAMA_FLOW_DIR)
            subprocess.run(cmd)
        else:
            print("Available model commands:")
            print("  list - List available models")
            print("  show - Show model details")
            
    elif args.command == 'version':
        print("Ollama Flow v3.0.0")
        print("Unified Multi-Agent Task Processing Framework")
        
    elif args.command == 'help':
        parser.print_help()
        
    else:
        # For other commands, try to find corresponding Python files
        cmd = [sys.executable, os.path.join(OLLAMA_FLOW_DIR, 'enhanced_main.py')]
        
        if args.command == 'dashboard':
            cmd.extend(['--web-dashboard'])
        elif args.command == 'cli-dash':
            cmd.extend(['--cli-dashboard'])
        elif args.command == 'cleanup':
            cmd.extend(['--cleanup'])
        elif args.command == 'stop':
            cmd.extend(['--stop-agents'])
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            return
        
        # Execute
        os.chdir(OLLAMA_FLOW_DIR)
        subprocess.run(cmd)

if __name__ == '__main__':
    main()
EOF
    
    # Make CLI executable
    chmod +x "$INSTALL_BASE/ollama-flow"
    echo -e "${GREEN}✅ CLI wrapper created${NC}"
}

create_symlinks() {
    echo -e "${YELLOW}🔗 Creating symlinks...${NC}"
    
    # Remove existing symlink/file
    if [[ -L "$BIN_DIR/$CLI_NAME" ]] || [[ -f "$BIN_DIR/$CLI_NAME" ]]; then
        echo -e "${YELLOW}⚠️ Removing existing CLI installation...${NC}"
        rm -f "$BIN_DIR/$CLI_NAME"
    fi
    
    # Create symlink to the wrapper
    ln -sf "$INSTALL_BASE/ollama-flow" "$BIN_DIR/$CLI_NAME"
    
    echo -e "${GREEN}✅ Symlink created: $BIN_DIR/$CLI_NAME -> $INSTALL_BASE/ollama-flow${NC}"
}

setup_path() {
    echo -e "${YELLOW}🛤️ Setting up PATH...${NC}"
    
    # Check if bin directory is in PATH
    if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
        echo -e "${YELLOW}⚠️ $BIN_DIR is not in your PATH${NC}"
        echo "Adding to ~/.bashrc..."
        
        # Add to bashrc
        echo "" >> ~/.bashrc
        echo "# Ollama Flow CLI" >> ~/.bashrc
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.bashrc
        
        echo -e "${GREEN}✅ Added to ~/.bashrc${NC}"
        echo -e "${YELLOW}💡 Run: source ~/.bashrc or restart terminal${NC}"
    else
        echo -e "${GREEN}✅ $BIN_DIR is already in PATH${NC}"
    fi
}

create_config() {
    echo -e "${YELLOW}⚙️ Creating configuration...${NC}"
    
    # Create config directory
    CONFIG_DIR="$HOME/.config/ollama-flow"
    mkdir -p "$CONFIG_DIR"
    
    # Create default configuration
    cat > "$CONFIG_DIR/config.json" << EOF
{
    "version": "3.0.0",
    "install_path": "$INSTALL_BASE",
    "default_model": "auto",
    "default_architecture": "HIERARCHICAL",
    "default_workers": 4,
    "auto_model_selection": true,
    "security_mode": true,
    "llm_chooser_config": "$INSTALL_BASE/llm_models.json"
}
EOF
    
    echo -e "${GREEN}✅ Configuration created${NC}"
}

test_installation() {
    echo -e "${YELLOW}🧪 Testing installation...${NC}"
    
    # Test if CLI is accessible
    if command -v "$CLI_NAME" &> /dev/null; then
        echo -e "${GREEN}✅ CLI is accessible from PATH${NC}"
        
        # Test version command
        if "$CLI_NAME" version &> /dev/null; then
            echo -e "${GREEN}✅ CLI functionality working${NC}"
        else
            echo -e "${YELLOW}⚠️ CLI needs PATH refresh${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ CLI not yet accessible (restart terminal or source ~/.bashrc)${NC}"
    fi
    
    # Test direct execution
    if "$INSTALL_BASE/ollama-flow" version &> /dev/null; then
        echo -e "${GREEN}✅ Direct execution working${NC}"
    else
        echo -e "${RED}❌ Direct execution failed${NC}"
    fi
}

show_completion() {
    echo -e "${GREEN}"
    echo "🎉 UNIFIED INSTALLATION COMPLETE!"
    echo "================================="
    echo -e "${NC}"
    echo "Ollama Flow v3.0.0 has been installed successfully!"
    echo
    echo -e "${BLUE}📍 Installation Details:${NC}"
    echo "  📁 Base Directory: $INSTALL_BASE"
    echo "  🔗 CLI Symlink: $BIN_DIR/$CLI_NAME"
    echo "  ⚙️ Configuration: $HOME/.config/ollama-flow/"
    echo
    echo -e "${BLUE}🚀 Usage Examples:${NC}"
    echo "  $CLI_NAME run \"Create a Python web scraper\""
    echo "  $CLI_NAME models list"
    echo "  $CLI_NAME dashboard"
    echo "  $CLI_NAME version"
    echo
    echo -e "${BLUE}📂 All Files Located In:${NC}"
    echo "  $INSTALL_BASE/"
    echo "  ├── agents/              # Agent modules"
    echo "  ├── orchestrator/        # Orchestration system"
    echo "  ├── enhanced_main.py     # Main entry point"
    echo "  ├── llm_chooser.py       # Model selection"
    echo "  ├── ollama-flow          # CLI wrapper"
    echo "  └── ..."
    echo
    echo -e "${YELLOW}⚠️ IMPORTANT: Restart your terminal or run:${NC}"
    echo "  source ~/.bashrc"
    echo
    echo -e "${GREEN}✅ Ready to use!${NC} Try: $CLI_NAME --help"
}

main() {
    print_banner
    check_requirements
    install_dependencies
    copy_files
    create_cli_wrapper
    create_symlinks
    setup_path
    create_config
    test_installation
    show_completion
}

# Run installation
main "$@"