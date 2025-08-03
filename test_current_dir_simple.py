#!/usr/bin/env python3
"""
Test current directory functionality
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_main import EnhancedOllamaFlow

def test_current_directory_detection():
    """Test current directory detection"""
    print("🔍 Testing Current Directory Detection")
    print("=" * 40)
    
    # Test resolve project folder function
    framework = EnhancedOllamaFlow()
    
    # Test with None (should use current directory)
    print("\n--- Test 1: No project folder specified ---")
    current_dir = framework._resolve_project_folder(None)
    expected_dir = os.path.abspath(os.getcwd())
    print(f"Expected: {expected_dir}")
    print(f"Got: {current_dir}")
    print(f"Match: {current_dir == expected_dir}")
    
    # Test with relative path
    print("\n--- Test 2: Relative path ---")
    rel_dir = framework._resolve_project_folder("./test_folder")
    expected_rel = os.path.abspath("./test_folder")
    print(f"Expected: {expected_rel}")
    print(f"Got: {rel_dir}")
    print(f"Exists: {os.path.exists(rel_dir)}")
    
    # Test with absolute path
    print("\n--- Test 3: Absolute path ---")
    abs_path = "/tmp/ollama_1"
    abs_dir = framework._resolve_project_folder(abs_path)
    print(f"Expected: {abs_path}")
    print(f"Got: {abs_dir}")
    print(f"Exists: {os.path.exists(abs_dir)}")
    
    # Cleanup test folder
    if os.path.exists("./test_folder"):
        os.rmdir("./test_folder")
    
    print("\n✅ Current directory detection tests completed!")

if __name__ == "__main__":
    test_current_directory_detection()