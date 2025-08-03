#!/usr/bin/env python3
"""
Unit tests for Monitoring System
"""

import unittest
import asyncio
import tempfile
import os
import sys
import sqlite3
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring_system import (
    MonitoringSystem, MetricsCollector, AlertManager, 
    MetricType, AlertLevel, MetricDataPoint, Alert, PerformanceAnalyzer
)

class TestMetricDataPoint(unittest.TestCase):
    """Test cases for MetricDataPoint dataclass"""
    
    def test_metric_data_point_creation(self):
        """Test MetricDataPoint creation"""
        metric = MetricDataPoint(
            metric_name="cpu_usage",
            metric_type=MetricType.RESOURCE,
            value=75.5,
            timestamp="2024-01-01T10:00:00",
            tags={"host": "server1"},
            metadata={"source": "psutil"}
        )
        
        self.assertEqual(metric.metric_name, "cpu_usage")
        self.assertEqual(metric.metric_type, MetricType.RESOURCE)
        self.assertEqual(metric.value, 75.5)
        self.assertEqual(metric.tags["host"], "server1")
        self.assertEqual(metric.metadata["source"], "psutil")

class TestAlert(unittest.TestCase):
    """Test cases for Alert dataclass"""
    
    def test_alert_creation(self):
        """Test Alert creation"""
        alert = Alert(
            alert_id="alert-001",
            alert_type="resource_threshold",
            level=AlertLevel.WARNING,
            message="CPU usage above 80%",
            metric_name="cpu_usage",
            metric_value=85.0,
            threshold=80.0,
            timestamp="2024-01-01T10:00:00",
            resolved=False,
            metadata={"host": "server1"}
        )
        
        self.assertEqual(alert.alert_id, "alert-001")
        self.assertEqual(alert.level, AlertLevel.WARNING)
        self.assertEqual(alert.metric_value, 85.0)
        self.assertFalse(alert.resolved)

class TestMetricsCollector(unittest.TestCase):
    """Test cases for MetricsCollector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_metrics.db")
        self.collector = MetricsCollector()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_collector_initialization(self):
        """Test metrics collector initialization"""
        self.assertEqual(self.collector.db_path, self.db_path)
        self.assertIsInstance(self.collector.metrics_buffer, dict)
        self.assertIsInstance(self.collector.collection_history, list)
        
        # Check if database file was created
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_record_metric(self):
        """Test recording a metric"""
        metric = MetricDataPoint(
            metric_name="test_metric",
            metric_type=MetricType.PERFORMANCE,
            value=42.0,
            timestamp=datetime.now().isoformat(),
            tags={"test": "true"},
            metadata={}
        )
        
        self.collector.record_metric(metric)
        
        # Check if metric was added to buffer
        self.assertIn("test_metric", self.collector.metrics_buffer)
        self.assertEqual(len(self.collector.metrics_buffer["test_metric"]), 1)
        self.assertEqual(self.collector.metrics_buffer["test_metric"][0].value, 42.0)
    
    def test_get_metrics_by_type(self):
        """Test getting metrics by type"""
        # Record metrics of different types
        performance_metric = MetricDataPoint(
            metric_name="response_time",
            metric_type=MetricType.PERFORMANCE,
            value=100.0,
            timestamp=datetime.now().isoformat(),
            tags={},
            metadata={}
        )
        
        resource_metric = MetricDataPoint(
            metric_name="memory_usage",
            metric_type=MetricType.RESOURCE,
            value=512.0,
            timestamp=datetime.now().isoformat(),
            tags={},
            metadata={}
        )
        
        self.collector.record_metric(performance_metric)
        self.collector.record_metric(resource_metric)
        
        # Get performance metrics
        perf_metrics = self.collector.get_metrics_by_type(MetricType.PERFORMANCE)
        
        self.assertEqual(len(perf_metrics), 1)
        self.assertEqual(perf_metrics[0].metric_name, "response_time")
    
    def test_get_latest_metrics(self):
        """Test getting latest metrics"""
        # Record multiple metrics with same name
        for i in range(3):
            metric = MetricDataPoint(
                metric_name="cpu_usage",
                metric_type=MetricType.RESOURCE,
                value=float(i * 10),
                timestamp=datetime.now().isoformat(),
                tags={},
                metadata={}
            )
            self.collector.record_metric(metric)
        
        # Get latest metrics
        latest = self.collector.get_latest_metrics("cpu_usage", count=2)
        
        self.assertEqual(len(latest), 2)
        # Should be in reverse chronological order (latest first)
        self.assertEqual(latest[0].value, 20.0)
    
    @patch('psutil.cpu_percent', return_value=25.5)
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test collecting system metrics"""
        mock_memory.return_value = Mock(percent=45.0, available=2000000)
        mock_disk.return_value = Mock(percent=35.0, free=10000000)
        
        self.collector.collect_system_metrics()
        
        # Should have collected CPU, memory, and disk metrics
        self.assertIn("system_cpu_usage", self.collector.metrics_buffer)
        self.assertIn("system_memory_usage", self.collector.metrics_buffer)
        self.assertIn("system_disk_usage", self.collector.metrics_buffer)
        
        # Check CPU value
        cpu_metric = self.collector.metrics_buffer["system_cpu_usage"][0]
        self.assertEqual(cpu_metric.value, 25.5)

class TestAlertManager(unittest.TestCase):
    """Test cases for AlertManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_alerts.db")
        self.alert_manager = AlertManager(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_alert_manager_initialization(self):
        """Test alert manager initialization"""
        self.assertEqual(self.alert_manager.db_path, self.db_path)
        self.assertIsInstance(self.alert_manager.alert_rules, dict)
        self.assertIsInstance(self.alert_manager.active_alerts, dict)
        
        # Check if database file was created
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_add_alert_rule(self):
        """Test adding an alert rule"""
        rule = {
            "metric_name": "cpu_usage",
            "condition": "greater_than",
            "threshold": 80.0,
            "level": AlertLevel.WARNING,
            "message": "CPU usage is high"
        }
        
        self.alert_manager.add_alert_rule("cpu_high", rule)
        
        self.assertIn("cpu_high", self.alert_manager.alert_rules)
        stored_rule = self.alert_manager.alert_rules["cpu_high"]
        self.assertEqual(stored_rule["threshold"], 80.0)
    
    def test_check_metric_against_rules(self):
        """Test checking metrics against alert rules"""
        # Add a rule
        rule = {
            "metric_name": "cpu_usage",
            "condition": "greater_than",
            "threshold": 75.0,
            "level": AlertLevel.WARNING,
            "message": "CPU usage above threshold"
        }
        self.alert_manager.add_alert_rule("cpu_high", rule)
        
        # Create a metric that triggers the rule
        metric = MetricDataPoint(
            metric_name="cpu_usage",
            metric_type=MetricType.RESOURCE,
            value=85.0,
            timestamp=datetime.now().isoformat(),
            tags={},
            metadata={}
        )
        
        alerts = self.alert_manager.check_metric_against_rules(metric)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].level, AlertLevel.WARNING)
        self.assertEqual(alerts[0].metric_value, 85.0)
    
    def test_resolve_alert(self):
        """Test resolving an alert"""
        # Create and trigger an alert
        rule = {
            "metric_name": "memory_usage",
            "condition": "greater_than",
            "threshold": 90.0,
            "level": AlertLevel.ERROR,
            "message": "Memory usage critical"
        }
        self.alert_manager.add_alert_rule("memory_high", rule)
        
        metric = MetricDataPoint(
            metric_name="memory_usage",
            metric_type=MetricType.RESOURCE,
            value=95.0,
            timestamp=datetime.now().isoformat(),
            tags={},
            metadata={}
        )
        
        alerts = self.alert_manager.check_metric_against_rules(metric)
        alert_id = alerts[0].alert_id
        
        # Resolve the alert
        success = self.alert_manager.resolve_alert(alert_id)
        
        self.assertTrue(success)
        self.assertTrue(self.alert_manager.active_alerts[alert_id].resolved)
    
    def test_get_active_alerts(self):
        """Test getting active alerts"""
        # Create multiple alerts
        rule1 = {
            "metric_name": "cpu_usage",
            "condition": "greater_than",
            "threshold": 80.0,
            "level": AlertLevel.WARNING,
            "message": "CPU high"
        }
        rule2 = {
            "metric_name": "disk_usage",
            "condition": "greater_than",
            "threshold": 95.0,
            "level": AlertLevel.CRITICAL,
            "message": "Disk almost full"
        }
        
        self.alert_manager.add_alert_rule("cpu_high", rule1)
        self.alert_manager.add_alert_rule("disk_full", rule2)
        
        # Trigger both alerts
        cpu_metric = MetricDataPoint("cpu_usage", MetricType.RESOURCE, 85.0, datetime.now().isoformat(), {}, {})
        disk_metric = MetricDataPoint("disk_usage", MetricType.RESOURCE, 98.0, datetime.now().isoformat(), {}, {})
        
        self.alert_manager.check_metric_against_rules(cpu_metric)
        self.alert_manager.check_metric_against_rules(disk_metric)
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        self.assertEqual(len(active_alerts), 2)
        
        # Get alerts by level
        critical_alerts = self.alert_manager.get_active_alerts(level=AlertLevel.CRITICAL)
        self.assertEqual(len(critical_alerts), 1)
        self.assertEqual(critical_alerts[0].level, AlertLevel.CRITICAL)

class TestPerformanceAnalyzer(unittest.TestCase):
    """Test cases for PerformanceAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = PerformanceAnalyzer()
    
    def test_analyzer_initialization(self):
        """Test performance analyzer initialization"""
        self.assertIsInstance(self.analyzer.analysis_history, list)
        self.assertIsInstance(self.analyzer.baseline_metrics, dict)
    
    def test_calculate_performance_score(self):
        """Test performance score calculation"""
        metrics = {
            "cpu_usage": 30.0,
            "memory_usage": 45.0,
            "response_time": 150.0,
            "error_rate": 0.02
        }
        
        score = self.analyzer.calculate_performance_score(metrics)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
    
    def test_analyze_trend(self):
        """Test trend analysis"""
        # Create sample time series data
        data_points = [10.0, 12.0, 11.0, 15.0, 18.0, 20.0, 22.0]
        
        trend = self.analyzer.analyze_trend(data_points)
        
        self.assertIn("direction", trend)
        self.assertIn("slope", trend)
        self.assertIn("confidence", trend)
        
        # Should detect upward trend
        self.assertEqual(trend["direction"], "increasing")
        self.assertGreater(trend["slope"], 0)
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        # Normal data with one anomaly
        normal_data = [50.0, 52.0, 48.0, 51.0, 49.0]
        anomaly_data = [50.0, 52.0, 48.0, 51.0, 120.0]  # 120 is anomalous
        
        # Should detect no anomalies in normal data
        normal_anomalies = self.analyzer.detect_anomalies(normal_data)
        self.assertEqual(len(normal_anomalies), 0)
        
        # Should detect anomaly in anomalous data
        anomalies = self.analyzer.detect_anomalies(anomaly_data)
        self.assertGreater(len(anomalies), 0)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        analysis_results = {
            "cpu_trend": {"direction": "increasing", "slope": 2.5},
            "memory_usage": 85.0,
            "response_time_trend": {"direction": "increasing", "slope": 10.0},
            "error_rate": 0.15
        }
        
        recommendations = self.analyzer.generate_recommendations(analysis_results)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should contain actionable recommendations
        rec_text = " ".join(recommendations).lower()
        self.assertTrue(any(keyword in rec_text for keyword in ["cpu", "memory", "response", "error"]))

class TestMonitoringSystem(unittest.TestCase):
    """Test cases for MonitoringSystem"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_monitoring.db")
        
        # Mock psutil to avoid system dependencies
        with patch('psutil.cpu_percent', return_value=40.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value = Mock(percent=50.0, available=4000000)
            mock_disk.return_value = Mock(percent=60.0, free=20000000)
            
            self.monitoring = MonitoringSystem(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_monitoring_system_initialization(self):
        """Test monitoring system initialization"""
        self.assertEqual(self.monitoring.db_path, self.db_path)
        self.assertIsNotNone(self.monitoring.metrics_collector)
        self.assertIsNotNone(self.monitoring.alert_manager)
        self.assertIsNotNone(self.monitoring.performance_analyzer)
    
    @patch('psutil.cpu_percent', return_value=35.0)
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_all_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test collecting all system metrics"""
        mock_memory.return_value = Mock(percent=40.0, available=5000000)
        mock_disk.return_value = Mock(percent=30.0, free=30000000)
        
        self.monitoring.collect_all_metrics()
        
        # Should have collected system metrics
        collector = self.monitoring.metrics_collector
        self.assertGreater(len(collector.metrics_buffer), 0)
    
    def test_add_custom_metric(self):
        """Test adding custom metrics"""
        self.monitoring.add_custom_metric(
            name="custom_test_metric",
            value=123.45,
            tags={"component": "test"},
            metadata={"source": "unit_test"}
        )
        
        # Should be recorded in metrics collector
        collector = self.monitoring.metrics_collector
        self.assertIn("custom_test_metric", collector.metrics_buffer)
        
        metric = collector.metrics_buffer["custom_test_metric"][0]
        self.assertEqual(metric.value, 123.45)
        self.assertEqual(metric.tags["component"], "test")
    
    def test_setup_alert_rules(self):
        """Test setting up alert rules"""
        self.monitoring.setup_default_alert_rules()
        
        # Should have created default alert rules
        alert_manager = self.monitoring.alert_manager
        self.assertGreater(len(alert_manager.alert_rules), 0)
        
        # Should have CPU alert rule
        self.assertIn("high_cpu_usage", alert_manager.alert_rules)
    
    def test_get_system_health_score(self):
        """Test getting system health score"""
        # Collect some metrics first
        self.monitoring.collect_all_metrics()
        
        health_score = self.monitoring.get_system_health_score()
        
        self.assertIsInstance(health_score, dict)
        self.assertIn("overall_score", health_score)
        self.assertIn("component_scores", health_score)
        self.assertIn("status", health_score)
        
        # Score should be between 0 and 100
        score = health_score["overall_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
    
    def test_get_monitoring_dashboard_data(self):
        """Test getting dashboard data"""
        # Collect metrics and set up alerts
        self.monitoring.collect_all_metrics()
        self.monitoring.setup_default_alert_rules()
        
        dashboard_data = self.monitoring.get_dashboard_data()
        
        self.assertIsInstance(dashboard_data, dict)
        self.assertIn("metrics_summary", dashboard_data)
        self.assertIn("active_alerts", dashboard_data)
        self.assertIn("system_health", dashboard_data)
        self.assertIn("performance_trends", dashboard_data)
        self.assertIn("last_updated", dashboard_data)

class TestMonitoringIntegration(unittest.TestCase):
    """Integration tests for Monitoring System"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "integration_monitoring.db")
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('psutil.cpu_percent', return_value=85.0)  # High CPU to trigger alerts
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_full_monitoring_workflow(self, mock_disk, mock_memory, mock_cpu):
        """Test complete monitoring workflow"""
        mock_memory.return_value = Mock(percent=70.0, available=1000000)
        mock_disk.return_value = Mock(percent=80.0, free=5000000)
        
        monitoring = MonitoringSystem(db_path=self.db_path)
        
        # 1. Set up monitoring
        monitoring.setup_default_alert_rules()
        
        # 2. Collect metrics (should trigger alerts due to high values)
        monitoring.collect_all_metrics()
        
        # 3. Add some custom metrics
        monitoring.add_custom_metric("agent_count", 5)
        monitoring.add_custom_metric("task_completion_rate", 0.95)
        
        # 4. Check for triggered alerts
        alert_manager = monitoring.alert_manager
        active_alerts = alert_manager.get_active_alerts()
        
        # Should have triggered CPU alert due to 85% usage
        cpu_alerts = [a for a in active_alerts if "cpu" in a.metric_name.lower()]
        self.assertGreater(len(cpu_alerts), 0)
        
        # 5. Get performance analysis
        health_score = monitoring.get_system_health_score()
        self.assertLess(health_score["overall_score"], 100.0)  # Should be impacted by high CPU
        
        # 6. Get dashboard data
        dashboard = monitoring.get_dashboard_data()
        self.assertGreater(len(dashboard["active_alerts"]), 0)
        self.assertIn("system_cpu_usage", dashboard["metrics_summary"])
        
        # 7. Resolve an alert
        if active_alerts:
            alert_id = active_alerts[0].alert_id
            success = alert_manager.resolve_alert(alert_id)
            self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()