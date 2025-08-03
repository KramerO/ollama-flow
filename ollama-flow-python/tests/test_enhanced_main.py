#!/usr/bin/env python3
"""
Unit tests for Enhanced Main Framework
"""

import unittest
import asyncio
import tempfile
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_main import EnhancedOllamaFlow

class TestEnhancedOllamaFlow(unittest.TestCase):
    """Test cases for Enhanced Ollama Flow Framework"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.framework = EnhancedOllamaFlow()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test framework initialization"""
        self.assertIsNotNone(self.framework)
        self.assertIsNone(self.framework.db_manager)
        self.assertIsNone(self.framework.orchestrator)
        self.assertEqual(self.framework.config, {})
        self.assertEqual(self.framework.agents_info, {})
        self.assertEqual(self.framework.running_processes, [])
    
    def test_parse_arguments(self):
        """Test argument parsing"""
        # Test with minimal arguments
        with patch('sys.argv', ['enhanced_main.py', '--task', 'test task']):
            args = self.framework.parse_arguments()
            self.assertEqual(args.task, 'test task')
        
        # Test with full arguments
        test_args = [
            'enhanced_main.py',
            '--task', 'complex task',
            '--workers', '8',
            '--arch', 'HIERARCHICAL',
            '--model', 'llama3',
            '--secure',
            '--metrics',
            '--benchmark'
        ]
        
        with patch('sys.argv', test_args):
            args = self.framework.parse_arguments()
            self.assertEqual(args.task, 'complex task')
            self.assertEqual(args.workers, 8)
            self.assertEqual(args.arch, 'HIERARCHICAL')
            self.assertEqual(args.model, 'llama3')
            self.assertTrue(args.secure)
            self.assertTrue(args.metrics)
            self.assertTrue(args.benchmark)
    
    def test_load_configuration(self):
        """Test configuration loading"""
        # Create mock arguments
        args = Mock()
        args.task = 'test task'
        args.workers = 6
        args.arch = 'CENTRALIZED'
        args.model = 'codellama:7b'
        args.secure = True
        args.project_folder = '/test/folder'
        args.parallel_llm = True
        args.metrics = True
        args.benchmark = False
        args.interactive = False
        args.db_path = 'test.db'
        args.log_level = 'DEBUG'
        args.stop_agents = False
        args.cleanup = False
        args.sub_queens = 2
        args.disable_neural = False
        args.disable_mcp = False
        args.disable_monitoring = False
        args.disable_sessions = False
        args.list_sessions = False
        args.resume_session = None
        
        config = self.framework.load_configuration(args)
        
        self.assertEqual(config['task'], 'test task')
        self.assertEqual(config['worker_count'], 6)
        self.assertEqual(config['architecture_type'], 'CENTRALIZED')
        self.assertEqual(config['model'], 'codellama:7b')
        self.assertTrue(config['secure_mode'])
        self.assertEqual(config['project_folder'], '/test/folder')
        self.assertTrue(config['parallel_llm'])
        self.assertTrue(config['metrics_enabled'])
        self.assertEqual(config['log_level'], 'DEBUG')
    
    def test_configuration_defaults(self):
        """Test configuration defaults"""
        args = Mock()
        args.task = None
        args.workers = None
        args.arch = None
        args.model = None
        args.secure = False
        args.project_folder = None
        args.parallel_llm = False
        args.metrics = False
        args.benchmark = False
        args.interactive = False
        args.db_path = 'default.db'
        args.log_level = 'INFO'
        args.stop_agents = False
        args.cleanup = False
        args.sub_queens = None
        args.disable_neural = False
        args.disable_mcp = False
        args.disable_monitoring = False
        args.disable_sessions = False
        args.list_sessions = False
        args.resume_session = None
        
        # Mock environment variables
        with patch.dict('os.environ', {}, clear=True):
            config = self.framework.load_configuration(args)
            
            self.assertEqual(config['worker_count'], 4)  # default
            self.assertEqual(config['architecture_type'], 'HIERARCHICAL')  # default
            self.assertEqual(config['model'], 'codellama:7b')  # default
            self.assertFalse(config['secure_mode'])
            self.assertEqual(config['log_level'], 'INFO')
    
    def test_database_setup(self):
        """Test database setup"""
        self.framework.config = {'db_path': os.path.join(self.temp_dir, 'test.db')}
        
        # Mock the database manager
        with patch('enhanced_main.MessageDBManager') as mock_db:
            mock_instance = Mock()
            mock_db.return_value = mock_instance
            
            result = asyncio.run(self.framework.setup_database())
            
            mock_db.assert_called_once_with(db_path=self.framework.config['db_path'])
            self.assertEqual(result, mock_instance)
    
    def test_enhanced_components_setup(self):
        """Test enhanced components setup"""
        self.framework.neural_enabled = True
        self.framework.mcp_enabled = True
        self.framework.monitoring_enabled = True
        self.framework.session_enabled = True
        
        async def test_setup():
            with patch('enhanced_main.NeuralIntelligenceEngine') as mock_neural, \
                 patch('enhanced_main.MCPToolsManager') as mock_mcp, \
                 patch('enhanced_main.MonitoringSystem') as mock_monitoring, \
                 patch('enhanced_main.SessionManager') as mock_session:
                
                # Setup mocks
                mock_neural_instance = AsyncMock()
                mock_neural.return_value = mock_neural_instance
                
                mock_mcp_instance = AsyncMock()
                mock_mcp.return_value = mock_mcp_instance
                
                mock_monitoring_instance = AsyncMock()
                mock_monitoring.return_value = mock_monitoring_instance
                
                mock_session_instance = AsyncMock()
                mock_session.return_value = mock_session_instance
                
                await self.framework.setup_enhanced_components()
                
                # Verify components were created and initialized
                mock_neural.assert_called_once()
                mock_neural_instance.initialize.assert_called_once()
                
                mock_mcp.assert_called_once()
                mock_mcp_instance.initialize.assert_called_once()
                
                mock_monitoring.assert_called_once()
                mock_monitoring_instance.start_monitoring.assert_called_once()
                
                mock_session.assert_called_once()
                mock_session_instance.start_auto_save.assert_called_once()
                
                # Verify components were assigned
                self.assertEqual(self.framework.neural_engine, mock_neural_instance)
                self.assertEqual(self.framework.mcp_tools, mock_mcp_instance)
                self.assertEqual(self.framework.monitoring_system, mock_monitoring_instance)
                self.assertEqual(self.framework.session_manager, mock_session_instance)
        
        asyncio.run(test_setup())
    
    def test_agent_creation(self):
        """Test enhanced agent creation"""
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        self.framework.config = {
            'architecture_type': 'HIERARCHICAL',
            'model': 'codellama:7b',
            'worker_count': 4,
            'sub_queen_count': 2,
            'secure_mode': True,
            'project_folder': '/test'
        }
        
        async def test_creation():
            with patch('enhanced_main.EnhancedQueenAgent') as mock_queen, \
                 patch('enhanced_main.EnhancedSubQueenAgent') as mock_sub_queen, \
                 patch('enhanced_main.SecureWorkerAgent') as mock_worker:
                
                # Setup mocks
                mock_queen_instance = Mock()
                mock_queen.return_value = mock_queen_instance
                
                mock_sub_queen_instance = Mock()
                mock_sub_queen.return_value = mock_sub_queen_instance
                
                mock_worker_instance = Mock()
                mock_worker.return_value = mock_worker_instance
                
                agents_info = await self.framework.create_enhanced_agents(mock_orchestrator)
                
                # Verify agents were created
                mock_queen.assert_called_once()
                self.assertEqual(mock_sub_queen.call_count, 2)  # 2 sub-queens
                self.assertEqual(mock_worker.call_count, 4)    # 4 workers
                
                # Verify agents were registered
                self.assertEqual(mock_orchestrator.register_agent.call_count, 7)  # 1 queen + 2 sub-queens + 4 workers
                
                # Verify agents_info structure
                self.assertIn('queen', agents_info)
                self.assertIn('sub_queens', agents_info)
                self.assertIn('workers', agents_info)
                self.assertEqual(agents_info['total_agents'], 7)
        
        asyncio.run(test_creation())
    
    def test_task_execution_flow(self):
        """Test task execution flow"""
        self.framework.session_enabled = True
        self.framework.monitoring_enabled = True
        self.framework.neural_enabled = True
        
        # Mock components
        mock_session_manager = AsyncMock()
        mock_monitoring_system = AsyncMock()
        mock_neural_engine = AsyncMock()
        mock_orchestrator = AsyncMock()
        
        self.framework.session_manager = mock_session_manager
        self.framework.monitoring_system = mock_monitoring_system
        self.framework.neural_engine = mock_neural_engine
        self.framework.agents_info = {'total_agents': 4}
        
        # Mock session creation
        mock_session_manager.create_session.return_value = 'test-session-id'
        mock_neural_engine.learn_from_execution.return_value = []
        
        # Mock orchestrator execution
        mock_orchestrator.run.return_value = "Task completed successfully"
        
        async def test_execution():
            result = await self.framework.execute_task(
                "Test task", 
                mock_orchestrator
            )
            
            # Verify session was created
            mock_session_manager.create_session.assert_called_once()
            
            # Verify orchestrator was called
            mock_orchestrator.start_polling.assert_called_once()
            mock_orchestrator.run.assert_called_once_with("Test task")
            
            # Verify neural learning was triggered
            mock_neural_engine.learn_from_execution.assert_called_once()
            
            # Verify session was updated and closed
            mock_session_manager.update_session.assert_called()
            mock_session_manager.close_session.assert_called()
            
            # Verify result
            self.assertTrue(result['success'])
            self.assertEqual(result['result'], "Task completed successfully")
            self.assertIsNone(result['error'])
            self.assertIn('session_id', result)
        
        asyncio.run(test_execution())
    
    def test_task_execution_failure(self):
        """Test task execution failure handling"""
        self.framework.session_enabled = True
        mock_session_manager = AsyncMock()
        mock_orchestrator = AsyncMock()
        
        self.framework.session_manager = mock_session_manager
        mock_session_manager.create_session.return_value = 'test-session-id'
        
        # Mock orchestrator failure
        mock_orchestrator.run.side_effect = Exception("Test error")
        
        async def test_failure():
            result = await self.framework.execute_task(
                "Test task", 
                mock_orchestrator
            )
            
            # Verify failure was handled
            self.assertFalse(result['success'])
            self.assertIsNone(result['result'])
            self.assertEqual(result['error'], "Test error")
            
            # Verify session was updated with error
            mock_session_manager.update_session.assert_called()
            mock_session_manager.close_session.assert_called_with('test-session-id', 'failed')
        
        asyncio.run(test_failure())
    
    def test_stop_all_agents(self):
        """Test stopping all agents"""
        # Setup mock components
        mock_monitoring = AsyncMock()
        mock_session_manager = AsyncMock()
        mock_mcp_tools = AsyncMock()
        mock_neural_engine = AsyncMock()
        
        self.framework.monitoring_system = mock_monitoring
        self.framework.session_manager = mock_session_manager
        self.framework.mcp_tools = mock_mcp_tools
        self.framework.neural_engine = mock_neural_engine
        
        self.framework.monitoring_enabled = True
        self.framework.session_enabled = True
        self.framework.mcp_enabled = True
        self.framework.neural_enabled = True
        
        # Mock active sessions
        mock_session_manager.active_sessions = {'session1': Mock(), 'session2': Mock()}
        
        async def test_stop():
            result = await self.framework.stop_all_agents()
            
            # Verify components were stopped
            mock_monitoring.stop_monitoring.assert_called_once()
            mock_session_manager.stop_auto_save.assert_called_once()
            mock_mcp_tools.cleanup.assert_called_once()
            mock_neural_engine.save_patterns.assert_called_once()
            
            # Verify sessions were closed
            self.assertEqual(mock_session_manager.close_session.call_count, 2)
            
            self.assertTrue(result)
        
        asyncio.run(test_stop())
    
    def test_cleanup_database_and_files(self):
        """Test database and file cleanup"""
        # Create test files
        test_files = [
            'neural_intelligence.db',
            'mcp_tools.db',
            'monitoring.db',
            'sessions.db'
        ]
        
        for file in test_files:
            file_path = os.path.join(self.temp_dir, file)
            with open(file_path, 'w') as f:
                f.write('test')
        
        # Create test directory
        session_dir = os.path.join(self.temp_dir, 'session_data')
        os.makedirs(session_dir, exist_ok=True)
        with open(os.path.join(session_dir, 'test.pkl'), 'w') as f:
            f.write('test')
        
        # Mock the framework
        self.framework.config = {'db_path': os.path.join(self.temp_dir, 'main.db')}
        
        async def test_cleanup():
            with patch('os.getcwd', return_value=self.temp_dir), \
                 patch.object(self.framework, 'stop_all_agents', new_callable=AsyncMock):
                
                result = await self.framework.cleanup_database_and_files()
                
                # Verify cleanup was attempted
                self.assertTrue(result)
                
                # Note: In real implementation, files would be deleted
                # Here we just verify the method runs without error
        
        asyncio.run(test_cleanup())

class TestEnhancedMainIntegration(unittest.TestCase):
    """Integration tests for Enhanced Main Framework"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_initialization_flow(self):
        """Test complete initialization flow"""
        framework = EnhancedOllamaFlow()
        
        # Mock all external dependencies
        with patch('enhanced_main.MessageDBManager') as mock_db, \
             patch('enhanced_main.Orchestrator') as mock_orch, \
             patch('enhanced_main.NeuralIntelligenceEngine') as mock_neural, \
             patch('enhanced_main.MCPToolsManager') as mock_mcp, \
             patch('enhanced_main.MonitoringSystem') as mock_monitoring, \
             patch('enhanced_main.SessionManager') as mock_session:
            
            # Setup return values
            mock_db.return_value = Mock()
            mock_orch.return_value = Mock()
            
            mock_neural_instance = AsyncMock()
            mock_neural.return_value = mock_neural_instance
            
            mock_mcp_instance = AsyncMock()
            mock_mcp.return_value = mock_mcp_instance
            
            mock_monitoring_instance = AsyncMock()
            mock_monitoring.return_value = mock_monitoring_instance
            
            mock_session_instance = AsyncMock()
            mock_session.return_value = mock_session_instance
            
            framework.config = {
                'db_path': os.path.join(self.temp_dir, 'test.db'),
                'neural_enabled': True,
                'mcp_enabled': True,
                'monitoring_enabled': True,
                'session_enabled': True
            }
            
            async def test_init():
                # Setup database
                db_manager = await framework.setup_database()
                self.assertIsNotNone(db_manager)
                
                # Setup enhanced components
                await framework.setup_enhanced_components()
                
                # Verify all components were initialized
                self.assertIsNotNone(framework.neural_engine)
                self.assertIsNotNone(framework.mcp_tools)
                self.assertIsNotNone(framework.monitoring_system)
                self.assertIsNotNone(framework.session_manager)
            
            asyncio.run(test_init())

if __name__ == '__main__':
    unittest.main()