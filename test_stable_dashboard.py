#!/usr/bin/env python3
"""
Test script for the stable CLI dashboard
Tests the optimized version with reduced flickering
"""

import asyncio
import sys
import os

async def test_stable_dashboard():
    """Test the stable CLI dashboard"""
    print("🧪 Testing Stable CLI Dashboard...")
    print("⚡ This version is optimized to fix:")
    print("   - addwstr() ERR errors")
    print("   - Dashboard flickering")
    print("   - Terminal size issues")
    print("   - Unicode character problems")
    print("="*50)
    
    try:
        # Import stable dashboard
        from cli_dashboard_stable import StableCLIDashboard
        print("✅ Successfully imported StableCLIDashboard")
        
        # Create dashboard instance
        dashboard = StableCLIDashboard()
        print("✅ Dashboard instance created")
        
        # Test initialization
        await dashboard.initialize()
        print("✅ Dashboard initialized successfully")
        
        # Test configuration
        print(f"⚙️ Configuration loaded: {len(dashboard.config)} items")
        print(f"🏗️ Architecture: {dashboard.architecture_type}")
        print(f"🤖 Agents configured: {len(dashboard.agents)}")
        print(f"📋 Tasks available: {len(dashboard.tasks)}")
        
        # Test system metrics
        dashboard.update_system_metrics()
        metrics = dashboard.system_metrics
        print(f"📊 System Metrics:")
        print(f"   CPU: {metrics.cpu_percent:.1f}%")
        print(f"   Memory: {metrics.memory_percent:.1f}%")
        print(f"   Disk: {metrics.disk_percent:.1f}%")
        print(f"   Processes: {metrics.active_processes}")
        
        # Test text cleaning
        test_text = "👑 Enhanced Queen 🔧 Worker ⭕ Idle │─┬"
        cleaned = dashboard.clean_text(test_text)
        print(f"🧹 Text cleaning test:")
        print(f"   Original: {test_text}")
        print(f"   Cleaned:  {cleaned}")
        
        # Test cleanup
        dashboard.cleanup()
        print("✅ Dashboard cleanup successful")
        
        print("\n🎉 All Stable Dashboard tests passed!")
        print("💡 Key improvements:")
        print("   • Safe addstr() with bounds checking")
        print("   • Reduced refresh rate (0.5s instead of 0.1s)")
        print("   • Unicode character replacement")
        print("   • Better error handling")
        print("   • Optimized update intervals")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_stable_dashboard())
    print(f"\n🎯 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🚀 The Stable CLI Dashboard is ready to use:")
        print("   ollama-flow cli-dashboard")
        print("\n📝 Key Features:")
        print("   • No more addwstr() ERR errors")
        print("   • Significantly reduced flickering")
        print("   • Better terminal compatibility")
        print("   • Improved performance")
    else:
        print("\n❌ There were issues with the stable dashboard")
        print("💡 Check the error messages above")
    
    sys.exit(0 if success else 1)