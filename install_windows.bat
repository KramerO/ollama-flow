@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: Ollama Flow - Windows Installation Script
:: =============================================================================
:: This script automatically installs all dependencies and sets up Ollama Flow
:: on Windows systems with enhanced Python framework support.
:: =============================================================================

echo.
echo ========================================
echo 🚀 Ollama Flow Windows Installer v2.0
echo ========================================
echo.
echo Installing Enhanced Ollama Flow Framework...
echo ✓ Neural Intelligence Engine
echo ✓ MCP Tools Ecosystem (24+ tools)
echo ✓ Real-time Monitoring System
echo ✓ Session Management
echo ✓ Performance Benchmarking
echo.

:: Check if running as administrator
net session >nul 2>&1
if not %errorLevel% == 0 (
    echo ⚠️  WARNUNG: Nicht als Administrator ausgeführt.
    echo    Einige Installationen könnten fehlschlagen.
    echo    Für beste Ergebnisse als Administrator ausführen.
    echo.
    pause
)

:: Set variables
set "PROJECT_DIR=%cd%"
set "PYTHON_DIR=%PROJECT_DIR%\ollama-flow-python"
set "DASHBOARD_DIR=%PROJECT_DIR%\dashboard"
set "PHI_DIR=%PROJECT_DIR%\phi_service"
set "LOG_FILE=%PROJECT_DIR%\install.log"

:: Initialize log file
echo [%date% %time%] Starting Ollama Flow installation > "%LOG_FILE%"

:: =============================================================================
:: 1. CHECK PREREQUISITES
:: =============================================================================
echo [1/7] 🔍 Checking prerequisites...

:: Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python nicht gefunden!
    echo.
    echo Bitte installieren Sie Python 3.10+ von https://python.org
    echo Stellen Sie sicher, dass Python zu PATH hinzugefügt wird.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo ✅ Python %PYTHON_VERSION% gefunden

:: Check pip
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ pip nicht gefunden!
    echo Bitte installieren Sie pip oder führen Sie 'python -m ensurepip' aus.
    pause
    exit /b 1
)
echo ✅ pip verfügbar

:: Check Node.js
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Node.js nicht gefunden!
    echo.
    echo Bitte installieren Sie Node.js 18+ von https://nodejs.org
    echo.
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version 2^>^&1') do set "NODE_VERSION=%%i"
echo ✅ Node.js %NODE_VERSION% gefunden

:: Check npm
npm --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ npm nicht gefunden!
    pause
    exit /b 1
)
echo ✅ npm verfügbar

:: Check Git
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Git nicht gefunden - optional aber empfohlen
) else (
    echo ✅ Git verfügbar
)

:: Check Ollama
ollama --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Ollama nicht gefunden!
    echo.
    echo Bitte installieren Sie Ollama von https://ollama.ai
    echo Ollama wird für die KI-Modelle benötigt.
    echo.
    set /p "continue=Trotzdem fortfahren? (j/n): "
    if /i "!continue!" neq "j" (
        exit /b 1
    )
) else (
    echo ✅ Ollama verfügbar
)

echo.

:: =============================================================================
:: 2. INSTALL NODE.JS DEPENDENCIES
:: =============================================================================
echo [2/7] 📦 Installing Node.js dependencies...

echo Installing npm packages...
npm install >> "%LOG_FILE%" 2>&1
if %errorLevel% neq 0 (
    echo ❌ Fehler beim Installieren der npm-Pakete
    echo Details in %LOG_FILE%
    pause
    exit /b 1
)
echo ✅ npm packages installed

echo Building TypeScript...
npm run build >> "%LOG_FILE%" 2>&1
if %errorLevel% neq 0 (
    echo ❌ Fehler beim TypeScript Build
    echo Details in %LOG_FILE%
    pause
    exit /b 1
)
echo ✅ TypeScript compiled

echo.

:: =============================================================================
:: 3. SETUP ENHANCED PYTHON FRAMEWORK
:: =============================================================================
echo [3/7] 🧠 Setting up Enhanced Python Framework...

if not exist "%PYTHON_DIR%" (
    echo ❌ ollama-flow-python Verzeichnis nicht gefunden!
    pause
    exit /b 1
)

cd "%PYTHON_DIR%"

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv >> "%LOG_FILE%" 2>&1
if %errorLevel% neq 0 (
    echo ❌ Fehler beim Erstellen der virtuellen Umgebung
    cd "%PROJECT_DIR%"
    pause
    exit /b 1
)
echo ✅ Virtual environment created

:: Activate virtual environment and install dependencies
echo Installing Python dependencies...
call venv\Scripts\activate
pip install --upgrade pip >> "%LOG_FILE%" 2>&1
pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
if %errorLevel% neq 0 (
    echo ❌ Fehler beim Installieren der Python-Abhängigkeiten
    echo Details in %LOG_FILE%
    cd "%PROJECT_DIR%"
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

:: Install additional enhanced features
echo Installing enhanced components...
pip install scikit-learn numpy flask flask-socketio requests aiohttp click rich typer >> "%LOG_FILE%" 2>&1
echo ✅ Enhanced components installed

call venv\Scripts\deactivate
cd "%PROJECT_DIR%"

echo.

:: =============================================================================
:: 4. SETUP DASHBOARD
:: =============================================================================
echo [4/7] 📊 Setting up Dashboard...

if exist "%DASHBOARD_DIR%" (
    cd "%DASHBOARD_DIR%"
    
    echo Creating dashboard virtual environment...
    python -m venv venv >> "%LOG_FILE%" 2>&1
    if %errorLevel% neq 0 (
        echo ⚠️  Dashboard venv creation failed, continuing...
    ) else (
        call venv\Scripts\activate
        pip install --upgrade pip >> "%LOG_FILE%" 2>&1
        if exist "requirements.txt" (
            pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
            echo ✅ Dashboard dependencies installed
        ) else (
            pip install flask psutil >> "%LOG_FILE%" 2>&1
            echo ✅ Basic dashboard dependencies installed
        )
        call venv\Scripts\deactivate
    )
    
    cd "%PROJECT_DIR%"
) else (
    echo ⚠️  Dashboard directory not found, skipping...
)

echo.

:: =============================================================================
:: 5. SETUP PHI SERVICE (if exists)
:: =============================================================================
echo [5/7] 🔬 Setting up Phi Service...

if exist "%PHI_DIR%" (
    cd "%PHI_DIR%"
    
    echo Creating phi service virtual environment...
    python -m venv venv >> "%LOG_FILE%" 2>&1
    if %errorLevel% neq 0 (
        echo ⚠️  Phi service venv creation failed, continuing...
    ) else (
        call venv\Scripts\activate
        pip install --upgrade pip >> "%LOG_FILE%" 2>&1
        if exist "requirements.txt" (
            pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
            echo ✅ Phi service dependencies installed
        )
        call venv\Scripts\deactivate
    )
    
    cd "%PROJECT_DIR%"
) else (
    echo ⚠️  Phi service directory not found, skipping...
)

echo.

:: =============================================================================
:: 6. CREATE CONFIGURATION FILES
:: =============================================================================
echo [6/7] ⚙️  Creating configuration files...

:: Create .env file for Python framework
cd "%PYTHON_DIR%"
if not exist ".env" (
    echo Creating .env configuration file...
    (
        echo # Ollama Flow Enhanced Configuration
        echo OLLAMA_MODEL=codellama:7b
        echo OLLAMA_WORKER_COUNT=4
        echo OLLAMA_ARCHITECTURE_TYPE=HIERARCHICAL
        echo OLLAMA_PROJECT_FOLDER=%PYTHON_DIR%\projects
        echo.
        echo # Enhanced Features ^(all enabled by default^)
        echo OLLAMA_NEURAL_ENABLED=true
        echo OLLAMA_MCP_ENABLED=true
        echo OLLAMA_MONITORING_ENABLED=true
        echo OLLAMA_SESSION_ENABLED=true
        echo.
        echo # Neural Intelligence Settings
        echo NEURAL_DB_PATH=neural_intelligence.db
        echo NEURAL_CONFIDENCE_THRESHOLD=0.7
        echo.
        echo # MCP Tools Settings
        echo MCP_DB_PATH=mcp_tools.db
        echo MCP_EXECUTION_TIMEOUT=300
        echo.
        echo # Monitoring Settings
        echo MONITORING_DB_PATH=monitoring.db
        echo MONITORING_INTERVAL=10
        echo ALERT_THRESHOLDS_CPU=80,95
        echo ALERT_THRESHOLDS_MEMORY=85,95
        echo.
        echo # Session Management
        echo SESSION_DB_PATH=sessions.db
        echo SESSION_AUTO_SAVE_INTERVAL=300
        echo SESSION_CLEANUP_DAYS=30
    ) > .env
    echo ✅ .env file created
)

:: Create projects directory
if not exist "projects" (
    mkdir projects
    echo ✅ Projects directory created
)

cd "%PROJECT_DIR%"

:: Create batch files for easy startup
echo Creating startup scripts...

:: Make CLI wrapper executable
echo Setting up CLI wrapper...

:: Enhanced main launcher
(
    echo @echo off
    echo cd /d "%PYTHON_DIR%"
    echo call venv\Scripts\activate
    echo python enhanced_main.py %%*
    echo pause
) > start_enhanced.bat

:: Dashboard launcher
(
    echo @echo off
    echo cd /d "%PYTHON_DIR%\dashboard"
    echo call ..\venv\Scripts\activate
    echo python simple_dashboard.py --port 5000
    echo pause
) > start_dashboard.bat

:: CLI Dashboard launcher
(
    echo @echo off
    echo cd /d "%PYTHON_DIR%"
    echo call venv\Scripts\activate
    echo python cli_dashboard.py
    echo pause
) > start_cli_dashboard.bat

:: Session dashboard launcher
(
    echo @echo off
    echo cd /d "%PYTHON_DIR%"
    echo call venv\Scripts\activate
    echo python test_session_dashboard_windows.py
    echo pause
) > start_session_dashboard.bat

:: Node.js server launcher
(
    echo @echo off
    echo cd /d "%PROJECT_DIR%"
    echo npm run start:server
    echo pause
) > start_nodejs_server.bat

echo ✅ Startup scripts created

:: Setup PATH integration
echo Setting up CLI integration...

:: Create a batch file that can be added to PATH
(
    echo @echo off
    echo "%PROJECT_DIR%\ollama-flow.bat" %%*
) > "%TEMP%\ollama-flow-path.bat"

:: Check if project directory is in PATH
echo %PATH% | findstr /i "%PROJECT_DIR%" >nul
if %errorLevel% neq 0 (
    echo.
    echo 📝 PATH Integration Setup:
    echo.
    echo To use 'ollama-flow' from anywhere, add this directory to your PATH:
    echo %PROJECT_DIR%
    echo.
    echo Option 1 - Manual Setup:
    echo   1. Press Win+R, type: sysdm.cpl
    echo   2. Go to Advanced ^> Environment Variables
    echo   3. Add "%PROJECT_DIR%" to your PATH
    echo.
    echo Option 2 - PowerShell ^(Run as Administrator^):
    echo   [Environment]::SetEnvironmentVariable^("Path", $env:Path + ";%PROJECT_DIR%", "User"^)
    echo.
    echo Option 3 - Command Prompt ^(Run as Administrator^):
    echo   setx PATH "%%PATH%%;%PROJECT_DIR%"
    echo.
    set /p "setup_path=Add to PATH automatically? (j/n - requires restart): "
    if /i "!setup_path!" == "j" (
        setx PATH "%PATH%;%PROJECT_DIR%" >nul 2>&1
        if %errorLevel% == 0 (
            echo ✅ PATH updated - restart command prompt to use 'ollama-flow' globally
        ) else (
            echo ⚠️  PATH update failed - you may need administrator rights
        )
    )
) else (
    echo ✅ CLI integration already configured
)

echo ✅ CLI wrapper setup complete

echo.

:: =============================================================================
:: 7. DOWNLOAD OLLAMA MODELS (if Ollama is available)
:: =============================================================================
echo [7/7] 🤖 Setting up AI Models...

ollama --version >nul 2>&1
if %errorLevel% == 0 (
    echo Downloading recommended AI models...
    echo This may take a few minutes...
    
    echo Downloading CodeLlama 7B...
    ollama pull codellama:7b >> "%LOG_FILE%" 2>&1
    if %errorLevel% == 0 (
        echo ✅ CodeLlama 7B downloaded
    ) else (
        echo ⚠️  CodeLlama 7B download failed - you can download it later
    )
    
    echo Checking for Llama3...
    ollama list | findstr "llama3" >nul 2>&1
    if %errorLevel% neq 0 (
        set /p "download_llama3=Download Llama3 model? (j/n): "
        if /i "!download_llama3!" == "j" (
            ollama pull llama3 >> "%LOG_FILE%" 2>&1
            if %errorLevel% == 0 (
                echo ✅ Llama3 downloaded
            )
        )
    ) else (
        echo ✅ Llama3 already available
    )
) else (
    echo ⚠️  Ollama not available - skipping model download
    echo You can install models later with:
    echo   ollama pull codellama:7b
    echo   ollama pull llama3
)

echo.

:: =============================================================================
:: INSTALLATION COMPLETE
:: =============================================================================
echo ========================================
echo 🎉 Installation Complete!
echo ========================================
echo.
echo Enhanced Ollama Flow Framework installed successfully!
echo.
echo 📋 What was installed:
echo ✅ Node.js backend with TypeScript
echo ✅ Enhanced Python framework with Neural Intelligence
echo ✅ MCP Tools Ecosystem (24+ specialized tools)
echo ✅ Real-time Monitoring System
echo ✅ Session Management with persistence
echo ✅ Web and CLI dashboards
echo ✅ Configuration files and startup scripts
echo ✅ CLI wrapper for easy command access
echo.
echo 🚀 Quick Start Options:
echo.
echo 1. CLI Wrapper (Global Access - after PATH setup):
echo    ollama-flow run "Create a web app" --workers 4
echo    ollama-flow dashboard
echo    ollama-flow sessions
echo    ollama-flow models pull codellama:7b
echo.
echo 2. Enhanced Python Framework (Direct):
echo    start_enhanced.bat
echo.
echo 3. Interactive CLI Dashboard:
echo    start_cli_dashboard.bat
echo.
echo 4. Web Dashboard:
echo    start_dashboard.bat
echo    Then visit: http://localhost:5000
echo.
echo 5. Session Management Dashboard:
echo    start_session_dashboard.bat
echo.
echo 6. Node.js Server (Legacy):
echo    start_nodejs_server.bat
echo.
echo 📖 Documentation:
echo ✓ README_WINDOWS.md - Comprehensive Windows guide
echo ✓ ENHANCED_FEATURES.md - New features overview
echo ✓ Installation log: %LOG_FILE%
echo.
echo 💡 Example Commands:
echo.
echo   CLI Wrapper (Global - after PATH setup):
echo   ollama-flow run "Create a web app" --workers 4
echo   ollama-flow enhanced --task "Complex project" --workers 8 --metrics --benchmark --secure
echo   ollama-flow dashboard
echo   ollama-flow status
echo   ollama-flow help
echo.
echo   Enhanced Framework (Direct):
echo   cd ollama-flow-python
echo   venv\Scripts\activate
echo   python enhanced_main.py --task "Create a web app" --workers 4
echo.
echo ⚠️  Important Notes:
echo • Make sure Ollama is running: ollama serve
echo • Check available models: ollama list
echo • Download models if needed: ollama pull codellama:7b
echo • Read README_WINDOWS.md for detailed usage instructions
echo.
echo 🆘 Need Help?
echo • Check README_WINDOWS.md for troubleshooting
echo • View logs in %LOG_FILE%
echo • Run enhanced_main.py --help for all options
echo.

:: Final system check
echo 🔍 Final System Check:
echo.

cd "%PYTHON_DIR%"
call venv\Scripts\activate >nul 2>&1
python -c "import ollama; print('✅ Ollama Python package: OK')" 2>nul || echo "⚠️  Ollama Python package needs check"
python -c "import flask; print('✅ Flask: OK')" 2>nul || echo "⚠️  Flask needs check"
python -c "import psutil; print('✅ psutil: OK')" 2>nul || echo "⚠️  psutil needs check"
python -c "import sklearn; print('✅ scikit-learn: OK')" 2>nul || echo "⚠️  scikit-learn needs check"
call venv\Scripts\deactivate >nul 2>&1

cd "%PROJECT_DIR%"

echo.
echo 🎯 Ready to use Ollama Flow Enhanced Framework!
echo.
echo Press any key to exit...
pause >nul

endlocal