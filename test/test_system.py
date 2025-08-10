#!/usr/bin/env python3
"""
Test Suite für das Ollama Flow Multi-Role System
===============================================
"""

import asyncio
import json
import os
from ollama_flow_coordinator import WorkflowCoordinator

async def test_basic_workflow():
    """Test eines einfachen Workflows."""
    print("🧪 Test 1: Basic Workflow")
    print("-" * 40)
    
    coordinator = WorkflowCoordinator("test_ollama_flow.db")
    
    # Test-Anfrage
    test_query = "Künstliche Intelligenz in der Medizin"
    
    try:
        result = await coordinator.process_workflow(test_query)
        
        # Validiere Ergebnisse
        assert result["status"] in ["completed", "failed"], "Invalid workflow status"
        assert result["original_query"] == test_query, "Query mismatch"
        
        if result["status"] == "completed":
            assert result["research_result"] is not None, "Missing research result"
            assert result["fact_check_result"] is not None, "Missing fact-check result"
            assert result["analysis_result"] is not None, "Missing analysis result"
            assert 0 <= result["final_confidence_score"] <= 1, "Invalid confidence score"
        
        print(f"✅ Test 1 erfolgreich - Status: {result['status']}")
        
        if result["status"] == "completed":
            print(f"   Confidence Score: {result['final_confidence_score']:.2f}")
            print(f"   Research Tasks: {len(result['research_result'])}")
            print(f"   Fact-Check Tasks: {len(result['fact_check_result'])}")
            print(f"   Analysis Tasks: {len(result['analysis_result'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 1 fehlgeschlagen: {str(e)}")
        return False

def test_drone_initialization():
    """Test der Drohnen-Initialisierung."""
    print("\n🧪 Test 2: Drone Initialization")
    print("-" * 40)
    
    try:
        coordinator = WorkflowCoordinator("test_ollama_flow.db")
        
        # Validiere Drohnen-Flotten
        assert len(coordinator.research_drones) == 3, "Wrong number of research drones"
        assert len(coordinator.fact_check_drones) == 2, "Wrong number of fact-check drones"
        assert len(coordinator.analyst_drones) == 2, "Wrong number of analyst drones"
        
        # Teste Status-Abfrage
        status = coordinator.get_drone_status()
        assert "research_drones" in status, "Missing research drones in status"
        assert "fact_check_drones" in status, "Missing fact-check drones in status"
        assert "analyst_drones" in status, "Missing analyst drones in status"
        
        print("✅ Test 2 erfolgreich")
        print(f"   Recherche-Drohnen: {len(status['research_drones'])}")
        print(f"   Fact-Check-Drohnen: {len(status['fact_check_drones'])}")
        print(f"   Analyse-Drohnen: {len(status['analyst_drones'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 2 fehlgeschlagen: {str(e)}")
        return False

def test_database_operations():
    """Test der Datenbank-Operationen."""
    print("\n🧪 Test 3: Database Operations")
    print("-" * 40)
    
    try:
        coordinator = WorkflowCoordinator("test_ollama_flow.db")
        
        # Test Drohnen-Speicherung
        test_drone = coordinator.research_drones[0].drone
        coordinator.db_manager.save_drone(test_drone)
        
        # Test Workflow-Ergebnis-Speicherung
        test_workflow = {
            "id": "test_workflow_123",
            "original_query": "Test Query",
            "research_result": [{"test": "data"}],
            "fact_check_result": [{"validation": True}],
            "analysis_result": [{"analysis": "complete"}],
            "final_confidence_score": 0.85,
            "created_at": "2024-01-01T12:00:00"
        }
        
        coordinator.save_workflow_result(test_workflow)
        
        print("✅ Test 3 erfolgreich")
        print("   Datenbank-Operationen funktionieren korrekt")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 3 fehlgeschlagen: {str(e)}")
        return False

async def run_full_test_suite():
    """Führt die komplette Test-Suite aus."""
    print("🚀 Ollama Flow Multi-Role System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Drone Initialization", test_drone_initialization()),
        ("Database Operations", test_database_operations()),
        ("Basic Workflow", await test_basic_workflow())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        if result:
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST ERGEBNISSE: {passed}/{total} Tests erfolgreich")
    
    if passed == total:
        print("🎉 Alle Tests erfolgreich!")
    else:
        print(f"⚠️  {total - passed} Tests fehlgeschlagen")
    
    # Cleanup
    try:
        if os.path.exists("test_ollama_flow.db"):
            os.remove("test_ollama_flow.db")
            print("🧹 Test-Datenbank bereinigt")
    except:
        pass
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(run_full_test_suite())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests unterbrochen.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler in Test Suite: {str(e)}")
        exit(1)