#!/usr/bin/env python3
"""
CLI Dashboard Demo - Shows dashboard features without full interface
Creates a static representation of what the dashboard looks like
"""

import os
import sys
import psutil
from datetime import datetime

def print_dashboard_demo():
    """Print a demo of what the CLI dashboard looks like"""
    
    # Terminal colors
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')
    
    width = 80
    
    # Header
    print(BLUE + BOLD + "🚀 OLLAMA FLOW - Enhanced CLI Dashboard v2.1.0".center(width) + END)
    print(CYAN + datetime.now().strftime("%Y-%m-%d %H:%M:%S").rjust(width-1) + END)
    print(BLUE + "═" * width + END)
    
    # Navigation
    nav = f"{BOLD}[1] Overview  [2] Tasks  [3] Resources  [4] Architecture  [5] Config  [6] Logs{END}"
    print(f"{HEADER}{nav}{END}")
    print()
    
    # Overview Panel
    print(BLUE + BOLD + "📊 SYSTEM OVERVIEW" + END)
    print()
    
    # Get real system metrics
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    # Quick stats in columns
    stats_left = [
        f"🔄 Active Tasks: 3",
        f"💾 Memory: {memory_percent:.1f}%",
        f"🔧 Model: phi3:mini"
    ]
    
    stats_right = [
        f"🤖 Active Agents: 7",
        f"🖥️  CPU: {cpu_percent:.1f}%",
        f"🏗️  Architecture: HIERARCHICAL"
    ]
    
    for i, (left, right) in enumerate(zip(stats_left, stats_right)):
        color_left = GREEN if "Active" in left else CYAN
        color_right = GREEN if "Active" in right else CYAN
        print(f"  {color_left}{left:<25}{END} {color_right}{right}{END}")
    
    print()
    
    # Architecture Preview
    print(BLUE + BOLD + "🏗️ ARCHITECTURE PREVIEW" + END)
    print(f"  {HEADER}👑 Enhanced Queen{END}")
    print("  │")
    print(f"  {GREEN}👥 Sub Queen A{END}   {GREEN}👥 Sub Queen B{END}")
    print("  │              │")
    print(f"  {CYAN}🔧 Worker 1    🔧 Worker 3{END}")
    print(f"  {CYAN}🔧 Worker 2    🔧 Worker 4{END}")
    print()
    
    # Tasks Panel Demo
    print(BLUE + "═" * width + END)
    print(BLUE + BOLD + "📋 ACTIVE TASKS (3)" + END)
    print()
    print(f"{UNDERLINE}{'ID':<8} {'Status':<10} {'Content':<35} {'Worker':<12} {'Progress':<8}{END}")
    
    tasks = [
        ("task_001", "active", "Create Flask web application", "worker-1", "75%"),
        ("task_002", "pending", "Build REST API endpoints", "None", "0%"),
        ("task_003", "active", "Write unit tests", "worker-2", "45%")
    ]
    
    for task_id, status, content, worker, progress in tasks:
        if status == "active":
            status_color = GREEN
        elif status == "pending":
            status_color = YELLOW
        else:
            status_color = RED
        
        print(f"{task_id:<8} {status_color}{status:<10}{END} {content:<35} {worker:<12} {progress:<8}")
    
    print()
    
    # Resources Panel Demo
    print(BLUE + "═" * width + END)
    print(BLUE + BOLD + "💻 SYSTEM RESOURCES" + END)
    print()
    
    # Create progress bars
    def create_progress_bar(percentage, width=40):
        filled = int(percentage * width / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar
    
    def get_color(percentage):
        if percentage < 50:
            return GREEN
        elif percentage < 80:
            return YELLOW
        else:
            return RED
    
    cpu_bar = create_progress_bar(cpu_percent, 30)
    cpu_color = get_color(cpu_percent)
    print(f"  CPU Usage: {cpu_percent:5.1f}% {cpu_color}[{cpu_bar}]{END}")
    
    mem_bar = create_progress_bar(memory_percent, 30)
    mem_color = get_color(memory_percent)
    print(f"  Memory:    {memory_percent:5.1f}% {mem_color}[{mem_bar}]{END}")
    
    disk_percent = psutil.disk_usage('/').percent
    disk_bar = create_progress_bar(disk_percent, 30)
    disk_color = get_color(disk_percent)
    print(f"  Disk:      {disk_percent:5.1f}% {disk_color}[{disk_bar}]{END}")
    
    print()
    print(f"  {CYAN}Active Processes: {len(psutil.pids())}{END}")
    print(f"  {CYAN}Ollama Processes: 2{END}")
    
    print()
    
    # Configuration Panel Demo
    print(BLUE + "═" * width + END)
    print(BLUE + BOLD + "⚙️ CONFIGURATION" + END)
    print()
    
    config_items = [
        ("Model", "phi3:mini"),
        ("Worker Count", "4"),
        ("Architecture", "HIERARCHICAL"),
        ("Secure Mode", "✓"),
        ("Parallel LLM", "✓"),
        ("Project Folder", "/tmp/ollama_1"),
        ("Dashboard Version", "v2.1.0")
    ]
    
    max_key_length = max(len(key) for key, _ in config_items)
    
    for key, value in config_items:
        print(f"  {BLUE}{key:>{max_key_length}}: {END}{value}")
    
    print()
    print(f"  {BLUE}Features:{END}")
    features = ["auto-shutdown", "web-dashboard", "neural-intelligence", "extended-formats"]
    for feature in features:
        print(f"    {GREEN}✓ {feature}{END}")
    
    # Footer
    print()
    print(BLUE + "═" * width + END)
    footer = "[1-6] Switch panels | [Q] Quit | [R] Refresh | [↑↓] Navigate"
    print(CYAN + footer.center(width) + END)
    
    print()
    print(f"{BOLD}🎯 CLI Dashboard Features:{END}")
    print(f"  • {GREEN}Real-time system monitoring{END}")
    print(f"  • {GREEN}Interactive architecture visualization{END}")
    print(f"  • {GREEN}Live task tracking with progress{END}")
    print(f"  • {GREEN}System resource usage graphs{END}")
    print(f"  • {GREEN}Configuration management{END}")
    print(f"  • {GREEN}Live log monitoring{END}")
    print(f"  • {GREEN}Keyboard navigation{END}")
    
    print()
    print(f"{BOLD}🚀 To launch the real dashboard:{END}")
    print(f"  {CYAN}ollama-flow cli-dashboard{END}")
    print()

if __name__ == "__main__":
    print_dashboard_demo()