#!/usr/bin/env python3
"""
Quick Setup Script for Ollama Flow Framework
For development and testing purposes
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Quick setup for development"""
    print("🚀 Ollama Flow Framework - Quick Setup")
    print("====================================")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print("✅ Python version check passed")
    
    # Install requirements
    print("📦 Installing requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)
    
    # Check Ollama
    print("🦙 Checking Ollama...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama found: {result.stdout.strip()}")
        else:
            print("❌ Ollama not found - please install from https://ollama.ai")
            return
    except FileNotFoundError:
        print("❌ Ollama not found - please install from https://ollama.ai")
        return
    
    # Pull model
    print("🤖 Checking model...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "codellama:7b" not in result.stdout:
            print("📥 Downloading codellama:7b model...")
            subprocess.run(["ollama", "pull", "codellama:7b"], check=True)
        print("✅ Model ready")
    except subprocess.CalledProcessError:
        print("⚠️ Could not download model - you can do this later with: ollama pull codellama:7b")
    
    # Create .env if it doesn't exist
    if not Path(".env").exists():
        print("⚙️ Creating .env file...")
        with open(".env", "w") as f:
            f.write("""OLLAMA_MODEL=codellama:7b
OLLAMA_WORKER_COUNT=4
OLLAMA_ARCHITECTURE_TYPE=HIERARCHICAL
OLLAMA_SECURE_MODE=true
OLLAMA_PARALLEL_LLM=true
OLLAMA_METRICS=true
OLLAMA_NEURAL_ENABLED=true
OLLAMA_MCP_ENABLED=true
OLLAMA_MONITORING_ENABLED=true
OLLAMA_SESSION_ENABLED=true
""")
        print("✅ Configuration created")
    
    # Make scripts executable
    scripts = ["ollama-flow", "install.py", "cli_dashboard.py"]
    for script in scripts:
        if Path(script).exists():
            try:
                Path(script).chmod(0o755)
                print(f"✅ Made {script} executable")
            except Exception:
                pass
    
    print(f"""
🎉 SETUP COMPLETE!
==================

Quick start commands:
  python enhanced_main.py --task "Create a web scraper" --workers 4
  python dashboard/flask_dashboard.py
  python cli_dashboard.py
  
Or use the CLI wrapper:
  ./ollama-flow run "Create a web scraper"
  ./ollama-flow dashboard
  ./ollama-flow cli-dash

For full installation: python install.py
    """)

if __name__ == "__main__":
    main()