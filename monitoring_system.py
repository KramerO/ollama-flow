"""
Advanced Monitoring and Analytics System for Ollama Flow Framework
Provides real-time monitoring, performance analytics, and system health tracking
"""

import asyncio
import json
import logging
import sqlite3
import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import os

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to collect"""
    PERFORMANCE = "performance"
    RESOURCE = "resource" 
    AGENT = "agent"
    SYSTEM = "system"
    NEURAL = "neural"
    SECURITY = "security"
    CUSTOM = "custom"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricDataPoint:
    """Single metric data point"""
    metric_name: str
    metric_type: MetricType
    value: Union[int, float, str, bool]
    timestamp: str
    tags: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """System alert"""
    alert_id: str
    alert_level: AlertLevel
    title: str
    description: str
    metric_name: str
    current_value: Any
    threshold: Any
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None

@dataclass 
class PerformanceReport:
    """Performance analysis report"""
    report_id: str
    report_type: str
    time_range: Dict[str, str]
    summary: Dict[str, Any]
    detailed_metrics: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: str

class MetricsCollector:
    """Collects various system and application metrics"""
    
    def __init__(self, collection_interval: int = 10):
        self.collection_interval = collection_interval
        self.metrics_buffer = deque(maxlen=1000)  # Keep last 1000 data points
        self.is_collecting = False
        self.collection_task = None
        self.custom_collectors: Dict[str, Callable] = {}
        
    def register_custom_collector(self, name: str, collector_func: Callable):
        """Register custom metric collector"""
        self.custom_collectors[name] = collector_func
        logger.info(f"Registered custom metric collector: {name}")
    
    async def start_collection(self):
        """Start metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """Main collection loop"""
        while self.is_collecting:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect performance metrics
                await self._collect_performance_metrics()
                
                # Collect custom metrics
                await self._collect_custom_metrics()
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        current_time = datetime.now().isoformat()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="cpu_usage",
            metric_type=MetricType.RESOURCE,
            value=cpu_percent,
            timestamp=current_time,
            tags={"resource": "cpu", "unit": "percent"},
            metadata={"cpu_count": psutil.cpu_count()}
        ))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="memory_usage",
            metric_type=MetricType.RESOURCE,
            value=memory.percent,
            timestamp=current_time,
            tags={"resource": "memory", "unit": "percent"},
            metadata={"total": memory.total, "available": memory.available}
        ))
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="disk_usage",
            metric_type=MetricType.RESOURCE,
            value=disk.percent,
            timestamp=current_time,
            tags={"resource": "disk", "unit": "percent"},
            metadata={"total": disk.total, "free": disk.free}
        ))
        
        # Network metrics
        network = psutil.net_io_counters()
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="network_bytes_sent",
            metric_type=MetricType.RESOURCE,
            value=network.bytes_sent,
            timestamp=current_time,
            tags={"resource": "network", "direction": "sent"},
            metadata={}
        ))
        
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="network_bytes_recv",
            metric_type=MetricType.RESOURCE,
            value=network.bytes_recv,
            timestamp=current_time,
            tags={"resource": "network", "direction": "received"},
            metadata={}
        ))
    
    async def _collect_performance_metrics(self):
        """Collect application performance metrics"""
        current_time = datetime.now().isoformat()
        
        # Process metrics
        current_process = psutil.Process()
        
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="process_memory_percent",
            metric_type=MetricType.PERFORMANCE,
            value=current_process.memory_percent(),
            timestamp=current_time,
            tags={"process": "ollama_flow", "metric": "memory"},
            metadata={"pid": current_process.pid}
        ))
        
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="process_cpu_percent",
            metric_type=MetricType.PERFORMANCE,
            value=current_process.cpu_percent(),
            timestamp=current_time,
            tags={"process": "ollama_flow", "metric": "cpu"},
            metadata={"pid": current_process.pid}
        ))
        
        # Thread count
        self.metrics_buffer.append(MetricDataPoint(
            metric_name="thread_count",
            metric_type=MetricType.PERFORMANCE,
            value=threading.active_count(),
            timestamp=current_time,
            tags={"process": "ollama_flow", "metric": "threads"},
            metadata={}
        ))
    
    async def _collect_custom_metrics(self):
        """Collect custom metrics from registered collectors"""
        for name, collector_func in self.custom_collectors.items():
            try:
                if asyncio.iscoroutinefunction(collector_func):
                    metrics = await collector_func()
                else:
                    metrics = collector_func()
                
                if isinstance(metrics, list):
                    self.metrics_buffer.extend(metrics)
                elif isinstance(metrics, MetricDataPoint):
                    self.metrics_buffer.append(metrics)
                    
            except Exception as e:
                logger.error(f"Error collecting custom metrics from {name}: {e}")
    
    def get_recent_metrics(self, metric_name: Optional[str] = None, 
                          limit: int = 100) -> List[MetricDataPoint]:
        """Get recent metrics"""
        if metric_name:
            return [m for m in list(self.metrics_buffer)[-limit:] if m.metric_name == metric_name]
        return list(self.metrics_buffer)[-limit:]

class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        
        self._init_database()
    
    def _init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                alert_level TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                current_value TEXT,
                threshold TEXT,
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TEXT
            )
        """)
        
        # Metrics history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_alert_rule(self, metric_name: str, condition: str, threshold: Any, 
                      alert_level: AlertLevel, title: str, description: str):
        """Add alert rule"""
        rule_id = f"{metric_name}_{condition}_{threshold}"
        self.alert_rules[rule_id] = {
            'metric_name': metric_name,
            'condition': condition,  # 'greater_than', 'less_than', 'equals'
            'threshold': threshold,
            'alert_level': alert_level,
            'title': title,
            'description': description
        }
        logger.info(f"Added alert rule: {rule_id}")
    
    def add_alert_handler(self, handler: Callable):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
    
    async def check_alerts(self, metrics: List[MetricDataPoint]):
        """Check metrics against alert rules"""
        for metric in metrics:
            await self._check_metric_against_rules(metric)
    
    async def _check_metric_against_rules(self, metric: MetricDataPoint):
        """Check single metric against all applicable rules"""
        for rule_id, rule in self.alert_rules.items():
            if rule['metric_name'] != metric.metric_name:
                continue
            
            condition_met = False
            condition = rule['condition']
            threshold = rule['threshold']
            
            try:
                if condition == 'greater_than' and float(metric.value) > float(threshold):
                    condition_met = True
                elif condition == 'less_than' and float(metric.value) < float(threshold):
                    condition_met = True
                elif condition == 'equals' and metric.value == threshold:
                    condition_met = True
            except (ValueError, TypeError):
                # Skip if values can't be compared
                continue
            
            if condition_met:
                await self._trigger_alert(rule_id, rule, metric)
            else:
                await self._resolve_alert(rule_id)
    
    async def _trigger_alert(self, rule_id: str, rule: Dict[str, Any], metric: MetricDataPoint):
        """Trigger an alert"""
        if rule_id in self.active_alerts:
            return  # Alert already active
        
        alert = Alert(
            alert_id=rule_id,
            alert_level=rule['alert_level'],
            title=rule['title'],
            description=rule['description'],
            metric_name=rule['metric_name'],
            current_value=metric.value,
            threshold=rule['threshold'],
            timestamp=metric.timestamp
        )
        
        self.active_alerts[rule_id] = alert
        
        # Store in database
        await self._store_alert(alert)
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        logger.warning(f"Alert triggered: {alert.title} - {alert.description}")
    
    async def _resolve_alert(self, rule_id: str):
        """Resolve an active alert"""
        if rule_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[rule_id]
        alert.resolved = True
        alert.resolved_at = datetime.now().isoformat()
        
        # Update in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts SET resolved = TRUE, resolved_at = ?
            WHERE alert_id = ?
        """, (alert.resolved_at, alert.alert_id))
        conn.commit()
        conn.close()
        
        del self.active_alerts[rule_id]
        logger.info(f"Alert resolved: {alert.title}")
    
    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO alerts 
            (alert_id, alert_level, title, description, metric_name, 
             current_value, threshold, timestamp, resolved, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.alert_id, alert.alert_level.value, alert.title, alert.description,
            alert.metric_name, str(alert.current_value), str(alert.threshold),
            alert.timestamp, alert.resolved, alert.resolved_at
        ))
        
        conn.commit()
        conn.close()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute("""
            SELECT alert_id, alert_level, title, description, metric_name,
                   current_value, threshold, timestamp, resolved, resolved_at
            FROM alerts 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (since_time,))
        
        alerts = []
        for row in cursor.fetchall():
            alert = Alert(
                alert_id=row[0],
                alert_level=AlertLevel(row[1]),
                title=row[2],
                description=row[3],
                metric_name=row[4],
                current_value=row[5],
                threshold=row[6],
                timestamp=row[7],
                resolved=bool(row[8]),
                resolved_at=row[9]
            )
            alerts.append(alert)
        
        conn.close()
        return alerts

class PerformanceAnalyzer:
    """Analyzes performance data and generates insights"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
    
    async def generate_performance_report(self, time_range_hours: int = 24, 
                                        report_type: str = "comprehensive") -> PerformanceReport:
        """Generate comprehensive performance report"""
        report_id = f"perf_report_{int(time.time())}"
        start_time = datetime.now() - timedelta(hours=time_range_hours)
        end_time = datetime.now()
        
        # Collect metrics for analysis
        metrics_data = await self._collect_metrics_for_analysis(start_time, end_time)
        
        # Generate summary
        summary = await self._generate_summary(metrics_data)
        
        # Analyze performance trends
        detailed_metrics = await self._analyze_performance_trends(metrics_data)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(summary, detailed_metrics)
        
        report = PerformanceReport(
            report_id=report_id,
            report_type=report_type,
            time_range={
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': time_range_hours
            },
            summary=summary,
            detailed_metrics=detailed_metrics,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
        
        # Store report
        await self._store_performance_report(report)
        
        return report
    
    async def _collect_metrics_for_analysis(self, start_time: datetime, 
                                          end_time: datetime) -> Dict[str, List[Any]]:
        """Collect metrics data for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT metric_name, metric_type, value, timestamp, tags, metadata
            FROM metrics_history 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (start_time.isoformat(), end_time.isoformat()))
        
        metrics_data = defaultdict(list)
        for row in cursor.fetchall():
            metric_name, metric_type, value, timestamp, tags, metadata = row
            try:
                # Try to convert to float for numerical analysis
                numeric_value = float(value)
            except (ValueError, TypeError):
                numeric_value = value
            
            metrics_data[metric_name].append({
                'value': numeric_value,
                'timestamp': timestamp,
                'tags': json.loads(tags) if tags else {},
                'metadata': json.loads(metadata) if metadata else {}
            })
        
        conn.close()
        return dict(metrics_data)
    
    async def _generate_summary(self, metrics_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Generate performance summary"""
        summary = {
            'total_metrics_collected': sum(len(values) for values in metrics_data.values()),
            'unique_metrics': len(metrics_data),
            'data_quality': 'good',  # Placeholder
            'coverage': {}
        }
        
        # Analyze key metrics
        key_metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
        for metric in key_metrics:
            if metric in metrics_data and metrics_data[metric]:
                values = [d['value'] for d in metrics_data[metric] if isinstance(d['value'], (int, float))]
                if values:
                    summary['coverage'][metric] = {
                        'data_points': len(values),
                        'avg': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'median': statistics.median(values)
                    }
                    
                    if len(values) > 1:
                        summary['coverage'][metric]['std_dev'] = statistics.stdev(values)
        
        return summary
    
    async def _analyze_performance_trends(self, metrics_data: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Analyze performance trends"""
        trends = []
        
        for metric_name, data_points in metrics_data.items():
            if len(data_points) < 2:
                continue
            
            numeric_values = [d['value'] for d in data_points if isinstance(d['value'], (int, float))]
            if len(numeric_values) < 2:
                continue
            
            # Calculate trend
            first_half = numeric_values[:len(numeric_values)//2]
            second_half = numeric_values[len(numeric_values)//2:]
            
            if first_half and second_half:
                first_avg = statistics.mean(first_half)
                second_avg = statistics.mean(second_half)
                
                trend_direction = 'increasing' if second_avg > first_avg else 'decreasing' if second_avg < first_avg else 'stable'
                trend_magnitude = abs(second_avg - first_avg) / max(first_avg, 0.001) * 100
                
                trends.append({
                    'metric_name': metric_name,
                    'trend_direction': trend_direction,
                    'trend_magnitude': trend_magnitude,
                    'first_period_avg': first_avg,
                    'second_period_avg': second_avg,
                    'data_points': len(numeric_values),
                    'volatility': statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                })
        
        return trends
    
    async def _generate_recommendations(self, summary: Dict[str, Any], 
                                      detailed_metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # CPU recommendations
        if 'cpu_usage' in summary['coverage']:
            cpu_stats = summary['coverage']['cpu_usage']
            if cpu_stats['avg'] > 70:
                recommendations.append(
                    f"High average CPU usage ({cpu_stats['avg']:.1f}%). "
                    "Consider optimizing algorithms or reducing parallel operations."
                )
            elif cpu_stats['max'] > 90:
                recommendations.append(
                    f"CPU usage spikes detected (max: {cpu_stats['max']:.1f}%). "
                    "Implement CPU usage monitoring and throttling."
                )
        
        # Memory recommendations
        if 'memory_usage' in summary['coverage']:
            memory_stats = summary['coverage']['memory_usage']
            if memory_stats['avg'] > 80:
                recommendations.append(
                    f"High average memory usage ({memory_stats['avg']:.1f}%). "
                    "Review memory allocation patterns and implement cleanup."
                )
        
        # Trend-based recommendations
        for trend in detailed_metrics:
            if trend['trend_direction'] == 'increasing' and trend['trend_magnitude'] > 20:
                if 'usage' in trend['metric_name']:
                    recommendations.append(
                        f"Resource usage trending upward for {trend['metric_name']} "
                        f"(+{trend['trend_magnitude']:.1f}%). Monitor for potential issues."
                    )
        
        # Data quality recommendations
        if summary['total_metrics_collected'] < 100:
            recommendations.append(
                "Low metrics collection count. Consider increasing collection frequency "
                "or checking collector health."
            )
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("System performance appears stable. Continue monitoring.")
        
        return recommendations
    
    async def _store_performance_report(self, report: PerformanceReport):
        """Store performance report in database"""
        conn = sqlite3.connect(self.db_path.replace('.db', '_reports.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_reports (
                report_id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                time_range TEXT NOT NULL,
                summary TEXT NOT NULL,
                detailed_metrics TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO performance_reports 
            (report_id, report_type, time_range, summary, detailed_metrics, recommendations, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            report.report_id,
            report.report_type,
            json.dumps(report.time_range),
            json.dumps(report.summary),
            json.dumps(report.detailed_metrics),
            json.dumps(report.recommendations),
            report.generated_at
        ))
        
        conn.commit()
        conn.close()

class MonitoringSystem:
    """Main monitoring system coordinator"""
    
    def __init__(self, db_path: str = "monitoring.db", collection_interval: int = 10):
        self.db_path = db_path
        self.metrics_collector = MetricsCollector(collection_interval)
        self.alert_manager = AlertManager(db_path)
        self.performance_analyzer = PerformanceAnalyzer(db_path)
        
        self.is_running = False
        self.monitoring_task = None
        
        # Setup default alert rules
        self._setup_default_alerts()
        
        # Setup default alert handlers
        self._setup_default_handlers()
    
    def _setup_default_alerts(self):
        """Setup default system alert rules"""
        # CPU usage alerts
        self.alert_manager.add_alert_rule(
            metric_name="cpu_usage",
            condition="greater_than",
            threshold=80.0,
            alert_level=AlertLevel.WARNING,
            title="High CPU Usage",
            description="CPU usage is above 80%"
        )
        
        self.alert_manager.add_alert_rule(
            metric_name="cpu_usage",
            condition="greater_than",
            threshold=95.0,
            alert_level=AlertLevel.CRITICAL,
            title="Critical CPU Usage",
            description="CPU usage is above 95%"
        )
        
        # Memory usage alerts
        self.alert_manager.add_alert_rule(
            metric_name="memory_usage",
            condition="greater_than",
            threshold=85.0,
            alert_level=AlertLevel.WARNING,
            title="High Memory Usage",
            description="Memory usage is above 85%"
        )
        
        self.alert_manager.add_alert_rule(
            metric_name="memory_usage",
            condition="greater_than",
            threshold=95.0,
            alert_level=AlertLevel.CRITICAL,
            title="Critical Memory Usage",
            description="Memory usage is above 95%"
        )
        
        # Disk usage alerts
        self.alert_manager.add_alert_rule(
            metric_name="disk_usage",
            condition="greater_than",
            threshold=90.0,
            alert_level=AlertLevel.WARNING,
            title="High Disk Usage",
            description="Disk usage is above 90%"
        )
    
    def _setup_default_handlers(self):
        """Setup default alert handlers"""
        def log_alert_handler(alert: Alert):
            logger.warning(f"ALERT [{alert.alert_level.value.upper()}]: {alert.title}")
            logger.warning(f"Description: {alert.description}")
            logger.warning(f"Current value: {alert.current_value}, Threshold: {alert.threshold}")
        
        self.alert_manager.add_alert_handler(log_alert_handler)
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_running:
            return
        
        logger.info("Starting monitoring system...")
        
        # Start metrics collection
        await self.metrics_collector.start_collection()
        
        # Start monitoring loop
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Monitoring system started")
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.is_running:
            return
        
        logger.info("Stopping monitoring system...")
        
        self.is_running = False
        
        # Stop metrics collection
        await self.metrics_collector.stop_collection()
        
        # Stop monitoring loop
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring system stopped")

    def start_monitoring_sync(self):
        """Start monitoring (synchronous wrapper)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                task = loop.create_task(self.start_monitoring())
                print("📊 Monitoring started as background task")
                return task
            else:
                # If no loop is running, run it
                return loop.run_until_complete(self.start_monitoring())
        except RuntimeError:
            # No event loop, create new one
            print("📊 Starting monitoring system...")
            return asyncio.run(self.start_monitoring())

    def stop_monitoring_sync(self):
        """Stop monitoring (synchronous wrapper)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                task = loop.create_task(self.stop_monitoring())
                print("📊 Monitoring stop requested as background task")
                return task
            else:
                # If no loop is running, run it
                return loop.run_until_complete(self.stop_monitoring())
        except RuntimeError:
            # No event loop, create new one
            print("📊 Stopping monitoring system...")
            return asyncio.run(self.stop_monitoring())
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Get recent metrics
                recent_metrics = self.metrics_collector.get_recent_metrics(limit=50)
                
                # Store metrics in database
                await self._store_metrics(recent_metrics)
                
                # Check for alerts
                await self.alert_manager.check_alerts(recent_metrics)
                
                # Sleep before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _store_metrics(self, metrics: List[MetricDataPoint]):
        """Store metrics in database"""
        if not metrics:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Insert metrics
        for metric in metrics:
            cursor.execute("""
                INSERT INTO metrics_history 
                (metric_name, metric_type, value, timestamp, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.metric_name,
                metric.metric_type.value,
                str(metric.value),
                metric.timestamp,
                json.dumps(metric.tags),
                json.dumps(metric.metadata)
            ))
        
        conn.commit()
        conn.close()
    
    def register_agent_collector(self, agents_info: Dict[str, Any]):
        """Register agent metrics collector"""
        def collect_agent_metrics():
            """Collect agent-specific metrics"""
            metrics = []
            current_time = datetime.now().isoformat()
            
            # Count active agents
            total_agents = agents_info.get('total_agents', 0)
            metrics.append(MetricDataPoint(
                metric_name="active_agents",
                metric_type=MetricType.AGENT,
                value=total_agents,
                timestamp=current_time,
                tags={"component": "agents"},
                metadata={}
            ))
            
            # Agent type distribution
            for agent_type, agents in agents_info.items():
                if agent_type == 'total_agents':
                    continue
                
                if isinstance(agents, list):
                    count = len(agents)
                elif agents:
                    count = 1
                else:
                    count = 0
                
                metrics.append(MetricDataPoint(
                    metric_name=f"agents_{agent_type}",
                    metric_type=MetricType.AGENT,
                    value=count,
                    timestamp=current_time,
                    tags={"component": "agents", "agent_type": agent_type},
                    metadata={}
                ))
            
            return metrics
        
        self.metrics_collector.register_custom_collector("agent_metrics", collect_agent_metrics)
    
    def register_neural_collector(self, neural_engine):
        """Register neural intelligence metrics collector"""
        def collect_neural_metrics():
            """Collect neural intelligence metrics"""
            metrics = []
            current_time = datetime.now().isoformat()
            
            try:
                neural_status = neural_engine.get_neural_status()
                
                metrics.append(MetricDataPoint(
                    metric_name="neural_patterns_total",
                    metric_type=MetricType.NEURAL,
                    value=neural_status['total_patterns'],
                    timestamp=current_time,
                    tags={"component": "neural_intelligence"},
                    metadata={}
                ))
                
                metrics.append(MetricDataPoint(
                    metric_name="neural_confidence_avg",
                    metric_type=MetricType.NEURAL,
                    value=neural_status['average_confidence'],
                    timestamp=current_time,
                    tags={"component": "neural_intelligence"},
                    metadata={}
                ))
                
                metrics.append(MetricDataPoint(
                    metric_name="neural_success_rate_avg",
                    metric_type=MetricType.NEURAL,
                    value=neural_status['average_success_rate'],
                    timestamp=current_time,
                    tags={"component": "neural_intelligence"},
                    metadata={}
                ))
                
            except Exception as e:
                logger.error(f"Error collecting neural metrics: {e}")
            
            return metrics
        
        self.metrics_collector.register_custom_collector("neural_metrics", collect_neural_metrics)
    
    def register_mcp_collector(self, mcp_tools_manager):
        """Register MCP tools metrics collector"""
        def collect_mcp_metrics():
            """Collect MCP tools metrics"""
            metrics = []
            current_time = datetime.now().isoformat()
            
            try:
                mcp_status = asyncio.run(mcp_tools_manager.get_tool_status())
                
                metrics.append(MetricDataPoint(
                    metric_name="mcp_tools_total",
                    metric_type=MetricType.SYSTEM,
                    value=mcp_status['total_tools'],
                    timestamp=current_time,
                    tags={"component": "mcp_tools"},
                    metadata={}
                ))
                
                metrics.append(MetricDataPoint(
                    metric_name="mcp_active_sessions",
                    metric_type=MetricType.SYSTEM,
                    value=mcp_status['active_sessions'],
                    timestamp=current_time,
                    tags={"component": "mcp_tools"},
                    metadata={}
                ))
                
                metrics.append(MetricDataPoint(
                    metric_name="mcp_execution_history",
                    metric_type=MetricType.SYSTEM,
                    value=mcp_status['execution_history_count'],
                    timestamp=current_time,
                    tags={"component": "mcp_tools"},
                    metadata={}
                ))
                
            except Exception as e:
                logger.error(f"Error collecting MCP metrics: {e}")
            
            return metrics
        
        self.metrics_collector.register_custom_collector("mcp_metrics", collect_mcp_metrics)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_recent_metrics(limit=10)
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Calculate system health score
        health_score = await self._calculate_health_score(recent_metrics)
        
        return {
            'monitoring_active': self.is_running,
            'metrics_collected': len(recent_metrics),
            'active_alerts': len(active_alerts),
            'alert_breakdown': {
                level.value: len([a for a in active_alerts if a.alert_level == level])
                for level in AlertLevel
            },
            'health_score': health_score,
            'health_status': 'excellent' if health_score > 80 else 'good' if health_score > 60 else 'poor',
            'last_update': datetime.now().isoformat()
        }
    
    async def _calculate_health_score(self, metrics: List[MetricDataPoint]) -> float:
        """Calculate overall system health score"""
        if not metrics:
            return 50.0  # Neutral score if no metrics
        
        score_components = []
        
        # CPU health
        cpu_metrics = [m for m in metrics if m.metric_name == 'cpu_usage']
        if cpu_metrics:
            latest_cpu = cpu_metrics[-1].value
            cpu_score = max(0, 100 - float(latest_cpu))
            score_components.append(cpu_score * 0.3)
        
        # Memory health
        memory_metrics = [m for m in metrics if m.metric_name == 'memory_usage']
        if memory_metrics:
            latest_memory = memory_metrics[-1].value
            memory_score = max(0, 100 - float(latest_memory))
            score_components.append(memory_score * 0.3)
        
        # Disk health
        disk_metrics = [m for m in metrics if m.metric_name == 'disk_usage']
        if disk_metrics:
            latest_disk = disk_metrics[-1].value
            disk_score = max(0, 100 - float(latest_disk))
            score_components.append(disk_score * 0.2)
        
        # Alert penalty
        active_alerts = self.alert_manager.get_active_alerts()
        alert_penalty = len(active_alerts) * 5  # 5 points per active alert
        
        base_score = sum(score_components) if score_components else 70.0
        final_score = max(0, base_score - alert_penalty)
        
        return min(100.0, final_score)
    
    async def generate_monitoring_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        # Generate performance report
        perf_report = await self.performance_analyzer.generate_performance_report(hours)
        
        # Get alert history
        alert_history = self.alert_manager.get_alert_history(hours)
        
        # Get system status
        system_status = await self.get_system_status()
        
        return {
            'report_id': f"monitoring_report_{int(time.time())}",
            'time_range_hours': hours,
            'generated_at': datetime.now().isoformat(),
            'system_status': system_status,
            'performance_report': asdict(perf_report),
            'alert_summary': {
                'total_alerts': len(alert_history),
                'by_level': {
                    level.value: len([a for a in alert_history if a.alert_level == level])
                    for level in AlertLevel
                },
                'resolved_alerts': len([a for a in alert_history if a.resolved]),
                'unresolved_alerts': len([a for a in alert_history if not a.resolved])
            },
            'recommendations': perf_report.recommendations + [
                "Continue monitoring system health",
                "Review alert thresholds periodically",
                "Optimize based on performance trends"
            ]
        }