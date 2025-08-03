#!/usr/bin/env python3
"""
Convenience script to stop all running Ollama Flow agents
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_main import EnhancedOllamaFlow

async def main():
    """Stop all agents"""
    print("🛑 Stopping all Ollama Flow agents...")
    
    try:
        framework = EnhancedOllamaFlow()
        success = await framework.stop_all_agents()
        
        if success:
            print("✅ All agents stopped successfully")
            return 0
        else:
            print("❌ Failed to stop some agents")
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