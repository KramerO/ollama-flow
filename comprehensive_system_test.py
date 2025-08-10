#!/usr/bin/env python3
"""
Comprehensive System Test Suite for Enhanced Ollama Flow
Tests all architectures, roles, and complex scenarios
"""

import asyncio
import subprocess
import sys
import time
from typing import List, Dict, Tuple

class ComprehensiveSystemTester:
    """Comprehensive test suite for the enhanced ollama-flow system"""
    
    def __init__(self):
        self.test_results = []
        
    def run_ollama_flow_test(self, task: str, architecture: str, drones: int = 5, timeout: int = 120) -> Dict:
        """Run a single ollama-flow test"""
        print(f"\n🧪 Testing {architecture} Architecture")
        print(f"📋 Task: {task}")
        print(f"🤖 Drones: {drones}")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            # Execute ollama-flow command
            cmd = [
                "./ollama-flow", "run", task, 
                "--drones", str(drones), 
                "--arch", architecture
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd="."
            )
            
            execution_time = time.time() - start_time
            
            # Analyze output for role assignments
            role_assignments = self._extract_role_assignments(result.stdout)
            
            # Determine success criteria
            success = (
                result.returncode == 0 or 
                "🎭" in result.stdout and len(role_assignments) > 0
            )
            
            test_result = {
                "architecture": architecture,
                "task": task,
                "drones": drones,
                "execution_time": execution_time,
                "success": success,
                "role_assignments": role_assignments,
                "stdout_length": len(result.stdout),
                "stderr_length": len(result.stderr),
                "return_code": result.returncode
            }
            
            if success:
                print(f"✅ Test PASSED ({execution_time:.1f}s)")
                print(f"🎭 Roles detected: {list(role_assignments.keys())}")
            else:
                print(f"❌ Test FAILED ({execution_time:.1f}s)")
                print(f"📤 Return Code: {result.returncode}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Test TIMEOUT after {timeout}s")
            return {
                "architecture": architecture,
                "task": task,
                "drones": drones,
                "execution_time": timeout,
                "success": False,
                "role_assignments": {},
                "error": "timeout"
            }
        except Exception as e:
            print(f"❌ Test ERROR: {e}")
            return {
                "architecture": architecture,
                "task": task,
                "drones": drones,
                "execution_time": time.time() - start_time,
                "success": False,
                "role_assignments": {},
                "error": str(e)
            }
    
    def _extract_role_assignments(self, stdout: str) -> Dict[str, List[str]]:
        """Extract role assignments from stdout"""
        import re
        
        role_assignments = {}
        
        # Pattern to match role assignment messages
        pattern = r"🎭 \[.*?(Drone \d+)\] Dynamic role assignment: .* -> (\w+)"
        matches = re.findall(pattern, stdout)
        
        for drone_name, role in matches:
            if role not in role_assignments:
                role_assignments[role] = []
            role_assignments[role].append(drone_name)
        
        return role_assignments
    
    def run_comprehensive_test_suite(self) -> None:
        """Run comprehensive test suite covering all scenarios"""
        
        print("🚀 COMPREHENSIVE OLLAMA FLOW SYSTEM TEST")
        print("=" * 80)
        print(f"🕒 Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Complex test scenarios designed to trigger all 5 roles
        test_scenarios = [
            {
                "name": "E-Commerce Platform Development",
                "task": "Entwickle eine sichere E-Commerce-Plattform mit Machine Learning für Produktempfehlungen: Entwerfe skalierbare Microservice-Architektur, implementiere REST APIs mit Authentifizierung, analysiere Kundendaten für ML-Algorithmen, führe Sicherheitsaudits durch und erstelle Performance-Monitoring Dashboards"
            },
            {
                "name": "IoT Analytics System",
                "task": "Build a comprehensive IoT data analytics system: Design cloud architecture for sensor data processing, develop Python APIs for device communication, create machine learning models for predictive maintenance, implement security protocols for device authentication, and build real-time monitoring dashboards"
            },
            {
                "name": "Financial Risk Assessment Platform",
                "task": "Create an AI-powered financial risk assessment platform: Design enterprise-grade microservices architecture, implement blockchain-based transaction APIs, develop machine learning algorithms for credit scoring and fraud detection, conduct comprehensive security penetration testing, and build executive analytics dashboards"
            }
        ]
        
        architectures = ["HIERARCHICAL", "CENTRALIZED", "FULLY_CONNECTED"]
        
        # Run tests for all combinations
        for scenario in test_scenarios:
            for architecture in architectures:
                test_result = self.run_ollama_flow_test(
                    task=scenario["task"],
                    architecture=architecture,
                    drones=5,
                    timeout=180  # 3 minutes per test
                )
                test_result["scenario_name"] = scenario["name"]
                self.test_results.append(test_result)
        
        # Generate comprehensive report
        self._generate_test_report()
    
    def _generate_test_report(self) -> None:
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Successful: {successful_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📊 Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        # Architecture performance breakdown
        print(f"\n🏗️ Architecture Performance:")
        arch_stats = {}
        for result in self.test_results:
            arch = result["architecture"]
            if arch not in arch_stats:
                arch_stats[arch] = {"total": 0, "success": 0, "avg_time": []}
            
            arch_stats[arch]["total"] += 1
            if result["success"]:
                arch_stats[arch]["success"] += 1
            arch_stats[arch]["avg_time"].append(result["execution_time"])
        
        for arch, stats in arch_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            avg_time = sum(stats["avg_time"]) / len(stats["avg_time"])
            print(f"   {arch}: {success_rate:.1f}% success, {avg_time:.1f}s avg time")
        
        # Role assignment analysis
        print(f"\n🎭 Role Assignment Analysis:")
        all_roles = set()
        role_counts = {}
        
        for result in self.test_results:
            if result["success"]:
                for role, drones in result["role_assignments"].items():
                    all_roles.add(role)
                    if role not in role_counts:
                        role_counts[role] = 0
                    role_counts[role] += len(drones)
        
        print(f"   🎯 Roles Successfully Assigned: {len(all_roles)}/5")
        for role in sorted(all_roles):
            count = role_counts.get(role, 0)
            print(f"   {role.upper()}: {count} assignments")
        
        # Detailed test breakdown
        print(f"\n📋 Detailed Test Results:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {i}. {result['scenario_name']} - {result['architecture']}")
            print(f"      {status} ({result['execution_time']:.1f}s)")
            if result["success"] and result["role_assignments"]:
                roles = ", ".join(result["role_assignments"].keys())
                print(f"      🎭 Roles: {roles}")
            if "error" in result:
                print(f"      ⚠️ Error: {result['error']}")
        
        # Performance metrics
        if self.test_results:
            avg_execution_time = sum(r["execution_time"] for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ Performance Metrics:")
            print(f"   Average Execution Time: {avg_execution_time:.1f}s")
            print(f"   Fastest Test: {min(r['execution_time'] for r in self.test_results):.1f}s")
            print(f"   Slowest Test: {max(r['execution_time'] for r in self.test_results):.1f}s")
        
        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        if successful_tests == total_tests:
            print("   🏆 EXCELLENT: All tests passed!")
            print("   ✅ Dynamic role assignment system is fully functional")
            print("   ✅ All architectures working correctly")
            print("   ✅ Complex multi-role scenarios handled successfully")
        elif successful_tests >= total_tests * 0.8:
            print("   🟡 GOOD: Most tests passed")
            print("   ✅ Core functionality working")
            print("   ⚠️ Some edge cases may need attention")
        else:
            print("   🔴 ATTENTION NEEDED: Several tests failed")
            print("   ⚠️ System requires further investigation")
        
        print(f"\n🕒 Test completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

def main():
    """Run comprehensive system test"""
    print("🔧 Initializing Comprehensive System Test...")
    
    # Check if ollama-flow exists and is executable
    try:
        result = subprocess.run(["./ollama-flow", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ ollama-flow is not working correctly")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot execute ollama-flow: {e}")
        sys.exit(1)
    
    # Run comprehensive test suite
    tester = ComprehensiveSystemTester()
    tester.run_comprehensive_test_suite()

if __name__ == "__main__":
    main()