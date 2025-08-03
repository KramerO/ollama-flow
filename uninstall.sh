#!/bin/bash
# Ollama Flow Framework - Complete Uninstallation Script
# Safely removes all components installed by the Ollama Flow installer

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
CLI_WRAPPER="$BIN_DIR/ollama-flow"

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
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                🗑️  OLLAMA FLOW UNINSTALLER                      ║"
    echo "║          Complete Removal of Multi-AI Framework                 ║"
    echo "║                                                                  ║"
    echo "║  This will remove ALL Ollama Flow components from your system   ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Confirm uninstallation
confirm_uninstall() {
    print_banner
    
    echo ""
    print_warning "This will completely remove Ollama Flow from your system!"
    echo ""
    echo "The following will be removed:"
    echo "  • Framework files: $INSTALL_DIR"
    echo "  • CLI wrapper: $CLI_WRAPPER"
    echo "  • Configuration: $CONFIG_DIR"
    echo "  • PATH entries in shell profiles"
    echo "  • Session databases and logs"
    echo ""
    print_warning "Python dependencies will be kept (shared with other projects)"
    print_warning "Ollama itself will NOT be removed (you may still need it)"
    echo ""
    
    if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
        print_status "Force mode enabled - proceeding without confirmation"
        return 0
    fi
    
    read -p "Are you sure you want to uninstall Ollama Flow? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
}

# Stop any running Ollama Flow processes
stop_running_processes() {
    print_status "Stopping any running Ollama Flow processes..."
    
    local stopped_count=0
    
    # Stop ollama-flow processes
    if pgrep -f "ollama-flow" > /dev/null; then
        print_status "Found running ollama-flow processes, stopping them..."
        pkill -f "ollama-flow" 2>/dev/null || true
        stopped_count=$((stopped_count + 1))
        sleep 1
    fi
    
    # Stop enhanced_main.py processes
    if pgrep -f "enhanced_main.py" > /dev/null; then
        print_status "Found running enhanced_main.py processes, stopping them..."
        pkill -f "enhanced_main.py" 2>/dev/null || true
        stopped_count=$((stopped_count + 1))
        sleep 1
    fi
    
    # Stop any Python processes running Ollama Flow components
    for process in "neural_intelligence" "mcp_tools" "monitoring_system" "session_manager" "cli_dashboard"; do
        if pgrep -f "$process" > /dev/null; then
            print_status "Stopping $process processes..."
            pkill -f "$process" 2>/dev/null || true
            stopped_count=$((stopped_count + 1))
        fi
    done
    
    if [ $stopped_count -gt 0 ]; then
        print_success "Stopped $stopped_count running process groups"
        sleep 2  # Allow processes to fully terminate
    else
        print_success "No running Ollama Flow processes found"
    fi
}

# Remove framework files
remove_framework_files() {
    print_status "Removing framework files..."
    
    if [ -d "$INSTALL_DIR" ]; then
        # Get size before removal for user feedback
        local size=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1 || echo "unknown")
        
        rm -rf "$INSTALL_DIR"
        print_success "Removed framework directory ($size): $INSTALL_DIR"
    else
        print_warning "Framework directory not found: $INSTALL_DIR"
    fi
}

# Remove CLI wrapper
remove_cli_wrapper() {
    print_status "Removing CLI wrapper..."
    
    if [ -f "$CLI_WRAPPER" ]; then
        rm -f "$CLI_WRAPPER"
        print_success "Removed CLI wrapper: $CLI_WRAPPER"
    else
        print_warning "CLI wrapper not found: $CLI_WRAPPER"
    fi
    
    # Remove any backup CLI wrapper
    if [ -f "$CLI_WRAPPER-old" ]; then
        rm -f "$CLI_WRAPPER-old"
        print_success "Removed backup CLI wrapper: $CLI_WRAPPER-old"
    fi
    
    # Remove symlinks if they exist
    if [ -L "$CLI_WRAPPER" ]; then
        rm -f "$CLI_WRAPPER"
        print_success "Removed CLI wrapper symlink: $CLI_WRAPPER"
    fi
}

# Remove configuration files
remove_configuration() {
    print_status "Removing configuration files..."
    
    if [ -d "$CONFIG_DIR" ]; then
        rm -rf "$CONFIG_DIR"
        print_success "Removed configuration directory: $CONFIG_DIR"
    else
        print_warning "Configuration directory not found: $CONFIG_DIR"
    fi
}

# Remove PATH entries from shell profiles
remove_path_entries() {
    print_status "Removing PATH entries from shell profiles..."
    
    local profiles=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile")
    local removed_count=0
    
    for profile in "${profiles[@]}"; do
        if [ -f "$profile" ]; then
            # Check if our PATH entry exists
            if grep -q "Added by Ollama Flow installer" "$profile" 2>/dev/null; then
                print_status "Cleaning PATH entry from $(basename "$profile")..."
                
                # Create backup
                cp "$profile" "$profile.backup-$(date +%Y%m%d-%H%M%S)"
                
                # Remove our PATH entry and the comment
                sed -i '/# Added by Ollama Flow installer/d' "$profile"
                sed -i '/export PATH="$HOME\/.local\/bin:$PATH"/d' "$profile"
                
                removed_count=$((removed_count + 1))
                print_success "Cleaned PATH entry from $(basename "$profile")"
            fi
        fi
    done
    
    if [ $removed_count -gt 0 ]; then
        print_success "Removed PATH entries from $removed_count shell profile(s)"
        print_warning "Restart your terminal or run 'source ~/.bashrc' to apply changes"
    else
        print_success "No PATH entries found to remove"
    fi
}

# Clean up databases and logs
cleanup_databases_and_logs() {
    print_status "Cleaning up databases and log files..."
    
    local cleanup_count=0
    
    # Find and remove Ollama Flow databases
    for db_file in "ollama_flow_messages.db" "neural_intelligence.db" "mcp_tools.db" "monitoring.db" "sessions.db"; do
        if find . -name "$db_file" -type f 2>/dev/null | head -1 | grep -q .; then
            find . -name "$db_file" -type f -delete 2>/dev/null || true
            cleanup_count=$((cleanup_count + 1))
        fi
    done
    
    # Find and remove log files
    for log_pattern in "ollama_flow*.log" "neural_*.log" "mcp_*.log" "monitoring_*.log"; do
        if find . -name "$log_pattern" -type f 2>/dev/null | head -1 | grep -q .; then
            find . -name "$log_pattern" -type f -delete 2>/dev/null || true
            cleanup_count=$((cleanup_count + 1))
        fi
    done
    
    # Remove temporary files
    for temp_pattern in "tmp_ollama*" "*.tmp" ".ollama_*"; do
        if find . -name "$temp_pattern" -type f 2>/dev/null | head -1 | grep -q .; then
            find . -name "$temp_pattern" -type f -delete 2>/dev/null || true
            cleanup_count=$((cleanup_count + 1))
        fi
    done
    
    if [ $cleanup_count -gt 0 ]; then
        print_success "Cleaned up $cleanup_count database/log files"
    else
        print_success "No database/log files found to clean"
    fi
}

# Optional: Remove Python dependencies
offer_dependency_removal() {
    print_status "Checking Python dependencies..."
    
    local ollama_deps=(
        "ollama"
        "httpx"
        "aiofiles"
        "asyncio-mqtt"
        "paho-mqtt"
        "rich"
        "pydantic"
    )
    
    echo ""
    print_warning "The following Python packages were installed for Ollama Flow:"
    for dep in "${ollama_deps[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            echo "  • $dep (installed)"
        else
            echo "  • $dep (not found)"
        fi
    done
    
    echo ""
    print_warning "These packages might be used by other projects!"
    echo ""
    read -p "Do you want to remove these Python packages? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing Python dependencies..."
        for dep in "${ollama_deps[@]}"; do
            if python3 -c "import $dep" 2>/dev/null; then
                python3 -m pip uninstall -y "$dep" 2>/dev/null || true
                print_success "Removed $dep"
            fi
        done
    else
        print_success "Python dependencies kept (recommended)"
    fi
}

# Verify uninstallation
verify_uninstall() {
    print_status "Verifying uninstallation..."
    
    local issues=0
    
    # Check framework directory
    if [ -d "$INSTALL_DIR" ]; then
        print_error "Framework directory still exists: $INSTALL_DIR"
        issues=$((issues + 1))
    fi
    
    # Check CLI wrapper
    if [ -f "$CLI_WRAPPER" ]; then
        print_error "CLI wrapper still exists: $CLI_WRAPPER"
        issues=$((issues + 1))
    fi
    
    # Check configuration
    if [ -d "$CONFIG_DIR" ]; then
        print_error "Configuration directory still exists: $CONFIG_DIR"
        issues=$((issues + 1))
    fi
    
    # Check if command still works
    if command -v ollama-flow >/dev/null 2>&1; then
        print_error "ollama-flow command still available"
        issues=$((issues + 1))
    fi
    
    if [ $issues -eq 0 ]; then
        print_success "✅ Uninstallation verification passed"
        return 0
    else
        print_error "❌ Uninstallation verification found $issues issue(s)"
        return 1
    fi
}

# Show post-uninstall information
show_post_uninstall_info() {
    print_success "🎉 UNINSTALLATION COMPLETE!"
    echo ""
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│                        REMOVAL SUMMARY                          │"
    echo "├─────────────────────────────────────────────────────────────────┤"
    echo "│ ✅ Framework files removed from ~/.ollama-flow                  │"
    echo "│ ✅ CLI wrapper removed from ~/.local/bin/ollama-flow            │"
    echo "│ ✅ Configuration removed from ~/.config/ollama-flow             │"
    echo "│ ✅ PATH entries cleaned from shell profiles                     │"
    echo "│ ✅ Databases and logs cleaned up                                │"
    echo "│ ✅ Running processes stopped                                    │"
    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
    echo "📝 What was NOT removed:"
    echo "   • Ollama (you may still need it for other projects)"
    echo "   • Python dependencies (shared with other projects)"
    echo "   • Shell profile backups (*.backup-* files)"
    echo ""
    echo "🔄 To reinstall Ollama Flow:"
    echo "   curl -fsSL https://ollama-flow.ai/install.sh | sh"
    echo ""
    echo "Thank you for using Ollama Flow! 👋"
}

# Main uninstallation function
main() {
    # Parse arguments
    local force_mode=false
    if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
        force_mode=true
    fi
    
    # Confirmation
    if [ "$force_mode" = true ]; then
        confirm_uninstall "--force"
    else
        confirm_uninstall
    fi
    
    print_status "Starting Ollama Flow uninstallation..."
    
    # Uninstallation steps
    stop_running_processes
    remove_framework_files
    remove_cli_wrapper
    remove_configuration
    remove_path_entries
    cleanup_databases_and_logs
    
    # Optional dependency removal
    if [ "$force_mode" = false ]; then
        offer_dependency_removal
    fi
    
    # Verification
    if verify_uninstall; then
        show_post_uninstall_info
        exit 0
    else
        print_error "Uninstallation completed with issues"
        print_warning "Some manual cleanup may be required"
        exit 1
    fi
}

# Handle help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_banner
    echo ""
    echo "USAGE:"
    echo "  bash uninstall.sh [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --force, -f    Force uninstall without confirmation"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  bash uninstall.sh                # Interactive uninstall"
    echo "  bash uninstall.sh --force        # Force uninstall"
    echo ""
    exit 0
fi

# Run main function
main "$@"