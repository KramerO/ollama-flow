#!/bin/bash

# Enhanced Ollama Flow Uninstaller v2.0
# Completely removes Ollama Flow and all associated components

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_FLOW_DIR="$HOME/ollama-flow"
OLD_INSTALL_DIR="$HOME/.ollama-flow"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/ollama-flow"
GLOBAL_BIN="/usr/local/bin/ollama-flow"

print_header() {
    echo -e "${RED}"
    echo "==============================================="
    echo "🗑️  OLLAMA FLOW ENHANCED UNINSTALLER v2.0"
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

# Function to remove directory safely
remove_directory() {
    local dir_path="$1"
    local dir_name="$2"
    
    if [ -d "$dir_path" ]; then
        print_info "Removing $dir_name: $dir_path"
        rm -rf "$dir_path"
        print_success "$dir_name removed"
    else
        print_info "$dir_name not found: $dir_path"
    fi
}

# Function to remove file safely
remove_file() {
    local file_path="$1"
    local file_name="$2"
    
    if [ -f "$file_path" ]; then
        print_info "Removing $file_name: $file_path"
        rm -f "$file_path"
        print_success "$file_name removed"
    else
        print_info "$file_name not found: $file_path"
    fi
}

# Check for active processes
check_active_processes() {
    print_section "Checking for Active Ollama Flow Processes"
    
    # Check for ollama-flow processes
    if pgrep -f "ollama-flow" > /dev/null; then
        print_warning "Active Ollama Flow processes found. Attempting to stop them..."
        pkill -f "ollama-flow" || true
        sleep 2
        
        # Force kill if still running
        if pgrep -f "ollama-flow" > /dev/null; then
            print_warning "Force killing remaining processes..."
            pkill -9 -f "ollama-flow" || true
        fi
        print_success "Processes stopped"
    else
        print_success "No active Ollama Flow processes found"
    fi
    
    # Check for Python processes running our code
    if pgrep -f "enhanced_main.py\|unified_agent.py" > /dev/null; then
        print_warning "Active Ollama Flow Python processes found. Stopping them..."
        pkill -f "enhanced_main.py\|unified_agent.py" || true
        sleep 1
    fi
}

# Remove installation directories
remove_installations() {
    print_section "Removing Installation Directories"
    
    # Remove main installation directory
    remove_directory "$OLLAMA_FLOW_DIR" "Main Ollama Flow directory"
    
    # Remove old installation directory
    remove_directory "$OLD_INSTALL_DIR" "Legacy installation directory"
    
    # Remove configuration directory
    remove_directory "$CONFIG_DIR" "Configuration directory"
    
    # Check for any remaining ollama-flow directories
    find "$HOME" -maxdepth 2 -name "*ollama-flow*" -type d 2>/dev/null | while read -r dir; do
        if [ "$dir" != "$OLLAMA_FLOW_DIR" ] && [ "$dir" != "$OLD_INSTALL_DIR" ] && [ "$dir" != "$CONFIG_DIR" ]; then
            print_warning "Found additional directory: $dir"
            read -p "Remove this directory? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                remove_directory "$dir" "Additional directory"
            fi
        fi
    done
}

# Remove CLI and executables
remove_cli() {
    print_section "Removing CLI and Executables"
    
    # Remove local binary
    remove_file "$BIN_DIR/ollama-flow" "Local CLI executable"
    
    # Remove global binary (requires sudo)
    if [ -f "$GLOBAL_BIN" ]; then
        print_info "Removing global CLI executable: $GLOBAL_BIN"
        if sudo rm -f "$GLOBAL_BIN" 2>/dev/null; then
            print_success "Global CLI executable removed"
        else
            print_warning "Could not remove global CLI executable (may require manual removal)"
        fi
    fi
    
    # Remove shell completion
    local completion_files=(
        "/etc/bash_completion.d/ollama-flow"
        "/usr/share/bash-completion/completions/ollama-flow"
        "$HOME/.bash_completion.d/ollama-flow"
    )
    
    for completion_file in "${completion_files[@]}"; do
        remove_file "$completion_file" "Shell completion"
    done
}

# Clean shell configuration
clean_shell_config() {
    print_section "Cleaning Shell Configuration"
    
    local shell_files=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile")
    
    for shell_file in "${shell_files[@]}"; do
        if [ -f "$shell_file" ]; then
            # Check if file contains ollama-flow references
            if grep -q "ollama-flow" "$shell_file" 2>/dev/null; then
                print_info "Cleaning ollama-flow references from $shell_file"
                
                # Create backup
                cp "$shell_file" "${shell_file}.backup.$(date +%Y%m%d_%H%M%S)"
                
                # Remove ollama-flow related lines
                sed -i '/# Ollama Flow/d' "$shell_file" 2>/dev/null || true
                sed -i '/ollama-flow/d' "$shell_file" 2>/dev/null || true
                sed -i '/OLLAMA_FLOW/d' "$shell_file" 2>/dev/null || true
                sed -i '/alias of=/d' "$shell_file" 2>/dev/null || true
                
                print_success "Cleaned $shell_file"
            fi
        fi
    done
}

# Remove Python packages
remove_python_packages() {
    print_section "Removing Python Packages"
    
    print_info "Checking for Ollama Flow Python packages..."
    
    # List of packages that might have been installed
    local packages=(
        "pydantic-settings"
        "typing-inspection"
    )
    
    for package in "${packages[@]}"; do
        if pip3 show "$package" > /dev/null 2>&1; then
            print_warning "Found Python package: $package"
            read -p "Remove this package? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pip3 uninstall "$package" -y || print_warning "Could not remove $package"
            fi
        fi
    done
}

# Remove logs and temporary files
remove_logs_temp() {
    print_section "Removing Logs and Temporary Files"
    
    # Remove log files
    local log_locations=(
        "$HOME/ollama_flow.log"
        "$HOME/logs/ollama_flow.log"
        "$OLLAMA_FLOW_DIR/logs"
        "/tmp/ollama-flow*"
        "/tmp/ollama_flow*"
    )
    
    for log_location in "${log_locations[@]}"; do
        if ls $log_location > /dev/null 2>&1; then
            print_info "Removing logs: $log_location"
            rm -rf $log_location
            print_success "Logs removed"
        fi
    done
    
    # Remove database files
    find "$HOME" -name "ollama_flow*.db" -type f 2>/dev/null | while read -r db_file; do
        print_info "Removing database: $db_file"
        rm -f "$db_file"
    done
    
    # Remove cache directories
    local cache_dirs=(
        "$HOME/.cache/ollama-flow"
        "$HOME/.local/share/ollama-flow"
    )
    
    for cache_dir in "${cache_dirs[@]}"; do
        remove_directory "$cache_dir" "Cache directory"
    done
}

# Remove systemd service (if exists)
remove_service() {
    print_section "Removing System Services"
    
    local service_files=(
        "/etc/systemd/system/ollama-flow.service"
        "$HOME/.config/systemd/user/ollama-flow.service"
    )
    
    for service_file in "${service_files[@]}"; do
        if [ -f "$service_file" ]; then
            print_info "Removing systemd service: $service_file"
            
            # Stop and disable service
            if systemctl is-active ollama-flow > /dev/null 2>&1; then
                sudo systemctl stop ollama-flow || true
            fi
            
            if systemctl is-enabled ollama-flow > /dev/null 2>&1; then
                sudo systemctl disable ollama-flow || true
            fi
            
            # Remove service file
            sudo rm -f "$service_file" || print_warning "Could not remove service file"
            
            # Reload systemd
            sudo systemctl daemon-reload || true
            
            print_success "Service removed"
        fi
    done
}

# Verification function
verify_removal() {
    print_section "Verifying Removal"
    
    local remaining_items=()
    
    # Check for remaining directories
    if [ -d "$OLLAMA_FLOW_DIR" ]; then
        remaining_items+=("Directory: $OLLAMA_FLOW_DIR")
    fi
    
    if [ -d "$OLD_INSTALL_DIR" ]; then
        remaining_items+=("Directory: $OLD_INSTALL_DIR")
    fi
    
    if [ -d "$CONFIG_DIR" ]; then
        remaining_items+=("Directory: $CONFIG_DIR")
    fi
    
    # Check for CLI executable
    if [ -f "$BIN_DIR/ollama-flow" ] || [ -f "$GLOBAL_BIN" ]; then
        remaining_items+=("CLI executable")
    fi
    
    # Check for running processes
    if pgrep -f "ollama-flow" > /dev/null; then
        remaining_items+=("Running processes")
    fi
    
    if [ ${#remaining_items[@]} -eq 0 ]; then
        print_success "✅ Complete removal verified - no Ollama Flow components found"
        return 0
    else
        print_warning "Some items may still remain:"
        for item in "${remaining_items[@]}"; do
            echo "  - $item"
        done
        return 1
    fi
}

# Interactive confirmation
confirm_removal() {
    print_header
    
    echo -e "${YELLOW}"
    echo "This will COMPLETELY remove Ollama Flow and all associated files."
    echo ""
    echo "The following will be removed:"
    echo "  • All Ollama Flow directories and files"
    echo "  • CLI executables and shell integration"
    echo "  • Configuration files and logs"
    echo "  • Python packages (optional)"
    echo "  • System services (if any)"
    echo ""
    echo "This action CANNOT be undone!"
    echo -e "${NC}"
    
    read -p "Are you absolutely sure you want to continue? (type 'yes' to confirm): " -r
    
    if [ "$REPLY" != "yes" ]; then
        print_info "Uninstallation cancelled."
        exit 0
    fi
    
    echo ""
    read -p "Last chance! Type 'DELETE' to proceed: " -r
    
    if [ "$REPLY" != "DELETE" ]; then
        print_info "Uninstallation cancelled."
        exit 0
    fi
}

# Show final summary
show_summary() {
    print_section "Uninstallation Summary"
    
    echo -e "${GREEN}"
    echo "🎉 Ollama Flow has been completely removed from your system!"
    echo ""
    echo "What was removed:"
    echo "  ✅ All installation directories"
    echo "  ✅ CLI executables and shell integration"
    echo "  ✅ Configuration files and logs"
    echo "  ✅ Temporary and cache files"
    echo "  ✅ System services (if any)"
    echo ""
    echo -e "${CYAN}"
    echo "Note:"
    echo "• Ollama itself was NOT removed (use 'sudo rm /usr/local/bin/ollama' if needed)"
    echo "• Downloaded Ollama models were NOT removed (use 'ollama rm <model>' if needed)"
    echo "• Some Python packages may remain (pydantic, etc.)"
    echo "• You may need to restart your terminal for PATH changes to take effect"
    echo ""
    echo -e "${PURPLE}Thank you for trying Ollama Flow! 🚀${NC}"
}

# Main uninstallation function
main() {
    # Interactive confirmation
    confirm_removal
    
    print_info "Starting enhanced uninstallation process..."
    
    # Execute removal steps
    check_active_processes
    remove_installations
    remove_cli
    clean_shell_config
    remove_python_packages
    remove_logs_temp
    remove_service
    
    # Verify removal
    if verify_removal; then
        show_summary
        exit 0
    else
        print_warning "Some components may not have been completely removed."
        print_info "You may need to manually remove remaining items."
        exit 1
    fi
}

# Error handling
trap 'print_error "Uninstallation failed! Some items may not have been removed."; exit 1' ERR

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Enhanced Ollama Flow Uninstaller v2.0"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo "  --force       Skip confirmation prompts (use with caution!)"
    echo ""
    echo "This script will completely remove Ollama Flow and all associated files."
    echo "Make sure to backup any important data before running."
    exit 0
fi

# Force mode (skip confirmations)
if [ "$1" = "--force" ]; then
    print_header
    print_warning "FORCE MODE: Skipping confirmations and removing everything!"
    sleep 3
    
    check_active_processes
    remove_installations
    remove_cli
    clean_shell_config
    remove_logs_temp
    remove_service
    verify_removal
    
    print_success "Force uninstallation completed!"
    exit 0
fi

# Run main uninstallation
main "$@"