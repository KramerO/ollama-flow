#!/usr/bin/env python3
"""
Enhanced CLI Dashboard for Ollama Flow Framework
Real-time monitoring of tasks, system resources, and agent architecture
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

class EnhancedCLIDashboard:
    """Enhanced CLI Dashboard with real-time monitoring"""
    
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
        
        # Update intervals
        self.fast_update_interval = 1.0  # For system metrics
        self.slow_update_interval = 5.0  # For tasks and agents
        
        # Threading
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # Display settings
        self.max_log_lines = 100
        self.selected_item = 0
        self.scroll_offset = 0
        
    async def initialize(self):
        """Initialize dashboard components"""
        try:
            self.db_manager = MessageDBManager(self.db_path)
            await self.load_initial_data()
            logger.info("CLI Dashboard initialized successfully")
        except Exception as e:
            logger.error(f"Dashboard initialization failed: {e}")
            raise
    
    async def load_initial_data(self):
        """Load initial data from database and system"""
        try:
            # Load configuration
            self.config = await self.load_configuration()
            
            # Load current tasks
            await self.update_tasks()
            
            # Load agents information
            await self.update_agents()
            
            # Update system metrics
            self.update_system_metrics()
            
        except Exception as e:
            logger.error(f"Failed to load initial data: {e}")
    
    async def load_configuration(self) -> Dict[str, Any]:
        """Load system configuration"""
        config = {
            'model': os.getenv('OLLAMA_MODEL', 'phi3:mini'),
            'worker_count': int(os.getenv('OLLAMA_WORKER_COUNT', '4')),
            'architecture_type': os.getenv('OLLAMA_ARCHITECTURE_TYPE', 'HIERARCHICAL'),
            'secure_mode': os.getenv('OLLAMA_SECURE_MODE', '').lower() == 'true',
            'parallel_llm': os.getenv('OLLAMA_PARALLEL_LLM', '').lower() == 'true',
            'project_folder': os.getenv('OLLAMA_PROJECT_FOLDER', os.getcwd()),
            'db_path': self.db_path,
            'dashboard_version': 'v2.1.0',
            'features': ['auto-shutdown', 'web-dashboard', 'neural-intelligence', 'extended-formats']
        }
        self.architecture_type = config['architecture_type']
        return config
    
    async def update_tasks(self):
        """Update task information from database"""
        try:
            if not self.db_manager:
                return
                
            # Get messages from database to reconstruct task state
            try:
                messages = self.db_manager.get_recent_messages(limit=100)
            except AttributeError:
                # Fallback if method doesn't exist
                messages = []
            
            # Clear existing tasks
            self.tasks.clear()
            
            # Parse messages to extract task information  
            for msg in messages:
                if msg.message_type == "task":
                    task_id = f"task_{len(self.tasks)}"
                    self.tasks[task_id] = TaskInfo(
                        id=task_id,
                        content=msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                        status="active" if msg.timestamp > time.time() - 300 else "completed",
                        start_time=datetime.fromtimestamp(msg.timestamp),
                        estimated_duration=300  # 5 minutes default
                    )
                    
        except Exception as e:
            logger.error(f"Failed to update tasks: {e}")
    
    async def update_agents(self):
        """Update agent information"""
        try:
            # Clear existing agents
            self.agents.clear()
            
            # Add mock agents based on configuration
            worker_count = self.config.get('worker_count', 4)
            architecture = self.config.get('architecture_type', 'HIERARCHICAL')
            
            # Queen Agent
            self.agents['queen-1'] = AgentInfo(
                id='queen-1',
                name='Enhanced Queen',
                type='Queen',
                status='active',
                completed_tasks=len([t for t in self.tasks.values() if t.status == 'completed']),
                cpu_usage=psutil.cpu_percent() * 0.3,
                memory_usage=psutil.virtual_memory().percent * 0.2
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
                    name=f'Secure Worker {i+1}',
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
        """Start background update thread"""
        def update_loop():
            fast_last_update = 0
            slow_last_update = 0
            
            while not self.stop_event.is_set():
                current_time = time.time()
                
                # Fast updates (system metrics)
                if current_time - fast_last_update >= self.fast_update_interval:
                    self.update_system_metrics()
                    fast_last_update = current_time
                
                # Slow updates (tasks and agents)
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
                
                # Refresh display
                if self.stdscr:
                    try:
                        self.draw_dashboard()
                        self.stdscr.refresh()
                    except curses.error:
                        pass  # Ignore refresh errors
                
                time.sleep(0.1)  # Small sleep to prevent CPU spinning
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def run(self):
        """Run the CLI dashboard"""
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
        """Main dashboard loop with curses"""
        self.stdscr = stdscr
        self.running = True
        
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        self.setup_colors()
        
        # Start update thread
        self.start_update_thread()
        
        # Main loop
        while self.running:
            try:
                self.draw_dashboard()
                self.stdscr.refresh()
                
                # Handle input
                self.stdscr.timeout(100)  # 100ms timeout
                key = self.stdscr.getch()
                
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
        """Draw the main dashboard"""
        if not self.stdscr:
            return
            
        try:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
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
        title = "🚀 OLLAMA FLOW - Enhanced CLI Dashboard v2.1.0"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Center title
        title_x = max(0, (width - len(title)) // 2)
        self.stdscr.addstr(0, title_x, title, curses.color_pair(4) | curses.A_BOLD)
        
        # Timestamp on right
        timestamp_x = max(0, width - len(timestamp) - 1)
        self.stdscr.addstr(0, timestamp_x, timestamp, curses.color_pair(5))
        
        # Separator line
        self.stdscr.addstr(1, 0, "═" * width, curses.color_pair(4))
    
    def draw_navigation(self, width: int):
        """Draw navigation bar"""
        nav_items = [
            ("1", "Overview", DashboardState.OVERVIEW),
            ("2", "Tasks", DashboardState.TASKS),
            ("3", "Resources", DashboardState.RESOURCES),
            ("4", "Architecture", DashboardState.ARCHITECTURE),
            ("5", "Config", DashboardState.CONFIG),
            ("6", "Logs", DashboardState.LOGS)
        ]
        
        x = 2
        for key, name, state in nav_items:
            if state == self.current_state:
                attr = curses.color_pair(7) | curses.A_BOLD  # Selected
            else:
                attr = curses.color_pair(4)
            
            nav_text = f"[{key}] {name}"
            self.stdscr.addstr(2, x, nav_text, attr)
            x += len(nav_text) + 3
        
    def draw_overview(self, start_y: int, height: int, width: int):
        """Draw overview panel"""
        y = start_y
        
        # System status
        self.stdscr.addstr(y, 2, "📊 SYSTEM OVERVIEW", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Quick stats
        active_tasks = len([t for t in self.tasks.values() if t.status == 'active'])
        active_agents = len([a for a in self.agents.values() if a.status == 'active'])
        
        stats = [
            f"🔄 Active Tasks: {active_tasks}",
            f"🤖 Active Agents: {active_agents}",
            f"💾 Memory: {self.system_metrics.memory_percent:.1f}%",
            f"🖥️  CPU: {self.system_metrics.cpu_percent:.1f}%",
            f"🔧 Model: {self.config.get('model', 'N/A')}",
            f"🏗️  Architecture: {self.architecture_type}"
        ]
        
        # Draw stats in columns
        col1_x, col2_x = 4, width // 2
        for i, stat in enumerate(stats):
            x = col1_x if i % 2 == 0 else col2_x
            stat_y = y + i // 2
            
            if stat_y < start_y + height - 2:
                color = curses.color_pair(1) if "Active" in stat else curses.color_pair(5)
                self.stdscr.addstr(stat_y, x, stat, color)
        
        # Architecture visualization (mini)
        y += len(stats) // 2 + 3
        if y < start_y + height - 5:
            self.stdscr.addstr(y, 2, "🏗️ ARCHITECTURE PREVIEW", curses.color_pair(4) | curses.A_BOLD)
            y += 1
            self.draw_mini_architecture(y, start_y + height - 2, width)
    
    def draw_tasks(self, start_y: int, height: int, width: int):
        """Draw tasks panel"""
        y = start_y
        
        self.stdscr.addstr(y, 2, f"📋 ACTIVE TASKS ({len(self.tasks)})", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        if not self.tasks:
            self.stdscr.addstr(y, 4, "No active tasks", curses.color_pair(3))
            return
        
        # Table headers
        headers = ["ID", "Status", "Content", "Worker", "Progress", "Duration"]
        col_widths = [8, 10, max(30, width - 60), 12, 10, 10]
        
        x = 2
        for i, (header, col_width) in enumerate(zip(headers, col_widths)):
            self.stdscr.addstr(y, x, header.ljust(col_width), curses.color_pair(4) | curses.A_UNDERLINE)
            x += col_width + 1
        y += 1
        
        # Task rows
        for i, (task_id, task) in enumerate(self.tasks.items()):
            if y >= start_y + height - 1:
                break
                
            # Status color
            if task.status == 'active':
                status_color = curses.color_pair(1)
            elif task.status == 'completed':
                status_color = curses.color_pair(1)
            elif task.status == 'failed':
                status_color = curses.color_pair(2)
            else:
                status_color = curses.color_pair(3)
            
            # Draw row
            x = 2
            row_data = [
                task_id[:7],
                task.status,
                task.content,
                task.assigned_worker or "None",
                f"{task.progress:.0f}%",
                f"{task.estimated_duration}s"
            ]
            
            for j, (data, col_width) in enumerate(zip(row_data, col_widths)):
                text = str(data)[:col_width].ljust(col_width)
                color = status_color if j == 1 else curses.color_pair(0)
                self.stdscr.addstr(y, x, text, color)
                x += col_width + 1
            
            y += 1
    
    def draw_resources(self, start_y: int, height: int, width: int):
        """Draw system resources panel"""
        y = start_y
        
        self.stdscr.addstr(y, 2, "💻 SYSTEM RESOURCES", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # CPU Usage
        cpu_bar = self.create_progress_bar(self.system_metrics.cpu_percent, 40)
        cpu_color = self.get_usage_color(self.system_metrics.cpu_percent)
        self.stdscr.addstr(y, 4, f"CPU Usage: {self.system_metrics.cpu_percent:5.1f}% ", curses.color_pair(0))
        self.stdscr.addstr(y, 25, cpu_bar, cpu_color)
        y += 1
        
        # Memory Usage
        mem_bar = self.create_progress_bar(self.system_metrics.memory_percent, 40)
        mem_color = self.get_usage_color(self.system_metrics.memory_percent)
        self.stdscr.addstr(y, 4, f"Memory:    {self.system_metrics.memory_percent:5.1f}% ", curses.color_pair(0))
        self.stdscr.addstr(y, 25, mem_bar, mem_color)
        y += 1
        
        # Disk Usage
        disk_bar = self.create_progress_bar(self.system_metrics.disk_percent, 40)
        disk_color = self.get_usage_color(self.system_metrics.disk_percent)
        self.stdscr.addstr(y, 4, f"Disk:      {self.system_metrics.disk_percent:5.1f}% ", curses.color_pair(0))
        self.stdscr.addstr(y, 25, disk_bar, disk_color)
        y += 2
        
        # Process Information
        self.stdscr.addstr(y, 4, f"Active Processes: {self.system_metrics.active_processes}", curses.color_pair(5))
        y += 1
        self.stdscr.addstr(y, 4, f"Ollama Processes: {self.system_metrics.ollama_processes}", curses.color_pair(5))
        y += 2
        
        # Network I/O
        if self.system_metrics.network_io:
            self.stdscr.addstr(y, 4, "Network I/O:", curses.color_pair(4) | curses.A_BOLD)
            y += 1
            
            bytes_sent = self.format_bytes(self.system_metrics.network_io.get('bytes_sent', 0))
            bytes_recv = self.format_bytes(self.system_metrics.network_io.get('bytes_recv', 0))
            
            self.stdscr.addstr(y, 6, f"Sent:     {bytes_sent}", curses.color_pair(0))
            y += 1
            self.stdscr.addstr(y, 6, f"Received: {bytes_recv}", curses.color_pair(0))
            y += 2
        
        # Agent Resource Usage
        if self.agents:
            self.stdscr.addstr(y, 4, "Agent Resource Usage:", curses.color_pair(4) | curses.A_BOLD)
            y += 1
            
            for agent_id, agent in list(self.agents.items())[:5]:  # Show first 5 agents
                if y >= start_y + height - 1:
                    break
                agent_info = f"{agent.name[:15]:15} CPU: {agent.cpu_usage:4.1f}% MEM: {agent.memory_usage:4.1f}%"
                self.stdscr.addstr(y, 6, agent_info, curses.color_pair(5))
                y += 1
    
    def draw_architecture(self, start_y: int, height: int, width: int):
        """Draw interactive architecture visualization"""
        y = start_y
        
        self.stdscr.addstr(y, 2, f"🏗️ ARCHITECTURE: {self.architecture_type}", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        if self.architecture_type == "HIERARCHICAL":
            self.draw_hierarchical_architecture(y, start_y + height - 2, width)
        elif self.architecture_type == "CENTRALIZED":
            self.draw_centralized_architecture(y, start_y + height - 2, width)
        else:  # FULLY_CONNECTED
            self.draw_fully_connected_architecture(y, start_y + height - 2, width)
    
    def draw_hierarchical_architecture(self, start_y: int, end_y: int, width: int):
        """Draw hierarchical architecture visualization"""
        y = start_y
        center_x = width // 2
        
        # Queen Agent (top)
        queen = "👑 Enhanced Queen"
        self.stdscr.addstr(y, center_x - len(queen) // 2, queen, curses.color_pair(6) | curses.A_BOLD)
        y += 2
        
        # Connection lines to sub-queens
        for i in range(3):
            self.stdscr.addstr(y, center_x - 1 + i, "│", curses.color_pair(4))
        y += 1
        
        # Sub-Queen Agents
        sub_queen_positions = [center_x - 20, center_x + 10]
        for i, x_pos in enumerate(sub_queen_positions):
            if y < end_y - 8:
                sub_queen = f"👥 Sub Queen {chr(65+i)}"
                self.stdscr.addstr(y, x_pos, sub_queen, curses.color_pair(1) | curses.A_BOLD)
        y += 2
        
        # Connection lines to workers
        if y < end_y - 6:
            # Draw horizontal connecting line
            line_start = min(sub_queen_positions) + 5
            line_end = max(sub_queen_positions) + 5
            for x in range(line_start, line_end + 1):
                self.stdscr.addstr(y, x, "─", curses.color_pair(4))
            
            # Vertical drops to workers
            for x_pos in sub_queen_positions:
                self.stdscr.addstr(y, x_pos + 5, "┬", curses.color_pair(4))
            y += 1
            
            for x_pos in sub_queen_positions:
                self.stdscr.addstr(y, x_pos + 5, "│", curses.color_pair(4))
            y += 1
        
        # Worker Agents
        worker_count = self.config.get('worker_count', 4)
        workers_per_sub = worker_count // 2
        
        for i, x_pos in enumerate(sub_queen_positions):
            if y < end_y - 4:
                for j in range(workers_per_sub):
                    worker_y = y + j
                    if worker_y < end_y - 1:
                        worker_id = f"worker-{i * workers_per_sub + j + 1}"
                        agent = self.agents.get(worker_id)
                        
                        if agent and agent.status == 'active':
                            worker_text = f"🔧 {agent.name}"
                            color = curses.color_pair(1)
                        else:
                            worker_text = f"⭕ Worker {i * workers_per_sub + j + 1}"
                            color = curses.color_pair(3)
                        
                        self.stdscr.addstr(worker_y, x_pos - 5, worker_text, color)
        
        # Legend
        legend_y = end_y - 3
        if legend_y > start_y:
            self.stdscr.addstr(legend_y, 4, "Legend:", curses.color_pair(4) | curses.A_BOLD)
            self.stdscr.addstr(legend_y + 1, 4, "👑 Queen  👥 Sub-Queen  🔧 Active Worker  ⭕ Idle Worker", curses.color_pair(0))
    
    def draw_centralized_architecture(self, start_y: int, end_y: int, width: int):
        """Draw centralized architecture visualization"""
        y = start_y
        center_x = width // 2
        
        # Queen Agent (center)
        queen = "👑 Enhanced Queen"
        self.stdscr.addstr(y + 5, center_x - len(queen) // 2, queen, curses.color_pair(6) | curses.A_BOLD)
        
        # Worker Agents in circle around queen
        worker_count = self.config.get('worker_count', 4)
        radius = min(8, width // 6)
        
        for i in range(worker_count):
            if y + 10 < end_y:
                # Calculate position in circle
                import math
                angle = 2 * math.pi * i / worker_count
                x = int(center_x + radius * math.cos(angle))
                y_pos = int(start_y + 5 + radius * math.sin(angle))
                
                # Draw connection line
                # Simple line drawing (could be improved)
                if abs(x - center_x) > abs(y_pos - (start_y + 5)):
                    # More horizontal
                    step_x = 1 if x > center_x else -1
                    for line_x in range(center_x, x, step_x):
                        if 0 <= line_x < width and start_y <= y_pos < end_y:
                            self.stdscr.addstr(y_pos, line_x, "─", curses.color_pair(4))
                else:
                    # More vertical  
                    step_y = 1 if y_pos > start_y + 5 else -1
                    for line_y in range(start_y + 5, y_pos, step_y):
                        if 0 <= x < width and start_y <= line_y < end_y:
                            self.stdscr.addstr(line_y, x, "│", curses.color_pair(4))
                
                # Draw worker
                worker_id = f"worker-{i + 1}"
                agent = self.agents.get(worker_id)
                
                if agent and agent.status == 'active':
                    worker_text = f"🔧 W{i+1}"
                    color = curses.color_pair(1)
                else:
                    worker_text = f"⭕ W{i+1}"
                    color = curses.color_pair(3)
                
                if 0 <= x < width - 5 and start_y <= y_pos < end_y:
                    self.stdscr.addstr(y_pos, x, worker_text, color)
    
    def draw_fully_connected_architecture(self, start_y: int, end_y: int, width: int):
        """Draw fully connected architecture visualization"""
        y = start_y
        
        # Show mesh network representation
        self.stdscr.addstr(y, 4, "Mesh Network - All agents interconnected", curses.color_pair(5))
        y += 2
        
        # Draw network nodes
        worker_count = self.config.get('worker_count', 4)
        nodes_per_row = min(4, width // 15)
        
        for i in range(worker_count + 1):  # +1 for queen
            row = i // nodes_per_row
            col = i % nodes_per_row
            
            node_y = y + row * 3
            node_x = 6 + col * 15
            
            if node_y < end_y - 2 and node_x < width - 10:
                if i == 0:  # Queen
                    node_text = "👑 Queen"
                    color = curses.color_pair(6) | curses.A_BOLD
                else:
                    worker_id = f"worker-{i}"
                    agent = self.agents.get(worker_id)
                    
                    if agent and agent.status == 'active':
                        node_text = f"🔧 W{i}"
                        color = curses.color_pair(1)
                    else:
                        node_text = f"⭕ W{i}"
                        color = curses.color_pair(3)
                
                self.stdscr.addstr(node_y, node_x, node_text, color)
                
                # Draw connections to previous nodes (simplified)
                if i > 0:
                    prev_row = (i - 1) // nodes_per_row
                    prev_col = (i - 1) % nodes_per_row
                    prev_x = 6 + prev_col * 15
                    
                    if row == prev_row:  # Same row - horizontal line
                        for x in range(prev_x + 8, node_x):
                            if x < width - 1:
                                self.stdscr.addstr(node_y, x, "─", curses.color_pair(4))
    
    def draw_mini_architecture(self, start_y: int, end_y: int, width: int):
        """Draw a mini architecture preview for overview"""
        if self.architecture_type == "HIERARCHICAL":
            y = start_y
            # Simple hierarchical representation
            self.stdscr.addstr(y, 4, "👑", curses.color_pair(6))
            self.stdscr.addstr(y + 1, 2, "👥   👥", curses.color_pair(1))
            self.stdscr.addstr(y + 2, 2, "🔧 🔧 🔧 🔧", curses.color_pair(5))
        elif self.architecture_type == "CENTRALIZED":
            y = start_y
            self.stdscr.addstr(y, 6, "👑", curses.color_pair(6))
            self.stdscr.addstr(y + 1, 2, "🔧   🔧   🔧", curses.color_pair(5))
        else:  # FULLY_CONNECTED
            y = start_y
            self.stdscr.addstr(y, 4, "Mesh Network", curses.color_pair(5))
    
    def draw_config(self, start_y: int, height: int, width: int):
        """Draw configuration panel"""
        y = start_y
        
        self.stdscr.addstr(y, 2, "⚙️ CONFIGURATION", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Display configuration items
        config_items = [
            ("Model", self.config.get('model', 'N/A')),
            ("Worker Count", str(self.config.get('worker_count', 'N/A'))),
            ("Architecture", self.config.get('architecture_type', 'N/A')),
            ("Secure Mode", "✓" if self.config.get('secure_mode') else "✗"),
            ("Parallel LLM", "✓" if self.config.get('parallel_llm') else "✗"),
            ("Project Folder", self.config.get('project_folder', 'N/A')),
            ("Database Path", self.config.get('db_path', 'N/A')),
            ("Dashboard Version", self.config.get('dashboard_version', 'N/A')),
        ]
        
        max_key_length = max(len(key) for key, _ in config_items)
        
        for key, value in config_items:
            if y >= start_y + height - 1:
                break
            
            # Truncate long values
            display_value = str(value)
            max_value_length = width - max_key_length - 8
            if len(display_value) > max_value_length:
                display_value = display_value[:max_value_length-3] + "..."
            
            self.stdscr.addstr(y, 4, f"{key:>{max_key_length}}: ", curses.color_pair(4))
            self.stdscr.addstr(y, 4 + max_key_length + 2, display_value, curses.color_pair(0))
            y += 1
        
        # Features section
        y += 1
        if y < start_y + height - 5:
            self.stdscr.addstr(y, 4, "Features:", curses.color_pair(4) | curses.A_BOLD)
            y += 1
            
            features = self.config.get('features', [])
            for feature in features:
                if y >= start_y + height - 1:
                    break
                self.stdscr.addstr(y, 6, f"✓ {feature}", curses.color_pair(1))
                y += 1
    
    def draw_logs(self, start_y: int, height: int, width: int):
        """Draw logs panel"""
        y = start_y
        
        self.stdscr.addstr(y, 2, f"📄 SYSTEM LOGS (Last {self.max_log_lines})", curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Read recent log entries
        try:
            log_file = "ollama_flow_dashboard.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-self.max_log_lines:]
                    
                for i, line in enumerate(lines):
                    if y >= start_y + height - 1:
                        break
                    
                    # Truncate long lines
                    display_line = line.rstrip()
                    if len(display_line) > width - 4:
                        display_line = display_line[:width-7] + "..."
                    
                    # Color based on log level
                    if "ERROR" in line:
                        color = curses.color_pair(2)
                    elif "WARNING" in line:
                        color = curses.color_pair(3)
                    elif "INFO" in line:
                        color = curses.color_pair(1)
                    else:
                        color = curses.color_pair(0)
                    
                    self.stdscr.addstr(y, 4, display_line, color)
                    y += 1
            else:
                self.stdscr.addstr(y, 4, "No log file found", curses.color_pair(3))
                
        except Exception as e:
            self.stdscr.addstr(y, 4, f"Error reading logs: {e}", curses.color_pair(2))
    
    def draw_footer(self, y: int, width: int):
        """Draw footer with help information"""
        footer_text = "[1-6] Switch panels | [Q] Quit | [R] Refresh | [↑↓] Navigate"
        footer_x = max(0, (width - len(footer_text)) // 2)
        self.stdscr.addstr(y, 0, "═" * width, curses.color_pair(4))
        self.stdscr.addstr(y, footer_x, footer_text, curses.color_pair(5))
    
    def handle_key(self, key: int):
        """Handle keyboard input"""
        if key == ord('q') or key == ord('Q'):
            self.running = False
        elif key == ord('r') or key == ord('R'):
            # Force refresh
            pass
        elif key >= ord('1') and key <= ord('6'):
            # Switch panels
            panel_map = {
                ord('1'): DashboardState.OVERVIEW,
                ord('2'): DashboardState.TASKS,
                ord('3'): DashboardState.RESOURCES,
                ord('4'): DashboardState.ARCHITECTURE,
                ord('5'): DashboardState.CONFIG,
                ord('6'): DashboardState.LOGS
            }
            self.current_state = panel_map[key]
        elif key == curses.KEY_UP:
            self.selected_item = max(0, self.selected_item - 1)
        elif key == curses.KEY_DOWN:
            self.selected_item += 1
    
    def create_progress_bar(self, percentage: float, width: int) -> str:
        """Create a text-based progress bar"""
        filled = int(percentage * width / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:5.1f}%"
    
    def get_usage_color(self, percentage: float) -> int:
        """Get color based on usage percentage"""
        if percentage < 50:
            return curses.color_pair(1)  # Green
        elif percentage < 80:
            return curses.color_pair(3)  # Yellow
        else:
            return curses.color_pair(2)  # Red
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} PB"
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.stop_event.set()
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        if self.db_manager:
            self.db_manager.close()
        
        logger.info("CLI Dashboard cleanup completed")

async def main():
    """Main entry point for CLI dashboard"""
    try:
        dashboard = EnhancedCLIDashboard()
        await dashboard.initialize()
        dashboard.run()
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed by user")
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        logger.error(f"Dashboard error: {e}")

if __name__ == "__main__":
    asyncio.run(main())