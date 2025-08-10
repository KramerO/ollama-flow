#!/usr/bin/env python3
"""
Test script to demonstrate role assignment visibility
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.drone_agent import DroneAgent, DroneRole

def demo_role_assignments():
    """Demonstrate enhanced role assignment visibility"""
    
    print("🚀 OLLAMA FLOW - DYNAMIC ROLE ASSIGNMENT DEMO")
    print("=" * 60)
    print()
    
    # Create drones with no initial roles
    drones = []
    for i in range(5):
        drone = DroneAgent(f"drone-agent-{i+1}", f"Drone {i+1}", "llama3:latest", "/tmp/test")
        drones.append(drone)
    
    # Test different task types  
    test_tasks = [
        "create a Python web application with user authentication",
        "analyze sales data and create visualization dashboard", 
        "conduct security audit and vulnerability assessment",
        "design microservices architecture for scalable system",
        "build machine learning model for recommendation engine"
    ]
    
    print("🎭 DYNAMIC ROLE ASSIGNMENTS:")
    print("-" * 60)
    
    for i, (drone, task) in enumerate(zip(drones, test_tasks)):
        print(f"\n📋 Task {i+1}: {task}")
        print(f"🤖 Assigned to: {drone.name}")
        
        # This will trigger the enhanced role assignment display
        assigned_role = drone.assign_dynamic_role(task)
        
        print("   " + "="*50)
    
    print("\n🎉 Role assignment demo complete!")
    print()
    print("💡 During real execution, you'll see these role assignments")
    print("   as each drone receives its task and analyzes it.")

if __name__ == "__main__":
    demo_role_assignments()