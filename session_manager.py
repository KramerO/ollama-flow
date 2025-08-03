"""
Session Management and Persistence System for Ollama Flow Framework
Provides session handling, state persistence, and cross-session memory
"""

import asyncio
import json
import sqlite3
import uuid
import logging
import pickle
import gzip
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import os

logger = logging.getLogger(__name__)

@dataclass
class SessionState:
    """Session state data"""
    session_id: str
    user_id: Optional[str]
    created_at: str
    last_active: str
    status: str  # 'active', 'paused', 'completed', 'failed'
    task_description: str
    architecture_type: str
    worker_count: int
    model_name: str
    secure_mode: bool
    project_folder: Optional[str]
    agent_states: Dict[str, Any]
    execution_context: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    neural_insights: List[Dict[str, Any]]
    mcp_tool_usage: List[Dict[str, Any]]
    custom_data: Dict[str, Any]

@dataclass
class SessionSummary:
    """Session summary for quick overview"""
    session_id: str
    task_description: str
    status: str
    created_at: str
    duration_seconds: Optional[float]
    success_rate: Optional[float]
    agents_used: int
    tasks_completed: int
    neural_patterns_learned: int

class SessionStorage:
    """Handles session data persistence"""
    
    def __init__(self, db_path: str = "sessions.db", data_dir: str = "./session_data"):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize session database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                status TEXT NOT NULL,
                task_description TEXT NOT NULL,
                architecture_type TEXT NOT NULL,
                worker_count INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                secure_mode BOOLEAN NOT NULL,
                project_folder TEXT,
                duration_seconds REAL,
                success_rate REAL,
                agents_used INTEGER DEFAULT 0,
                tasks_completed INTEGER DEFAULT 0,
                neural_patterns_learned INTEGER DEFAULT 0,
                data_file_path TEXT,
                custom_metadata TEXT
            )
        """)
        
        # Session events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # Session metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_unit TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def save_session(self, session_state: SessionState) -> bool:
        """Save session state to storage"""
        try:
            # Save complex data to file
            data_file = self.data_dir / f"{session_state.session_id}.pkl.gz"
            complex_data = {
                'agent_states': session_state.agent_states,
                'execution_context': session_state.execution_context,
                'performance_metrics': session_state.performance_metrics,
                'neural_insights': session_state.neural_insights,
                'mcp_tool_usage': session_state.mcp_tool_usage,
                'custom_data': session_state.custom_data
            }
            
            with gzip.open(data_file, 'wb') as f:
                pickle.dump(complex_data, f)
            
            # Save metadata to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, created_at, last_active, status, task_description,
                 architecture_type, worker_count, model_name, secure_mode, project_folder,
                 data_file_path, custom_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_state.session_id,
                session_state.user_id,
                session_state.created_at,
                session_state.last_active,
                session_state.status,
                session_state.task_description,
                session_state.architecture_type,
                session_state.worker_count,
                session_state.model_name,
                session_state.secure_mode,
                session_state.project_folder,
                str(data_file),
                json.dumps({})  # Reserved for future metadata
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session_state.session_id}: {e}")
            return False
    
    async def load_session(self, session_id: str) -> Optional[SessionState]:
        """Load session state from storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, user_id, created_at, last_active, status, task_description,
                       architecture_type, worker_count, model_name, secure_mode, project_folder,
                       data_file_path
                FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Load complex data from file
            data_file = Path(row[11])
            complex_data = {}
            
            if data_file.exists():
                try:
                    with gzip.open(data_file, 'rb') as f:
                        complex_data = pickle.load(f)
                except Exception as e:
                    logger.warning(f"Could not load session data file: {e}")
            
            session_state = SessionState(
                session_id=row[0],
                user_id=row[1],
                created_at=row[2],
                last_active=row[3],
                status=row[4],
                task_description=row[5],
                architecture_type=row[6],
                worker_count=row[7],
                model_name=row[8],
                secure_mode=bool(row[9]),
                project_folder=row[10],
                agent_states=complex_data.get('agent_states', {}),
                execution_context=complex_data.get('execution_context', {}),
                performance_metrics=complex_data.get('performance_metrics', {}),
                neural_insights=complex_data.get('neural_insights', []),
                mcp_tool_usage=complex_data.get('mcp_tool_usage', []),
                custom_data=complex_data.get('custom_data', {})
            )
            
            conn.close()
            return session_state
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    async def list_sessions(self, user_id: Optional[str] = None, 
                           status: Optional[str] = None,
                           limit: int = 50) -> List[SessionSummary]:
        """List sessions with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT session_id, task_description, status, created_at, duration_seconds,
                       success_rate, agents_used, tasks_completed, neural_patterns_learned
                FROM sessions
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            sessions = []
            for row in cursor.fetchall():
                session = SessionSummary(
                    session_id=row[0],
                    task_description=row[1],
                    status=row[2],
                    created_at=row[3],
                    duration_seconds=row[4],
                    success_rate=row[5],
                    agents_used=row[6] or 0,
                    tasks_completed=row[7] or 0,
                    neural_patterns_learned=row[8] or 0
                )
                sessions.append(session)
            
            conn.close()
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and associated data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get data file path
            cursor.execute("SELECT data_file_path FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            
            # Delete from database
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM session_events WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM session_metrics WHERE session_id = ?", (session_id,))
            
            conn.commit()
            conn.close()
            
            # Delete data file
            if row and row[0]:
                data_file = Path(row[0])
                if data_file.exists():
                    data_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def log_event(self, session_id: str, event_type: str, event_data: Dict[str, Any]):
        """Log session event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO session_events (session_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                event_type,
                json.dumps(event_data),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging event for session {session_id}: {e}")
    
    async def record_metric(self, session_id: str, metric_name: str, 
                           metric_value: float, metric_unit: str = ""):
        """Record session metric"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO session_metrics (session_id, metric_name, metric_value, metric_unit, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                metric_name,
                metric_value,
                metric_unit,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording metric for session {session_id}: {e}")

class SessionManager:
    """Main session management coordinator"""
    
    def __init__(self, db_path: str = "sessions.db", data_dir: str = "./session_data"):
        self.storage = SessionStorage(db_path, data_dir)
        self.active_sessions: Dict[str, SessionState] = {}
        self.session_callbacks: Dict[str, List[callable]] = {}
        
        # Auto-save interval
        self.auto_save_task = None
        self.auto_save_interval = 300  # 5 minutes
    
    async def create_session(self, task_description: str, architecture_type: str = "HIERARCHICAL",
                           worker_count: int = 4, model_name: str = "codellama:7b",
                           secure_mode: bool = True, project_folder: Optional[str] = None,
                           user_id: Optional[str] = None) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        session_state = SessionState(
            session_id=session_id,
            user_id=user_id,
            created_at=current_time,
            last_active=current_time,
            status='active',
            task_description=task_description,
            architecture_type=architecture_type,
            worker_count=worker_count,
            model_name=model_name,
            secure_mode=secure_mode,
            project_folder=project_folder,
            agent_states={},
            execution_context={},
            performance_metrics={},
            neural_insights=[],
            mcp_tool_usage=[],
            custom_data={}
        )
        
        self.active_sessions[session_id] = session_state
        
        # Save initial state
        await self.storage.save_session(session_state)
        
        # Log creation event
        await self.storage.log_event(session_id, "session_created", {
            'task_description': task_description,
            'architecture_type': architecture_type,
            'worker_count': worker_count
        })
        
        logger.info(f"Created session {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session state"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from storage
        session_state = await self.storage.load_session(session_id)
        if session_state:
            self.active_sessions[session_id] = session_state
            
        return session_state
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session state"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_active = datetime.now().isoformat()
        
        # Save to storage
        await self.storage.save_session(session)
        
        # Log update event
        await self.storage.log_event(session_id, "session_updated", updates)
        
        return True
    
    async def close_session(self, session_id: str, status: str = 'completed') -> bool:
        """Close session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.status = status
        session.last_active = datetime.now().isoformat()
        
        # Calculate duration
        created_time = datetime.fromisoformat(session.created_at)
        closed_time = datetime.now()
        duration = (closed_time - created_time).total_seconds()
        
        # Update database with final metrics
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions SET status = ?, duration_seconds = ?, last_active = ?
            WHERE session_id = ?
        """, (status, duration, session.last_active, session_id))
        conn.commit()
        conn.close()
        
        # Save final state
        await self.storage.save_session(session)
        
        # Log closure event
        await self.storage.log_event(session_id, "session_closed", {
            'status': status,
            'duration_seconds': duration
        })
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Closed session {session_id} with status {status}")
        return True
    
    async def resume_session(self, session_id: str) -> bool:
        """Resume paused session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        if session.status != 'paused':
            logger.warning(f"Cannot resume session {session_id} with status {session.status}")
            return False
        
        session.status = 'active'
        session.last_active = datetime.now().isoformat()
        
        await self.storage.save_session(session)
        await self.storage.log_event(session_id, "session_resumed", {})
        
        logger.info(f"Resumed session {session_id}")
        return True
    
    async def pause_session(self, session_id: str) -> bool:
        """Pause active session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        if session.status != 'active':
            logger.warning(f"Cannot pause session {session_id} with status {session.status}")
            return False
        
        session.status = 'paused'
        session.last_active = datetime.now().isoformat()
        
        await self.storage.save_session(session)
        await self.storage.log_event(session_id, "session_paused", {})
        
        logger.info(f"Paused session {session_id}")
        return True
    
    async def add_agent_state(self, session_id: str, agent_id: str, agent_state: Dict[str, Any]):
        """Add agent state to session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.agent_states[agent_id] = agent_state
        session.last_active = datetime.now().isoformat()
        
        await self.storage.save_session(session)
        return True
    
    async def add_neural_insight(self, session_id: str, insight: Dict[str, Any]):
        """Add neural insight to session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        insight['timestamp'] = datetime.now().isoformat()
        session.neural_insights.append(insight)
        session.last_active = datetime.now().isoformat()
        
        await self.storage.save_session(session)
        return True
    
    async def add_mcp_usage(self, session_id: str, tool_usage: Dict[str, Any]):
        """Add MCP tool usage to session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        tool_usage['timestamp'] = datetime.now().isoformat()
        session.mcp_tool_usage.append(tool_usage)
        session.last_active = datetime.now().isoformat()
        
        await self.storage.save_session(session)
        return True
    
    async def record_performance_metric(self, session_id: str, metric_name: str, 
                                      metric_value: float, metric_unit: str = ""):
        """Record performance metric"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Store in session
        if 'metrics' not in session.performance_metrics:
            session.performance_metrics['metrics'] = {}
        
        session.performance_metrics['metrics'][metric_name] = {
            'value': metric_value,
            'unit': metric_unit,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in database
        await self.storage.record_metric(session_id, metric_name, metric_value, metric_unit)
        await self.storage.save_session(session)
        
        return True
    
    async def list_sessions(self, user_id: Optional[str] = None, 
                           status: Optional[str] = None) -> List[SessionSummary]:
        """List sessions"""
        return await self.storage.list_sessions(user_id, status)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return await self.storage.delete_session(session_id)
    
    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """Cleanup sessions older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        
        # Get old session IDs
        cursor.execute("""
            SELECT session_id FROM sessions 
            WHERE created_at < ? AND status IN ('completed', 'failed')
        """, (cutoff_str,))
        
        old_sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Delete old sessions
        deleted_count = 0
        for session_id in old_sessions:
            if await self.delete_session(session_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old sessions")
        return deleted_count
    
    async def start_auto_save(self):
        """Start automatic session saving"""
        if self.auto_save_task:
            return
        
        self.auto_save_task = asyncio.create_task(self._auto_save_loop())
        logger.info("Started auto-save for sessions")
    
    async def stop_auto_save(self):
        """Stop automatic session saving"""
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except asyncio.CancelledError:
                pass
            self.auto_save_task = None
        logger.info("Stopped auto-save for sessions")
    
    async def _auto_save_loop(self):
        """Auto-save loop"""
        while True:
            try:
                # Save all active sessions
                for session in self.active_sessions.values():
                    await self.storage.save_session(session)
                
                await asyncio.sleep(self.auto_save_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-save loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        
        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        # Sessions by status
        cursor.execute("SELECT status, COUNT(*) FROM sessions GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        # Average duration
        cursor.execute("SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL")
        avg_duration = cursor.fetchone()[0] or 0
        
        # Average success rate
        cursor.execute("SELECT AVG(success_rate) FROM sessions WHERE success_rate IS NOT NULL")
        avg_success_rate = cursor.fetchone()[0] or 0
        
        # Recent activity (last 24 hours)
        recent_cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE created_at > ?", (recent_cutoff,))
        recent_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': len(self.active_sessions),
            'status_distribution': status_counts,
            'average_duration_seconds': avg_duration,
            'average_success_rate': avg_success_rate,
            'recent_sessions_24h': recent_sessions,
            'statistics_generated_at': datetime.now().isoformat()
        }