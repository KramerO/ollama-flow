@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: Ollama Flow CLI Wrapper for Windows
:: =============================================================================
:: This script provides a unified command-line interface for all Ollama Flow
:: operations, making it easy to access all features with simple commands.
:: =============================================================================

:: Get script directory
set "SCRIPT_DIR=%~dp0"
set "PYTHON_DIR=%SCRIPT_DIR%ollama-flow-python"
set "DASHBOARD_DIR=%SCRIPT_DIR%dashboard"

:: Set colors for output (if supported)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "CYAN=[96m"
set "RESET=[0m"

:: Main command handling
if "%1"=="" goto show_help
if "%1"=="help" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help

if "%1"=="run" goto run_task
if "%1"=="task" goto run_task
if "%1"=="enhanced" goto run_enhanced
if "%1"=="dashboard" goto start_dashboard
if "%1"=="web" goto start_dashboard
if "%1"=="cli" goto start_cli_dashboard
if "%1"=="sessions" goto start_sessions
if "%1"=="server" goto start_server
if "%1"=="nodejs" goto start_server
if "%1"=="status" goto show_status
if "%1"=="health" goto show_health
if "%1"=="models" goto manage_models
if "%1"=="ollama" goto manage_models
if "%1"=="install" goto install_deps
if "%1"=="setup" goto install_deps
if "%1"=="test" goto run_tests
if "%1"=="benchmark" goto run_benchmark
if "%1"=="logs" goto show_logs
if "%1"=="config" goto show_config
if "%1"=="version" goto show_version
if "%1"=="update" goto update_system
if "%1"=="clean" goto clean_system

:: If no match, try to run as enhanced task
goto run_enhanced

:: =============================================================================
:: HELP SYSTEM
:: =============================================================================
:show_help
echo %CYAN%
echo ========================================
echo 🚀 Ollama Flow CLI Wrapper v2.0
echo ========================================
echo %RESET%
echo Unified command-line interface for Ollama Flow Enhanced Framework
echo.
echo %GREEN%USAGE:%RESET%
echo   ollama-flow ^<command^> [options]
echo.
echo %GREEN%CORE COMMANDS:%RESET%
echo   %YELLOW%run/task%RESET%       Run a task with the enhanced framework
echo   %YELLOW%enhanced%RESET%       Run enhanced framework directly
echo   %YELLOW%dashboard%RESET%      Start web dashboard
echo   %YELLOW%cli%RESET%            Start CLI dashboard  
echo   %YELLOW%sessions%RESET%       Start session management dashboard
echo   %YELLOW%server%RESET%         Start Node.js server (legacy)
echo.
echo %GREEN%SYSTEM COMMANDS:%RESET%
echo   %YELLOW%status%RESET%         Show system status
echo   %YELLOW%health%RESET%         Run health check
echo   %YELLOW%models%RESET%         Manage Ollama models
echo   %YELLOW%install%RESET%        Install/update dependencies
echo   %YELLOW%test%RESET%           Run test suite
echo   %YELLOW%benchmark%RESET%      Run performance benchmarks
echo   %YELLOW%logs%RESET%           View system logs
echo   %YELLOW%config%RESET%         Show configuration
echo   %YELLOW%version%RESET%        Show version information
echo   %YELLOW%update%RESET%         Update system components
echo   %YELLOW%clean%RESET%          Clean temporary files
echo.
echo %GREEN%EXAMPLES:%RESET%
echo   %CYAN%ollama-flow run "Create a web app" --workers 4%RESET%
echo   %CYAN%ollama-flow enhanced --task "Build API" --arch HIERARCHICAL%RESET%
echo   %CYAN%ollama-flow dashboard%RESET%
echo   %CYAN%ollama-flow sessions%RESET%
echo   %CYAN%ollama-flow models pull codellama:7b%RESET%
echo   %CYAN%ollama-flow test%RESET%
echo   %CYAN%ollama-flow benchmark%RESET%
echo.
echo %GREEN%ENHANCED FRAMEWORK OPTIONS:%RESET%
echo   --task "description"      Task description
echo   --workers N               Number of worker agents (2-12)
echo   --arch TYPE              Architecture (HIERARCHICAL/CENTRALIZED/FULLY_CONNECTED)
echo   --model NAME             Ollama model to use
echo   --project-folder PATH    Project output folder
echo   --secure                 Enable security mode
echo   --metrics                Enable metrics collection
echo   --benchmark              Enable benchmarking
echo   --interactive            Interactive mode
echo   --verbose                Verbose output
echo   --debug                  Debug mode
echo.
goto end

:: =============================================================================
:: TASK EXECUTION
:: =============================================================================
:run_task
shift
if "%1"=="" (
    echo %RED%❌ Task description required%RESET%
    echo Usage: ollama-flow run "task description" [options]
    goto end
)

echo %CYAN%🚀 Running Ollama Flow Enhanced Task...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found. Please run: ollama-flow install%RESET%
    goto end
)

call venv\Scripts\activate
python enhanced_main.py --task %*
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:run_enhanced
echo %CYAN%🧠 Starting Enhanced Ollama Flow Framework...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found. Please run: ollama-flow install%RESET%
    goto end
)

call venv\Scripts\activate
python enhanced_main.py %*
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:: =============================================================================
:: DASHBOARD COMMANDS
:: =============================================================================
:start_dashboard
echo %CYAN%📊 Starting Web Dashboard...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found. Please run: ollama-flow install%RESET%
    goto end
)

call venv\Scripts\activate
echo %GREEN%✅ Dashboard starting at http://localhost:5000%RESET%
echo %YELLOW%Press Ctrl+C to stop%RESET%
python dashboard\simple_dashboard.py --port 5000 %2 %3 %4 %5
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:start_cli_dashboard
echo %CYAN%💻 Starting CLI Dashboard...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found. Please run: ollama-flow install%RESET%
    goto end
)

call venv\Scripts\activate
python cli_dashboard.py %2 %3 %4 %5
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:start_sessions
echo %CYAN%💾 Starting Session Management Dashboard...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found. Please run: ollama-flow install%RESET%
    goto end
)

call venv\Scripts\activate
python test_session_dashboard_windows.py %2 %3 %4 %5
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:start_server
echo %CYAN%🌐 Starting Node.js Server...%RESET%
echo %GREEN%✅ Server starting at http://localhost:3000%RESET%
echo %YELLOW%Press Ctrl+C to stop%RESET%
npm run start:server
goto end

:: =============================================================================
:: SYSTEM INFORMATION
:: =============================================================================
:show_status
echo %CYAN%🔍 Ollama Flow System Status%RESET%
echo =====================================

:: Check Python environment
cd /d "%PYTHON_DIR%"
if exist "venv\Scripts\activate.bat" (
    echo %GREEN%✅ Python Environment: OK%RESET%
    call venv\Scripts\activate >nul 2>&1
    
    :: Check key packages
    python -c "import ollama; print('✅ Ollama Package: OK')" 2>nul || echo %RED%❌ Ollama Package: Missing%RESET%
    python -c "import flask; print('✅ Flask: OK')" 2>nul || echo %RED%❌ Flask: Missing%RESET%
    python -c "import psutil; print('✅ psutil: OK')" 2>nul || echo %RED%❌ psutil: Missing%RESET%
    
    call venv\Scripts\deactivate >nul 2>&1
) else (
    echo %RED%❌ Python Environment: Not installed%RESET%
)

:: Check Node.js
node --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do echo %GREEN%✅ Node.js: %%i%RESET%
) else (
    echo %RED%❌ Node.js: Not installed%RESET%
)

:: Check Ollama
ollama --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do echo %GREEN%✅ Ollama: %%i%RESET%
    
    echo.
    echo %YELLOW%Available Models:%RESET%
    ollama list 2>nul || echo %RED%❌ Could not list models%RESET%
) else (
    echo %RED%❌ Ollama: Not installed%RESET%
)

:: Check system resources
echo.
echo %YELLOW%System Resources:%RESET%
cd /d "%PYTHON_DIR%"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate >nul 2>&1
    python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%%, Memory: {psutil.virtual_memory().percent}%%, Disk: {psutil.disk_usage(\".\").percent}%%')" 2>nul || echo %RED%❌ Could not get system info%RESET%
    call venv\Scripts\deactivate >nul 2>&1
)

cd /d "%SCRIPT_DIR%"
goto end

:show_health
echo %CYAN%🏥 Running Health Check...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found%RESET%
    goto end
)

call venv\Scripts\activate
python enhanced_main.py --health-check %2 %3 %4 %5
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:: =============================================================================
:: MODEL MANAGEMENT
:: =============================================================================
:manage_models
shift
if "%1"=="" (
    echo %CYAN%🤖 Available Ollama Models:%RESET%
    ollama list 2>nul || echo %RED%❌ Ollama not available%RESET%
    goto end
)

if "%1"=="list" (
    echo %CYAN%🤖 Available Ollama Models:%RESET%
    ollama list
    goto end
)

if "%1"=="pull" (
    if "%2"=="" (
        echo %RED%❌ Model name required%RESET%
        echo Usage: ollama-flow models pull ^<model-name^>
        goto end
    )
    echo %CYAN%📥 Downloading model: %2%RESET%
    ollama pull %2
    goto end
)

if "%1"=="remove" (
    if "%2"=="" (
        echo %RED%❌ Model name required%RESET%
        echo Usage: ollama-flow models remove ^<model-name^>
        goto end
    )
    echo %CYAN%🗑️ Removing model: %2%RESET%
    ollama rm %2
    goto end
)

if "%1"=="update" (
    echo %CYAN%🔄 Updating recommended models...%RESET%
    ollama pull codellama:7b
    ollama pull llama3
    goto end
)

echo %RED%❌ Unknown models command: %1%RESET%
echo Available: list, pull, remove, update
goto end

:: =============================================================================
:: DEVELOPMENT COMMANDS
:: =============================================================================
:install_deps
echo %CYAN%📦 Installing/Updating Dependencies...%RESET%
call "%SCRIPT_DIR%install_windows.bat"
goto end

:run_tests
echo %CYAN%🧪 Running Test Suite...%RESET%

:: Python tests
cd /d "%PYTHON_DIR%"
if exist "venv\Scripts\activate.bat" (
    echo %YELLOW%Running Python tests...%RESET%
    call venv\Scripts\activate
    pytest %2 %3 %4 %5
    call venv\Scripts\deactivate
) else (
    echo %RED%❌ Python environment not found%RESET%
)

:: Node.js tests
cd /d "%SCRIPT_DIR%"
echo %YELLOW%Running Node.js tests...%RESET%
npm test

goto end

:run_benchmark
echo %CYAN%⚡ Running Performance Benchmarks...%RESET%
cd /d "%PYTHON_DIR%"
if not exist "venv\Scripts\activate.bat" (
    echo %RED%❌ Virtual environment not found%RESET%
    goto end
)

call venv\Scripts\activate
python enhanced_main.py --benchmark %2 %3 %4 %5
call venv\Scripts\deactivate
cd /d "%SCRIPT_DIR%"
goto end

:: =============================================================================
:: UTILITY COMMANDS
:: =============================================================================
:show_logs
echo %CYAN%📋 System Logs%RESET%
echo =============

if exist "%SCRIPT_DIR%install.log" (
    echo %YELLOW%Installation Log (last 20 lines):%RESET%
    powershell "Get-Content '%SCRIPT_DIR%install.log' | Select-Object -Last 20"
    echo.
)

if exist "%PYTHON_DIR%\ollama_flow.log" (
    echo %YELLOW%Ollama Flow Log (last 20 lines):%RESET%
    powershell "Get-Content '%PYTHON_DIR%\ollama_flow.log' | Select-Object -Last 20"
    echo.
)

if exist "%PYTHON_DIR%\dashboard.log" (
    echo %YELLOW%Dashboard Log (last 10 lines):%RESET%
    powershell "Get-Content '%PYTHON_DIR%\dashboard.log' | Select-Object -Last 10"
)

goto end

:show_config
echo %CYAN%⚙️ Configuration%RESET%
echo ================

echo %YELLOW%Installation Directory:%RESET% %SCRIPT_DIR%
echo %YELLOW%Python Directory:%RESET% %PYTHON_DIR%

if exist "%PYTHON_DIR%\.env" (
    echo.
    echo %YELLOW%Environment Configuration (.env):%RESET%
    type "%PYTHON_DIR%\.env"
) else (
    echo %RED%❌ .env file not found%RESET%
)

goto end

:show_version
echo %CYAN%ℹ️ Version Information%RESET%
echo ====================

echo %YELLOW%Ollama Flow CLI Wrapper:%RESET% v2.0
echo %YELLOW%Enhanced Framework:%RESET% v2.1.1

:: Check Python version
python --version 2>nul && (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo %YELLOW%Python:%RESET% %%i
) || echo %RED%Python: Not available%RESET%

:: Check Node.js version
node --version 2>nul && (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do echo %YELLOW%Node.js:%RESET% %%i
) || echo %RED%Node.js: Not available%RESET%

:: Check Ollama version
ollama --version 2>nul && (
    for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do echo %YELLOW%Ollama:%RESET% %%i
) || echo %RED%Ollama: Not available%RESET%

goto end

:update_system
echo %CYAN%🔄 Updating System Components...%RESET%

echo %YELLOW%Updating Python packages...%RESET%
cd /d "%PYTHON_DIR%"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
    pip install --upgrade pip
    pip install --upgrade -r requirements.txt
    call venv\Scripts\deactivate
)

echo %YELLOW%Updating Node.js packages...%RESET%
cd /d "%SCRIPT_DIR%"
npm update

echo %YELLOW%Updating Ollama models...%RESET%
ollama pull codellama:7b 2>nul || echo %RED%❌ Could not update codellama:7b%RESET%

echo %GREEN%✅ Update complete%RESET%
goto end

:clean_system
echo %CYAN%🧹 Cleaning Temporary Files...%RESET%

:: Clean Python cache
echo %YELLOW%Cleaning Python cache...%RESET%
cd /d "%PYTHON_DIR%"
if exist "__pycache__" rmdir /s /q "__pycache__"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"

:: Clean Node.js cache
echo %YELLOW%Cleaning Node.js cache...%RESET%
cd /d "%SCRIPT_DIR%"
if exist "node_modules\.cache" rmdir /s /q "node_modules\.cache"

:: Clean logs (older than 7 days)
echo %YELLOW%Cleaning old logs...%RESET%
forfiles /p "%PYTHON_DIR%" /m "*.log" /d -7 /c "cmd /c del @path" 2>nul

:: Clean temporary databases
if exist "%PYTHON_DIR%\temp_*.db" del /q "%PYTHON_DIR%\temp_*.db"

echo %GREEN%✅ Cleanup complete%RESET%
goto end

:: =============================================================================
:: END
:: =============================================================================
:end
endlocal
exit /b 0