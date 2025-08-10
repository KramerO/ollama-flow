#!/usr/bin/env python3
"""
Workload Metrics Analysis System
Sammelt und analysiert Metriken zur Bestimmung der optimalen Agent-Anzahl
"""

import asyncio
import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from collections import deque
import psutil
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WorkloadSeverity(Enum):
    """Workload-Schweregrade für Scaling-Entscheidungen"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

@dataclass
class TaskMetrics:
    """Metriken für eine einzelne Aufgabe"""
    task_id: str
    submitted_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    agent_id: Optional[str] = None
    complexity_score: float = 0.0
    priority: int = 1
    estimated_duration: float = 60.0  # Sekunden
    actual_duration: Optional[float] = None
    status: str = "pending"  # pending, running, completed, failed
    retry_count: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)

    @property
    def wait_time(self) -> Optional[float]:
        """Zeit zwischen Submission und Start"""
        if self.started_at and self.submitted_at:
            return self.started_at - self.submitted_at
        return None
    
    @property
    def queue_age(self) -> float:
        """Wie lange ist die Task schon in der Queue"""
        if self.status == "pending":
            return time.time() - self.submitted_at
        return 0.0

@dataclass
class AgentMetrics:
    """Metriken für einen einzelnen Agent"""
    agent_id: str
    role: str
    status: str = "idle"  # idle, busy, overloaded, error
    current_task_id: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    last_activity: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=10))
    
    @property
    def average_response_time(self) -> float:
        """Durchschnittliche Antwortzeit der letzten Tasks"""
        return statistics.mean(self.response_times) if self.response_times else 0.0
    
    @property
    def success_rate(self) -> float:
        """Erfolgsrate des Agents"""
        total = self.tasks_completed + self.tasks_failed
        return (self.tasks_completed / total * 100) if total > 0 else 100.0
    
    @property
    def idle_time(self) -> float:
        """Zeit seit letzter Aktivität"""
        return time.time() - self.last_activity if self.status == "idle" else 0.0

@dataclass
class SystemMetrics:
    """System-weite Metriken"""
    timestamp: float = field(default_factory=time.time)
    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    overloaded_agents: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    queue_length: int = 0
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    system_cpu: float = 0.0
    system_memory: float = 0.0
    throughput: float = 0.0  # Tasks pro Sekunde
    error_rate: float = 0.0

class WorkloadMetricsCollector:
    """Sammelt und analysiert Workload-Metriken für Auto-Scaling"""
    
    def __init__(self, history_size: int = 100):
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_history: deque = deque(maxlen=history_size)
        self.collection_interval = 5.0  # Sekunden
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
        self.lock = threading.Lock()
        
        # Schwellenwerte für Scaling-Entscheidungen
        self.thresholds = {
            'high_queue_length': 10,
            'high_wait_time': 30.0,  # Sekunden
            'high_cpu_usage': 80.0,  # Prozent
            'high_memory_usage': 85.0,  # Prozent
            'low_idle_agents': 0.2,  # 20% idle agents minimum
            'agent_overload_threshold': 0.8,  # 80% agents busy = overload
            'min_agents': 2,
            'max_agents': 16,
            'scale_up_cooldown': 60.0,  # Sekunden
            'scale_down_cooldown': 120.0,  # Sekunden
        }
        
        self.last_scale_action = 0.0
        self.scale_history: deque = deque(maxlen=50)
        
    async def start_collection(self):
        """Startet die kontinuierliche Metrik-Sammlung"""
        if self.running:
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("🔍 Workload metrics collection started")
    
    async def stop_collection(self):
        """Stoppt die Metrik-Sammlung"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("🔍 Workload metrics collection stopped")
    
    async def _collection_loop(self):
        """Hauptschleife für Metrik-Sammlung"""
        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Sammelt aktuelle System-Metriken"""
        with self.lock:
            # System-Ressourcen
            system_cpu = psutil.cpu_percent(interval=None)
            system_memory = psutil.virtual_memory().percent
            
            # Task-Metriken aggregieren
            pending_tasks = len([t for t in self.task_metrics.values() if t.status == "pending"])
            running_tasks = len([t for t in self.task_metrics.values() if t.status == "running"])
            completed_tasks = len([t for t in self.task_metrics.values() if t.status == "completed"])
            failed_tasks = len([t for t in self.task_metrics.values() if t.status == "failed"])
            
            # Agent-Metriken aggregieren
            active_agents = len([a for a in self.agent_metrics.values() if a.status in ["busy", "overloaded"]])
            idle_agents = len([a for a in self.agent_metrics.values() if a.status == "idle"])
            overloaded_agents = len([a for a in self.agent_metrics.values() if a.status == "overloaded"])
            
            # Durchschnittswerte berechnen
            wait_times = [t.wait_time for t in self.task_metrics.values() if t.wait_time is not None]
            avg_wait_time = statistics.mean(wait_times) if wait_times else 0.0
            
            processing_times = [t.actual_duration for t in self.task_metrics.values() if t.actual_duration is not None]
            avg_processing_time = statistics.mean(processing_times) if processing_times else 0.0
            
            # Durchsatz berechnen (Tasks der letzten Minute)
            recent_completed = [
                t for t in self.task_metrics.values() 
                if t.completed_at and t.completed_at > time.time() - 60
            ]
            throughput = len(recent_completed) / 60.0  # Tasks pro Sekunde
            
            # Error Rate
            total_recent = len([
                t for t in self.task_metrics.values()
                if t.completed_at and t.completed_at > time.time() - 300  # 5 Minuten
            ])
            recent_failed = len([
                t for t in recent_completed if t.status == "failed"
            ])
            error_rate = (recent_failed / total_recent * 100) if total_recent > 0 else 0.0
            
            # System-Metriken erstellen
            system_metrics = SystemMetrics(
                timestamp=time.time(),
                total_agents=len(self.agent_metrics),
                active_agents=active_agents,
                idle_agents=idle_agents,
                overloaded_agents=overloaded_agents,
                pending_tasks=pending_tasks,
                running_tasks=running_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                queue_length=pending_tasks,
                average_wait_time=avg_wait_time,
                average_processing_time=avg_processing_time,
                system_cpu=system_cpu,
                system_memory=system_memory,
                throughput=throughput,
                error_rate=error_rate
            )
            
            self.system_history.append(system_metrics)
            
            # Debug-Logging alle 30 Sekunden
            if len(self.system_history) % 6 == 0:  # Bei 5s Intervall = 30s
                logger.debug(f"📊 System Metrics: {active_agents}/{len(self.agent_metrics)} agents active, "
                           f"{pending_tasks} pending, {avg_wait_time:.1f}s avg wait, "
                           f"{throughput:.2f} tasks/s throughput")
    
    def record_task_submitted(self, task_id: str, complexity_score: float = 1.0, 
                             priority: int = 1, estimated_duration: float = 60.0) -> TaskMetrics:
        """Registriert eine neue Task"""
        with self.lock:
            task_metrics = TaskMetrics(
                task_id=task_id,
                submitted_at=time.time(),
                complexity_score=complexity_score,
                priority=priority,
                estimated_duration=estimated_duration
            )
            self.task_metrics[task_id] = task_metrics
            return task_metrics
    
    def record_task_started(self, task_id: str, agent_id: str):
        """Registriert Task-Start"""
        with self.lock:
            if task_id in self.task_metrics:
                self.task_metrics[task_id].started_at = time.time()
                self.task_metrics[task_id].agent_id = agent_id
                self.task_metrics[task_id].status = "running"
            
            if agent_id in self.agent_metrics:
                self.agent_metrics[agent_id].status = "busy"
                self.agent_metrics[agent_id].current_task_id = task_id
                self.agent_metrics[agent_id].last_activity = time.time()
    
    def record_task_completed(self, task_id: str, success: bool = True, 
                            resource_usage: Optional[Dict[str, float]] = None):
        """Registriert Task-Abschluss"""
        with self.lock:
            if task_id not in self.task_metrics:
                return
            
            task = self.task_metrics[task_id]
            task.completed_at = time.time()
            task.status = "completed" if success else "failed"
            
            if task.started_at:
                task.actual_duration = task.completed_at - task.started_at
            
            if resource_usage:
                task.resource_usage = resource_usage
            
            # Agent-Metriken aktualisieren
            if task.agent_id and task.agent_id in self.agent_metrics:
                agent = self.agent_metrics[task.agent_id]
                agent.status = "idle"
                agent.current_task_id = None
                agent.last_activity = time.time()
                
                if success:
                    agent.tasks_completed += 1
                else:
                    agent.tasks_failed += 1
                
                if task.actual_duration:
                    agent.total_processing_time += task.actual_duration
                    agent.response_times.append(task.actual_duration)
    
    def register_agent(self, agent_id: str, role: str) -> AgentMetrics:
        """Registriert einen neuen Agent"""
        with self.lock:
            agent_metrics = AgentMetrics(agent_id=agent_id, role=role)
            self.agent_metrics[agent_id] = agent_metrics
            logger.info(f"📝 Registered agent {agent_id} with role {role}")
            return agent_metrics
    
    def unregister_agent(self, agent_id: str):
        """Entfernt einen Agent aus dem Monitoring"""
        with self.lock:
            if agent_id in self.agent_metrics:
                del self.agent_metrics[agent_id]
                logger.info(f"📝 Unregistered agent {agent_id}")
    
    def update_agent_status(self, agent_id: str, status: str, 
                           cpu_usage: float = 0.0, memory_usage: float = 0.0):
        """Aktualisiert Agent-Status und Ressourcen-Nutzung"""
        with self.lock:
            if agent_id in self.agent_metrics:
                agent = self.agent_metrics[agent_id]
                agent.status = status
                agent.cpu_usage = cpu_usage
                agent.memory_usage = memory_usage
                agent.last_activity = time.time()
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Gibt die neuesten System-Metriken zurück"""
        with self.lock:
            return self.system_history[-1] if self.system_history else None
    
    def get_workload_severity(self) -> WorkloadSeverity:
        """Bestimmt den aktuellen Workload-Schweregrad"""
        current = self.get_current_metrics()
        if not current:
            return WorkloadSeverity.LOW
        
        # Kritische Bedingungen
        if (current.error_rate > 15.0 or 
            current.average_wait_time > 120.0 or
            current.system_cpu > 95.0 or
            current.system_memory > 95.0):
            return WorkloadSeverity.CRITICAL
        
        # Sehr hohe Last
        if (current.queue_length > 20 or
            current.average_wait_time > 60.0 or
            current.system_cpu > 85.0 or
            current.overloaded_agents > current.total_agents * 0.6):
            return WorkloadSeverity.VERY_HIGH
        
        # Hohe Last
        if (current.queue_length > self.thresholds['high_queue_length'] or
            current.average_wait_time > self.thresholds['high_wait_time'] or
            current.system_cpu > self.thresholds['high_cpu_usage'] or
            current.idle_agents < current.total_agents * self.thresholds['low_idle_agents']):
            return WorkloadSeverity.HIGH
        
        # Moderate Last
        if (current.queue_length > 3 or
            current.average_wait_time > 10.0 or
            current.system_cpu > 60.0 or
            current.active_agents > current.total_agents * 0.7):
            return WorkloadSeverity.MODERATE
        
        # Niedrige Last
        if (current.queue_length > 1 or
            current.active_agents > current.total_agents * 0.3):
            return WorkloadSeverity.LOW
        
        return WorkloadSeverity.VERY_LOW
    
    def should_scale_up(self) -> Tuple[bool, str]:
        """Prüft ob Scale-Up erforderlich ist"""
        current = self.get_current_metrics()
        if not current:
            return False, "No metrics available"
        
        severity = self.get_workload_severity()
        
        # Cooldown prüfen
        if time.time() - self.last_scale_action < self.thresholds['scale_up_cooldown']:
            return False, "Scale-up cooldown active"
        
        # Maximum bereits erreicht
        if current.total_agents >= self.thresholds['max_agents']:
            return False, f"Maximum agents ({self.thresholds['max_agents']}) reached"
        
        # Kritische Bedingungen - sofortiges Scale-Up
        if severity == WorkloadSeverity.CRITICAL:
            return True, f"Critical workload: {severity.value}"
        
        # Hohe Last - Scale-Up empfohlen
        if severity in [WorkloadSeverity.VERY_HIGH, WorkloadSeverity.HIGH]:
            reasons = []
            if current.queue_length > self.thresholds['high_queue_length']:
                reasons.append(f"queue_length: {current.queue_length}")
            if current.average_wait_time > self.thresholds['high_wait_time']:
                reasons.append(f"wait_time: {current.average_wait_time:.1f}s")
            if current.system_cpu > self.thresholds['high_cpu_usage']:
                reasons.append(f"cpu: {current.system_cpu:.1f}%")
            
            if reasons:
                return True, f"High workload - {', '.join(reasons)}"
        
        return False, f"Workload manageable: {severity.value}"
    
    def should_scale_down(self) -> Tuple[bool, str]:
        """Prüft ob Scale-Down möglich ist"""
        current = self.get_current_metrics()
        if not current:
            return False, "No metrics available"
        
        severity = self.get_workload_severity()
        
        # Cooldown prüfen
        if time.time() - self.last_scale_action < self.thresholds['scale_down_cooldown']:
            return False, "Scale-down cooldown active"
        
        # Minimum bereits erreicht
        if current.total_agents <= self.thresholds['min_agents']:
            return False, f"Minimum agents ({self.thresholds['min_agents']}) reached"
        
        # Nur bei sehr niedriger Last scale down
        if severity not in [WorkloadSeverity.VERY_LOW, WorkloadSeverity.LOW]:
            return False, f"Workload too high for scale-down: {severity.value}"
        
        # Zusätzliche Checks für sicheres Scale-Down
        if (current.queue_length == 0 and 
            current.idle_agents >= current.total_agents * 0.7 and
            current.system_cpu < 40.0 and
            current.throughput < 0.1):  # Sehr niedrige Aktivität
            
            # Prüfe ob genug idle Agents für längere Zeit
            idle_history = [
                m.idle_agents for m in list(self.system_history)[-5:]  # Letzte 5 Messungen
                if m.idle_agents >= m.total_agents * 0.7
            ]
            
            if len(idle_history) >= 3:  # Mindestens 3 von 5 Messungen
                return True, f"Low workload sustained: {severity.value}, {current.idle_agents} idle agents"
        
        return False, f"Not safe to scale down: active_agents={current.active_agents}, queue={current.queue_length}"
    
    def record_scale_action(self, action: str, from_count: int, to_count: int, reason: str):
        """Registriert eine Scaling-Aktion"""
        self.last_scale_action = time.time()
        scale_event = {
            'timestamp': self.last_scale_action,
            'action': action,
            'from_count': from_count,
            'to_count': to_count,
            'reason': reason
        }
        self.scale_history.append(scale_event)
        logger.info(f"🔄 Scale {action}: {from_count} → {to_count} agents ({reason})")
    
    def get_scaling_recommendations(self) -> Dict[str, Any]:
        """Gibt Scaling-Empfehlungen zurück"""
        current = self.get_current_metrics()
        if not current:
            return {"error": "No metrics available"}
        
        severity = self.get_workload_severity()
        scale_up, scale_up_reason = self.should_scale_up()
        scale_down, scale_down_reason = self.should_scale_down()
        
        # Empfohlene Agent-Anzahl basierend auf verschiedenen Faktoren
        recommended_count = current.total_agents
        
        if scale_up:
            # Aggressive Scaling bei kritischer Last
            if severity == WorkloadSeverity.CRITICAL:
                recommended_count = min(current.total_agents * 2, self.thresholds['max_agents'])
            elif severity == WorkloadSeverity.VERY_HIGH:
                recommended_count = min(current.total_agents + 3, self.thresholds['max_agents'])
            else:  # HIGH
                recommended_count = min(current.total_agents + 1, self.thresholds['max_agents'])
        
        elif scale_down:
            # Konservativer Scale-Down
            recommended_count = max(current.total_agents - 1, self.thresholds['min_agents'])
        
        return {
            'current_agents': current.total_agents,
            'recommended_agents': recommended_count,
            'workload_severity': severity.value,
            'should_scale_up': scale_up,
            'should_scale_down': scale_down,
            'scale_up_reason': scale_up_reason,
            'scale_down_reason': scale_down_reason,
            'current_metrics': {
                'queue_length': current.queue_length,
                'avg_wait_time': current.average_wait_time,
                'active_agents': current.active_agents,
                'idle_agents': current.idle_agents,
                'system_cpu': current.system_cpu,
                'throughput': current.throughput,
                'error_rate': current.error_rate
            },
            'last_scale_action': self.last_scale_action,
            'cooldown_remaining': max(0, self.thresholds['scale_up_cooldown'] - (time.time() - self.last_scale_action))
        }
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Gibt detaillierte Statistiken zurück"""
        with self.lock:
            current = self.get_current_metrics()
            if not current:
                return {}
            
            # Task-Statistiken
            all_tasks = list(self.task_metrics.values())
            completed_tasks = [t for t in all_tasks if t.status == "completed"]
            
            # Agent-Statistiken
            agent_stats = {}
            for agent_id, agent in self.agent_metrics.items():
                agent_stats[agent_id] = {
                    'role': agent.role,
                    'status': agent.status,
                    'tasks_completed': agent.tasks_completed,
                    'success_rate': agent.success_rate,
                    'avg_response_time': agent.average_response_time,
                    'idle_time': agent.idle_time,
                    'cpu_usage': agent.cpu_usage,
                    'memory_usage': agent.memory_usage
                }
            
            return {
                'system_metrics': current,
                'workload_severity': self.get_workload_severity().value,
                'scaling_recommendations': self.get_scaling_recommendations(),
                'agent_stats': agent_stats,
                'task_summary': {
                    'total_tasks': len(all_tasks),
                    'completed_tasks': len(completed_tasks),
                    'success_rate': (len(completed_tasks) / len(all_tasks) * 100) if all_tasks else 0,
                    'avg_completion_time': statistics.mean([t.actual_duration for t in completed_tasks if t.actual_duration]) if completed_tasks else 0
                },
                'scale_history': list(self.scale_history)[-10:],  # Letzte 10 Scaling-Events
                'thresholds': self.thresholds
            }

# Globaler Metrics Collector (Singleton-Pattern)
_metrics_collector: Optional[WorkloadMetricsCollector] = None

def get_metrics_collector() -> WorkloadMetricsCollector:
    """Gibt den globalen Metrics Collector zurück (Singleton)"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = WorkloadMetricsCollector()
    return _metrics_collector