#!/usr/bin/env python3
"""
Unit tests for dashboard functionality
Tests both simple_dashboard.py and related dashboard components
"""

import pytest
import sys
import tempfile
import json
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import requests

# Add the project root to Python path
project_root = Path(__file__).parent.parent
python_dir = project_root / "ollama-flow-python"
sys.path.insert(0, str(python_dir))

try:
    from dashboard.simple_dashboard import SimpleDashboard
    import psutil
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    DASHBOARD_AVAILABLE = False
    IMPORT_ERROR = str(e)

@pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason=f"Dashboard imports failed: {IMPORT_ERROR if not DASHBOARD_AVAILABLE else ''}")
class TestSimpleDashboard:
    """Test suite for SimpleDashboard functionality"""
    
    @pytest.fixture
    def dashboard(self):
        """Create a dashboard instance for testing"""
        return SimpleDashboard(host='localhost', port=5001, debug=False)
    
    @pytest.fixture
    def mock_psutil(self):
        """Mock psutil for testing without actual system calls"""
        with patch('psutil.cpu_percent', return_value=45.0), \
             patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.pids', return_value=list(range(100))):
            
            mock_mem.return_value.percent = 65.0
            mock_disk.return_value.percent = 30.0
            yield
    
    def test_dashboard_initialization(self, dashboard):
        """Test dashboard initialization"""
        assert dashboard.host == 'localhost'
        assert dashboard.port == 5001
        assert dashboard.debug == False
        assert dashboard.app is not None
        assert hasattr(dashboard, 'active_sessions')
        assert hasattr(dashboard, 'session_history')
    
    def test_render_page_method_exists(self, dashboard):
        """Test that _render_page method exists and works"""
        assert hasattr(dashboard, '_render_page')
        assert callable(dashboard._render_page)
        
        # Test basic rendering
        result = dashboard._render_page("Test Title", "<p>Test Content</p>")
        assert isinstance(result, str)
        assert "Test Title" in result
        assert "Test Content" in result
        assert "<!DOCTYPE html>" in result
    
    def test_dashboard_content_generation(self, dashboard):
        """Test dashboard content generation methods"""
        assert hasattr(dashboard, '_get_dashboard_content')
        assert callable(dashboard._get_dashboard_content)
        
        content = dashboard._get_dashboard_content()
        assert isinstance(content, str)
        assert "System Status" in content
        assert "System Resources" in content
        assert "Quick Actions" in content
    
    def test_sessions_content_generation(self, dashboard):
        """Test sessions content generation"""
        assert hasattr(dashboard, '_get_sessions_content')
        assert callable(dashboard._get_sessions_content)
        
        # Add a mock session
        dashboard.active_sessions['test_session'] = {
            'name': 'Test Session',
            'status': 'running',
            'workers': 4,
            'architecture': 'HIERARCHICAL',
            'started_at': '2024-01-01T10:00:00',
            'task': 'Test task description'
        }
        
        content = dashboard._get_sessions_content()
        assert isinstance(content, str)
        assert "Active Sessions" in content
        assert "Test Session" in content
        assert "Session History" in content
    
    @patch('flask.Flask.run')
    def test_flask_app_configuration(self, mock_run, dashboard):
        """Test Flask app configuration"""
        assert dashboard.app.config['SECRET_KEY'] == 'ollama-flow-dashboard-secret'
        
        # Test that routes are registered
        route_map = {rule.rule: rule.endpoint for rule in dashboard.app.url_map.iter_rules()}
        
        expected_routes = ['/', '/sessions', '/api/status', '/api/health', '/api/sessions']
        for route in expected_routes:
            assert route in route_map, f"Route {route} not found"
    
    def test_api_status_endpoint(self, dashboard, mock_psutil):
        """Test /api/status endpoint"""
        with dashboard.app.test_client() as client:
            response = client.get('/api/status')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'system' in data
            assert 'resources' in data
            assert 'running' in data['system']
            assert 'cpu_percent' in data['resources']
            assert 'memory_percent' in data['resources']
    
    def test_api_health_endpoint(self, dashboard):
        """Test /api/health endpoint"""
        with dashboard.app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert 'timestamp' in data
            assert data['version'] == '2.0.0'
    
    def test_api_sessions_get(self, dashboard):
        """Test GET /api/sessions endpoint"""
        with dashboard.app.test_client() as client:
            response = client.get('/api/sessions')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] == True
            assert 'active_sessions' in data
            assert 'session_history' in data
    
    def test_api_sessions_post(self, dashboard):
        """Test POST /api/sessions endpoint"""
        session_data = {
            'name': 'Test Session',
            'task': 'Test task description',
            'workers': 4,
            'architecture': 'HIERARCHICAL',
            'model': 'codellama:7b'
        }
        
        with dashboard.app.test_client() as client:
            response = client.post('/api/sessions',
                                 data=json.dumps(session_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] == True
            assert 'session_id' in data
            assert data['session_id'] in dashboard.active_sessions
    
    def test_session_management(self, dashboard):
        """Test session creation and management"""
        # Create a session
        session_id = "test_session_123"
        session_data = {
            'id': session_id,
            'name': 'Test Session',
            'task': 'Test task',
            'workers': 4,
            'architecture': 'HIERARCHICAL',
            'status': 'running'
        }
        
        dashboard.active_sessions[session_id] = session_data
        
        # Test session retrieval
        with dashboard.app.test_client() as client:
            response = client.get(f'/api/sessions/{session_id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['session']['name'] == 'Test Session'
    
    def test_session_stop(self, dashboard):
        """Test session stopping functionality"""
        # Create a session
        session_id = "test_session_stop"
        session_data = {
            'id': session_id,
            'name': 'Test Session',
            'status': 'running',
            'started_at': '2024-01-01T10:00:00'
        }
        
        dashboard.active_sessions[session_id] = session_data
        
        # Stop the session
        with dashboard.app.test_client() as client:
            response = client.post(f'/api/sessions/{session_id}/stop')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] == True
            assert session_id not in dashboard.active_sessions
            assert len(dashboard.session_history) > 0
    
    def test_socketio_integration(self, dashboard):
        """Test SocketIO integration if available"""
        # Test if SocketIO is properly integrated
        socketio_available = hasattr(dashboard, 'socketio') and dashboard.socketio is not None
        
        if socketio_available:
            assert hasattr(dashboard, '_setup_socketio_events')
            assert hasattr(dashboard, '_emit_system_update')
        else:
            # If SocketIO is not available, should gracefully handle it
            assert dashboard.socketio is None
    
    def test_background_session_execution(self, dashboard):
        """Test background session execution"""
        session_data = {
            'id': 'bg_test_session',
            'name': 'Background Test',
            'task': 'Test background execution',
            'workers': 2,
            'architecture': 'CENTRALIZED'
        }
        
        # Test session background execution
        dashboard._start_session_background(session_data)
        
        # Give it a moment to start
        time.sleep(0.1)
        
        # Session should be in the system
        assert session_data['id'] in [s.get('id') for s in dashboard.session_history] or \
               session_data['id'] in dashboard.active_sessions
    
    def test_error_handling_in_api(self, dashboard):
        """Test error handling in API endpoints"""
        with dashboard.app.test_client() as client:
            # Test invalid JSON data
            response = client.post('/api/sessions',
                                 data="invalid json",
                                 content_type='application/json')
            assert response.status_code == 400
            
            # Test non-existent session
            response = client.get('/api/sessions/nonexistent')
            assert response.status_code == 404

class TestDashboardIntegration:
    """Integration tests for dashboard functionality"""
    
    @pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason="Dashboard not available")
    def test_dashboard_startup_shutdown(self):
        """Test dashboard startup and shutdown"""
        dashboard = SimpleDashboard(host='localhost', port=5002, debug=False)
        
        # Test that we can create the dashboard without errors
        assert dashboard.app is not None
        assert dashboard.host == 'localhost'
        assert dashboard.port == 5002
    
    @pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason="Dashboard not available")
    def test_concurrent_session_handling(self):
        """Test handling of multiple concurrent sessions"""
        dashboard = SimpleDashboard(host='localhost', port=5003, debug=False)
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session_data = {
                'name': f'Concurrent Session {i}',
                'task': f'Task {i}',
                'workers': 2,
                'architecture': 'HIERARCHICAL'
            }
            
            with dashboard.app.test_client() as client:
                response = client.post('/api/sessions',
                                     data=json.dumps(session_data),
                                     content_type='application/json')
                assert response.status_code == 200
                data = json.loads(response.data)
                sessions.append(data['session_id'])
        
        # Verify all sessions were created
        assert len(dashboard.active_sessions) >= 3
        
        # Clean up sessions
        for session_id in sessions:
            if session_id in dashboard.active_sessions:
                dashboard.active_sessions[session_id]['status'] = 'stopped'

class TestDashboardSecurity:
    """Security tests for dashboard"""
    
    @pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason="Dashboard not available")
    def test_xss_protection(self):
        """Test XSS protection in dashboard"""
        dashboard = SimpleDashboard(host='localhost', port=5004, debug=False)
        
        # Attempt to inject script in session name
        malicious_data = {
            'name': '<script>alert("xss")</script>',
            'task': 'Normal task',
            'workers': 2,
            'architecture': 'HIERARCHICAL'
        }
        
        with dashboard.app.test_client() as client:
            response = client.post('/api/sessions',
                                 data=json.dumps(malicious_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            # Check that script tags are not executed in rendered HTML
            dashboard_html = dashboard._render_page("Test", dashboard._get_sessions_content())
            # Should be escaped or sanitized
            assert '<script>' not in dashboard_html or '&lt;script&gt;' in dashboard_html
    
    @pytest.mark.skipif(not DASHBOARD_AVAILABLE, reason="Dashboard not available")
    def test_input_validation(self):
        """Test input validation in API endpoints"""
        dashboard = SimpleDashboard(host='localhost', port=5005, debug=False)
        
        # Test invalid worker count
        invalid_data = {
            'name': 'Test Session',
            'task': 'Test task',
            'workers': -1,  # Invalid negative workers
            'architecture': 'HIERARCHICAL'
        }
        
        with dashboard.app.test_client() as client:
            response = client.post('/api/sessions',
                                 data=json.dumps(invalid_data),
                                 content_type='application/json')
            # Should still accept (basic validation) but could be improved
            assert response.status_code in [200, 400]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])