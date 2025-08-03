#!/usr/bin/env python3
"""
Test script for CLI Dashboard
Tests dashboard initialization without full curses interface
"""

import asyncio
import sys
import os

async def test_cli_dashboard():
    """Test CLI dashboard initialization"""
    print("🧪 Testing CLI Dashboard...")
    
    try:
        from cli_dashboard_enhanced import EnhancedCLIDashboard
        print("✅ Successfully imported EnhancedCLIDashboard")
        
        # Test initialization
        dashboard = EnhancedCLIDashboard()
        print("✅ Dashboard instance created")
        
        # Test async initialization
        await dashboard.initialize()
        print("✅ Dashboard initialized successfully")
        
        # Test data loading
        print(f"📊 System metrics: CPU {dashboard.system_metrics.cpu_percent:.1f}%, Memory {dashboard.system_metrics.memory_percent:.1f}%")
        print(f"🔧 Configuration: {len(dashboard.config)} items loaded")
        print(f"📋 Tasks: {len(dashboard.tasks)} active tasks")
        print(f"🤖 Agents: {len(dashboard.agents)} agents configured")
        
        print("✅ All tests passed - CLI Dashboard is ready!")
        
        # Cleanup
        dashboard.cleanup()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cli_dashboard())
    sys.exit(0 if success else 1)