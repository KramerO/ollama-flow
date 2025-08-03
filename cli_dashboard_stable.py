#!/usr/bin/env python3
"""
STABLE CLI Dashboard for Ollama Flow Framework
Optimized version that fixes flickering and addwstr() ERR errors
"""

import asyncio
import curses
import json
import logging
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import psutil
from db_manager import MessageDBManager
from agents.enhanced_queen_agent import EnhancedQueenAgent
from orchestrator.orchestrator import Orchestrator

# Configure logging to file only (no console output for dashboard)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ollama_flow_dashboard.log')]
)
logger = logging.getLogger(__name__)

class DashboardState(Enum):
    OVERVIEW = "overview"
    TASKS = "tasks" 
    RESOURCES = "resources"
    ARCHITECTURE = "architecture"
    CONFIG = "config"
    LOGS = "logs"

@dataclass
class TaskInfo:
    id: str
    content: str
    status: str
    assigned_worker: Optional[str] = None
    priority: str = "medium"
    progress: float = 0.0
    start_time: Optional[datetime] = None
    estimated_duration: int = 0
    dependencies: List[str] = field(default_factory=list)

@dataclass
class AgentInfo:
    id: str
    name: str
    type: str
    status: str
    current_task: Optional[str] = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    active_processes: int
    ollama_processes: int
    timestamp: datetime

class StableCLIDashboard:
    """Stable CLI Dashboard with optimized rendering to prevent flickering"""
    
    def __init__(self, db_path: str = "ollama_flow_messages.db"):
        self.db_path = db_path
        self.db_manager: Optional[MessageDBManager] = None
        self.current_state = DashboardState.OVERVIEW
        self.running = False
        self.stdscr = None
        
        # Dashboard data
        self.tasks: Dict[str, TaskInfo] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.system_metrics: SystemMetrics = SystemMetrics(0, 0, 0, {}, 0, 0, datetime.now())
        self.config: Dict[str, Any] = {}
        self.logs: List[str] = []
        self.architecture_type = "HIERARCHICAL"
        
        # Display optimization
        self.last_refresh = 0
        self.refresh_interval = 0.5  # Reduced refresh rate to prevent flickering
        self.terminal_size = (24, 80)  # Default terminal size
        
        # Update intervals
        self.fast_update_interval = 2.0  # Slower updates
        self.slow_update_interval = 10.0  # Much slower updates
        
        # Threading
        self.update_thread = None
        self.stop_event = threading.Event()
        
        print("📊 Stable CLI Dashboard initialized")
    
    def safe_addstr(self, y: int, x: int, text: str, attr=0, max_width: Optional[int] = None):
        """Safely add string to screen with bounds checking"""
        if not self.stdscr:
            return
            
        try:
            height, width = self.terminal_size
            
            # Bounds checking
            if y < 0 or y >= height - 1:
                return
            if x < 0 or x >= width - 1:
                return
                
            # Truncate text if too long
            if max_width:
                available_width = min(max_width, width - x - 1)
            else:
                available_width = width - x - 1
                
            if available_width <= 0:
                return
                
            # Remove unicode characters that might cause issues
            clean_text = self.clean_text(text)
            if len(clean_text) > available_width:
                clean_text = clean_text[:available_width-3] + "..."
            
            # Safe addstr call
            self.stdscr.addstr(y, x, clean_text, attr)
            
        except curses.error:
            # Ignore display errors silently
            pass
    
    def clean_text(self, text: str) -> str:
        """Clean text of problematic unicode characters"""
        # Replace problematic emojis with simple text
        replacements = {
            '👑': '[Q]',
            '👥': '[S]', 
            '🔧': '[W]',
            '⭕': '[I]',
            '📊': '[M]',
            '🏗️': '[A]',
            '⚙️': '[C]',
            '🚀': '[R]',
            '✅': '[OK]',
            '❌': '[X]',
            '⚠️': '[!]',
            '🔄': '[>]',
            '📋': '[L]',
            '💾': '[D]',
            '🎯': '[T]',
            '│': '|',
            '─': '-',
            '┬': '+',
            '└': '+',
            '├': '+',
            '┤': '+',
            '┐': '+',
            '┌': '+'
        }
        
        result = text
        for emoji, replacement in replacements.items():
            result = result.replace(emoji, replacement)
            
        return result
    
    async def initialize(self):
        """Initialize dashboard components"""
        try:
            print("🚀 Starting stable CLI dashboard...")
            print("📋 Features: Real-time monitoring, System resources, Task tracking")
            print("⌨️  Controls: [1-6] Switch panels | [Q] Quit | [R] Refresh")
            print("=" * 60)
            
            # Initialize database
            self.db_manager = MessageDBManager(self.db_path)
            
            # Load initial data
            await self.update_tasks()
            await self.update_agents()
            self.update_system_metrics()
            self.load_config()
            
            print("✅ Stable CLI Dashboard initialized successfully")
            print("🎯 Launching optimized dashboard interface...")
            
        except Exception as e:
            logger.error(f"Dashboard initialization failed: {e}")
            print(f"❌ Dashboard Error: {e}")
            raise
    
    def load_config(self):
        """Load configuration data"""
        try:
            self.config = {
                'worker_count': 4,
                'max_concurrent_tasks': 8,
                'auto_scaling': True,
                'resource_monitoring': True,
                'log_level': 'INFO',
                'architecture': 'HIERARCHICAL',
                'security_enabled': True,
                'neural_intelligence': True,
                'performance_tracking': True
            }
            
            # Try to load from file if exists
            config_path = 'ollama_flow_config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    async def update_tasks(self):
        """Update task information"""
        try:
            # Create sample tasks for demonstration
            sample_tasks = [
                ("analyze-codebase", "Analyze codebase patterns", "in_progress", 0.75),
                ("security-scan", "Run security vulnerability scan", "completed", 1.0),
                ("performance-test", "Execute performance benchmarks", "pending", 0.0),
                ("documentation", "Generate API documentation", "in_progress", 0.45),
                ("deployment", "Deploy to production", "pending", 0.0)
            ]
            
            self.tasks.clear()
            for i, (task_id, content, status, progress) in enumerate(sample_tasks):
                self.tasks[task_id] = TaskInfo(
                    id=task_id,
                    content=content,
                    status=status,
                    progress=progress,
                    priority="high" if i < 2 else "medium",
                    assigned_worker=f"worker-{(i % 4) + 1}" if status != "pending" else None,
                    start_time=datetime.now() - timedelta(minutes=i * 10)
                )
                
        except Exception as e:
            logger.error(f"Failed to update tasks: {e}")
    
    async def update_agents(self):
        """Update agent information"""
        try:
            worker_count = self.config.get('worker_count', 4)
            architecture = self.config.get('architecture', 'HIERARCHICAL')
            self.architecture_type = architecture
            
            self.agents.clear()
            
            # Enhanced Queen Agent
            self.agents['enhanced-queen'] = AgentInfo(
                id='enhanced-queen',
                name='Enhanced Queen',
                type='EnhancedQueen',
                status='active',
                completed_tasks=len(self.tasks),
                cpu_usage=psutil.cpu_percent() * 0.3,
                memory_usage=psutil.virtual_memory().percent * 0.25
            )
            
            # Sub-Queen Agents (for hierarchical)
            if architecture == 'HIERARCHICAL':
                for i in range(2):
                    self.agents[f'sub-queen-{i+1}'] = AgentInfo(
                        id=f'sub-queen-{i+1}',
                        name=f'Sub Queen {chr(65+i)}',
                        type='SubQueen',
                        status='active',
                        completed_tasks=len(self.tasks) // 3,
                        cpu_usage=psutil.cpu_percent() * 0.2,
                        memory_usage=psutil.virtual_memory().percent * 0.15
                    )
            
            # Worker Agents
            for i in range(worker_count):
                status = 'active' if i < len(self.tasks) else 'idle'
                current_task = list(self.tasks.keys())[i] if i < len(self.tasks) else None
                
                self.agents[f'worker-{i+1}'] = AgentInfo(
                    id=f'worker-{i+1}',
                    name=f'Worker {i+1}',
                    type='SecureWorker',
                    status=status,
                    current_task=current_task,
                    completed_tasks=max(0, len(self.tasks) - worker_count + i),
                    cpu_usage=psutil.cpu_percent() * 0.1 if status == 'active' else 0.0,
                    memory_usage=psutil.virtual_memory().percent * 0.1 if status == 'active' else 0.0
                )
                
        except Exception as e:
            logger.error(f"Failed to update agents: {e}")
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Count processes
            active_processes = len(psutil.pids())
            
            # Count Ollama processes
            ollama_processes = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'ollama' in cmdline.lower():
                        ollama_processes += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.system_metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=(disk.used / disk.total) * 100,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                active_processes=active_processes,
                ollama_processes=ollama_processes,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def start_update_thread(self):
        """Start background update thread with reduced frequency"""
        def update_loop():
            fast_last_update = 0
            slow_last_update = 0
            
            while not self.stop_event.is_set():
                current_time = time.time()
                
                # Fast updates (system metrics) - reduced frequency
                if current_time - fast_last_update >= self.fast_update_interval:
                    self.update_system_metrics()
                    fast_last_update = current_time
                
                # Slow updates (tasks and agents) - much reduced frequency
                if current_time - slow_last_update >= self.slow_update_interval:
                    try:
                        # Run async updates in sync context
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.update_tasks())
                        loop.run_until_complete(self.update_agents())
                        loop.close()
                    except Exception as e:
                        logger.error(f"Update loop error: {e}")
                    slow_last_update = current_time
                
                # Sleep longer to reduce CPU usage
                time.sleep(0.5)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def run(self):
        """Run the stable CLI dashboard"""
        try:
            # Initialize curses
            curses.wrapper(self._main_loop)
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            print(f"❌ Dashboard Error: {e}")
        finally:
            self.cleanup()
    
    def _main_loop(self, stdscr):
        """Main dashboard loop with optimized rendering"""
        self.stdscr = stdscr
        self.running = True
        
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        self.setup_colors()
        
        # Get terminal size
        self.terminal_size = stdscr.getmaxyx()
        
        # Start update thread
        self.start_update_thread()
        
        # Main loop with controlled refresh rate
        while self.running:
            try:
                current_time = time.time()
                
                # Only refresh if enough time has passed
                if current_time - self.last_refresh >= self.refresh_interval:
                    self.draw_dashboard()
                    stdscr.refresh()
                    self.last_refresh = current_time
                
                # Handle input with longer timeout
                stdscr.timeout(500)  # 500ms timeout
                key = stdscr.getch()
                
                if key != -1:  # Key pressed
                    self.handle_key(key)
                    
            except curses.error:
                continue
            except KeyboardInterrupt:
                break
    
    def setup_colors(self):
        """Setup color pairs for the dashboard"""
        try:
            # Basic colors
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success/Active
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # Error/Critical
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning/Pending
            curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Info/Headers
            curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Accent
            curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Special
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Selected
        except curses.error:
            pass  # Color not supported
    
    def draw_dashboard(self):
        """Draw the main dashboard with safe rendering"""
        if not self.stdscr:
            return
            
        try:
            self.stdscr.clear()
            height, width = self.terminal_size
            
            # Update terminal size if changed
            try:
                new_height, new_width = self.stdscr.getmaxyx()
                if (new_height, new_width) != self.terminal_size:
                    self.terminal_size = (new_height, new_width)
                    height, width = new_height, new_width
            except curses.error:
                pass
            
            # Draw header
            self.draw_header(width)
            
            # Draw navigation
            self.draw_navigation(width)
            
            # Draw main content based on state
            content_start_y = 4
            content_height = height - 6
            
            if self.current_state == DashboardState.OVERVIEW:
                self.draw_overview(content_start_y, content_height, width)
            elif self.current_state == DashboardState.TASKS:
                self.draw_tasks(content_start_y, content_height, width)
            elif self.current_state == DashboardState.RESOURCES:
                self.draw_resources(content_start_y, content_height, width)
            elif self.current_state == DashboardState.ARCHITECTURE:
                self.draw_architecture(content_start_y, content_height, width)
            elif self.current_state == DashboardState.CONFIG:
                self.draw_config(content_start_y, content_height, width)
            elif self.current_state == DashboardState.LOGS:
                self.draw_logs(content_start_y, content_height, width)
            
            # Draw footer
            self.draw_footer(height - 1, width)
            
        except curses.error as e:
            logger.error(f"Draw error: {e}")
    
    def draw_header(self, width: int):
        """Draw dashboard header"""
        title = "OLLAMA FLOW - Stable CLI Dashboard"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Center title
        title_x = max(0, (width - len(title)) // 2)
        self.safe_addstr(0, title_x, title, curses.color_pair(4) | curses.A_BOLD)
        
        # Right-align timestamp
        time_x = max(0, width - len(timestamp) - 2)
        self.safe_addstr(0, time_x, timestamp, curses.color_pair(5))
        
        # Draw separator line
        separator = "=" * min(width - 2, 60)
        self.safe_addstr(1, 1, separator, curses.color_pair(4))
    
    def draw_navigation(self, width: int):
        """Draw navigation bar"""
        nav_items = [
            f"[1] Overview{'*' if self.current_state == DashboardState.OVERVIEW else ''}",
            f"[2] Tasks{'*' if self.current_state == DashboardState.TASKS else ''}",
            f"[3] Resources{'*' if self.current_state == DashboardState.RESOURCES else ''}",
            f"[4] Architecture{'*' if self.current_state == DashboardState.ARCHITECTURE else ''}",
            f"[5] Config{'*' if self.current_state == DashboardState.CONFIG else ''}",
            f"[6] Logs{'*' if self.current_state == DashboardState.LOGS else ''}",
            "[Q] Quit",
            "[R] Refresh"
        ]
        
        nav_text = " | ".join(nav_items)
        if len(nav_text) > width - 4:
            nav_text = nav_text[:width-7] + "..."
        
        self.safe_addstr(2, 2, nav_text, curses.color_pair(5))
    
    def draw_overview(self, start_y: int, height: int, width: int):
        """Draw overview panel"""
        y = start_y
        
        # System overview
        self.safe_addstr(y, 2, "[M] SYSTEM OVERVIEW", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # System metrics summary
        cpu = self.system_metrics.cpu_percent
        memory = self.system_metrics.memory_percent
        disk = self.system_metrics.disk_percent
        
        self.safe_addstr(y, 4, f"CPU: {cpu:.1f}%", curses.color_pair(1 if cpu < 80 else 2))
        self.safe_addstr(y, 20, f"Memory: {memory:.1f}%", curses.color_pair(1 if memory < 80 else 2))
        self.safe_addstr(y, 40, f"Disk: {disk:.1f}%", curses.color_pair(1 if disk < 80 else 2))
        y += 2
        
        # Task summary
        completed = len([t for t in self.tasks.values() if t.status == 'completed'])
        in_progress = len([t for t in self.tasks.values() if t.status == 'in_progress'])
        pending = len([t for t in self.tasks.values() if t.status == 'pending'])
        
        self.safe_addstr(y, 2, f"[T] TASKS: {completed} completed, {in_progress} running, {pending} pending", curses.color_pair(4))
        y += 2
        
        # Agent summary
        active_agents = len([a for a in self.agents.values() if a.status == 'active'])
        total_agents = len(self.agents)
        
        self.safe_addstr(y, 2, f"[A] AGENTS: {active_agents}/{total_agents} active ({self.architecture_type})", curses.color_pair(4))
        y += 2
        
        # Mini architecture preview
        self.draw_mini_architecture(y, height - (y - start_y), width)
    
    def draw_mini_architecture(self, start_y: int, height: int, width: int):
        """Draw mini architecture visualization"""
        y = start_y
        
        self.safe_addstr(y, 2, f"[A] ARCHITECTURE: {self.architecture_type}", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        if self.architecture_type == "HIERARCHICAL":
            # Simple hierarchical view
            self.safe_addstr(y, 10, "[Q] Enhanced Queen", curses.color_pair(6))
            y += 1
            self.safe_addstr(y, 12, "|", curses.color_pair(4))
            y += 1
            self.safe_addstr(y, 6, "[S] Sub A", curses.color_pair(1))
            self.safe_addstr(y, 20, "[S] Sub B", curses.color_pair(1))
            y += 1
            self.safe_addstr(y, 2, "[W] [W] [W] [W]", curses.color_pair(5))
        else:
            # Simple centralized view
            self.safe_addstr(y + 1, 10, "[Q] Queen", curses.color_pair(6))
            self.safe_addstr(y, 2, "[W]", curses.color_pair(5))
            self.safe_addstr(y, 18, "[W]", curses.color_pair(5))
            self.safe_addstr(y + 2, 2, "[W]", curses.color_pair(5))
            self.safe_addstr(y + 2, 18, "[W]", curses.color_pair(5))
    
    def draw_tasks(self, start_y: int, height: int, width: int):
        """Draw tasks panel"""
        y = start_y
        
        self.safe_addstr(y, 2, "[T] ACTIVE TASKS", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Header
        self.safe_addstr(y, 2, "ID", curses.color_pair(4))
        self.safe_addstr(y, 18, "STATUS", curses.color_pair(4))
        self.safe_addstr(y, 30, "PROGRESS", curses.color_pair(4))
        self.safe_addstr(y, 45, "WORKER", curses.color_pair(4))
        y += 1
        
        self.safe_addstr(y, 2, "-" * min(60, width - 4), curses.color_pair(4))
        y += 1
        
        # Task list
        for task_id, task in list(self.tasks.items())[:height - 6]:
            if y >= start_y + height - 2:
                break
                
            # Status color
            if task.status == 'completed':
                color = curses.color_pair(1)
            elif task.status == 'in_progress':
                color = curses.color_pair(3)
            else:
                color = curses.color_pair(2)
            
            # Task info
            self.safe_addstr(y, 2, task_id[:15], color, 15)
            self.safe_addstr(y, 18, task.status[:10], color, 10)
            self.safe_addstr(y, 30, f"{task.progress:.1%}", color)
            self.safe_addstr(y, 45, task.assigned_worker or "None", color)
            y += 1
    
    def draw_resources(self, start_y: int, height: int, width: int):
        """Draw resources panel"""
        y = start_y
        
        self.safe_addstr(y, 2, "[M] SYSTEM RESOURCES", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # CPU
        cpu_percent = self.system_metrics.cpu_percent
        cpu_bar = self.create_progress_bar(cpu_percent, 30)
        color = curses.color_pair(1 if cpu_percent < 80 else 2)
        self.safe_addstr(y, 2, f"CPU:    {cpu_percent:5.1f}% {cpu_bar}", color)
        y += 2
        
        # Memory
        mem_percent = self.system_metrics.memory_percent
        mem_bar = self.create_progress_bar(mem_percent, 30)
        color = curses.color_pair(1 if mem_percent < 80 else 2)
        self.safe_addstr(y, 2, f"Memory: {mem_percent:5.1f}% {mem_bar}", color)
        y += 2
        
        # Disk
        disk_percent = self.system_metrics.disk_percent
        disk_bar = self.create_progress_bar(disk_percent, 30)
        color = curses.color_pair(1 if disk_percent < 80 else 2)
        self.safe_addstr(y, 2, f"Disk:   {disk_percent:5.1f}% {disk_bar}", color)
        y += 3
        
        # Process info
        self.safe_addstr(y, 2, f"Active Processes: {self.system_metrics.active_processes}", curses.color_pair(5))
        y += 1
        self.safe_addstr(y, 2, f"Ollama Processes: {self.system_metrics.ollama_processes}", curses.color_pair(5))
    
    def create_progress_bar(self, percent: float, width: int) -> str:
        """Create a simple text progress bar"""
        filled = int((percent / 100.0) * width)
        return "[" + "=" * filled + " " * (width - filled) + "]"
    
    def draw_architecture(self, start_y: int, height: int, width: int):
        """Draw architecture panel"""
        y = start_y
        
        self.safe_addstr(y, 2, f"[A] ARCHITECTURE: {self.architecture_type}", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Agent list
        self.safe_addstr(y, 2, "AGENT", curses.color_pair(4))
        self.safe_addstr(y, 20, "TYPE", curses.color_pair(4))
        self.safe_addstr(y, 35, "STATUS", curses.color_pair(4))
        self.safe_addstr(y, 50, "TASKS", curses.color_pair(4))
        y += 1
        
        self.safe_addstr(y, 2, "-" * min(60, width - 4), curses.color_pair(4))
        y += 1
        
        for agent_id, agent in list(self.agents.items())[:height - 6]:
            if y >= start_y + height - 2:
                break
                
            color = curses.color_pair(1 if agent.status == 'active' else 3)
            
            self.safe_addstr(y, 2, agent.name[:17], color, 17)
            self.safe_addstr(y, 20, agent.type[:13], color, 13)
            self.safe_addstr(y, 35, agent.status[:13], color, 13)
            self.safe_addstr(y, 50, str(agent.completed_tasks), color)
            y += 1
    
    def draw_config(self, start_y: int, height: int, width: int):
        """Draw configuration panel"""
        y = start_y
        
        self.safe_addstr(y, 2, "[C] CONFIGURATION", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        for key, value in list(self.config.items())[:height - 4]:
            if y >= start_y + height - 2:
                break
                
            self.safe_addstr(y, 2, f"{key}:", curses.color_pair(5))
            self.safe_addstr(y, 25, str(value), curses.color_pair(1))
            y += 1
    
    def draw_logs(self, start_y: int, height: int, width: int):
        """Draw logs panel"""
        y = start_y
        
        self.safe_addstr(y, 2, "[L] RECENT LOGS", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Sample log entries
        sample_logs = [
            "INFO: Dashboard started successfully",
            "INFO: System metrics updated",
            "INFO: Tasks synchronized",
            "INFO: Agents status updated",
            "INFO: Configuration loaded"
        ]
        
        for i, log in enumerate(sample_logs[:height - 4]):
            if y >= start_y + height - 2:
                break
                
            timestamp = (datetime.now() - timedelta(minutes=i)).strftime("%H:%M:%S")
            self.safe_addstr(y, 2, f"{timestamp} {log}", curses.color_pair(5), width - 4)
            y += 1
    
    def draw_footer(self, y: int, width: int):
        """Draw footer with status"""
        status = f"Stable Dashboard | Agents: {len(self.agents)} | Tasks: {len(self.tasks)} | Refresh: {self.refresh_interval}s"
        self.safe_addstr(y, 2, status, curses.color_pair(4), width - 4)
    
    def handle_key(self, key: int):
        """Handle keyboard input"""
        if key == ord('q') or key == ord('Q'):
            self.running = False
        elif key == ord('r') or key == ord('R'):
            # Force refresh
            self.last_refresh = 0
        elif key == ord('1'):
            self.current_state = DashboardState.OVERVIEW
        elif key == ord('2'):
            self.current_state = DashboardState.TASKS
        elif key == ord('3'):
            self.current_state = DashboardState.RESOURCES
        elif key == ord('4'):
            self.current_state = DashboardState.ARCHITECTURE
        elif key == ord('5'):
            self.current_state = DashboardState.CONFIG
        elif key == ord('6'):
            self.current_state = DashboardState.LOGS
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.stop_event:
            self.stop_event.set()
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
        
        logger.info("Dashboard cleaned up successfully")

# Usage function for external access
async def run_stable_dashboard():
    """Run the stable CLI dashboard"""
    dashboard = StableCLIDashboard()
    await dashboard.initialize()
    dashboard.run()

if __name__ == "__main__":
    asyncio.run(run_stable_dashboard())