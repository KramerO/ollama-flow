#!/bin/bash

# 🚀 GPU System Manager v2.0 - Unified Management System
# Complete GPU optimization, monitoring and management for ollama-flow
# AMD RX 6650 XT optimized with intelligent auto-scaling

set -e

VERSION="2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
LOG_DIR="$SCRIPT_DIR/logs"
BACKUP_DIR="$SCRIPT_DIR/backups"

# Create required directories
mkdir -p "$CONFIG_DIR" "$LOG_DIR" "$BACKUP_DIR"

# ===== CONFIGURATION MANAGEMENT =====
GPU_CONFIG_FILE="$CONFIG_DIR/gpu_system.conf"
PERFORMANCE_PROFILES="$CONFIG_DIR/performance_profiles.json"
SYSTEM_STATE="$CONFIG_DIR/system_state.json"

# Initialize configuration if not exists
init_configuration() {
    if [ ! -f "$GPU_CONFIG_FILE" ]; then
        cat > "$GPU_CONFIG_FILE" << 'EOF'
# GPU System Configuration v2.0
GPU_VENDOR="AMD"
GPU_MODEL="RX_6650_XT"
MAX_WORKERS=16
DEFAULT_WORKERS=8
MAX_GPU_LAYERS=45
DEFAULT_GPU_LAYERS=35
MEMORY_THRESHOLD=80
AUTO_SCALING=true
MONITORING_ENABLED=true
OPTIMIZATION_LEVEL="balanced"
EOF
    fi
    
    if [ ! -f "$PERFORMANCE_PROFILES" ]; then
        cat > "$PERFORMANCE_PROFILES" << 'EOF'
{
  "profiles": {
    "eco": {
      "workers": 4,
      "gpu_layers": 25,
      "parallel_requests": 4,
      "memory_limit": 60,
      "description": "Energy efficient mode for simple tasks"
    },
    "balanced": {
      "workers": 8,
      "gpu_layers": 35,
      "parallel_requests": 8,
      "memory_limit": 80,
      "description": "Optimal balance of performance and efficiency"
    },
    "performance": {
      "workers": 12,
      "gpu_layers": 40,
      "parallel_requests": 12,
      "memory_limit": 90,
      "description": "High performance for complex tasks"
    },
    "max": {
      "workers": 16,
      "gpu_layers": 45,
      "parallel_requests": 16,
      "memory_limit": 95,
      "description": "Maximum performance, all resources utilized"
    }
  }
}
EOF
    fi
}

# Load configuration
load_config() {
    source "$GPU_CONFIG_FILE" 2>/dev/null || true
}

# ===== COLORS AND UI =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

print_logo() {
    echo -e "${BLUE}${BOLD}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║                                                      ║"
    echo "║       🚀 GPU System Manager v$VERSION                  ║"
    echo "║       Unified ollama-flow GPU Management             ║"
    echo "║                                                      ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${CYAN}${BOLD}▶ $1${NC}"
    echo -e "${DIM}$(printf '─%.0s' {1..50})${NC}"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# ===== SYSTEM MONITORING =====
get_system_metrics() {
    local metrics_file="$LOG_DIR/system_metrics_$(date +%Y%m%d_%H%M%S).json"
    
    # GPU metrics
    local gpu_stats=""
    if command -v radeontop >/dev/null 2>&1; then
        gpu_stats=$(timeout 2 radeontop -d - -l 1 2>/dev/null | head -1 || echo "")
    fi
    
    # System metrics
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "0")
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "0")
    local disk_usage=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | cut -d'%' -f1 || echo "0")
    
    # Ollama process info
    local ollama_processes=$(pgrep ollama | wc -l || echo "0")
    local python_processes=$(pgrep -f "python.*main.py" | wc -l || echo "0")
    
    # Create metrics JSON
    cat > "$metrics_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "gpu": {
    "stats": "$gpu_stats",
    "vendor": "$GPU_VENDOR",
    "model": "$GPU_MODEL"
  },
  "system": {
    "cpu_usage": $cpu_usage,
    "memory_usage": $memory_usage,
    "disk_usage": $disk_usage
  },
  "processes": {
    "ollama": $ollama_processes,
    "python_workers": $python_processes
  },
  "configuration": {
    "workers": $DEFAULT_WORKERS,
    "gpu_layers": $DEFAULT_GPU_LAYERS,
    "optimization_level": "$OPTIMIZATION_LEVEL"
  }
}
EOF
    
    echo "$metrics_file"
}

# ===== INTELLIGENT AUTO-SCALING =====
auto_scale_resources() {
    local current_load="$1"
    local target_workers="$2"
    
    # Get current GPU memory usage
    local gpu_memory=0
    if command -v radeontop >/dev/null 2>&1; then
        gpu_memory=$(timeout 2 radeontop -d - -l 1 2>/dev/null | grep -o 'vram [0-9]*\.[0-9]*%' | grep -o '[0-9]*\.[0-9]*' | head -1 || echo "0")
        gpu_memory=${gpu_memory%.*}  # Remove decimal part
    fi
    
    local recommended_profile="balanced"
    local recommended_workers=$DEFAULT_WORKERS
    
    # Auto-scaling logic
    if [ "$gpu_memory" -gt 85 ]; then
        recommended_profile="eco"
        recommended_workers=4
        print_warning "High GPU memory usage ($gpu_memory%) - switching to ECO mode"
    elif [ "$gpu_memory" -gt 70 ]; then
        recommended_profile="balanced"
        recommended_workers=8
        print_info "Moderate GPU usage ($gpu_memory%) - using BALANCED mode"
    elif [ "$gpu_memory" -lt 30 ] && [ "$target_workers" -gt 8 ]; then
        recommended_profile="performance"
        recommended_workers=12
        print_info "Low GPU usage ($gpu_memory%) - scaling up to PERFORMANCE mode"
    fi
    
    # Apply profile
    apply_performance_profile "$recommended_profile"
    echo "$recommended_workers"
}

# ===== PERFORMANCE PROFILES =====
apply_performance_profile() {
    local profile="$1"
    
    if [ ! -f "$PERFORMANCE_PROFILES" ]; then
        print_error "Performance profiles not found"
        return 1
    fi
    
    # Extract profile settings (simplified JSON parsing)
    case "$profile" in
        "eco")
            export OLLAMA_NUM_PARALLEL=4
            export OLLAMA_GPU_LAYERS=25
            export OLLAMA_MAX_LOADED_MODELS=2
            export OLLAMA_MAX_QUEUE=25
            ;;
        "balanced")
            export OLLAMA_NUM_PARALLEL=8
            export OLLAMA_GPU_LAYERS=35
            export OLLAMA_MAX_LOADED_MODELS=4
            export OLLAMA_MAX_QUEUE=50
            ;;
        "performance")
            export OLLAMA_NUM_PARALLEL=12
            export OLLAMA_GPU_LAYERS=40
            export OLLAMA_MAX_LOADED_MODELS=6
            export OLLAMA_MAX_QUEUE=75
            ;;
        "max")
            export OLLAMA_NUM_PARALLEL=16
            export OLLAMA_GPU_LAYERS=45
            export OLLAMA_MAX_LOADED_MODELS=8
            export OLLAMA_MAX_QUEUE=100
            ;;
        *)
            print_error "Unknown profile: $profile"
            return 1
            ;;
    esac
    
    # Apply additional GPU optimizations
    export OLLAMA_FLASH_ATTENTION=1
    export OLLAMA_KEEP_ALIVE=15m
    export OLLAMA_CONCURRENT_REQUESTS=$OLLAMA_NUM_PARALLEL
    
    # AMD specific optimizations
    export HSA_OVERRIDE_GFX_VERSION=10.3.0
    export GPU_MAX_HEAP_SIZE=100
    export GPU_MAX_ALLOC_PERCENT=95
    
    print_success "Applied performance profile: $profile"
    print_info "Parallel requests: $OLLAMA_NUM_PARALLEL, GPU layers: $OLLAMA_GPU_LAYERS"
}

# ===== SYSTEM OPTIMIZATION =====
optimize_system() {
    print_section "System Optimization"
    
    # CPU Governor optimization
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
        print_success "CPU governor set to performance mode"
    fi
    
    # Memory optimization
    if [ -w /proc/sys/vm/swappiness ]; then
        echo "10" | sudo tee /proc/sys/vm/swappiness >/dev/null 2>&1 || true
        print_success "Memory swappiness optimized"
    fi
    
    # GPU power management
    if [ -d /sys/class/drm/card0/device ]; then
        echo "high" | sudo tee /sys/class/drm/card*/device/power_dpm_force_performance_level >/dev/null 2>&1 || true
        print_success "GPU power management optimized"
    fi
    
    print_success "System optimization completed"
}

# ===== HEALTH MONITORING =====
monitor_system_health() {
    local duration=${1:-60}
    local interval=5
    local output_file="$LOG_DIR/health_monitor_$(date +%Y%m%d_%H%M%S).log"
    
    print_info "🔍 Starting system health monitoring ($duration seconds)"
    print_info "Output: $output_file"
    
    {
        echo "# System Health Monitor - $(date)"
        echo "# Time,GPU_Usage%,VRAM%,CPU%,Memory%,Ollama_Processes,Python_Workers"
        
        for i in $(seq 1 $((duration/interval))); do
            local timestamp=$(date '+%H:%M:%S')
            
            # Get metrics
            local gpu_usage="0"
            local vram_usage="0"
            if command -v radeontop >/dev/null 2>&1; then
                local gpu_stats=$(timeout 2 radeontop -d - -l 1 2>/dev/null | head -1 || echo "")
                if [ -n "$gpu_stats" ]; then
                    gpu_usage=$(echo "$gpu_stats" | grep -o 'gpu [0-9]*\.[0-9]*%' | grep -o '[0-9]*\.[0-9]*' || echo "0")
                    vram_usage=$(echo "$gpu_stats" | grep -o 'vram [0-9]*\.[0-9]*%' | grep -o '[0-9]*\.[0-9]*' || echo "0")
                fi
            fi
            
            local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "0")
            local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "0")
            local ollama_processes=$(pgrep ollama | wc -l || echo "0")
            local python_workers=$(pgrep -f "python.*main.py" | wc -l || echo "0")
            
            echo "$timestamp,$gpu_usage,$vram_usage,$cpu_usage,$memory_usage,$ollama_processes,$python_workers"
            
            sleep $interval
        done
    } > "$output_file" &
    
    local monitor_pid=$!
    echo "$monitor_pid" > "$LOG_DIR/health_monitor.pid"
    
    print_success "Health monitor started (PID: $monitor_pid)"
}

# ===== MAIN COMMANDS =====
show_status() {
    print_logo
    print_section "System Status"
    
    # Load current configuration
    load_config
    
    # Hardware info
    local gpu_info=$(lspci | grep -i amd | grep -i vga | head -1 | cut -d: -f3- | xargs || echo "AMD GPU not detected")
    printf "%-20s %s\n" "GPU Hardware:" "$gpu_info"
    printf "%-20s %s\n" "Max Workers:" "$MAX_WORKERS"
    printf "%-20s %s\n" "GPU Layers:" "$DEFAULT_GPU_LAYERS"
    printf "%-20s %s\n" "Optimization:" "$OPTIMIZATION_LEVEL"
    
    # Current performance metrics
    if command -v radeontop >/dev/null 2>&1; then
        print_section "Current GPU Metrics"
        timeout 3 radeontop -d - -l 1 | head -1 || print_warning "GPU metrics unavailable"
    fi
    
    # Process status
    print_section "Process Status"
    local ollama_count=$(pgrep ollama | wc -l || echo "0")
    local python_count=$(pgrep -f "python.*main.py" | wc -l || echo "0")
    printf "%-20s %s\n" "Ollama processes:" "$ollama_count"
    printf "%-20s %s\n" "Python workers:" "$python_count"
    
    # Recent logs
    print_section "Recent Activity"
    if [ -d "$LOG_DIR" ] && [ "$(ls -A $LOG_DIR)" ]; then
        echo "Latest logs:"
        ls -lt "$LOG_DIR" | head -3 | awk '{print "  " $9 " - " $6 " " $7 " " $8}'
    else
        print_info "No recent activity logs"
    fi
}

install_system() {
    print_logo
    print_info "🚀 Starting complete GPU system installation..."
    
    # Run the comprehensive installer
    if [ -f "$SCRIPT_DIR/install_gpu_complete.sh" ]; then
        chmod +x "$SCRIPT_DIR/install_gpu_complete.sh"
        "$SCRIPT_DIR/install_gpu_complete.sh"
    else
        print_error "GPU installer not found: install_gpu_complete.sh"
        exit 1
    fi
    
    # Initialize configuration
    init_configuration
    print_success "GPU system installation completed!"
}

show_help() {
    print_logo
    
    echo -e "${BOLD}🎯 System Management Commands:${NC}"
    echo ""
    echo -e "${CYAN}  install                 ${NC} Complete GPU system installation"
    echo -e "${CYAN}  status                  ${NC} Show comprehensive system status"
    echo -e "${CYAN}  optimize                ${NC} Optimize system for current workload"
    echo -e "${CYAN}  profile <name>          ${NC} Apply performance profile (eco/balanced/performance/max)"
    echo -e "${CYAN}  monitor [duration]      ${NC} Start system health monitoring"
    echo -e "${CYAN}  metrics                 ${NC} Generate current system metrics"
    echo -e "${CYAN}  logs                    ${NC} Show recent logs and metrics"
    echo -e "${CYAN}  cleanup                 ${NC} Clean up old logs and temporary files"
    echo ""
    echo -e "${BOLD}🔧 Configuration:${NC}"
    echo -e "${CYAN}  config show             ${NC} Show current configuration"
    echo -e "${CYAN}  config edit             ${NC} Edit configuration file"
    echo -e "${CYAN}  config reset            ${NC} Reset to default configuration"
    echo ""
    echo -e "${BOLD}💡 Usage Examples:${NC}"
    echo ""
    echo -e "${GREEN}  $0 install              ${NC} # Complete installation"
    echo -e "${GREEN}  $0 profile performance  ${NC} # Switch to high performance"
    echo -e "${GREEN}  $0 monitor 300          ${NC} # Monitor for 5 minutes"
    echo -e "${GREEN}  $0 optimize             ${NC} # Auto-optimize current setup"
    echo ""
}

# ===== MAIN FUNCTION =====
main() {
    # Initialize configuration
    init_configuration
    load_config
    
    local command="${1:-help}"
    shift 2>/dev/null || true
    
    case "$command" in
        "install")
            install_system "$@"
            ;;
        "status"|"info")
            show_status
            ;;
        "optimize")
            optimize_system
            ;;
        "profile")
            local profile="${1:-balanced}"
            apply_performance_profile "$profile"
            ;;
        "monitor")
            local duration="${1:-60}"
            monitor_system_health "$duration"
            ;;
        "metrics")
            local metrics_file=$(get_system_metrics)
            print_success "Metrics saved to: $metrics_file"
            cat "$metrics_file"
            ;;
        "logs")
            print_info "Log directory: $LOG_DIR"
            if [ -d "$LOG_DIR" ]; then
                ls -la "$LOG_DIR"
            else
                print_warning "No logs directory found"
            fi
            ;;
        "cleanup")
            print_info "Cleaning up old logs..."
            find "$LOG_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
            find "$LOG_DIR" -name "*.json" -mtime +7 -delete 2>/dev/null || true
            print_success "Cleanup completed"
            ;;
        "config")
            local config_cmd="${1:-show}"
            case "$config_cmd" in
                "show")
                    print_info "Configuration file: $GPU_CONFIG_FILE"
                    cat "$GPU_CONFIG_FILE"
                    ;;
                "edit")
                    ${EDITOR:-nano} "$GPU_CONFIG_FILE"
                    ;;
                "reset")
                    rm -f "$GPU_CONFIG_FILE"
                    init_configuration
                    print_success "Configuration reset to defaults"
                    ;;
            esac
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"