@echo off
echo Checking for Node.js and npm...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js from https://nodejs.org/ and try again.
    pause
    exit /b 1
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo npm is not installed. Please install Node.js from https://nodejs.org/ and try again.
    pause
    exit /b 1
)
echo Node.js and npm are installed.

echo Checking for Python and pip...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python from https://www.python.org/ and try again.
    pause
    exit /b 1
)
where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo pip is not installed. Please install Python from https://www.python.org/ and try again.
    pause
    exit /b 1
)
echo Python and pip are installed.

echo Installing Node.js dependencies...
npm install
if %errorlevel% neq 0 (
    echo Failed to install Node.js dependencies.
    pause
    exit /b 1
)

echo Building TypeScript project...
npm run build
if %errorlevel% neq 0 (
    echo Failed to build TypeScript project.
    pause
    exit /b 1
)

echo Setting up Python virtual environment and installing dependencies for dashboard...
cd dashboard
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create Python virtual environment.
    pause
    exit /b 1
)
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate Python virtual environment.
    pause
    exit /b 1
)
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)
deactivate
cd ..

echo.
echo Installation complete!
echo.
echo To run the Ollama Flow server (Node.js):
echo   cd /d "%~dp0"
echo   npm start
echo.
echo To run the Dashboard (Python):
echo   cd /d "%~dp0dashboard"
echo   call venv\Scripts\activate
echo   python app.py
echo   deactivate
echo.
echo Make sure Ollama is running in the background for the server to function correctly.
pause