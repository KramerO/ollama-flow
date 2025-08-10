#!/usr/bin/env python3
"""
Auto-Scaling Engine für Ollama Flow
Koordiniert GPU-basiertes Auto-Scaling mit dynamischer Agent-Verwaltung
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from gpu_autoscaler import GPUAutoScaler
from workload_metrics import WorkloadMetricsCollector, WorkloadSeverity
from agents.drone_agent import DroneAgent, DroneRole
from enhanced_db_manager import EnhancedDBManager

logger = logging.getLogger(__name__)

class ScalingStrategy(Enum):
    """Verschiedene Scaling-Strategien"""
    GPU_MEMORY_BASED = "gpu_memory"  # Basierend auf GPU-Speicher (Standard)
    WORKLOAD_BASED = "workload"      # Basierend auf Task-Queue und Auslastung
    HYBRID = "hybrid"                # Kombination aus beiden
    CONSERVATIVE = "conservative"     # Vorsichtige Scaling-Entscheidungen
    AGGRESSIVE = "aggressive"         # Aggressive Scaling-Entscheidungen

@dataclass
class ScalingEvent:
    """Repräsentiert ein Scaling-Event"""
    timestamp: float
    action: str  # scale_up, scale_down, maintain
    from_count: int
    to_count: int
    strategy: ScalingStrategy
    reason: str
    gpu_memory_mb: int
    gpu_utilization: float
    queue_length: int
    success: bool
    execution_time: float = 0.0

class AutoScalingEngine:
    """Hauptklasse für automatisches Scaling von AI-Agents"""
    
    def __init__(self, 
                 strategy: ScalingStrategy = ScalingStrategy.GPU_MEMORY_BASED,
                 model: str = "phi3:mini"):
        
        self.strategy = strategy
        self.model = model
        self.running = False
        
        # Core Components
        self.gpu_scaler = GPUAutoScaler(default_model=model)
        self.workload_collector = WorkloadMetricsCollector()
        self.db_manager: Optional[EnhancedDBManager] = None
        
        # Agent Management
        self.active_agents: Dict[str, DroneAgent] = {}
        self.agent_creation_queue: List[DroneRole] = []
        self.scaling_events: List[ScalingEvent] = []
        
        # Callbacks
        self.agent_creation_callback: Optional[Callable] = None
        self.agent_termination_callback: Optional[Callable] = None
        self.scaling_notification_callback: Optional[Callable] = None
        
        # Scaling Configuration
        self.config = {
            'min_agents': 1,
            'max_agents': 8,
            'scaling_check_interval': 20.0,  # Sekunden
            'decision_history_size': 10,
            'consensus_threshold': 0.7,  # 70% Konsens für Hybrid-Strategie
            'emergency_scale_threshold': 0.95,  # 95% Resource-Auslastung
            'scale_batch_size': 2,  # Max Agents pro Scaling-Aktion
        }
        
        # Task Management
        self.engine_task: Optional[asyncio.Task] = None
        self.last_decision_time = 0.0
        
        logger.info(f"🔄 Auto-Scaling Engine initialized with {strategy.value} strategy")
    
    def set_callbacks(self, 
                     creation_callback: Optional[Callable] = None,
                     termination_callback: Optional[Callable] = None,
                     notification_callback: Optional[Callable] = None):
        """Setzt Callback-Funktionen für Agent-Management"""
        self.agent_creation_callback = creation_callback
        self.agent_termination_callback = termination_callback
        self.scaling_notification_callback = notification_callback
        
        # GPU-Scaler Callback setzen
        self.gpu_scaler.set_scaling_callback(self._handle_gpu_scaling)
    
    def set_database_manager(self, db_manager: EnhancedDBManager):
        """Setzt den Datenbank-Manager"""
        self.db_manager = db_manager
    
    async def start(self):
        """Startet die Auto-Scaling-Engine"""
        if self.running:
            return
        
        self.running = True
        
        # Komponenten starten
        if self.strategy in [ScalingStrategy.GPU_MEMORY_BASED, ScalingStrategy.HYBRID]:
            await self.gpu_scaler.start_autoscaling()
        
        if self.strategy in [ScalingStrategy.WORKLOAD_BASED, ScalingStrategy.HYBRID]:
            await self.workload_collector.start_collection()
        
        # Haupt-Engine starten
        self.engine_task = asyncio.create_task(self._main_scaling_loop())
        
        logger.info(f"🔄 Auto-Scaling Engine started with {self.strategy.value} strategy")
    
    async def stop(self):
        """Stoppt die Auto-Scaling-Engine"""
        self.running = False
        
        if self.engine_task:
            self.engine_task.cancel()
            try:
                await self.engine_task
            except asyncio.CancelledError:
                pass
        
        # Komponenten stoppen
        await self.gpu_scaler.stop_autoscaling()
        await self.workload_collector.stop_collection()
        
        logger.info("🔄 Auto-Scaling Engine stopped")
    
    async def _main_scaling_loop(self):
        """Haupt-Scaling-Schleife"""
        while self.running:
            try:
                await self._evaluate_scaling_decision()
                await asyncio.sleep(self.config['scaling_check_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-scaling loop: {e}")
                await asyncio.sleep(self.config['scaling_check_interval'])
    
    async def _evaluate_scaling_decision(self):
        """Evaluiert und trifft Scaling-Entscheidungen"""
        start_time = time.time()
        current_count = len(self.active_agents)
        
        try:
            decision = await self._make_scaling_decision()
            
            if decision['action'] != 'maintain':
                event = ScalingEvent(
                    timestamp=start_time,
                    action=decision['action'],
                    from_count=current_count,
                    to_count=decision['target_count'],
                    strategy=self.strategy,
                    reason=decision['reason'],
                    gpu_memory_mb=decision.get('gpu_memory_mb', 0),
                    gpu_utilization=decision.get('gpu_utilization', 0.0),
                    queue_length=decision.get('queue_length', 0),
                    success=False,
                    execution_time=0.0
                )
                
                # Scaling-Aktion ausführen
                success = await self._execute_scaling(decision)
                
                event.success = success
                event.execution_time = time.time() - start_time
                self.scaling_events.append(event)
                
                # Event-Historie begrenzen
                if len(self.scaling_events) > 100:
                    self.scaling_events = self.scaling_events[-50:]
                
                # Notification senden
                if self.scaling_notification_callback:
                    try:
                        await self.scaling_notification_callback(event)
                    except Exception as e:
                        logger.error(f"Error in scaling notification callback: {e}")
        
        except Exception as e:
            logger.error(f"Error evaluating scaling decision: {e}")
    
    async def _make_scaling_decision(self) -> Dict[str, Any]:
        """Trifft Scaling-Entscheidung basierend auf gewählter Strategie"""
        current_count = len(self.active_agents)
        
        if self.strategy == ScalingStrategy.GPU_MEMORY_BASED:
            return await self._gpu_based_decision(current_count)
        
        elif self.strategy == ScalingStrategy.WORKLOAD_BASED:
            return await self._workload_based_decision(current_count)
        
        elif self.strategy == ScalingStrategy.HYBRID:
            return await self._hybrid_decision(current_count)
        
        elif self.strategy == ScalingStrategy.CONSERVATIVE:
            return await self._conservative_decision(current_count)
        
        elif self.strategy == ScalingStrategy.AGGRESSIVE:
            return await self._aggressive_decision(current_count)
        
        else:
            return {
                'action': 'maintain',
                'target_count': current_count,
                'reason': f'Unknown strategy: {self.strategy}'
            }
    
    async def _gpu_based_decision(self, current_count: int) -> Dict[str, Any]:
        """GPU-Memory-basierte Scaling-Entscheidung"""
        gpu_status = self.gpu_scaler.get_gpu_status()
        recommendations = self.gpu_scaler.get_scaling_recommendations()
        
        if 'error' in recommendations:
            return {
                'action': 'maintain',
                'target_count': current_count,
                'reason': recommendations['error']
            }
        
        action = recommendations['recommended_action']
        target_count = recommendations.get('recommended_count', current_count)
        
        return {
            'action': action if action != 'none' else 'maintain',
            'target_count': target_count,
            'reason': recommendations['reason'],
            'gpu_memory_mb': gpu_status['available_memory_mb'],
            'gpu_utilization': gpu_status['average_gpu_utilization']
        }
    
    async def _workload_based_decision(self, current_count: int) -> Dict[str, Any]:
        """Workload-basierte Scaling-Entscheidung"""
        metrics = self.workload_collector.get_current_metrics()
        if not metrics:
            return {
                'action': 'maintain',
                'target_count': current_count,
                'reason': 'No workload metrics available'
            }
        
        severity = self.workload_collector.get_workload_severity()
        should_scale_up, scale_up_reason = self.workload_collector.should_scale_up()
        should_scale_down, scale_down_reason = self.workload_collector.should_scale_down()
        
        if should_scale_up:
            target_count = min(current_count + 1, self.config['max_agents'])
            return {
                'action': 'scale_up',
                'target_count': target_count,
                'reason': scale_up_reason,
                'queue_length': metrics.queue_length,
                'workload_severity': severity.value
            }
        
        elif should_scale_down:
            target_count = max(current_count - 1, self.config['min_agents'])
            return {
                'action': 'scale_down',
                'target_count': target_count,
                'reason': scale_down_reason,
                'queue_length': metrics.queue_length,
                'workload_severity': severity.value
            }
        
        return {
            'action': 'maintain',
            'target_count': current_count,
            'reason': f'Workload stable: {severity.value}',
            'queue_length': metrics.queue_length
        }
    
    async def _hybrid_decision(self, current_count: int) -> Dict[str, Any]:
        """Hybrid-Entscheidung (GPU + Workload)"""
        gpu_decision = await self._gpu_based_decision(current_count)
        workload_decision = await self._workload_based_decision(current_count)
        
        # Konsens-Algorithmus
        gpu_action = gpu_decision['action']
        workload_action = workload_decision['action']
        
        # Einigkeit - Entscheidung übernehmen
        if gpu_action == workload_action:
            return {
                **gpu_decision,
                'reason': f"GPU+Workload consensus: {gpu_decision['reason']} | {workload_decision['reason']}"
            }
        
        # GPU sagt scale_up, Workload sagt maintain -> GPU hat Vorrang (Memory-Limits)
        if gpu_action == 'scale_up' and workload_action == 'maintain':
            return {
                **gpu_decision,
                'reason': f"GPU memory priority: {gpu_decision['reason']}"
            }
        
        # Workload sagt scale_up, GPU sagt maintain -> prüfe GPU-Kapazität
        if workload_action == 'scale_up' and gpu_action == 'maintain':
            gpu_status = self.gpu_scaler.get_gpu_status()
            if gpu_status['available_memory_mb'] > 2048:  # Genug Memory frei
                return {
                    **workload_decision,
                    'reason': f"Workload priority (GPU capacity available): {workload_decision['reason']}"
                }
        
        # Scale_down - beide müssen zustimmen oder GPU-Memory ist kritisch
        if 'scale_down' in [gpu_action, workload_action]:
            gpu_status = self.gpu_scaler.get_gpu_status()
            if gpu_status['average_memory_utilization'] < 50.0:  # Niedrige Memory-Nutzung
                return {
                    'action': 'scale_down',
                    'target_count': max(current_count - 1, self.config['min_agents']),
                    'reason': f"Hybrid scale-down: GPU memory low utilization"
                }
        
        # Default: Maintain bei Uneinigkeit
        return {
            'action': 'maintain',
            'target_count': current_count,
            'reason': f"No consensus: GPU={gpu_action}, Workload={workload_action}"
        }
    
    async def _conservative_decision(self, current_count: int) -> Dict[str, Any]:
        """Konservative Scaling-Entscheidung"""
        base_decision = await self._hybrid_decision(current_count)
        
        # Konservativ - nur bei eindeutigen Signalen skalieren
        if base_decision['action'] == 'scale_up':
            # Zusätzliche Checks für Scale-Up
            gpu_status = self.gpu_scaler.get_gpu_status()
            if gpu_status['average_memory_utilization'] > 80.0:  # Hohe Memory-Nutzung
                return base_decision
            else:
                return {
                    'action': 'maintain',
                    'target_count': current_count,
                    'reason': f"Conservative: GPU memory not critical ({gpu_status['average_memory_utilization']:.1f}%)"
                }
        
        elif base_decision['action'] == 'scale_down':
            # Nur scale down wenn sehr niedrige Auslastung
            gpu_status = self.gpu_scaler.get_gpu_status()
            if (gpu_status['average_memory_utilization'] < 30.0 and 
                gpu_status['average_gpu_utilization'] < 20.0):
                return base_decision
            else:
                return {
                    'action': 'maintain',
                    'target_count': current_count,
                    'reason': "Conservative: Maintaining current scale"
                }
        
        return base_decision
    
    async def _aggressive_decision(self, current_count: int) -> Dict[str, Any]:
        """Aggressive Scaling-Entscheidung"""
        base_decision = await self._hybrid_decision(current_count)
        
        # Aggressiv - proaktives Scaling
        if base_decision['action'] == 'maintain':
            gpu_status = self.gpu_scaler.get_gpu_status()
            
            # Proaktives Scale-Up bei verfügbarem Memory
            if (gpu_status['available_memory_mb'] > 4096 and 
                current_count < self.config['max_agents'] // 2):
                return {
                    'action': 'scale_up',
                    'target_count': current_count + 1,
                    'reason': f"Aggressive: Proactive scaling with {gpu_status['available_memory_mb']}MB available"
                }
        
        elif base_decision['action'] == 'scale_up':
            # Batch-Scaling bei viel verfügbarem Memory
            gpu_status = self.gpu_scaler.get_gpu_status()
            if gpu_status['available_memory_mb'] > 8192:  # Viel Memory frei
                batch_size = min(self.config['scale_batch_size'], 
                               self.config['max_agents'] - current_count)
                return {
                    **base_decision,
                    'target_count': current_count + batch_size,
                    'reason': f"Aggressive batch scaling: +{batch_size} agents"
                }
        
        return base_decision
    
    async def _execute_scaling(self, decision: Dict[str, Any]) -> bool:
        """Führt die Scaling-Entscheidung aus"""
        action = decision['action']
        target_count = decision['target_count']
        current_count = len(self.active_agents)
        
        try:
            if action == 'scale_up':
                agents_to_add = target_count - current_count
                return await self._scale_up(agents_to_add, decision['reason'])
            
            elif action == 'scale_down':
                agents_to_remove = current_count - target_count
                return await self._scale_down(agents_to_remove, decision['reason'])
            
            return True  # maintain
        
        except Exception as e:
            logger.error(f"Error executing scaling action {action}: {e}")
            return False
    
    async def _scale_up(self, count: int, reason: str) -> bool:
        """Skaliert Agents nach oben"""
        if not self.agent_creation_callback:
            logger.warning("No agent creation callback set")
            return False
        
        success_count = 0
        for i in range(count):
            try:
                # Bestimme optimale Rolle für neuen Agent
                role = self._determine_optimal_role()
                
                # Agent erstellen
                agent = await self.agent_creation_callback(role, self.model)
                if agent:
                    self.active_agents[agent.agent_id] = agent
                    success_count += 1
                    
                    # GPU-Scaler über neue Agent-Anzahl informieren
                    self.gpu_scaler.update_agent_count(len(self.active_agents))
                    
                    logger.info(f"🔄 Scaled up: +1 {role.value} agent (total: {len(self.active_agents)})")
                
            except Exception as e:
                logger.error(f"Error creating agent during scale-up: {e}")
        
        return success_count > 0
    
    async def _scale_down(self, count: int, reason: str) -> bool:
        """Skaliert Agents nach unten"""
        if not self.agent_termination_callback:
            logger.warning("No agent termination callback set")
            return False
        
        # Wähle Agents zum Entfernen (idle Agents bevorzugen)
        agents_to_remove = self._select_agents_for_removal(count)
        
        success_count = 0
        for agent_id in agents_to_remove:
            try:
                agent = self.active_agents.get(agent_id)
                if agent:
                    # Agent terminieren
                    success = await self.agent_termination_callback(agent)
                    if success:
                        del self.active_agents[agent_id]
                        success_count += 1
                        
                        # GPU-Scaler über neue Agent-Anzahl informieren
                        self.gpu_scaler.update_agent_count(len(self.active_agents))
                        
                        logger.info(f"🔄 Scaled down: -1 {agent.role.value} agent (total: {len(self.active_agents)})")
                
            except Exception as e:
                logger.error(f"Error terminating agent {agent_id} during scale-down: {e}")
        
        return success_count > 0
    
    def _determine_optimal_role(self) -> DroneRole:
        """Bestimmt die optimale Rolle für einen neuen Agent"""
        # Zähle aktuelle Rollen
        role_counts = {}
        for agent in self.active_agents.values():
            role = agent.role
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Finde Rolle mit geringster Anzahl
        all_roles = list(DroneRole)
        min_count = float('inf')
        optimal_role = DroneRole.DEVELOPER  # Default
        
        for role in all_roles:
            count = role_counts.get(role, 0)
            if count < min_count:
                min_count = count
                optimal_role = role
        
        return optimal_role
    
    def _select_agents_for_removal(self, count: int) -> List[str]:
        """Wählt Agents zum Entfernen aus (idle Agents bevorzugen)"""
        if count >= len(self.active_agents):
            return list(self.active_agents.keys())
        
        # Priorität: idle Agents zuerst
        idle_agents = []
        busy_agents = []
        
        for agent_id, agent in self.active_agents.items():
            # Hier würden wir den Agent-Status prüfen
            # Für jetzt nehmen wir eine einfache Heuristik
            idle_agents.append(agent_id)  # Vereinfacht
        
        # Wähle aus idle Agents
        selected = idle_agents[:count]
        if len(selected) < count:
            # Füge busy Agents hinzu falls nötig
            selected.extend(busy_agents[:count - len(selected)])
        
        return selected
    
    async def _handle_gpu_scaling(self, action: str, from_count: int, 
                                 to_count: int, reason: str) -> bool:
        """Callback für GPU-Scaler"""
        decision = {
            'action': action,
            'target_count': to_count,
            'reason': f"GPU-driven: {reason}"
        }
        
        return await self._execute_scaling(decision)
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Scaling-Status zurück"""
        current_count = len(self.active_agents)
        
        # GPU-Status
        gpu_status = self.gpu_scaler.get_gpu_status()
        
        # Workload-Status
        workload_metrics = self.workload_collector.get_current_metrics()
        
        # Letzte Scaling-Events
        recent_events = self.scaling_events[-5:] if self.scaling_events else []
        
        return {
            'strategy': self.strategy.value,
            'current_model': self.model,
            'active_agents': current_count,
            'agent_details': {
                agent_id: {
                    'role': agent.role.value,
                    'status': getattr(agent, 'status', 'unknown')
                }
                for agent_id, agent in self.active_agents.items()
            },
            'gpu_status': gpu_status,
            'workload_metrics': {
                'queue_length': workload_metrics.queue_length if workload_metrics else 0,
                'active_agents': workload_metrics.active_agents if workload_metrics else 0,
                'throughput': workload_metrics.throughput if workload_metrics else 0.0
            } if workload_metrics else {},
            'recent_scaling_events': [
                {
                    'timestamp': event.timestamp,
                    'action': event.action,
                    'from_count': event.from_count,
                    'to_count': event.to_count,
                    'reason': event.reason,
                    'success': event.success
                }
                for event in recent_events
            ],
            'config': self.config,
            'running': self.running
        }
    
    def update_model(self, model: str):
        """Aktualisiert das verwendete Modell"""
        self.model = model
        self.gpu_scaler.set_model(model)
        logger.info(f"🔄 Auto-Scaling Engine switched to model: {model}")
    
    def update_strategy(self, strategy: ScalingStrategy):
        """Aktualisiert die Scaling-Strategie"""
        old_strategy = self.strategy
        self.strategy = strategy
        logger.info(f"🔄 Auto-Scaling strategy changed: {old_strategy.value} -> {strategy.value}")
    
    def register_agent(self, agent: DroneAgent):
        """Registriert einen neuen Agent"""
        self.active_agents[agent.agent_id] = agent
        self.gpu_scaler.update_agent_count(len(self.active_agents))
        
        # Bei Workload-Collector registrieren
        self.workload_collector.register_agent(agent.agent_id, agent.role.value)
        
        logger.info(f"🔄 Registered agent {agent.agent_id} ({agent.role.value})")
    
    def unregister_agent(self, agent_id: str):
        """Entfernt einen Agent aus der Verwaltung"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            self.gpu_scaler.update_agent_count(len(self.active_agents))
            
            # Bei Workload-Collector entfernen
            self.workload_collector.unregister_agent(agent_id)
            
            logger.info(f"🔄 Unregistered agent {agent_id}")
    
    def get_recommendations(self) -> Dict[str, Any]:
        """Gibt Scaling-Empfehlungen zurück ohne Ausführung"""
        current_count = len(self.active_agents)
        
        # Simuliere Entscheidung ohne Ausführung
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            decision = loop.run_until_complete(self._make_scaling_decision())
        finally:
            loop.close()
        
        return {
            'current_agents': current_count,
            'recommended_action': decision['action'],
            'recommended_count': decision.get('target_count', current_count),
            'reason': decision['reason'],
            'strategy': self.strategy.value,
            'gpu_recommendations': self.gpu_scaler.get_scaling_recommendations(),
            'workload_recommendations': self.workload_collector.get_scaling_recommendations()
        }