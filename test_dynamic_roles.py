#!/usr/bin/env python3
"""
Test script for dynamic role assignment system
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.drone_agent import DroneAgent, DroneRole

def test_role_assignment():
    """Test the dynamic role assignment for different task types"""
    
    # Create a drone with no initial role
    drone = DroneAgent("test-drone-1", "Test Drone", "llama3:latest", "/tmp/test_roles")
    
    print("🧪 Testing Dynamic Role Assignment System")
    print("=" * 50)
    
    # Test different types of tasks
    test_cases = [
        ("create a Python calculator application", "DEVELOPER"),
        ("analyze sales data and create visualization", "ANALYST"),  
        ("build machine learning model for predictions", "DATASCIENTIST"),
        ("design microservices architecture", "IT_ARCHITECT"),
        ("conduct security audit and vulnerability assessment", "SECURITY_SPECIALIST"),
        ("develop web scraper for competitor analysis", "DEVELOPER"),
        ("analyze security risks in the system", "SECURITY_SPECIALIST"),
        ("create dashboard with charts and metrics", "ANALYST"),
        ("train neural network on image data", "DATASCIENTIST"),
        ("design database schema and API endpoints", "IT_ARCHITECT")
    ]
    
    results = []
    
    for task, expected_role in test_cases:
        print(f"\n📋 Task: {task}")
        
        # Reset drone role to None for each test
        drone.role = None
        
        # Test role assignment
        assigned_role = drone.assign_dynamic_role(task)
        
        success = assigned_role.value.upper() == expected_role
        status = "✅ PASS" if success else "❌ FAIL"
        
        print(f"   Expected: {expected_role}")
        print(f"   Assigned: {assigned_role.value.upper()}")
        print(f"   Result: {status}")
        
        results.append({
            'task': task,
            'expected': expected_role,
            'assigned': assigned_role.value.upper(),
            'success': success
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    accuracy = (passed / total) * 100
    
    print(f"✅ Passed: {passed}/{total} ({accuracy:.1f}%)")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Dynamic role assignment works perfectly!")
    else:
        print("\n⚠️  Some tests failed. Review the role assignment logic.")
        
        # Show failed tests
        failed = [r for r in results if not r['success']]
        for fail in failed:
            print(f"   ❌ '{fail['task']}' -> Expected: {fail['expected']}, Got: {fail['assigned']}")

if __name__ == "__main__":
    test_role_assignment()