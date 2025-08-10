#!/usr/bin/env python3
"""
Real-time Role Assignment Monitor
Shows live updates of drone roles during execution
"""

import time
import os
import sys
from pathlib import Path
from typing import Dict, List
import json

class RoleMonitor:
    def __init__(self):
        self.drone_roles: Dict[str, str] = {}
        self.task_assignments: Dict[str, str] = {}
        self.start_time = time.time()
        
    def update_drone_role(self, drone_id: str, drone_name: str, old_role: str, new_role: str, task: str):
        """Update drone role assignment"""
        self.drone_roles[drone_id] = {
            'name': drone_name,
            'role': new_role,
            'previous_role': old_role,
            'task': task,
            'timestamp': time.time(),
            'duration': time.time() - self.start_time
        }
        self.display_status()
    
    def display_status(self):
        """Display current role assignments"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🚀 OLLAMA FLOW - DYNAMIC ROLE MONITOR")
        print("=" * 60)
        print(f"⏱️  Runtime: {time.time() - self.start_time:.1f}s")
        print(f"🤖 Active Drones: {len(self.drone_roles)}")
        print()
        
        if not self.drone_roles:
            print("⏳ Waiting for drone role assignments...")
            return
            
        print("🎭 CURRENT ROLE ASSIGNMENTS:")
        print("-" * 60)
        
        role_colors = {
            'developer': '💻',
            'analyst': '📊', 
            'datascientist': '🧠',
            'it_architect': '🏗️',
            'security_specialist': '🔒'
        }
        
        for drone_id, info in self.drone_roles.items():
            role_icon = role_colors.get(info['role'].lower(), '🤖')
            duration = f"{info['duration']:.1f}s"
            
            print(f"{role_icon} {info['name']} - {info['role'].upper()}")
            print(f"   📝 Task: {info['task'][:50]}...")
            print(f"   🔄 Changed from: {info['previous_role']} → {info['role']}")
            print(f"   ⏱️  Duration: {duration}")
            print()
    
    def save_report(self, output_file: str = "role_assignments.json"):
        """Save role assignment report"""
        report = {
            'total_runtime': time.time() - self.start_time,
            'total_drones': len(self.drone_roles),
            'assignments': self.drone_roles,
            'generated_at': time.ctime()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Role assignment report saved to: {output_file}")

# Global monitor instance
monitor = RoleMonitor()

def update_role(drone_id: str, drone_name: str, old_role: str, new_role: str, task: str):
    """Update role assignment in monitor"""
    monitor.update_drone_role(drone_id, drone_name, old_role, new_role, task)

def show_final_report():
    """Show final role assignment report"""
    monitor.save_report()
    print("\n🎉 Role Assignment Summary:")
    print("=" * 40)
    
    role_counts = {}
    for info in monitor.drone_roles.values():
        role = info['role']
        role_counts[role] = role_counts.get(role, 0) + 1
    
    for role, count in role_counts.items():
        print(f"  {role.upper()}: {count} drone(s)")

if __name__ == "__main__":
    # Interactive monitoring mode
    try:
        monitor.display_status()
        
        # Keep monitoring until interrupted
        while True:
            time.sleep(1)
            # In real usage, this would be updated by the drone agents
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
        show_final_report()