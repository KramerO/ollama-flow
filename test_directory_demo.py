#!/usr/bin/env python3
"""
Demo: Current Directory Project Folder System
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def demonstrate_current_directory():
    """Demonstrate how the current directory system works"""
    print("🔍 Enhanced Project Folder System - Current Directory Demo")
    print("=" * 65)
    
    print(f"\n📂 Current working directory: {os.getcwd()}")
    
    # Show the CLI improvements
    print("\n🎯 New CLI Behavior:")
    print("━" * 40)
    print("1. ✅ If you run: ollama-flow run 'task'")
    print(f"   → Uses current directory: {os.getcwd()}")
    print("\n2. ✅ If you run: ollama-flow run 'task' --project-folder /custom/path")
    print("   → Uses specified path: /custom/path")
    print("\n3. ✅ If you run from any directory:")
    print("   → Always uses that directory as project folder")
    
    print("\n🛠️ Enhanced Features:")
    print("━" * 40)
    print("✅ Automatic directory detection")
    print("✅ Directory creation if it doesn't exist")
    print("✅ Absolute path resolution") 
    print("✅ Path validation and security checks")
    print("✅ Clear feedback about which directory is being used")
    
    print("\n📋 Usage Examples:")
    print("━" * 40)
    print("# Work in current directory")
    print("$ cd /my/project")
    print("$ ollama-flow run 'create a Flask app'")
    print("→ Files created in /my/project/")
    print()
    print("# Work in specific directory")
    print("$ ollama-flow run 'create a script' --project-folder /tmp/test")
    print("→ Files created in /tmp/test/")
    print()
    print("# Work from anywhere")
    print("$ cd /home/user")
    print("$ ollama-flow run 'build something'")
    print("→ Files created in /home/user/")
    
    print("\n🎉 Benefits:")
    print("━" * 40)
    print("• No more manual path specification needed")
    print("• Works intuitively from any directory")
    print("• Safe directory handling with validation")
    print("• Clear visibility into where files are created")
    print("• Flexible - can still specify custom paths when needed")
    
    print(f"\n✨ Ready to use! Current session will use: {os.getcwd()}")

if __name__ == "__main__":
    demonstrate_current_directory()