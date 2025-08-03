#!/usr/bin/env python3
"""
CLI Dashboard for Enhanced Ollama Flow Framework
Provides terminal-based monitoring and control interface
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

import psutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_main import EnhancedOllamaFlow
from neural_intelligence import NeuralIntelligenceEngine
from mcp_tools import MCPToolsManager
from monitoring_system import MonitoringSystem
from session_manager import SessionManager

logger = logging.getLogger(__name__)

class CLIDashboard:
    """Terminal-based dashboard for Ollama Flow Framework"""
    
    def __init__(self):
        self.framework: Optional[EnhancedOllamaFlow] = None
        self.neural_engine: Optional[NeuralIntelligenceEngine] = None
        self.mcp_tools: Optional[MCPToolsManager] = None
        self.monitoring_system: Optional[MonitoringSystem] = None
        self.session_manager: Optional[SessionManager] = None
        
        # Dashboard state
        self.current_view = "main"
        self.is_running = False
        self.current_task = None
        self.execution_thread = None
        self.update_interval = 1.0
        
        # Screen dimensions
        self.height = 0
        self.width = 0
        
        # Data storage
        self.system_metrics = {}
        self.recent_sessions = []
        self.neural_patterns = []
        self.log_entries = []
        self.performance_history = []
        
        # Colors
        self.colors = {
            'header': None,
            'success': None,
            'error': None,
            'warning': None,
            'info': None
        }
        
        # Initialize components
        asyncio.create_task(self._initialize_components())
    
    async def _initialize_components(self):
        """Initialize enhanced components"""
        try:
            self.neural_engine = NeuralIntelligenceEngine()
            await self.neural_engine.initialize()
            
            self.mcp_tools = MCPToolsManager()
            await self.mcp_tools.initialize()
            
            self.monitoring_system = MonitoringSystem()
            await self.monitoring_system.start_monitoring()
            
            self.session_manager = SessionManager()
            await self.session_manager.start_auto_save()
            
            self._add_log_entry("Enhanced components initialized", "success")
            
        except Exception as e:
            self._add_log_entry(f"Failed to initialize components: {e}", "error")
    
    def _setup_colors(self, stdscr):
        """Setup color pairs for the terminal"""
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)    # header
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # success
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)     # error
            curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # warning
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)   # info
            
            self.colors = {
                'header': curses.color_pair(1) | curses.A_BOLD,
                'success': curses.color_pair(2),
                'error': curses.color_pair(3),
                'warning': curses.color_pair(4),
                'info': curses.color_pair(5)
            }
    
    def _draw_header(self, stdscr, y: int) -> int:
        """Draw the dashboard header"""
        title = "🚀 OLLAMA FLOW DASHBOARD"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "RUNNING" if self.is_running else "IDLE"
        status_color = self.colors['success'] if self.is_running else self.colors['info']
        
        # Title
        stdscr.addstr(y, (self.width - len(title)) // 2, title, self.colors['header'])
        y += 1
        
        # Status line
        status_line = f"Status: {status} | Time: {timestamp}"
        stdscr.addstr(y, (self.width - len(status_line)) // 2, f"Status: ", self.colors['info'])
        stdscr.addstr(status, status_color)
        stdscr.addstr(f" | Time: {timestamp}", self.colors['info'])
        y += 2
        
        # Separator
        stdscr.addstr(y, 0, "=" * self.width, self.colors['header'])
        y += 1
        
        return y
    
    def _draw_system_metrics(self, stdscr, y: int) -> int:
        """Draw system performance metrics"""
        stdscr.addstr(y, 0, "SYSTEM METRICS", self.colors['header'])
        y += 1
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # CPU
            cpu_bar = self._create_progress_bar(cpu_percent, 50)
            stdscr.addstr(y, 0, f"CPU:    {cpu_percent:5.1f}% ", self.colors['info'])
            color = self.colors['error'] if cpu_percent > 80 else self.colors['warning'] if cpu_percent > 60 else self.colors['success']
            stdscr.addstr(cpu_bar, color)
            y += 1
            
            # Memory
            mem_bar = self._create_progress_bar(memory.percent, 50)
            stdscr.addstr(y, 0, f"Memory: {memory.percent:5.1f}% ", self.colors['info'])
            color = self.colors['error'] if memory.percent > 80 else self.colors['warning'] if memory.percent > 60 else self.colors['success']
            stdscr.addstr(mem_bar, color)
            y += 1
            
            # Disk
            disk_bar = self._create_progress_bar(disk.percent, 50)
            stdscr.addstr(y, 0, f"Disk:   {disk.percent:5.1f}% ", self.colors['info'])
            color = self.colors['error'] if disk.percent > 90 else self.colors['warning'] if disk.percent > 70 else self.colors['success']
            stdscr.addstr(disk_bar, color)
            y += 1
            
            # Store metrics for history
            self.performance_history.append({
                'timestamp': time.time(),
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': disk.percent
            })
            
            # Keep only last 60 entries (1 minute at 1 second intervals)
            if len(self.performance_history) > 60:
                self.performance_history.pop(0)
            
        except Exception as e:
            stdscr.addstr(y, 0, f"Error getting system metrics: {e}", self.colors['error'])
            y += 1
        
        return y + 1
    
    def _draw_current_task(self, stdscr, y: int) -> int:
        """Draw current task information"""
        stdscr.addstr(y, 0, "CURRENT TASK", self.colors['header'])
        y += 1
        
        if self.is_running and self.current_task:
            stdscr.addstr(y, 0, "Status: ", self.colors['info'])
            stdscr.addstr("EXECUTING", self.colors['success'])
            y += 1
            
            # Task description (wrap if too long)
            task_desc = self.current_task
            max_width = self.width - 12
            if len(task_desc) > max_width:
                task_desc = task_desc[:max_width-3] + "..."
            
            stdscr.addstr(y, 0, f"Task: {task_desc}", self.colors['info'])
            y += 1
            
            # Progress indicator
            progress_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            progress_char = progress_chars[int(time.time() * 2) % len(progress_chars)]
            stdscr.addstr(y, 0, f"Progress: {progress_char} Working...", self.colors['warning'])
            y += 1
            
        else:
            stdscr.addstr(y, 0, "Status: IDLE", self.colors['info'])
            y += 1
            stdscr.addstr(y, 0, "No task currently running", self.colors['info'])
            y += 1
        
        return y + 1
    
    def _draw_recent_sessions(self, stdscr, y: int) -> int:
        """Draw recent sessions"""
        stdscr.addstr(y, 0, "RECENT SESSIONS", self.colors['header'])
        y += 1
        
        if not self.recent_sessions:
            stdscr.addstr(y, 0, "No recent sessions", self.colors['info'])
            y += 1
        else:
            for i, session in enumerate(self.recent_sessions[:5]):  # Show last 5
                status_icon = {
                    'completed': '✓',
                    'failed': '✗',
                    'active': '●',
                    'paused': '⏸'
                }.get(session.get('status', 'unknown'), '?')
                
                status_color = {
                    'completed': self.colors['success'],
                    'failed': self.colors['error'],
                    'active': self.colors['warning'],
                    'paused': self.colors['info']
                }.get(session.get('status', 'unknown'), self.colors['info'])
                
                task_desc = session.get('task_description', 'Unknown task')
                if len(task_desc) > 40:
                    task_desc = task_desc[:37] + "..."
                
                stdscr.addstr(y, 0, f"{status_icon} ", status_color)
                stdscr.addstr(f"{task_desc} ", self.colors['info'])
                stdscr.addstr(f"({session.get('status', 'unknown')})", status_color)
                y += 1
        
        return y + 1
    
    def _draw_neural_insights(self, stdscr, y: int) -> int:
        """Draw neural intelligence insights"""
        stdscr.addstr(y, 0, "NEURAL INTELLIGENCE", self.colors['header'])
        y += 1
        
        if not self.neural_patterns:
            stdscr.addstr(y, 0, "No patterns learned yet", self.colors['info'])
            y += 1
        else:
            total_patterns = len(self.neural_patterns)
            avg_confidence = sum(p.get('confidence', 0) for p in self.neural_patterns) / total_patterns if total_patterns > 0 else 0
            
            stdscr.addstr(y, 0, f"Total Patterns: {total_patterns}", self.colors['info'])
            y += 1
            stdscr.addstr(y, 0, f"Avg Confidence: {avg_confidence:.2f}", self.colors['info'])
            y += 1
            
            # Show top 3 patterns
            sorted_patterns = sorted(self.neural_patterns, key=lambda x: x.get('confidence', 0), reverse=True)
            for pattern in sorted_patterns[:3]:
                pattern_type = pattern.get('pattern_type', 'unknown')
                confidence = pattern.get('confidence', 0)
                confidence_color = self.colors['success'] if confidence > 0.8 else self.colors['warning'] if confidence > 0.6 else self.colors['error']
                
                stdscr.addstr(y, 2, f"• {pattern_type}: ", self.colors['info'])
                stdscr.addstr(f"{confidence:.2f}", confidence_color)
                y += 1
        
        return y + 1
    
    def _draw_activity_log(self, stdscr, y: int) -> int:
        """Draw activity log"""
        available_height = self.height - y - 3  # Leave space for controls
        
        stdscr.addstr(y, 0, "ACTIVITY LOG", self.colors['header'])
        y += 1
        
        if not self.log_entries:
            stdscr.addstr(y, 0, "No recent activity", self.colors['info'])
            return y + 1
        
        # Show recent log entries
        display_entries = self.log_entries[-available_height:] if len(self.log_entries) > available_height else self.log_entries
        
        for entry in display_entries:
            if y >= self.height - 2:
                break
                
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            message = entry['message']
            log_type = entry['type']
            
            # Truncate message if too long
            max_msg_width = self.width - 12
            if len(message) > max_msg_width:
                message = message[:max_msg_width-3] + "..."
            
            color = self.colors.get(log_type, self.colors['info'])
            stdscr.addstr(y, 0, f"[{timestamp}] {message}", color)
            y += 1
        
        return y
    
    def _draw_controls(self, stdscr, y: int) -> int:
        """Draw control instructions"""
        controls = [
            "Controls: [Q]uit | [R]un Task | [S]top Task | [C]leanup | [V]iew Sessions | [N]eural Patterns"
        ]
        
        # Position at bottom of screen
        control_y = self.height - len(controls) - 1
        
        for i, control in enumerate(controls):
            if control_y + i < self.height:
                stdscr.addstr(control_y + i, 0, control, self.colors['header'])
        
        return control_y
    
    def _create_progress_bar(self, percentage: float, width: int) -> str:
        """Create a text-based progress bar"""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:5.1f}%"
    
    def _add_log_entry(self, message: str, log_type: str = "info"):
        """Add entry to activity log"""
        self.log_entries.append({
            'timestamp': datetime.now(),
            'message': message,
            'type': log_type
        })
        
        # Keep only last 100 entries
        if len(self.log_entries) > 100:
            self.log_entries.pop(0)
    
    async def _update_data(self):
        """Update dashboard data"""
        try:
            # Update recent sessions
            if self.session_manager:
                sessions = await self.session_manager.list_sessions(limit=10)
                self.recent_sessions = [
                    {
                        'session_id': s.session_id,
                        'task_description': s.task_description,
                        'status': s.status,
                        'created_at': s.created_at
                    }
                    for s in sessions
                ]
            
            # Update neural patterns
            if self.neural_engine:
                patterns = await self.neural_engine.get_all_patterns()
                self.neural_patterns = [
                    {
                        'pattern_type': p.pattern_type,
                        'confidence': p.confidence,
                        'success_rate': p.success_rate,
                        'usage_count': p.usage_count
                    }
                    for p in patterns[:10]  # Top 10 patterns
                ]
                
        except Exception as e:
            self._add_log_entry(f"Error updating data: {e}", "error")
    
    def _execute_task_background(self, task: str, workers: int = 4, architecture: str = "HIERARCHICAL"):
        """Execute task in background thread"""
        try:
            self.is_running = True
            self.current_task = task
            self._add_log_entry(f"Starting task: {task[:50]}...", "info")
            
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create and configure framework
            self.framework = EnhancedOllamaFlow()
            self.framework.config = {
                'worker_count': workers,
                'architecture_type': architecture,
                'model': 'codellama:7b',
                'secure_mode': True,
                'project_folder': None,
                'parallel_llm': True,
                'metrics_enabled': True,
                'benchmark_mode': True,
                'db_path': 'ollama_flow_messages.db',
                'log_level': 'INFO'
            }
            
            # Execute task
            success = loop.run_until_complete(self.framework.run_single_task(task))
            
            if success:
                self._add_log_entry("Task completed successfully", "success")
            else:
                self._add_log_entry("Task failed", "error")
            
            loop.close()
            
        except Exception as e:
            self._add_log_entry(f"Task execution error: {e}", "error")
        finally:
            self.is_running = False
            self.current_task = None
    
    def _handle_input(self, stdscr):
        """Handle user input"""
        try:
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                return False  # Quit
            
            elif key == ord('r') or key == ord('R'):
                if not self.is_running:
                    # Simple task input (in real implementation, you'd want a proper input dialog)
                    task = "Create a simple Python web scraper for news articles"
                    self.execution_thread = threading.Thread(
                        target=self._execute_task_background,
                        args=(task,)
                    )
                    self.execution_thread.start()
                    self._add_log_entry("Task execution started", "info")
                else:
                    self._add_log_entry("Task already running", "warning")
            
            elif key == ord('s') or key == ord('S'):
                if self.is_running and self.framework:
                    # Stop current task
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.framework.stop_all_agents())
                    loop.close()
                    self._add_log_entry("Task stop requested", "warning")
                else:
                    self._add_log_entry("No task to stop", "info")
            
            elif key == ord('c') or key == ord('C'):
                # Cleanup
                if self.framework:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(self.framework.cleanup_database_and_files())
                    loop.close()
                    
                    if success:
                        self._add_log_entry("Cleanup completed", "success")
                    else:
                        self._add_log_entry("Cleanup failed", "error")
                else:
                    self._add_log_entry("No framework to cleanup", "info")
            
            elif key == ord('v') or key == ord('V'):
                self.current_view = "sessions"
                self._add_log_entry("Switched to sessions view", "info")
            
            elif key == ord('n') or key == ord('N'):
                self.current_view = "neural"
                self._add_log_entry("Switched to neural patterns view", "info")
            
            elif key == ord('m') or key == ord('M'):
                self.current_view = "main"
                self._add_log_entry("Switched to main view", "info")
        
        except Exception as e:
            self._add_log_entry(f"Input handling error: {e}", "error")
        
        return True  # Continue running
    
    async def _main_loop(self, stdscr):
        """Main dashboard loop"""
        # Setup
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(100) # 100ms timeout for input
        
        self._setup_colors(stdscr)
        
        last_update = 0
        
        while True:
            try:
                current_time = time.time()
                
                # Update screen dimensions
                self.height, self.width = stdscr.getmaxyx()
                
                # Clear screen
                stdscr.clear()
                
                # Update data periodically
                if current_time - last_update > self.update_interval:
                    await self._update_data()
                    last_update = current_time
                
                # Draw dashboard
                y = 0
                y = self._draw_header(stdscr, y)
                
                if self.current_view == "main":
                    y = self._draw_system_metrics(stdscr, y)
                    y = self._draw_current_task(stdscr, y)
                    y = self._draw_recent_sessions(stdscr, y)
                    y = self._draw_neural_insights(stdscr, y)
                
                y = self._draw_activity_log(stdscr, y)
                self._draw_controls(stdscr, y)
                
                # Handle input
                if not self._handle_input(stdscr):
                    break
                
                # Refresh screen
                stdscr.refresh()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except curses.error:
                # Handle terminal resize or other curses errors
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._add_log_entry(f"Main loop error: {e}", "error")
                await asyncio.sleep(1)
    
    async def run(self):
        """Run the CLI dashboard"""
        self._add_log_entry("Starting Ollama Flow CLI Dashboard", "info")
        
        try:
            await curses.wrapper(self._main_loop)
        except KeyboardInterrupt:
            self._add_log_entry("Dashboard interrupted by user", "info")
        except Exception as e:
            self._add_log_entry(f"Dashboard error: {e}", "error")
        finally:
            # Cleanup
            if self.monitoring_system:
                await self.monitoring_system.stop_monitoring()
            if self.session_manager:
                await self.session_manager.stop_auto_save()
            
            print("\n👋 Ollama Flow CLI Dashboard stopped")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Flow CLI Dashboard")
    parser.add_argument("--update-interval", type=float, default=1.0, 
                       help="Update interval in seconds")
    
    args = parser.parse_args()
    
    # Create and run dashboard
    dashboard = CLIDashboard()
    dashboard.update_interval = args.update_interval
    
    await dashboard.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")