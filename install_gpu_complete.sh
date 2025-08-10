#!/bin/bash

# 🚀 Complete GPU Acceleration Installer für ollama-flow
# AMD RX 6650 XT optimiert mit OpenCL, Vulkan und Performance Tuning
# Version: 2.0 - Refactored & Enhanced

set -e

# ===== CONFIGURATION =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/gpu_install.log"
BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ===== UTILITY FUNCTIONS =====
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${BLUE}${BOLD}========================================${NC}"
    echo -e "${BLUE}${BOLD}   🚀 GPU Acceleration Installer v2.0${NC}"
    echo -e "${BLUE}${BOLD}   AMD RX 6650 XT + OpenCL + Vulkan${NC}"
    echo -e "${BLUE}${BOLD}========================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}${BOLD}━━━ $1 ━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR: $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
    log "INFO: $1"
}

# ===== SYSTEM CHECKS =====
check_prerequisites() {
    print_section "System Prerequisites Check"
    
    # Check OS
    if ! grep -q "kali\|debian\|ubuntu" /etc/os-release; then
        print_warning "Nicht-Debian basiertes System erkannt. Installation kann fehlschlagen."
    else
        print_success "Debian-basiertes System erkannt"
    fi
    
    # Check AMD GPU
    if lspci | grep -i amd | grep -i vga > /dev/null; then
        GPU_INFO=$(lspci | grep -i amd | grep -i vga | head -1 | cut -d: -f3-)
        print_success "AMD GPU gefunden:$GPU_INFO"
    else
        print_error "Keine AMD GPU gefunden! Installation abgebrochen."
        exit 1
    fi
    
    # Check internet connection
    if ping -c 1 google.com > /dev/null 2>&1; then
        print_success "Internet-Verbindung verfügbar"
    else
        print_error "Keine Internet-Verbindung! Installation abgebrochen."
        exit 1
    fi
    
    # Check disk space (min 2GB)
    AVAILABLE_SPACE=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -lt 2097152 ]; then
        print_warning "Weniger als 2GB freier Speicherplatz verfügbar"
    else
        print_success "Ausreichend Speicherplatz verfügbar"
    fi
}

# ===== BACKUP FUNCTIONS =====
create_backups() {
    print_section "Creating Configuration Backups"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup bashrc
    if [ -f ~/.bashrc ]; then
        cp ~/.bashrc "$BACKUP_DIR/bashrc.backup"
        print_success "~/.bashrc gesichert"
    fi
    
    # Backup existing configs
    for config in config*.json; do
        if [ -f "$config" ]; then
            cp "$config" "$BACKUP_DIR/"
            print_success "$config gesichert"
        fi
    done
    
    print_info "Backups erstellt in: $BACKUP_DIR"
}

# ===== PACKAGE INSTALLATION =====
install_system_packages() {
    print_section "Installing System Packages"
    
    print_info "Aktualisiere Paket-Repository..."
    sudo apt update || {
        print_error "apt update fehlgeschlagen"
        exit 1
    }
    
    # Essential packages
    local ESSENTIAL_PACKAGES=(
        "build-essential"
        "cmake" 
        "pkg-config"
        "git"
        "wget"
        "curl"
        "htop"
        "iotop"
    )
    
    print_info "Installiere Essential Packages..."
    sudo apt install -y "${ESSENTIAL_PACKAGES[@]}" || {
        print_error "Essential packages Installation fehlgeschlagen"
        exit 1
    }
    print_success "Essential packages installiert"
}

install_opencl_vulkan() {
    print_section "Installing OpenCL & Vulkan Support"
    
    # OpenCL packages
    local OPENCL_PACKAGES=(
        "mesa-opencl-icd"
        "opencl-headers" 
        "clinfo"
        "mesa-utils"
        "ocl-icd-opencl-dev"
        "opencl-c-headers"
    )
    
    print_info "Installiere OpenCL packages..."
    sudo apt install -y "${OPENCL_PACKAGES[@]}" || {
        print_warning "Einige OpenCL packages konnten nicht installiert werden"
    }
    
    # Vulkan packages
    local VULKAN_PACKAGES=(
        "vulkan-tools"
        "vulkan-validationlayers-dev"
        "libvulkan-dev"
        "mesa-vulkan-drivers"
        "spirv-tools"
    )
    
    print_info "Installiere Vulkan packages..."
    sudo apt install -y "${VULKAN_PACKAGES[@]}" || {
        print_warning "Einige Vulkan packages konnten nicht installiert werden"
    }
    
    # GPU monitoring tools
    local MONITORING_PACKAGES=(
        "radeontop"
        "glxinfo"
        "vulkan-utils"
    )
    
    print_info "Installiere GPU Monitoring tools..."
    sudo apt install -y "${MONITORING_PACKAGES[@]}" || {
        print_warning "Einige Monitoring tools konnten nicht installiert werden"
    }
    
    print_success "OpenCL & Vulkan Installation abgeschlossen"
}

# ===== GPU OPTIMIZATION =====
configure_gpu_environment() {
    print_section "Configuring GPU Environment"
    
    # Create GPU optimization section in bashrc
    print_info "Konfiguriere GPU Umgebungsvariablen..."
    
    # Remove existing GPU config if present
    sed -i '/# ========================================/,/# ========================================/d' ~/.bashrc 2>/dev/null || true
    sed -i '/# 🚀 OLLAMA-FLOW GPU OPTIMIZATIONS/,/echo "🚀 GPU optimizations loaded for ollama-flow!"/d' ~/.bashrc 2>/dev/null || true
    
    cat >> ~/.bashrc << 'EOF'

# ========================================
# 🚀 OLLAMA-FLOW GPU OPTIMIZATIONS v2.0
# ========================================

# OpenCL Configuration
export OCL_ICD_VENDORS=/usr/lib/x86_64-linux-gnu/OpenCL/vendors
export OPENCL_VENDOR_PATH=/usr/lib/x86_64-linux-gnu/OpenCL/vendors

# Vulkan Configuration  
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json
export VK_LAYER_PATH=/usr/share/vulkan/explicit_layer.d

# AMD GPU Optimizations (RX 6650 XT specific)
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export GPU_MAX_HEAP_SIZE=100
export GPU_MAX_ALLOC_PERCENT=95
export GPU_USE_SYNC_OBJECTS=1
export GPU_FORCE_64BIT_PTR=1

# Ollama GPU Performance Settings
export OLLAMA_NUM_PARALLEL=12
export OLLAMA_MAX_LOADED_MODELS=6
export OLLAMA_GPU_LAYERS=40
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KEEP_ALIVE=15m
export OLLAMA_MAX_QUEUE=100
export OLLAMA_CONCURRENT_REQUESTS=16

# Performance Tuning
export OMP_NUM_THREADS=$(nproc)
export MKL_NUM_THREADS=$(nproc)
export OPENBLAS_NUM_THREADS=$(nproc)
export VECLIB_MAXIMUM_THREADS=$(nproc)
export NUMEXPR_NUM_THREADS=$(nproc)

# Memory Management
export MALLOC_ARENA_MAX=4
export MALLOC_MMAP_THRESHOLD_=1048576

# Ollama-Flow Paths
export OLLAMA_FLOW_HOME="$HOME/projects/ollama-flow"
export OLLAMA_MODELS="$OLLAMA_FLOW_HOME/models"

# GPU Utilities
alias gpu-status='radeontop'
alias gpu-info='clinfo && vulkaninfo --summary'
alias gpu-test='glxinfo | grep -i opengl'

echo "🚀 GPU optimizations v2.0 loaded for ollama-flow!"

EOF

    print_success "GPU Umgebungsvariablen konfiguriert"
}

# ===== LLAMA.CPP OPTIMIZATION =====
optimize_llama_cpp() {
    print_section "Optimizing llama.cpp for GPU"
    
    if [ ! -d "llama.cpp" ]; then
        print_warning "llama.cpp Verzeichnis nicht gefunden, überspringe Optimierung"
        return
    fi
    
    cd llama.cpp
    
    print_info "Kompiliere llama.cpp mit GPU-Optimierungen..."
    make clean || true
    
    # Try Vulkan first, fallback to OpenCL, then CPU
    if make GGML_VULKAN=1 -j$(nproc) 2>/dev/null; then
        print_success "llama.cpp mit Vulkan Support kompiliert"
        echo "vulkan" > .gpu_backend
    elif make GGML_OPENCL=1 -j$(nproc) 2>/dev/null; then
        print_success "llama.cpp mit OpenCL Support kompiliert"  
        echo "opencl" > .gpu_backend
    else
        make -j$(nproc)
        print_success "llama.cpp mit CPU Optimierungen kompiliert"
        echo "cpu" > .gpu_backend
    fi
    
    cd "$SCRIPT_DIR"
}

# ===== TESTING =====
test_installation() {
    print_section "Testing GPU Installation"
    
    # Source new environment
    source ~/.bashrc 2>/dev/null || true
    
    # Test OpenCL
    print_info "Teste OpenCL..."
    if command -v clinfo >/dev/null 2>&1; then
        if clinfo | grep -q "Platform Name"; then
            print_success "OpenCL funktioniert"
        else
            print_warning "OpenCL installiert aber keine Plattformen gefunden"
        fi
    else
        print_error "clinfo nicht gefunden"
    fi
    
    # Test Vulkan  
    print_info "Teste Vulkan..."
    if command -v vulkaninfo >/dev/null 2>&1; then
        if vulkaninfo --summary 2>/dev/null | grep -q "Vulkan Instance Version"; then
            print_success "Vulkan funktioniert"
        else
            print_warning "Vulkan installiert aber nicht funktional"
        fi
    else
        print_error "vulkaninfo nicht gefunden"
    fi
    
    # Test GPU monitoring
    print_info "Teste GPU Monitoring..."
    if command -v radeontop >/dev/null 2>&1; then
        print_success "radeontop verfügbar"
    else
        print_warning "radeontop nicht verfügbar"
    fi
    
    # Test GPU memory
    print_info "GPU Memory Status:"
    if command -v radeontop >/dev/null 2>&1; then
        timeout 3 radeontop -d - | head -2 || true
    fi
}

# ===== MAIN INSTALLATION =====
main() {
    print_header
    log "Starting GPU installation v2.0"
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Nicht als root ausführen! Verwende sudo nur wenn nötig."
        exit 1
    fi
    
    # Main installation steps
    check_prerequisites
    create_backups
    install_system_packages
    install_opencl_vulkan
    configure_gpu_environment
    optimize_llama_cpp
    test_installation
    
    print_section "Installation Complete"
    print_success "GPU Acceleration Installation erfolgreich!"
    
    echo -e "\n${BOLD}📋 Next Steps:${NC}"
    echo -e "${CYAN}1. Neue Terminal-Session starten oder: source ~/.bashrc${NC}"
    echo -e "${CYAN}2. GPU Status testen: ./ollama-flow-gpu status${NC}"
    echo -e "${CYAN}3. Performance Test: ./ollama-flow-gpu benchmark${NC}"
    echo -e "${CYAN}4. Komplexe Tasks: ./ollama-flow-gpu run \"Your task\" --workers 8${NC}"
    
    echo -e "\n${BOLD}🔧 Troubleshooting:${NC}"
    echo -e "${CYAN}- Logs: $LOG_FILE${NC}"
    echo -e "${CYAN}- Backups: $BACKUP_DIR${NC}"
    echo -e "${CYAN}- GPU Test: gpu-info${NC}"
    
    print_success "Installation abgeschlossen! 🚀"
}

# Execute main function
main "$@"