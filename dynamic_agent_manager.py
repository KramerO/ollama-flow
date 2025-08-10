#!/usr/bin/env python3
"""
Dynamic Agent Manager für Ollama Flow
Verwaltet dynamische Erstellung und Terminierung von AI-Agents basierend auf Auto-Scaling
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from agents.drone_agent import DroneAgent, DroneRole
from agents.queen_agent import QueenAgent
from agents.sub_queen_agent import SubQueenAgent
from enhanced_db_manager import EnhancedDBManager
from orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class AgentLifecycleState(Enum):
    """Agent-Lebenszyklus-Zustand"""
    CREATING = "creating"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    ERROR = "error"

@dataclass
class AgentLifecycleInfo:
    """Informationen über Agent-Lebenszyklus"""
    agent_id: str
    role: DroneRole
    state: AgentLifecycleState
    created_at: float
    initialized_at: Optional[float] = None
    last_activity: Optional[float] = None
    termination_requested: Optional[float] = None
    terminated_at: Optional[float] = None
    error_message: Optional[str] = None
    creation_reason: str = ""
    termination_reason: str = ""
    
    @property
    def lifetime_seconds(self) -> float:
        """Lebensdauer des Agents in Sekunden"""
        end_time = self.terminated_at or time.time()
        return end_time - self.created_at
    
    @property
    def idle_time_seconds(self) -> float:
        """Idle-Zeit in Sekunden"""
        if self.state == AgentLifecycleState.IDLE and self.last_activity:
            return time.time() - self.last_activity
        return 0.0

class DynamicAgentManager:
    """Manager für dynamische Agent-Erstellung und -Verwaltung"""
    
    def __init__(self, 
                 orchestrator: Optional[Orchestrator] = None,
                 db_manager: Optional[EnhancedDBManager] = None):
        
        self.orchestrator = orchestrator
        self.db_manager = db_manager
        
        # Agent-Verwaltung
        self.active_agents: Dict[str, DroneAgent] = {}
        self.agent_lifecycle: Dict[str, AgentLifecycleInfo] = {}
        self.creation_queue: List[Dict[str, Any]] = []
        self.termination_queue: List[str] = []
        
        # Management-Tasks
        self.running = False
        self.manager_task: Optional[asyncio.Task] = None
        self.lifecycle_task: Optional[asyncio.Task] = None
        
        # Konfiguration
        self.config = {
            'max_agents': 16,
            'min_agents': 1,
            'agent_timeout_seconds': 300,  # 5 Minuten Timeout für Initialisierung
            'idle_timeout_seconds': 600,   # 10 Minuten Idle-Timeout
            'cleanup_interval_seconds': 60, # Cleanup alle 60 Sekunden
            'batch_creation_size': 3,       # Max gleichzeitige Agent-Erstellung
            'graceful_shutdown_timeout': 30, # Timeout für graceful shutdown
        }
        
        # Callbacks für Lifecycle-Events
        self.lifecycle_callbacks: Dict[AgentLifecycleState, List[Callable]] = {
            state: [] for state in AgentLifecycleState
        }
        
        # Statistiken
        self.stats = {
            'total_created': 0,
            'total_terminated': 0,
            'creation_failures': 0,
            'termination_failures': 0,
            'average_lifetime': 0.0,
            'current_active': 0
        }
        
        logger.info("🤖 Dynamic Agent Manager initialized")
    
    def set_orchestrator(self, orchestrator: Orchestrator):
        """Setzt den Orchestrator"""
        self.orchestrator = orchestrator
    
    def set_db_manager(self, db_manager: EnhancedDBManager):
        """Setzt den DB-Manager"""
        self.db_manager = db_manager
    
    def add_lifecycle_callback(self, state: AgentLifecycleState, callback: Callable):
        """Fügt Callback für Lifecycle-Event hinzu"""
        self.lifecycle_callbacks[state].append(callback)
    
    async def start(self):
        """Startet den Dynamic Agent Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Management-Tasks starten
        self.manager_task = asyncio.create_task(self._management_loop())
        self.lifecycle_task = asyncio.create_task(self._lifecycle_cleanup_loop())
        
        logger.info("🤖 Dynamic Agent Manager started")
    
    async def stop(self):
        """Stoppt den Dynamic Agent Manager"""
        self.running = False
        
        # Tasks stoppen
        if self.manager_task:
            self.manager_task.cancel()
            try:
                await self.manager_task
            except asyncio.CancelledError:
                pass
        
        if self.lifecycle_task:
            self.lifecycle_task.cancel()
            try:
                await self.lifecycle_task
            except asyncio.CancelledError:
                pass
        
        # Alle aktiven Agents graceful beenden
        await self._shutdown_all_agents()
        
        logger.info("🤖 Dynamic Agent Manager stopped")
    
    async def create_agent(self, role: DroneRole, model: str = "phi3:mini", 
                          reason: str = "auto-scaling") -> Optional[DroneAgent]:
        """Erstellt einen neuen Agent"""
        agent_id = f"drone_{role.value}_{uuid.uuid4().hex[:8]}"
        
        # Lifecycle-Info erstellen
        lifecycle_info = AgentLifecycleInfo(
            agent_id=agent_id,
            role=role,
            state=AgentLifecycleState.CREATING,
            created_at=time.time(),
            creation_reason=reason
        )
        
        self.agent_lifecycle[agent_id] = lifecycle_info
        await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.CREATING)
        
        try:
            # Agent erstellen
            agent = DroneAgent(
                agent_id=agent_id,
                name=f"Dynamic{role.value.title()}_{agent_id[-8:]}",
                role=role,
                model=model
            )
            
            # Agent konfigurieren
            if self.orchestrator:
                agent.set_orchestrator(self.orchestrator)
            
            if self.db_manager:
                agent.set_db_manager(self.db_manager)
            
            # Initialisierung
            lifecycle_info.state = AgentLifecycleState.INITIALIZING
            await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.INITIALIZING)
            
            # Agent in aktive Liste aufnehmen
            self.active_agents[agent_id] = agent
            
            # Initialisierung abgeschlossen
            lifecycle_info.state = AgentLifecycleState.ACTIVE
            lifecycle_info.initialized_at = time.time()
            lifecycle_info.last_activity = time.time()
            
            await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.ACTIVE)
            
            # Statistiken aktualisieren
            self.stats['total_created'] += 1
            self.stats['current_active'] = len(self.active_agents)
            
            logger.info(f"🤖 Created agent {agent_id} with role {role.value} (reason: {reason})")
            
            return agent
            
        except Exception as e:
            # Fehlerbehandlung
            lifecycle_info.state = AgentLifecycleState.ERROR
            lifecycle_info.error_message = str(e)
            
            await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.ERROR)
            
            self.stats['creation_failures'] += 1
            logger.error(f"Failed to create agent {agent_id}: {e}")
            
            return None
    
    async def terminate_agent(self, agent_id: str, reason: str = "auto-scaling") -> bool:
        """Terminiert einen Agent"""
        if agent_id not in self.active_agents:
            logger.warning(f"Agent {agent_id} not found for termination")
            return False
        
        lifecycle_info = self.agent_lifecycle.get(agent_id)
        if not lifecycle_info:
            logger.warning(f"No lifecycle info found for agent {agent_id}")
            return False
        
        try:
            # Termination markieren
            lifecycle_info.state = AgentLifecycleState.TERMINATING
            lifecycle_info.termination_requested = time.time()
            lifecycle_info.termination_reason = reason
            
            await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.TERMINATING)
            
            agent = self.active_agents[agent_id]
            
            # Graceful shutdown
            await self._graceful_agent_shutdown(agent)
            
            # Agent aus aktiver Liste entfernen
            del self.active_agents[agent_id]
            
            # Termination abgeschlossen
            lifecycle_info.state = AgentLifecycleState.TERMINATED
            lifecycle_info.terminated_at = time.time()
            
            await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.TERMINATED)
            
            # Statistiken aktualisieren
            self.stats['total_terminated'] += 1
            self.stats['current_active'] = len(self.active_agents)
            self._update_average_lifetime()
            
            logger.info(f"🤖 Terminated agent {agent_id} (reason: {reason})")
            
            return True
            
        except Exception as e:
            lifecycle_info.state = AgentLifecycleState.ERROR
            lifecycle_info.error_message = str(e)
            
            await self._notify_lifecycle_change(lifecycle_info, AgentLifecycleState.ERROR)
            
            self.stats['termination_failures'] += 1
            logger.error(f"Failed to terminate agent {agent_id}: {e}")
            
            return False
    
    async def _graceful_agent_shutdown(self, agent: DroneAgent):
        """Führt graceful shutdown eines Agents durch"""
        try:
            # Warte auf Abschluss aktueller Aufgaben (mit Timeout)
            shutdown_start = time.time()
            timeout = self.config['graceful_shutdown_timeout']
            
            while (hasattr(agent, 'is_busy') and agent.is_busy() and 
                   time.time() - shutdown_start < timeout):
                await asyncio.sleep(1)
            
            # Agent-spezifische Cleanup-Operationen
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
            
            # Polling-Task stoppen falls vorhanden
            if hasattr(agent, 'polling_task') and agent.polling_task:
                agent.polling_task.cancel()
                try:
                    await agent.polling_task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown of agent {agent.agent_id}: {e}")
    
    async def _management_loop(self):
        """Haupt-Management-Schleife"""
        while self.running:
            try:
                await self._process_creation_queue()
                await self._process_termination_queue()
                await asyncio.sleep(1)  # Kurzes Intervall für responsive Verarbeitung
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in management loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_creation_queue(self):
        """Verarbeitet Agent-Erstellung-Queue"""
        if not self.creation_queue:
            return
        
        # Batch-Processing
        batch_size = min(len(self.creation_queue), self.config['batch_creation_size'])
        batch = self.creation_queue[:batch_size]
        self.creation_queue = self.creation_queue[batch_size:]
        
        # Parallel erstellen
        creation_tasks = []
        for creation_request in batch:
            task = asyncio.create_task(
                self.create_agent(
                    creation_request['role'],
                    creation_request.get('model', 'phi3:mini'),
                    creation_request.get('reason', 'queued')
                )
            )
            creation_tasks.append(task)
        
        # Warten auf Abschluss
        await asyncio.gather(*creation_tasks, return_exceptions=True)
    
    async def _process_termination_queue(self):
        """Verarbeitet Agent-Termination-Queue"""
        if not self.termination_queue:
            return
        
        # Sequenzielle Terminierung (sicherer)
        agent_id = self.termination_queue.pop(0)
        await self.terminate_agent(agent_id, "queued_termination")
    
    async def _lifecycle_cleanup_loop(self):
        """Lifecycle-Cleanup und Monitoring"""
        while self.running:
            try:
                await self._cleanup_stale_agents()
                await self._update_agent_states()
                await asyncio.sleep(self.config['cleanup_interval_seconds'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lifecycle cleanup loop: {e}")
                await asyncio.sleep(self.config['cleanup_interval_seconds'])
    
    async def _cleanup_stale_agents(self):
        """Bereinigt stale/timeout Agents"""
        current_time = time.time()
        agents_to_terminate = []
        
        for agent_id, lifecycle_info in self.agent_lifecycle.items():
            # Timeout bei Initialisierung
            if (lifecycle_info.state == AgentLifecycleState.INITIALIZING and
                current_time - lifecycle_info.created_at > self.config['agent_timeout_seconds']):
                
                logger.warning(f"Agent {agent_id} initialization timeout, terminating")
                agents_to_terminate.append((agent_id, "initialization_timeout"))
            
            # Idle-Timeout
            elif (lifecycle_info.state == AgentLifecycleState.IDLE and
                  lifecycle_info.idle_time_seconds > self.config['idle_timeout_seconds']):
                
                logger.info(f"Agent {agent_id} idle timeout, terminating")
                agents_to_terminate.append((agent_id, "idle_timeout"))
        
        # Terminate stale agents
        for agent_id, reason in agents_to_terminate:
            await self.terminate_agent(agent_id, reason)
    
    async def _update_agent_states(self):
        """Aktualisiert Agent-Zustände"""
        for agent_id, agent in self.active_agents.items():
            lifecycle_info = self.agent_lifecycle.get(agent_id)
            if not lifecycle_info:
                continue
            
            # Heuristik für Agent-Status (vereinfacht)
            old_state = lifecycle_info.state
            new_state = self._determine_agent_state(agent, lifecycle_info)
            
            if old_state != new_state:
                lifecycle_info.state = new_state
                lifecycle_info.last_activity = time.time()
                await self._notify_lifecycle_change(lifecycle_info, new_state)
    
    def _determine_agent_state(self, agent: DroneAgent, 
                              lifecycle_info: AgentLifecycleInfo) -> AgentLifecycleState:
        """Bestimmt aktuellen Agent-Zustand (vereinfachte Heuristik)"""
        
        # Prüfe ob Agent busy ist (würde echte Implementation benötigen)
        if hasattr(agent, 'is_busy') and agent.is_busy():
            return AgentLifecycleState.BUSY
        
        # Prüfe letzte Aktivität
        if lifecycle_info.last_activity:
            idle_time = time.time() - lifecycle_info.last_activity
            if idle_time > 60:  # 1 Minute
                return AgentLifecycleState.IDLE
        
        return AgentLifecycleState.ACTIVE
    
    async def _notify_lifecycle_change(self, lifecycle_info: AgentLifecycleInfo, 
                                     new_state: AgentLifecycleState):
        """Benachrichtigt über Lifecycle-Änderungen"""
        callbacks = self.lifecycle_callbacks.get(new_state, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(lifecycle_info)
                else:
                    callback(lifecycle_info)
            except Exception as e:
                logger.error(f"Error in lifecycle callback for {new_state}: {e}")
    
    def _update_average_lifetime(self):
        """Aktualisiert durchschnittliche Agent-Lebensdauer"""
        terminated_agents = [
            info for info in self.agent_lifecycle.values()
            if info.state == AgentLifecycleState.TERMINATED
        ]
        
        if terminated_agents:
            total_lifetime = sum(agent.lifetime_seconds for agent in terminated_agents)
            self.stats['average_lifetime'] = total_lifetime / len(terminated_agents)
    
    async def _shutdown_all_agents(self):
        """Beendet alle aktiven Agents"""
        if not self.active_agents:
            return
        
        logger.info(f"🤖 Shutting down {len(self.active_agents)} active agents")
        
        shutdown_tasks = []
        for agent_id in list(self.active_agents.keys()):
            task = asyncio.create_task(self.terminate_agent(agent_id, "system_shutdown"))
            shutdown_tasks.append(task)
        
        # Warte auf alle Shutdowns
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        logger.info("🤖 All agents shut down")
    
    # Public API Methods
    
    def queue_agent_creation(self, role: DroneRole, model: str = "phi3:mini", 
                           reason: str = "auto-scaling"):
        """Fügt Agent-Erstellung zur Queue hinzu"""
        self.creation_queue.append({
            'role': role,
            'model': model,
            'reason': reason
        })
        logger.info(f"🤖 Queued agent creation: {role.value}")
    
    def queue_agent_termination(self, agent_id: str):
        """Fügt Agent-Termination zur Queue hinzu"""
        if agent_id in self.active_agents:
            self.termination_queue.append(agent_id)
            logger.info(f"🤖 Queued agent termination: {agent_id}")
    
    def get_agent_count(self) -> int:
        """Gibt aktuelle Agent-Anzahl zurück"""
        return len(self.active_agents)
    
    def get_agents_by_role(self, role: DroneRole) -> List[DroneAgent]:
        """Gibt Agents einer bestimmten Rolle zurück"""
        return [agent for agent in self.active_agents.values() if agent.role == role]
    
    def get_idle_agents(self) -> List[str]:
        """Gibt IDs der idle Agents zurück"""
        idle_agents = []
        for agent_id, lifecycle_info in self.agent_lifecycle.items():
            if lifecycle_info.state == AgentLifecycleState.IDLE:
                idle_agents.append(agent_id)
        return idle_agents
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Gibt detaillierten Status zurück"""
        role_distribution = {}
        state_distribution = {}
        
        for agent in self.active_agents.values():
            role = agent.role.value
            role_distribution[role] = role_distribution.get(role, 0) + 1
        
        for lifecycle_info in self.agent_lifecycle.values():
            state = lifecycle_info.state.value
            state_distribution[state] = state_distribution.get(state, 0) + 1
        
        return {
            'active_agents': len(self.active_agents),
            'total_managed_agents': len(self.agent_lifecycle),
            'creation_queue_size': len(self.creation_queue),
            'termination_queue_size': len(self.termination_queue),
            'role_distribution': role_distribution,
            'state_distribution': state_distribution,
            'statistics': self.stats,
            'config': self.config,
            'running': self.running,
            'recent_agents': [
                {
                    'agent_id': info.agent_id,
                    'role': info.role.value,
                    'state': info.state.value,
                    'lifetime_seconds': info.lifetime_seconds,
                    'creation_reason': info.creation_reason,
                    'termination_reason': info.termination_reason
                }
                for info in list(self.agent_lifecycle.values())[-10:]  # Letzte 10
            ]
        }
    
    # Callback Methods für Auto-Scaling Engine
    
    async def autoscaling_create_agent(self, role: DroneRole, model: str) -> Optional[DroneAgent]:
        """Callback für Auto-Scaling Engine - Agent erstellen"""
        return await self.create_agent(role, model, "auto_scaling")
    
    async def autoscaling_terminate_agent(self, agent: DroneAgent) -> bool:
        """Callback für Auto-Scaling Engine - Agent terminieren"""
        return await self.terminate_agent(agent.agent_id, "auto_scaling")
    
    def get_agents_for_termination(self, count: int) -> List[DroneAgent]:
        """Gibt Agents zurück die für Termination geeignet sind"""
        # Priorität: Idle agents zuerst
        candidates = []
        
        for agent_id, lifecycle_info in self.agent_lifecycle.items():
            if lifecycle_info.state == AgentLifecycleState.IDLE:
                agent = self.active_agents.get(agent_id)
                if agent:
                    candidates.append((agent, lifecycle_info.idle_time_seconds))
        
        # Sortiere nach Idle-Zeit (längste zuerst)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Nimm die ersten 'count' Agents
        return [agent for agent, _ in candidates[:count]]