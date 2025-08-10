#!/usr/bin/env python3
"""
Test script to verify the role assignment fix is working
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.drone_agent import DroneAgent, DroneRole

def test_role_assignment_fix():
    """Test that role assignment works without errors"""
    
    print("🧪 Testing Dynamic Role Assignment Fix")
    print("=" * 50)
    
    test_cases = [
        ("create a simple python hello world script", DroneRole.DEVELOPER),
        ("analyze sales data and create visualization", DroneRole.ANALYST),
        ("create machine learning model for image recognition", DroneRole.DATA_SCIENTIST),
        ("design microservices architecture", DroneRole.IT_ARCHITECT),
        ("conduct security audit and vulnerability scan", DroneRole.SECURITY_SPECIALIST)
    ]
    
    for i, (task, expected_role) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {task}")
        print("-" * 60)
        
        # Create drone with no initial role
        drone = DroneAgent(f"test-drone-{i}", f"Test Drone {i}", "llama3:latest", "/tmp/test")
        
        # Verify initial state
        assert drone.role is None, f"Expected no initial role, got {drone.role}"
        
        # Test role assignment
        try:
            assigned_role = drone.assign_dynamic_role(task)
            
            # Verify role assignment worked
            assert drone.role is not None, "Role should not be None after assignment"
            assert drone.role == expected_role, f"Expected {expected_role}, got {drone.role}"
            assert assigned_role == expected_role, f"Return value mismatch: expected {expected_role}, got {assigned_role}"
            
            # Verify capabilities are set
            assert len(drone.capabilities) > 0, "Capabilities should be set after role assignment"
            
            print(f"✅ Role assignment successful: {assigned_role.value}")
            print(f"✅ Capabilities: {', '.join(drone.capabilities[:3])}...")
            
        except Exception as e:
            print(f"❌ Role assignment failed: {e}")
            return False
    
    print(f"\n🎉 All role assignment tests passed!")
    return True

def test_none_role_handling():
    """Test that methods handle None role gracefully"""
    
    print(f"\n🧪 Testing None Role Handling")
    print("=" * 50)
    
    # Create drone with no role
    drone = DroneAgent("test-none", "None Test", "llama3:latest", "/tmp/test")
    
    try:
        # Test get_role_info with None role
        info = drone.get_role_info()
        assert info['role'] == 'dynamic', f"Expected 'dynamic', got {info['role']}"
        print("✅ get_role_info handles None role correctly")
        
        # Test role display methods
        role_name = drone.role.value if drone.role else "dynamic"
        print(f"✅ Role name handling: {role_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ None role handling failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DYNAMIC ROLE ASSIGNMENT FIX VERIFICATION")
    print("=" * 60)
    
    success1 = test_role_assignment_fix()
    success2 = test_none_role_handling()
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED - Role assignment fix is working!")
        print("✅ Dynamic role assignment is now functional")
        print("✅ NoneType errors have been resolved")
        print("✅ Role assignment visibility is restored")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED - Further fixes needed")
        sys.exit(1)