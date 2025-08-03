# 🚀 Windows Installation Guide - Ollama Flow Framework v2.1.0

## Quick Installation for Windows

### Option 1: Direct Installation (Recommended)

```powershell
# Navigate to project directory
cd C:\Users\vorad\Projekte\ollama-python-test

# Run the fixed installer
python .\install.py

# If installation completes successfully:
# Activate the virtual environment
C:\Users\vorad\.ollama-flow\venv\Scripts\activate

# Test the installation
python enhanced_main.py --help
```

### Option 2: Manual Installation (If installer fails)

```powershell
# 1. Create virtual environment manually
python -m venv C:\Users\vorad\.ollama-flow\venv

# 2. Activate virtual environment
C:\Users\vorad\.ollama-flow\venv\Scripts\activate

# 3. Install requirements
pip install ollama python-dotenv psutil scikit-learn numpy flask flask-socketio requests aiohttp click rich typer

# 4. Test framework
python enhanced_main.py --help
```

### Option 3: Use requirements.txt

```powershell
# Activate virtual environment
C:\Users\vorad\.ollama-flow\venv\Scripts\activate

# Install from requirements file
pip install -r requirements.txt

# Test installation
python enhanced_main.py --version
```

## Install Ollama (Required)

1. **Download Ollama for Windows:**
   - Visit: https://ollama.ai/download
   - Download Windows installer
   - Run installer

2. **Install CodeLlama model:**
```powershell
ollama pull codellama:7b
```

3. **Verify Ollama installation:**
```powershell
ollama --version
ollama list
```

## Test the Framework

### 1. Basic Test
```powershell
python enhanced_main.py --task "Create a hello world Python script" --workers 2
```

### 2. Start Dashboard
```powershell
python dashboard\simple_dashboard.py --port 5000
```

Then open browser to: http://localhost:5000

### 3. Session Management Test
```powershell
python test_session_dashboard.py
```

## Common Windows Issues & Solutions

### Issue: pip upgrade fails
**Solution**: The fixed installer now skips pip upgrade on Windows (non-critical)

### Issue: Virtual environment activation
**Solution**: Use full path:
```powershell
C:\Users\vorad\.ollama-flow\venv\Scripts\activate
```

### Issue: Ollama not found
**Solution**: 
1. Install Ollama from https://ollama.ai/download
2. Restart PowerShell
3. Run `ollama --version` to verify

### Issue: Permission denied
**Solution**: Run PowerShell as Administrator

### Issue: Module not found
**Solution**: Ensure virtual environment is activated:
```powershell
C:\Users\vorad\.ollama-flow\venv\Scripts\activate
```

## Framework Features Available

### ✅ Core Framework
- Enhanced Multi-AI Agent Orchestration
- Neural Intelligence Engine
- MCP Tools Manager (24+ tools)
- Monitoring System
- Session Management

### ✅ Dashboard Features
- Web Dashboard with Session Management
- Real-time system monitoring
- Session creation and control
- Session history and statistics

### ✅ CLI Tools
- `python enhanced_main.py` - Main framework
- `python dashboard\simple_dashboard.py` - Web dashboard
- `python cli_dashboard.py` - CLI dashboard
- `.\ollama-flow` - CLI wrapper (requires setup)

## Quick Start Commands

```powershell
# Activate environment
C:\Users\vorad\.ollama-flow\venv\Scripts\activate

# Run a simple task
python enhanced_main.py --task "Create a Python calculator" --workers 4 --arch HIERARCHICAL

# Start web dashboard
python dashboard\simple_dashboard.py

# Start CLI dashboard
python cli_dashboard.py

# Run comprehensive tests
python -m pytest tests/ -v
```

## Support

If you encounter any issues:

1. **Check Ollama**: `ollama --version`
2. **Check Python**: Ensure you're using the virtual environment
3. **Check Dependencies**: `pip list` in activated environment
4. **Check Logs**: Look for error messages in console output

The framework is now ready to use on Windows with all v2.1.0 features including the new session management dashboard!