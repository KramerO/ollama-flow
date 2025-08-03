#!/usr/bin/env python3
"""
Test script for the new command-line based AI system
"""
import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.orchestrator import Orchestrator
from db_manager import MessageDBManager

async def test_translation():
    """Test German to English translation"""
    print("🌐 Testing German to English translation...")
    
    db_manager = MessageDBManager("test.db")
    # db_manager.initialize_db()  # Check if method exists
    orchestrator = Orchestrator(db_manager, model="codellama:7b")
    
    # Test German detection
    german_texts = [
        "erstelle mir eine hello world flask app und speichere sie als app.py",
        "programmiere eine web scraper anwendung",
        "baue eine REST API mit authentication"
    ]
    
    english_texts = [
        "create a hello world flask app and save it as app.py",
        "this is already english text",
        "build something simple"
    ]
    
    print("\n--- German Detection Tests ---")
    for text in german_texts:
        is_german = orchestrator._detect_german_language(text)
        print(f"'{text}' -> German: {is_german}")
    
    print("\n--- English Detection Tests ---")
    for text in english_texts:
        is_german = orchestrator._detect_german_language(text)
        print(f"'{text}' -> German: {is_german}")
    
    print("\n--- Translation Tests ---")
    for text in german_texts:
        if orchestrator._detect_german_language(text):
            translated = await orchestrator._translate_german_to_english(text)
            print(f"DE: {text}")
            print(f"EN: {translated}")
            print()
    
    # Cleanup
    os.unlink("test.db")

async def test_worker_command_parsing():
    """Test worker agent command parsing"""
    print("\n💻 Testing Worker Agent Command Parsing...")
    
    from agents.worker_agent import WorkerAgent
    
    worker = WorkerAgent("test-worker", "Test Worker", project_folder_path="/tmp/ollama_1")
    
    # Test command parsing
    test_responses = [
        """
To create a Flask app, run these commands:

```bash
pip install flask
```

```bash
cat > app.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)
EOF
```

Execute: `python app.py`
        """,
        """
Here's what you need to do:

Command: `touch newfile.txt`
Run: `echo "Hello World" > newfile.txt`
Execute: `ls -la`
        """
    ]
    
    for i, response in enumerate(test_responses):
        print(f"\n--- Test Response {i+1} ---")
        print("AI Response:")
        print(response)
        print("\nExtracted Commands:")
        commands_output = await worker._parse_and_execute_commands(response)
        print(commands_output)

if __name__ == "__main__":
    print("🔬 Testing New Command-line Based AI System")
    print("=" * 50)
    
    try:
        asyncio.run(test_translation())
        asyncio.run(test_worker_command_parsing())
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)