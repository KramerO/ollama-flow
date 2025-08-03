#!/usr/bin/env python3
"""
Unit tests for MCP Tools Manager
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

from mcp_tools import MCPToolsManager, MCPToolType, MCPToolResult, MCPToolRegistry

class TestMCPToolResult(unittest.TestCase):
    """Test cases for MCPToolResult dataclass"""
    
    def test_mcp_tool_result_creation(self):
        """Test MCPToolResult creation"""
        result = MCPToolResult(
            tool_name="test-tool",
            success=True,
            result={"output": "success", "value": 42},
            execution_time=1.5,
            metadata={"category": "test"},
            timestamp="2024-01-01T10:00:00"
        )
        
        self.assertEqual(result.tool_name, "test-tool")
        self.assertTrue(result.success)
        self.assertEqual(result.result["value"], 42)
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(result.metadata["category"], "test")
    
    def test_mcp_tool_result_failure(self):
        """Test MCPToolResult for failure case"""
        result = MCPToolResult(
            tool_name="test-tool",
            success=False,
            result="Tool execution failed",
            execution_time=0.5,
            metadata={},
            timestamp="2024-01-01T10:00:00"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.result, "Tool execution failed")

class TestMCPToolRegistry(unittest.TestCase):
    """Test cases for MCP Tool Registry"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = MCPToolRegistry()
    
    def test_registry_initialization(self):
        """Test registry initialization"""
        self.assertIsInstance(self.registry.tools, dict)
        self.assertIsInstance(self.registry.tool_metadata, dict)
        self.assertIsInstance(self.registry.execution_history, list)
        self.assertEqual(len(self.registry.tools), 0)
    
    def test_tool_registration(self):
        """Test tool registration"""
        def test_tool(**kwargs):
            return {"result": "test"}
        
        self.registry.register_tool(
            name="test_tool",
            func=test_tool,
            category=MCPToolType.ORCHESTRATION,
            description="A test tool",
            parameters={"param1": "string"}
        )
        
        self.assertIn("test_tool", self.registry.tools)
        self.assertIn("test_tool", self.registry.tool_metadata)
        self.assertEqual(self.registry.tool_metadata["test_tool"]["category"], MCPToolType.ORCHESTRATION)
        self.assertEqual(self.registry.tool_metadata["test_tool"]["description"], "A test tool")
    
    def test_get_tool(self):
        """Test getting a registered tool"""
        def test_tool():
            return "test result"
        
        self.registry.register_tool("test_tool", test_tool, MCPToolType.ANALYSIS, "Test")
        
        retrieved_tool = self.registry.get_tool("test_tool")
        self.assertEqual(retrieved_tool, test_tool)
        
        # Test non-existent tool
        non_existent = self.registry.get_tool("non_existent")
        self.assertIsNone(non_existent)
    
    def test_list_tools(self):
        """Test listing tools"""
        def tool1():
            pass
        def tool2():
            pass
        
        self.registry.register_tool("tool1", tool1, MCPToolType.ORCHESTRATION, "Tool 1")
        self.registry.register_tool("tool2", tool2, MCPToolType.MEMORY, "Tool 2")
        
        # List all tools
        all_tools = self.registry.list_tools()
        self.assertEqual(len(all_tools), 2)
        self.assertIn("tool1", all_tools)
        self.assertIn("tool2", all_tools)
        
        # List tools by category
        orchestration_tools = self.registry.list_tools(MCPToolType.ORCHESTRATION)
        self.assertEqual(len(orchestration_tools), 1)
        self.assertIn("tool1", orchestration_tools)
    
    def test_tool_execution_sync(self):
        """Test synchronous tool execution"""
        def sync_tool(value=10):
            return {"result": value * 2}
        
        self.registry.register_tool("sync_tool", sync_tool, MCPToolType.ANALYSIS, "Sync tool")
        
        async def test_execution():
            result = await self.registry.execute_tool("sync_tool", value=5)
            
            self.assertIsInstance(result, MCPToolResult)
            self.assertEqual(result.tool_name, "sync_tool")
            self.assertTrue(result.success)
            self.assertEqual(result.result["result"], 10)
            self.assertGreater(result.execution_time, 0)
        
        asyncio.run(test_execution())
    
    def test_tool_execution_async(self):
        """Test asynchronous tool execution"""
        async def async_tool(delay=0.01):
            await asyncio.sleep(delay)
            return {"result": "async_complete"}
        
        self.registry.register_tool("async_tool", async_tool, MCPToolType.COORDINATION, "Async tool")
        
        async def test_execution():
            result = await self.registry.execute_tool("async_tool", delay=0.01)
            
            self.assertIsInstance(result, MCPToolResult)
            self.assertEqual(result.tool_name, "async_tool")
            self.assertTrue(result.success)
            self.assertEqual(result.result["result"], "async_complete")
            self.assertGreater(result.execution_time, 0.01)
        
        asyncio.run(test_execution())
    
    def test_tool_execution_failure(self):
        """Test tool execution failure handling"""
        def failing_tool():
            raise ValueError("Tool failed")
        
        self.registry.register_tool("failing_tool", failing_tool, MCPToolType.SECURITY, "Failing tool")
        
        async def test_failure():
            result = await self.registry.execute_tool("failing_tool")
            
            self.assertIsInstance(result, MCPToolResult)
            self.assertEqual(result.tool_name, "failing_tool")
            self.assertFalse(result.success)
            self.assertIn("Tool failed", result.result)
        
        asyncio.run(test_failure())
    
    def test_execution_history(self):
        """Test execution history tracking"""
        def simple_tool():
            return "done"
        
        self.registry.register_tool("simple_tool", simple_tool, MCPToolType.MONITORING, "Simple tool")
        
        async def test_history():
            # Execute tool multiple times
            for i in range(3):
                await self.registry.execute_tool("simple_tool")
            
            # Check execution history
            self.assertEqual(len(self.registry.execution_history), 3)
            
            # All executions should be for our tool
            for execution in self.registry.execution_history:
                self.assertEqual(execution.tool_name, "simple_tool")
                self.assertTrue(execution.success)
        
        asyncio.run(test_history())

class TestMCPToolsManager(unittest.TestCase):
    """Test cases for MCP Tools Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_mcp.db")
        
        # Mock psutil to avoid system dependencies
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value = Mock(percent=60.0, available=1000000)
            mock_disk.return_value = Mock(percent=70.0, free=5000000)
            
            self.manager = MCPToolsManager(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.db_path, self.db_path)
        self.assertIsInstance(self.manager.registry, MCPToolRegistry)
        self.assertIsInstance(self.manager.active_sessions, dict)
        
        # Check if database file was created
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_database_tables_creation(self):
        """Test database tables creation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['tool_executions', 'mcp_sessions', 'tool_metrics']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_built_in_tools_registration(self):
        """Test that built-in tools are registered"""
        tools = self.manager.registry.list_tools()
        
        # Should have registered some built-in tools
        self.assertGreater(len(tools), 0)
        
        # Check for specific tool categories
        orchestration_tools = self.manager.registry.list_tools(MCPToolType.ORCHESTRATION)
        memory_tools = self.manager.registry.list_tools(MCPToolType.MEMORY)
        
        self.assertGreater(len(orchestration_tools), 0)
        self.assertGreater(len(memory_tools), 0)
    
    @patch('psutil.cpu_percent', return_value=45.0)
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_metrics_tool(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics tool execution"""
        mock_memory.return_value = Mock(percent=55.0, available=2000000)
        mock_disk.return_value = Mock(percent=65.0, free=10000000)
        
        async def test_metrics():
            # Execute system monitor tool
            result = await self.manager.registry.execute_tool("system_monitor")
            
            self.assertTrue(result.success)
            self.assertIn("cpu", result.result)
            self.assertIn("usage_percent", result.result["cpu"])
            self.assertIn("memory", result.result)
            self.assertIn("disk", result.result)
            self.assertEqual(result.result["cpu"]["usage_percent"], 45.0)
        
        asyncio.run(test_metrics())
    
    def test_session_management(self):
        """Test session management functionality"""
        async def test_sessions():
            # Create session using swarm_init tool
            result = await self.manager.registry.execute_tool(
                "swarm_init", 
                topology="mesh", 
                max_agents=5
            )
            
            self.assertTrue(result.success)
            self.assertIn("session_id", result.result)
            
            session_id = result.result["session_id"]
            self.assertIn(session_id, self.manager.active_sessions)
        
        asyncio.run(test_sessions())
    
    def test_memory_operations(self):
        """Test memory storage and retrieval"""
        async def test_memory():
            # Store memory
            store_result = await self.manager.registry.execute_tool(
                "memory_store",
                key="test_key",
                data={"data": "test_value", "timestamp": "2024-01-01"},
                category="test"
            )
            
            self.assertTrue(store_result.success)
            
            # Retrieve memory
            retrieve_result = await self.manager.registry.execute_tool(
                "memory_retrieve",
                key="test_key",
                category="test"
            )
            
            self.assertTrue(retrieve_result.success)
            self.assertEqual(retrieve_result.result["data"]["data"], "test_value")
        
        asyncio.run(test_memory())
    
    def test_performance_analysis(self):
        """Test performance analysis tool"""
        async def test_performance():
            # Mock performance data
            metrics = {
                "execution_time": 25.5,
                "memory_usage": 512,
                "cpu_usage": 75.0,
                "agents_active": 3
            }
            
            result = await self.manager.registry.execute_tool(
                "performance_analyze",
                target="system",
                timeframe=3600
            )
            
            self.assertTrue(result.success)
            self.assertIn("metrics", result.result)
            self.assertIn("performance_score", result.result)
        
        asyncio.run(test_performance())
    
    def test_tool_execution_history_memory(self):
        """Test tool execution history in memory"""
        async def test_memory_history():
            # Execute a tool multiple times
            for i in range(3):
                await self.manager.registry.execute_tool("system_monitor")
            
            # Check execution history in memory
            history = self.manager.registry.execution_history
            
            self.assertGreaterEqual(len(history), 3)
            
            # Last executions should be system_monitor
            recent_executions = [e for e in history[-3:] if e.tool_name == "system_monitor"]
            self.assertEqual(len(recent_executions), 3)
        
        asyncio.run(test_memory_history())
    
    def test_error_handling(self):
        """Test error handling and logging"""
        async def test_errors():
            # Try to execute non-existent tool
            result = await self.manager.registry.execute_tool("non_existent_tool")
            
            self.assertFalse(result.success)
            self.assertIn("not found", result.result)
        
        asyncio.run(test_errors())

class TestMCPToolsIntegration(unittest.TestCase):
    """Integration tests for MCP Tools Manager"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "integration_test.db")
        
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('psutil.cpu_percent', return_value=30.0)
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_full_workflow(self, mock_disk, mock_memory, mock_cpu):
        """Test complete MCP tools workflow"""
        mock_memory.return_value = Mock(percent=40.0, available=3000000)
        mock_disk.return_value = Mock(percent=50.0, free=15000000)
        
        async def test_workflow():
            manager = MCPToolsManager(db_path=self.db_path)
            
            # 1. Initialize swarm
            swarm_result = await manager.registry.execute_tool(
                "swarm_init",
                topology="hierarchical",
                max_agents=6
            )
            
            self.assertTrue(swarm_result.success)
            session_id = swarm_result.result["session_id"]
            
            # 2. Store configuration in memory
            config_result = await manager.registry.execute_tool(
                "memory_store",
                key="swarm_config",
                data={"topology": "hierarchical", "agents": 6},
                category=session_id
            )
            
            self.assertTrue(config_result.success)
            
            # 3. Get system metrics
            metrics_result = await manager.registry.execute_tool("system_monitor")
            
            self.assertTrue(metrics_result.success)
            self.assertIn("cpu", metrics_result.result)
            self.assertIn("usage_percent", metrics_result.result["cpu"])
            
            # 4. Analyze performance
            perf_result = await manager.registry.execute_tool(
                "performance_analyze",
                target="system",
                timeframe=3600
            )
            
            self.assertTrue(perf_result.success)
            
            # 5. Verify execution history
            history_count = len(manager.registry.execution_history)
            self.assertGreaterEqual(history_count, 4)
            
            # 6. Verify execution history in memory (registry doesn't persist to DB)
            self.assertGreaterEqual(history_count, 4)
        
        asyncio.run(test_workflow())

if __name__ == '__main__':
    unittest.main()