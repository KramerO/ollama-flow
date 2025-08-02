#!/bin/bash

echo "Checking for Node.js and npm..."
if ! command -v node &> /dev/null
then
    echo "Node.js is not installed. Please install Node.js from https://nodejs.org/ and try again."
    exit 1
fi
if ! command -v npm &> /dev/null
then
    echo "npm is not installed. Please install Node.js from https://nodejs.org/ and try again."
    exit 1
fi
echo "Node.js and npm are installed."

echo "Checking for Python and pip..."
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3 from https://www.python.org/ and try again."
    exit 1
fi
if ! command -v pip3 &> /dev/null
then
    echo "pip 3 is not installed. Please install Python 3 from https://www.python.org/ and try again."
    exit 1
fi
echo "Python and pip are installed."

echo "Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Failed to install Node.js dependencies."
    exit 1
fi

echo "Building TypeScript project..."
npm run build
if [ $? -ne 0 ]; then
    echo "Failed to build TypeScript project."
    exit 1
fi

echo "Setting up Python virtual environment and installing dependencies for dashboard..."
cd dashboard
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Failed to create Python virtual environment."
    exit 1
fi
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate Python virtual environment."
    exit 1
fi
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install Python dependencies."
    exit 1
fi
deactivate
cd ..

echo ""
echo "Installation complete!"
echo ""
echo "To run the Ollama Flow server (Node.js):"
echo "  cd "$(dirname "$0")""
echo "  npm start"
echo ""
echo "To run the Dashboard (Python):"
echo "  cd "$(dirname "$0")"/dashboard"
echo "  source venv/bin/activate"
echo "  python app.py"
echo "  deactivate"
echo ""
echo "Make sure Ollama is running in the background for the server to function correctly."
