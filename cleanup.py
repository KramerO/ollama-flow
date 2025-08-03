#!/usr/bin/env python3
"""
Convenience script to cleanup Ollama Flow database and temporary files
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_main import EnhancedOllamaFlow

async def main():
    """Cleanup database and files"""
    print("🧹 Cleaning up Ollama Flow database and files...")
    
    try:
        framework = EnhancedOllamaFlow()
        success = await framework.cleanup_database_and_files()
        
        if success:
            print("✅ Cleanup completed successfully")
            return 0
        else:
            print("❌ Cleanup failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)