#!/usr/bin/env python3
"""
Quick test script to verify Flask app creation functionality
"""
import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents.worker_agent import WorkerAgent
from agents.base_agent import AgentMessage

async def test_flask_creation():
    """Test Flask app creation directly"""
    print("🧪 Testing Flask app creation...")
    
    # Set up test directory
    test_dir = "/tmp/ollama_1"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create worker agent
    worker = WorkerAgent("test-worker", "Test Worker", project_folder_path=test_dir)
    
    # Create test message
    message = AgentMessage(
        sender_id="test",
        receiver_id="test-worker",
        message_type="task",
        content="erstelle mir eine hello world flask app und speichere sie als app.py",
        request_id="test-123"
    )
    
    # Mock the send_message method to capture response
    responses = []
    async def mock_send_message(receiver_id, message_type, content, request_id):
        responses.append({
            'receiver_id': receiver_id,
            'message_type': message_type,
            'content': content,
            'request_id': request_id
        })
        print(f"📤 Response: {message_type}")
        print(f"📝 Content preview: {content[:200]}...")
    
    worker.send_message = mock_send_message
    
    # Process the message
    print("🔄 Processing message...")
    await worker.receive_message(message)
    
    # Check results
    app_py_path = os.path.join(test_dir, "app.py")
    
    if os.path.exists(app_py_path):
        print("✅ app.py created successfully!")
        with open(app_py_path, 'r') as f:
            content = f.read()
        print(f"📄 File content ({len(content)} chars):")
        print("=" * 50)
        print(content)
        print("=" * 50)
        
        # Verify Flask content
        if "from flask import Flask" in content and "@app.route" in content:
            print("✅ Flask app content is valid!")
            return True
        else:
            print("❌ Flask app content is invalid!")
            return False
    else:
        print("❌ app.py was not created!")
        print(f"Directory contents: {os.listdir(test_dir)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_flask_creation())
    sys.exit(0 if success else 1)