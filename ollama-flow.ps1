#Requires -Version 5.1

<#
.SYNOPSIS
    Ollama Flow CLI Wrapper for Windows PowerShell
    
.DESCRIPTION
    PowerShell version of the Ollama Flow CLI wrapper with enhanced features,
    better error handling, and improved user experience.
    
.PARAMETER Command
    The command to execute (run, dashboard, models, etc.)
    
.PARAMETER Arguments
    Additional arguments to pass to the command
    
.EXAMPLE
    .\ollama-flow.ps1 run "Create a web app" --workers 4
    
.EXAMPLE
    .\ollama-flow.ps1 dashboard
    
.EXAMPLE
    .\ollama-flow.ps1 models pull codellama:7b
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "",
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments = @()
)

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonDir = Join-Path $ScriptDir "ollama-flow-python"
$DashboardDir = Join-Path $ScriptDir "dashboard"

# Color definitions
$Colors = @{
    Green = "Green"
    Yellow = "Yellow" 
    Red = "Red"
    Blue = "Blue"
    Cyan = "Cyan"
    Magenta = "Magenta"
}

# Helper function for colored output
function Write-ColoredText {
    param(
        [string]$Text,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if ($Colors.ContainsKey($Color)) {
        Write-Host $Text -ForegroundColor $Colors[$Color] -NoNewline:$NoNewline
    } else {
        Write-Host $Text -NoNewline:$NoNewline
    }
}

# Helper function to check if virtual environment exists
function Test-VirtualEnvironment {
    $venvPath = Join-Path $PythonDir "venv\Scripts\activate.ps1"
    return Test-Path $venvPath
}

# Helper function to activate virtual environment
function Invoke-InVirtualEnvironment {
    param(
        [Parameter(Mandatory=$true)]
        [scriptblock]$ScriptBlock
    )
    
    if (-not (Test-VirtualEnvironment)) {
        Write-ColoredText "❌ Virtual environment not found. Please run: ollama-flow install" "Red"
        return
    }
    
    Push-Location $PythonDir
    try {
        # Activate virtual environment
        & "venv\Scripts\Activate.ps1"
        
        # Execute the script block
        & $ScriptBlock
        
        # Deactivate virtual environment
        deactivate
    }
    finally {
        Pop-Location
    }
}

# Main command dispatcher
function Invoke-OllamaFlowCommand {
    param(
        [string]$Cmd,
        [string[]]$Args
    )
    
    switch ($Cmd.ToLower()) {
        { $_ -in @("", "help", "--help", "-h") } { Show-Help }
        { $_ -in @("run", "task") } { Invoke-RunTask $Args }
        "enhanced" { Invoke-Enhanced $Args }
        { $_ -in @("dashboard", "web") } { Start-Dashboard $Args }
        "cli" { Start-CliDashboard $Args }
        "sessions" { Start-Sessions $Args }
        { $_ -in @("server", "nodejs") } { Start-Server $Args }
        "status" { Show-Status }
        "health" { Show-Health $Args }
        { $_ -in @("models", "ollama") } { Manage-Models $Args }
        { $_ -in @("install", "setup") } { Install-Dependencies }
        "test" { Invoke-Tests $Args }
        "benchmark" { Invoke-Benchmark $Args }
        "logs" { Show-Logs }
        "config" { Show-Config }
        "version" { Show-Version }
        "update" { Update-System }
        "clean" { Clean-System }
        default { 
            Write-ColoredText "❌ Unknown command: $Cmd" "Red"
            Write-ColoredText "Run 'ollama-flow help' for available commands" "Yellow"
        }
    }
}

# Command implementations
function Show-Help {
    Write-ColoredText @"

========================================
🚀 Ollama Flow CLI Wrapper v2.0 (PowerShell)
========================================

"@ "Cyan"
    
    Write-Host "Unified command-line interface for Ollama Flow Enhanced Framework"
    Write-Host ""
    
    Write-ColoredText "USAGE:" "Green"
    Write-Host "  ollama-flow <command> [options]"
    Write-Host ""
    
    Write-ColoredText "CORE COMMANDS:" "Green"
    Write-ColoredText "  run/task       " "Yellow" -NoNewline
    Write-Host "Run a task with the enhanced framework"
    Write-ColoredText "  enhanced       " "Yellow" -NoNewline
    Write-Host "Run enhanced framework directly"
    Write-ColoredText "  dashboard      " "Yellow" -NoNewline
    Write-Host "Start web dashboard"
    Write-ColoredText "  cli            " "Yellow" -NoNewline
    Write-Host "Start CLI dashboard"
    Write-ColoredText "  sessions       " "Yellow" -NoNewline
    Write-Host "Start session management dashboard"
    Write-ColoredText "  server         " "Yellow" -NoNewline
    Write-Host "Start Node.js server (legacy)"
    Write-Host ""
    
    Write-ColoredText "SYSTEM COMMANDS:" "Green"
    Write-ColoredText "  status         " "Yellow" -NoNewline
    Write-Host "Show system status"
    Write-ColoredText "  health         " "Yellow" -NoNewline
    Write-Host "Run health check"
    Write-ColoredText "  models         " "Yellow" -NoNewline
    Write-Host "Manage Ollama models"
    Write-ColoredText "  install        " "Yellow" -NoNewline
    Write-Host "Install/update dependencies"
    Write-ColoredText "  test           " "Yellow" -NoNewline
    Write-Host "Run test suite"
    Write-ColoredText "  benchmark      " "Yellow" -NoNewline
    Write-Host "Run performance benchmarks"
    Write-ColoredText "  logs           " "Yellow" -NoNewline
    Write-Host "View system logs"
    Write-ColoredText "  config         " "Yellow" -NoNewline
    Write-Host "Show configuration"
    Write-ColoredText "  version        " "Yellow" -NoNewline
    Write-Host "Show version information"
    Write-ColoredText "  update         " "Yellow" -NoNewline
    Write-Host "Update system components"
    Write-ColoredText "  clean          " "Yellow" -NoNewline
    Write-Host "Clean temporary files"
    Write-Host ""
    
    Write-ColoredText "EXAMPLES:" "Green"
    Write-ColoredText "  ollama-flow run `"Create a web app`" --workers 4" "Cyan"
    Write-ColoredText "  ollama-flow enhanced --task `"Build API`" --arch HIERARCHICAL" "Cyan"
    Write-ColoredText "  ollama-flow dashboard" "Cyan"
    Write-ColoredText "  ollama-flow models pull codellama:7b" "Cyan"
    Write-Host ""
}

function Invoke-RunTask {
    param([string[]]$Args)
    
    if ($Args.Count -eq 0) {
        Write-ColoredText "❌ Task description required" "Red"
        Write-Host "Usage: ollama-flow run `"task description`" [options]"
        return
    }
    
    Write-ColoredText "🚀 Running Ollama Flow Enhanced Task..." "Cyan"
    
    Invoke-InVirtualEnvironment {
        python enhanced_main.py --task $Args
    }
}

function Invoke-Enhanced {
    param([string[]]$Args)
    
    Write-ColoredText "🧠 Starting Enhanced Ollama Flow Framework..." "Cyan"
    
    Invoke-InVirtualEnvironment {
        python enhanced_main.py $Args
    }
}

function Start-Dashboard {
    param([string[]]$Args)
    
    Write-ColoredText "📊 Starting Web Dashboard..." "Cyan"
    Write-ColoredText "✅ Dashboard starting at http://localhost:5000" "Green"
    Write-ColoredText "Press Ctrl+C to stop" "Yellow"
    
    Invoke-InVirtualEnvironment {
        python dashboard\simple_dashboard.py --port 5000 $Args
    }
}

function Start-CliDashboard {
    param([string[]]$Args)
    
    Write-ColoredText "💻 Starting CLI Dashboard..." "Cyan"
    
    Invoke-InVirtualEnvironment {
        python cli_dashboard.py $Args
    }
}

function Start-Sessions {
    param([string[]]$Args)
    
    Write-ColoredText "💾 Starting Session Management Dashboard..." "Cyan"
    
    Invoke-InVirtualEnvironment {
        python test_session_dashboard_windows.py $Args
    }
}

function Start-Server {
    param([string[]]$Args)
    
    Write-ColoredText "🌐 Starting Node.js Server..." "Cyan"
    Write-ColoredText "✅ Server starting at http://localhost:3000" "Green"
    Write-ColoredText "Press Ctrl+C to stop" "Yellow"
    
    Push-Location $ScriptDir
    try {
        npm run start:server
    }
    finally {
        Pop-Location
    }
}

function Show-Status {
    Write-ColoredText @"
🔍 Ollama Flow System Status
=====================================
"@ "Cyan"
    
    # Check Python environment
    if (Test-VirtualEnvironment) {
        Write-ColoredText "✅ Python Environment: OK" "Green"
        
        # Check key packages
        Invoke-InVirtualEnvironment {
            try {
                python -c "import ollama; print('✅ Ollama Package: OK')"
                python -c "import flask; print('✅ Flask: OK')"
                python -c "import psutil; print('✅ psutil: OK')"
            }
            catch {
                Write-ColoredText "❌ Some Python packages missing" "Red"
            }
        }
    } else {
        Write-ColoredText "❌ Python Environment: Not installed" "Red"
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>$null
        if ($nodeVersion) {
            Write-ColoredText "✅ Node.js: $nodeVersion" "Green"
        }
    }
    catch {
        Write-ColoredText "❌ Node.js: Not installed" "Red"
    }
    
    # Check Ollama
    try {
        $ollamaVersion = ollama --version 2>$null
        if ($ollamaVersion) {
            Write-ColoredText "✅ Ollama: $ollamaVersion" "Green"
            
            Write-Host ""
            Write-ColoredText "Available Models:" "Yellow"
            ollama list 2>$null
        }
    }
    catch {
        Write-ColoredText "❌ Ollama: Not installed" "Red"
    }
    
    # System resources
    Write-Host ""
    Write-ColoredText "System Resources:" "Yellow"
    
    if (Test-VirtualEnvironment) {
        Invoke-InVirtualEnvironment {
            try {
                python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%, Disk: {psutil.disk_usage(\".\").percent}%')"
            }
            catch {
                Write-ColoredText "❌ Could not get system info" "Red"
            }
        }
    }
}

function Show-Health {
    param([string[]]$Args)
    
    Write-ColoredText "🏥 Running Health Check..." "Cyan"
    
    Invoke-InVirtualEnvironment {
        python enhanced_main.py --health-check $Args
    }
}

function Manage-Models {
    param([string[]]$Args)
    
    if ($Args.Count -eq 0) {
        Write-ColoredText "🤖 Available Ollama Models:" "Cyan"
        try {
            ollama list
        }
        catch {
            Write-ColoredText "❌ Ollama not available" "Red"
        }
        return
    }
    
    switch ($Args[0].ToLower()) {
        "list" {
            Write-ColoredText "🤖 Available Ollama Models:" "Cyan"
            ollama list
        }
        "pull" {
            if ($Args.Count -lt 2) {
                Write-ColoredText "❌ Model name required" "Red"
                Write-Host "Usage: ollama-flow models pull <model-name>"
                return
            }
            Write-ColoredText "📥 Downloading model: $($Args[1])" "Cyan"
            ollama pull $Args[1]
        }
        "remove" {
            if ($Args.Count -lt 2) {
                Write-ColoredText "❌ Model name required" "Red"
                Write-Host "Usage: ollama-flow models remove <model-name>"
                return
            }
            Write-ColoredText "🗑️ Removing model: $($Args[1])" "Cyan"
            ollama rm $Args[1]
        }
        "update" {
            Write-ColoredText "🔄 Updating recommended models..." "Cyan"
            ollama pull codellama:7b
            ollama pull llama3
        }
        default {
            Write-ColoredText "❌ Unknown models command: $($Args[0])" "Red"
            Write-Host "Available: list, pull, remove, update"
        }
    }
}

function Install-Dependencies {
    Write-ColoredText "📦 Installing/Updating Dependencies..." "Cyan"
    
    $installScript = Join-Path $ScriptDir "install_windows.bat"
    if (Test-Path $installScript) {
        & $installScript
    } else {
        Write-ColoredText "❌ install_windows.bat not found" "Red"
    }
}

function Invoke-Tests {
    param([string[]]$Args)
    
    Write-ColoredText "🧪 Running Test Suite..." "Cyan"
    
    # Python tests
    if (Test-VirtualEnvironment) {
        Write-ColoredText "Running Python tests..." "Yellow"
        Invoke-InVirtualEnvironment {
            pytest $Args
        }
    } else {
        Write-ColoredText "❌ Python environment not found" "Red"
    }
    
    # Node.js tests
    Write-ColoredText "Running Node.js tests..." "Yellow"
    Push-Location $ScriptDir
    try {
        npm test
    }
    finally {
        Pop-Location
    }
}

function Invoke-Benchmark {
    param([string[]]$Args)
    
    Write-ColoredText "⚡ Running Performance Benchmarks..." "Cyan"
    
    Invoke-InVirtualEnvironment {
        python enhanced_main.py --benchmark $Args
    }
}

function Show-Logs {
    Write-ColoredText @"
📋 System Logs
=============
"@ "Cyan"
    
    $installLog = Join-Path $ScriptDir "install.log"
    if (Test-Path $installLog) {
        Write-ColoredText "Installation Log (last 20 lines):" "Yellow"
        Get-Content $installLog | Select-Object -Last 20
        Write-Host ""
    }
    
    $flowLog = Join-Path $PythonDir "ollama_flow.log"
    if (Test-Path $flowLog) {
        Write-ColoredText "Ollama Flow Log (last 20 lines):" "Yellow"
        Get-Content $flowLog | Select-Object -Last 20
        Write-Host ""
    }
    
    $dashboardLog = Join-Path $PythonDir "dashboard.log"
    if (Test-Path $dashboardLog) {
        Write-ColoredText "Dashboard Log (last 10 lines):" "Yellow"
        Get-Content $dashboardLog | Select-Object -Last 10
    }
}

function Show-Config {
    Write-ColoredText @"
⚙️ Configuration
================
"@ "Cyan"
    
    Write-ColoredText "Installation Directory: " "Yellow" -NoNewline
    Write-Host $ScriptDir
    Write-ColoredText "Python Directory: " "Yellow" -NoNewline
    Write-Host $PythonDir
    
    $envFile = Join-Path $PythonDir ".env"
    if (Test-Path $envFile) {
        Write-Host ""
        Write-ColoredText "Environment Configuration (.env):" "Yellow"
        Get-Content $envFile
    } else {
        Write-ColoredText "❌ .env file not found" "Red"
    }
}

function Show-Version {
    Write-ColoredText @"
ℹ️ Version Information
====================
"@ "Cyan"
    
    Write-ColoredText "Ollama Flow CLI Wrapper: " "Yellow" -NoNewline
    Write-Host "v2.0 (PowerShell)"
    Write-ColoredText "Enhanced Framework: " "Yellow" -NoNewline
    Write-Host "v2.1.1"
    
    # Check Python version
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-ColoredText "Python: " "Yellow" -NoNewline
            Write-Host $pythonVersion.Replace("Python ", "")
        }
    }
    catch {
        Write-ColoredText "Python: " "Yellow" -NoNewline
        Write-ColoredText "Not available" "Red"
    }
    
    # Check Node.js version
    try {
        $nodeVersion = node --version 2>$null
        if ($nodeVersion) {
            Write-ColoredText "Node.js: " "Yellow" -NoNewline
            Write-Host $nodeVersion
        }
    }
    catch {
        Write-ColoredText "Node.js: " "Yellow" -NoNewline
        Write-ColoredText "Not available" "Red"
    }
    
    # Check Ollama version
    try {
        $ollamaVersion = ollama --version 2>$null
        if ($ollamaVersion) {
            Write-ColoredText "Ollama: " "Yellow" -NoNewline
            Write-Host $ollamaVersion
        }
    }
    catch {
        Write-ColoredText "Ollama: " "Yellow" -NoNewline
        Write-ColoredText "Not available" "Red"
    }
}

function Update-System {
    Write-ColoredText "🔄 Updating System Components..." "Cyan"
    
    Write-ColoredText "Updating Python packages..." "Yellow"
    if (Test-VirtualEnvironment) {
        Invoke-InVirtualEnvironment {
            pip install --upgrade pip
            pip install --upgrade -r requirements.txt
        }
    }
    
    Write-ColoredText "Updating Node.js packages..." "Yellow"
    Push-Location $ScriptDir
    try {
        npm update
    }
    finally {
        Pop-Location
    }
    
    Write-ColoredText "Updating Ollama models..." "Yellow"
    try {
        ollama pull codellama:7b 2>$null
    }
    catch {
        Write-ColoredText "❌ Could not update codellama:7b" "Red"
    }
    
    Write-ColoredText "✅ Update complete" "Green"
}

function Clean-System {
    Write-ColoredText "🧹 Cleaning Temporary Files..." "Cyan"
    
    # Clean Python cache
    Write-ColoredText "Cleaning Python cache..." "Yellow"
    Push-Location $PythonDir
    try {
        Get-ChildItem -Path . -Recurse -Name "__pycache__" -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Recurse -Name "*.pyc" -Force | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    finally {
        Pop-Location
    }
    
    # Clean Node.js cache
    Write-ColoredText "Cleaning Node.js cache..." "Yellow"
    $nodeCache = Join-Path $ScriptDir "node_modules\.cache"
    if (Test-Path $nodeCache) {
        Remove-Item $nodeCache -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Clean old logs (older than 7 days)
    Write-ColoredText "Cleaning old logs..." "Yellow"
    Get-ChildItem -Path $PythonDir -Name "*.log" | Where-Object {
        (Get-Item (Join-Path $PythonDir $_)).LastWriteTime -lt (Get-Date).AddDays(-7)
    } | ForEach-Object {
        Remove-Item (Join-Path $PythonDir $_) -Force -ErrorAction SilentlyContinue
    }
    
    # Clean temporary databases
    Get-ChildItem -Path $PythonDir -Name "temp_*.db" | ForEach-Object {
        Remove-Item (Join-Path $PythonDir $_) -Force -ErrorAction SilentlyContinue
    }
    
    Write-ColoredText "✅ Cleanup complete" "Green"
}

# Main execution
if ($Command -eq "" -and $Arguments.Count -eq 0) {
    Show-Help
} else {
    Invoke-OllamaFlowCommand $Command $Arguments
}