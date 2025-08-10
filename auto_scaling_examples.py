#!/usr/bin/env python3
"""
Auto-Scaling Examples für Ollama Flow
Demonstriert verschiedene Anwendungsfälle und Konfigurationen
"""

import asyncio
import json
from enhanced_framework import EnhancedOllamaFlow
from auto_scaling_engine import ScalingStrategy
from dynamic_agent_manager import AgentLifecycleState

async def basic_auto_scaling_example():
    """Basis-Beispiel für Auto-Scaling"""
    print("🚀 Basis Auto-Scaling Beispiel")
    
    # System mit Auto-Scaling erstellen
    system = EnhancedOllamaFlow(
        auto_scaling=True,
        scaling_strategy="GPU_MEMORY_BASED",
        model="phi3:mini"
    )
    
    # System initialisieren
    await system.initialize()
    
    # Task verarbeiten
    result = await system.process_task("Create a simple Python calculator")
    print(f"✅ Task Result: {result[:100]}...")
    
    # Status anzeigen
    if system.auto_scaling_engine:
        status = system.auto_scaling_engine.get_scaling_status()
        print(f"📊 Active Agents: {status['active_agents']}")
        print(f"📊 Strategy: {status['strategy']}")

async def hybrid_scaling_example():
    """Hybrid-Scaling mit GPU und Workload-Metriken"""
    print("\n🔄 Hybrid Auto-Scaling Beispiel")
    
    system = EnhancedOllamaFlow(
        auto_scaling=True,
        scaling_strategy="HYBRID",
        model="phi3:mini"
    )
    
    await system.initialize()
    
    # Mehrere Tasks parallel verarbeiten (simuliert hohe Last)
    tasks = [
        "Create a REST API in Python",
        "Write a data analysis script", 
        "Create a web scraper",
        "Build a machine learning model"
    ]
    
    # Tasks parallel senden
    results = await asyncio.gather(
        *[system.process_task(task) for task in tasks],
        return_exceptions=True
    )
    
    print(f"✅ Processed {len(results)} tasks")
    
    # Scaling-Status nach hoher Last
    if system.auto_scaling_engine:
        status = system.auto_scaling_engine.get_scaling_status()
        print(f"📈 Agents after load: {status['active_agents']}")
        
        # Empfehlungen abrufen
        recommendations = system.auto_scaling_engine.get_recommendations()
        print(f"🎯 Recommended action: {recommendations['recommended_action']}")
        print(f"🎯 Recommended agents: {recommendations['recommended_count']}")

async def custom_scaling_callback_example():
    """Beispiel mit Custom Scaling Callbacks"""
    print("\n📞 Custom Callbacks Beispiel")
    
    scaling_events = []
    agent_lifecycle_events = []
    
    async def scaling_notification_handler(event):
        """Handler für Scaling-Events"""
        scaling_events.append({
            'timestamp': event.timestamp,
            'action': event.action,
            'from_count': event.from_count,
            'to_count': event.to_count,
            'reason': event.reason
        })
        print(f"🔔 Scaling Event: {event.action} {event.from_count}→{event.to_count} ({event.reason})")
    
    async def agent_lifecycle_handler(lifecycle_info):
        """Handler für Agent-Lifecycle-Events"""
        agent_lifecycle_events.append({
            'agent_id': lifecycle_info.agent_id,
            'state': lifecycle_info.state.value,
            'role': lifecycle_info.role.value,
            'reason': lifecycle_info.creation_reason
        })
        print(f"🤖 Agent {lifecycle_info.agent_id} → {lifecycle_info.state.value}")
    
    system = EnhancedOllamaFlow(
        auto_scaling=True,
        scaling_strategy="AGGRESSIVE",
        model="phi3:mini"
    )
    
    await system.initialize()
    
    # Callbacks registrieren
    if system.auto_scaling_engine:
        system.auto_scaling_engine.set_callbacks(
            notification_callback=scaling_notification_handler
        )
    
    if system.dynamic_agent_manager:
        system.dynamic_agent_manager.add_lifecycle_callback(
            AgentLifecycleState.ACTIVE, agent_lifecycle_handler
        )
        system.dynamic_agent_manager.add_lifecycle_callback(
            AgentLifecycleState.TERMINATED, agent_lifecycle_handler
        )
    
    # Task verarbeiten
    await system.process_task("Create a complex web application with multiple components")
    
    print(f"📊 Captured {len(scaling_events)} scaling events")
    print(f"📊 Captured {len(agent_lifecycle_events)} lifecycle events")

async def environment_based_scaling_example():
    """Beispiel für unterschiedliche Umgebungskonfigurationen"""
    print("\n🌍 Environment-basierte Konfiguration")
    
    # Konfiguration laden
    with open('auto_scaling_config.json', 'r') as f:
        config = json.load(f)
    
    environments = ['development', 'testing', 'production']
    
    for env in environments:
        print(f"\n--- {env.upper()} Environment ---")
        
        env_config = config['auto_scaling']['environments'][env]
        
        system = EnhancedOllamaFlow(
            auto_scaling=True,
            scaling_strategy=env_config['strategy'],
            model="phi3:mini"
        )
        
        await system.initialize()
        
        # Konfiguration anpassen
        if system.auto_scaling_engine:
            system.auto_scaling_engine.config.update({
                'scaling_check_interval': env_config['scale_check_interval'],
                'cooldown_period': env_config['cooldown_period']
            })
            
            system.auto_scaling_engine.gpu_scaler.scaling_config.update({
                'memory_safety_margin': env_config['memory_safety_margin']
            })
        
        print(f"✅ {env} configuration loaded")
        print(f"   Strategy: {env_config['strategy']}")
        print(f"   Check Interval: {env_config['scale_check_interval']}s")
        print(f"   Cooldown: {env_config['cooldown_period']}s")

async def monitoring_and_status_example():
    """Beispiel für Monitoring und Status-Abfragen"""
    print("\n📊 Monitoring und Status Beispiel")
    
    system = EnhancedOllamaFlow(
        auto_scaling=True,
        scaling_strategy="HYBRID",
        model="phi3:mini"
    )
    
    await system.initialize()
    
    # GPU-Status
    if system.auto_scaling_engine:
        gpu_status = system.auto_scaling_engine.gpu_scaler.get_gpu_status()
        print("🎮 GPU Status:")
        print(f"   Total Memory: {gpu_status.get('total_memory_mb', 0)}MB")
        print(f"   Available Memory: {gpu_status.get('available_memory_mb', 0)}MB")
        print(f"   GPU Utilization: {gpu_status.get('average_gpu_utilization', 0):.1f}%")
        print(f"   Current Model: {gpu_status.get('current_model', 'unknown')}")
        print(f"   Max Agents: {gpu_status.get('max_agents', 0)}")
        
        # Scaling-Empfehlungen
        recommendations = system.auto_scaling_engine.get_recommendations()
        print(f"\n🎯 Scaling Recommendations:")
        print(f"   Current Agents: {recommendations['current_agents']}")
        print(f"   Recommended Action: {recommendations['recommended_action']}")
        print(f"   Recommended Count: {recommendations['recommended_count']}")
        print(f"   Reason: {recommendations['reason']}")
        
        # Scaling-Status
        scaling_status = system.auto_scaling_engine.get_scaling_status()
        print(f"\n🔄 Scaling Status:")
        print(f"   Strategy: {scaling_status['strategy']}")
        print(f"   Active Agents: {scaling_status['active_agents']}")
        print(f"   Running: {scaling_status['running']}")
        
        # Agent-Details
        if scaling_status['agent_details']:
            print(f"   Agent Details:")
            for agent_id, details in scaling_status['agent_details'].items():
                print(f"     - {agent_id}: {details['role']} ({details['status']})")
    
    # Dynamic Agent Manager Status
    if system.dynamic_agent_manager:
        dam_status = system.dynamic_agent_manager.get_detailed_status()
        print(f"\n🤖 Dynamic Agent Manager Status:")
        print(f"   Active Agents: {dam_status['active_agents']}")
        print(f"   Total Managed: {dam_status['total_managed_agents']}")
        print(f"   Creation Queue: {dam_status['creation_queue_size']}")
        print(f"   Termination Queue: {dam_status['termination_queue_size']}")
        
        if dam_status['role_distribution']:
            print(f"   Role Distribution:")
            for role, count in dam_status['role_distribution'].items():
                print(f"     - {role}: {count}")

async def performance_optimization_example():
    """Beispiel für Performance-Optimierung"""
    print("\n⚡ Performance Optimization Beispiel")
    
    system = EnhancedOllamaFlow(
        auto_scaling=True,
        scaling_strategy="AGGRESSIVE",
        model="phi3:mini"
    )
    
    await system.initialize()
    
    # Optimierte Konfiguration für hohen Durchsatz
    if system.auto_scaling_engine and system.dynamic_agent_manager:
        # Schnelleres Scaling
        system.auto_scaling_engine.config.update({
            'scaling_check_interval': 5.0,    # Sehr frequent prüfen
            'cooldown_period': 10.0,          # Kurze Cooldown
            'scale_batch_size': 5             # Mehr Agents parallel
        })
        
        # Batch-Processing optimieren
        system.dynamic_agent_manager.config.update({
            'batch_creation_size': 5,         # 5 Agents parallel erstellen
            'cleanup_interval_seconds': 30    # Häufigeres Cleanup
        })
        
        # GPU-Konfiguration optimieren
        system.auto_scaling_engine.gpu_scaler.scaling_config.update({
            'memory_safety_margin': 0.10,    # Weniger Reserve für mehr Agents
            'scale_up_threshold': 0.60,      # Früher hochskalieren
            'scale_down_threshold': 0.30     # Später runterskalieren
        })
        
        print("⚙️ Optimierte Konfiguration angewendet:")
        print("   - Schnellere Scaling-Checks (5s)")
        print("   - Kürzere Cooldown-Periode (10s)")
        print("   - Batch-Agent-Erstellung (5 parallel)")
        print("   - Aggressivere Memory-Schwellenwerte")
    
    # Performance-Test
    start_time = asyncio.get_event_loop().time()
    
    tasks = [
        "Create a simple calculator",
        "Write a hello world program", 
        "Create a basic web server",
        "Write a file reader function",
        "Create a data structure implementation"
    ]
    
    results = await asyncio.gather(
        *[system.process_task(task) for task in tasks],
        return_exceptions=True
    )
    
    end_time = asyncio.get_event_loop().time()
    
    print(f"⏱️ Performance Results:")
    print(f"   Tasks: {len(tasks)}")
    print(f"   Total Time: {end_time - start_time:.2f}s")
    print(f"   Avg Time per Task: {(end_time - start_time) / len(tasks):.2f}s")
    print(f"   Successful: {len([r for r in results if not isinstance(r, Exception)])}")

async def main():
    """Hauptfunktion - führt alle Beispiele aus"""
    print("🎯 Ollama Flow Auto-Scaling Examples")
    print("=" * 50)
    
    examples = [
        basic_auto_scaling_example,
        hybrid_scaling_example,
        custom_scaling_callback_example,
        environment_based_scaling_example,
        monitoring_and_status_example,
        performance_optimization_example
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n[{i}/{len(examples)}] Running {example.__name__}...")
            await example()
            print("✅ Example completed successfully")
        except Exception as e:
            print(f"❌ Example failed: {e}")
        
        if i < len(examples):
            await asyncio.sleep(2)  # Kurze Pause zwischen Beispielen
    
    print("\n🎉 All examples completed!")

if __name__ == "__main__":
    asyncio.run(main())