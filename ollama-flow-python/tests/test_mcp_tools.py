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

from mcp_tools import MCPToolsManager, MCPTool, ToolCategory, ToolResult

class TestMCPTool(unittest.TestCase):
    """Test cases for MCPTool dataclass"""
    
    def test_mcp_tool_creation(self):
        """Test MCPTool creation"""
        tool = MCPTool(
            tool_id="test-tool-1",
            name="Test Tool",
            category=ToolCategory.ORCHESTRATION,
            description="A test tool",
            parameters={"param1": "string", "param2": "integer"},
            required_parameters=["param1"],
            execution_count=5,
            average_duration=2.5,
            success_rate=0.95,
            last_used="2024-01-01T10:00:00"
        )
        
        self.assertEqual(tool.tool_id, "test-tool-1")
        self.assertEqual(tool.name, "Test Tool")
        self.assertEqual(tool.category, ToolCategory.ORCHESTRATION)
        self.assertEqual(tool.description, "A test tool")
        self.assertEqual(tool.execution_count, 5)
        self.assertEqual(tool.success_rate, 0.95)
        self.assertIn("param1", tool.parameters)
        self.assertIn("param1", tool.required_parameters)

class TestToolResult(unittest.TestCase):
    """Test cases for ToolResult dataclass"""
    
    def test_tool_result_creation(self):
        """Test ToolResult creation"""
        result = ToolResult(
            tool_id="test-tool-1",
            success=True,
            result_data={"output": "success", "value": 42},
            error_message=None,
            execution_time=1.5,
            timestamp="2024-01-01T10:00:00"
        )
        
        self.assertEqual(result.tool_id, "test-tool-1")
        self.assertTrue(result.success)
        self.assertEqual(result.result_data["value"], 42)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.execution_time, 1.5)
    
    def test_tool_result_failure(self):
        """Test ToolResult for failure case"""
        result = ToolResult(
            tool_id="test-tool-1",
            success=False,
            result_data=None,
            error_message="Tool execution failed",
            execution_time=0.5,
            timestamp="2024-01-01T10:00:00"
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.result_data)
        self.assertEqual(result.error_message, "Tool execution failed")

class TestMCPToolsManager(unittest.TestCase):
    """Test cases for MCP Tools Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_mcp.db")
        self.manager = MCPToolsManager(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.db_path, self.db_path)
        self.assertIsInstance(self.manager.tools, dict)
        self.assertIsInstance(self.manager.active_sessions, dict)
        self.assertIsInstance(self.manager.execution_history, list)
        self.assertFalse(self.manager.is_initialized)
    
    def test_database_initialization(self):
        """Test database initialization"""
        asyncio.run(self.manager.initialize())
        
        # Check if database file was created
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables were created
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['mcp_tools', 'tool_executions', 'tool_sessions']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
        self.assertTrue(self.manager.is_initialized)
    
    def test_tools_registration(self):
        """Test tools registration during initialization"""
        asyncio.run(self.manager.initialize())
        
        # Check if tools were registered
        self.assertGreater(len(self.manager.tools), 0)
        
        # Check for specific tool categories
        categories = set()
        for tool in self.manager.tools.values():
            categories.add(tool.category)
        
        expected_categories = {
            ToolCategory.ORCHESTRATION,
            ToolCategory.MEMORY,
            ToolCategory.ANALYSIS,
            ToolCategory.COORDINATION,
            ToolCategory.AUTOMATION,
            ToolCategory.MONITORING,
            ToolCategory.OPTIMIZATION,
            ToolCategory.SECURITY
        }
        
        # Should have tools from multiple categories
        self.assertGreater(len(categories.intersection(expected_categories)), 3)
    
    def test_tool_execution_success(self):
        """Test successful tool execution"""
        async def test_execution():
            await self.manager.initialize()
            
            # Get a test tool (swarm_init should be available)
            test_tools = [t for t in self.manager.tools.values() if t.name == "swarm_init"]
            self.assertGreater(len(test_tools), 0)
            
            test_tool = test_tools[0]
            
            # Execute tool with valid parameters
            parameters = {
                "topology": "mesh",
                "max_agents": 5,
                "strategy": "balanced"
            }
            
            result = await self.manager.execute_tool(test_tool.tool_id, parameters)
            
            self.assertIsInstance(result, ToolResult)
            self.assertEqual(result.tool_id, test_tool.tool_id)
            self.assertTrue(result.success)
            self.assertIsNotNone(result.result_data)
            self.assertIsNone(result.error_message)
            self.assertGreater(result.execution_time, 0)
        
        asyncio.run(test_execution())
    
    def test_tool_execution_missing_parameters(self):
        """Test tool execution with missing required parameters"""
        async def test_missing_params():
            await self.manager.initialize()
            
            # Get a tool that requires parameters
            test_tools = [t for t in self.manager.tools.values() if t.required_parameters]
            self.assertGreater(len(test_tools), 0)
            
            test_tool = test_tools[0]
            
            # Execute tool without required parameters
            result = await self.manager.execute_tool(test_tool.tool_id, {})
            
            self.assertIsInstance(result, ToolResult)
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Missing required parameter", result.error_message)
        
        asyncio.run(test_missing_params())
    
    def test_tool_execution_invalid_tool(self):
        """Test execution of non-existent tool"""
        async def test_invalid_tool():
            await self.manager.initialize()
            
            result = await self.manager.execute_tool("non-existent-tool", {})
            
            self.assertIsInstance(result, ToolResult)
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Tool not found", result.error_message)
        
        asyncio.run(test_invalid_tool())
    
    def test_session_management(self):
        """Test session creation and management"""
        async def test_sessions():
            await self.manager.initialize()
            
            # Create a session
            session_id = await self.manager.create_session("test_session", {
                "user": "test_user",
                "context": "unit_test"
            })
            
            self.assertIsNotNone(session_id)
            self.assertIn(session_id, self.manager.active_sessions)
            
            # Get session info
            session_info = await self.manager.get_session_info(session_id)
            
            self.assertIsNotNone(session_info)
            self.assertEqual(session_info["session_name"], "test_session")
            self.assertEqual(session_info["context"]["user"], "test_user")
            
            # Close session
            success = await self.manager.close_session(session_id)
            
            self.assertTrue(success)
            self.assertNotIn(session_id, self.manager.active_sessions)
        
        asyncio.run(test_sessions())
    
    def test_tool_statistics_tracking(self):
        """Test tool execution statistics tracking"""
        async def test_statistics():
            await self.manager.initialize()
            
            # Get a test tool
            test_tools = list(self.manager.tools.values())
            self.assertGreater(len(test_tools), 0)
            
            test_tool = test_tools[0]
            initial_count = test_tool.execution_count
            
            # Execute tool multiple times
            for i in range(3):
                await self.manager.execute_tool(test_tool.tool_id, {})
            
            # Check updated statistics
            updated_tool = self.manager.tools[test_tool.tool_id]
            self.assertEqual(updated_tool.execution_count, initial_count + 3)
            
            # Check execution history
            self.assertGreaterEqual(len(self.manager.execution_history), 3)
            
            # Recent executions should be for our test tool
            recent_executions = [e for e in self.manager.execution_history[-3:] 
                               if e.tool_id == test_tool.tool_id]
            self.assertEqual(len(recent_executions), 3)
        
        asyncio.run(test_statistics())
    
    def test_tool_categories_filtering(self):
        """Test filtering tools by category"""
        async def test_filtering():
            await self.manager.initialize()
            
            # Get tools by category
            orchestration_tools = await self.manager.get_tools_by_category(ToolCategory.ORCHESTRATION)
            
            self.assertIsInstance(orchestration_tools, list)
            self.assertGreater(len(orchestration_tools), 0)
            
            # All tools should be from orchestration category
            for tool in orchestration_tools:
                self.assertEqual(tool.category, ToolCategory.ORCHESTRATION)
        
        asyncio.run(test_filtering())
    
    def test_tool_search(self):
        """Test tool search functionality"""
        async def test_search():
            await self.manager.initialize()
            
            # Search for tools containing "swarm"
            search_results = await self.manager.search_tools("swarm")
            
            self.assertIsInstance(search_results, list)
            
            # Results should contain tools with "swarm" in name or description
            for tool in search_results:
                self.assertTrue(
                    "swarm" in tool.name.lower() or 
                    "swarm" in tool.description.lower()
                )
        
        asyncio.run(test_search())
    
    def test_tool_status_reporting(self):
        """Test tool status reporting"""
        async def test_status():
            await self.manager.initialize()
            
            # Execute some tools to generate data
            test_tools = list(self.manager.tools.values())[:3]
            for tool in test_tools:
                await self.manager.execute_tool(tool.tool_id, {})
            
            # Get tool status
            status = await self.manager.get_tool_status()
            
            self.assertIsInstance(status, dict)
            self.assertIn("total_tools", status)
            self.assertIn("active_sessions", status)
            self.assertIn("execution_history_count", status)
            self.assertIn("categories", status)
            self.assertIn("recent_executions", status)
            
            self.assertGreater(status["total_tools"], 0)
            self.assertGreaterEqual(status["execution_history_count"], 3)
        
        asyncio.run(test_status())
    
    def test_execution_history_persistence(self):
        """Test execution history persistence"""
        async def test_persistence():
            await self.manager.initialize()
            
            # Execute a tool
            test_tool = list(self.manager.tools.values())[0]
            result = await self.manager.execute_tool(test_tool.tool_id, {})
            
            # Check if execution was stored in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT tool_id, success, execution_time FROM tool_executions 
                WHERE tool_id = ? ORDER BY timestamp DESC LIMIT 1
            """, (test_tool.tool_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], test_tool.tool_id)
            self.assertEqual(bool(row[1]), result.success)
            self.assertEqual(row[2], result.execution_time)
        
        asyncio.run(test_persistence())
    
    def test_cleanup_functionality(self):
        """Test cleanup functionality"""
        async def test_cleanup():
            await self.manager.initialize()
            
            # Create some test data
            session_id = await self.manager.create_session("cleanup_test", {})
            
            # Execute some tools
            test_tool = list(self.manager.tools.values())[0]
            await self.manager.execute_tool(test_tool.tool_id, {})
            
            # Cleanup
            await self.manager.cleanup()
            
            # Verify cleanup
            self.assertEqual(len(self.manager.active_sessions), 0)
            
            # Database should still exist but connections should be closed
            self.assertTrue(os.path.exists(self.db_path))
        
        asyncio.run(test_cleanup())

class TestSpecificMCPTools(unittest.TestCase):
    """Test specific MCP tools functionality"""
    
    def setUp(self):
        """Set up test fixtures for specific tools"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_specific_tools.db")
        self.manager = MCPToolsManager(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_swarm_init_tool(self):
        """Test swarm initialization tool"""
        async def test_swarm_init():
            await self.manager.initialize()
            
            # Find swarm_init tool
            swarm_tools = [t for t in self.manager.tools.values() if t.name == "swarm_init"]
            self.assertGreater(len(swarm_tools), 0)
            
            swarm_tool = swarm_tools[0]
            
            # Test with valid topology
            result = await self.manager.execute_tool(swarm_tool.tool_id, {
                "topology": "hierarchical",
                "max_agents": 8,
                "strategy": "specialized"
            })
            
            self.assertTrue(result.success)
            self.assertIn("swarm_id", result.result_data)
            self.assertIn("topology", result.result_data)
            self.assertEqual(result.result_data["topology"], "hierarchical")
        
        asyncio.run(test_swarm_init())
    
    def test_memory_store_tool(self):
        """Test memory storage tool"""
        async def test_memory_store():
            await self.manager.initialize()
            
            # Find memory_store tool
            memory_tools = [t for t in self.manager.tools.values() if t.name == "memory_store"]
            self.assertGreater(len(memory_tools), 0)
            
            memory_tool = memory_tools[0]
            
            # Test storing data
            result = await self.manager.execute_tool(memory_tool.tool_id, {
                "key": "test_key",
                "value": {"data": "test_value", "timestamp": "2024-01-01"},
                "namespace": "test_namespace"
            })
            
            self.assertTrue(result.success)
            self.assertIn("stored", result.result_data)
            self.assertTrue(result.result_data["stored"])
        
        asyncio.run(test_memory_store())
    
    def test_performance_analyze_tool(self):
        """Test performance analysis tool"""
        async def test_performance_analyze():
            await self.manager.initialize()
            
            # Find performance_analyze tool
            perf_tools = [t for t in self.manager.tools.values() if t.name == "performance_analyze"]
            self.assertGreater(len(perf_tools), 0)
            
            perf_tool = perf_tools[0]
            
            # Test performance analysis
            result = await self.manager.execute_tool(perf_tool.tool_id, {
                "metrics": {
                    "execution_time": 25.5,
                    "memory_usage": 512,
                    "cpu_usage": 75.0
                },
                "baseline": {
                    "execution_time": 30.0,
                    "memory_usage": 600,
                    "cpu_usage": 80.0
                }
            })
            
            self.assertTrue(result.success)
            self.assertIn("analysis", result.result_data)
            self.assertIn("recommendations", result.result_data)
            self.assertIn("performance_score", result.result_data)
        
        asyncio.run(test_performance_analyze())

class TestMCPToolsIntegration(unittest.TestCase):
    """Integration tests for MCP Tools Manager"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "integration_mcp.db")
        
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_simulation(self):
        """Test complete MCP tools workflow"""
        async def test_workflow():
            manager = MCPToolsManager(db_path=self.db_path)
            await manager.initialize()
            
            # 1. Initialize swarm
            swarm_tools = [t for t in manager.tools.values() if t.name == "swarm_init"]
            swarm_result = await manager.execute_tool(swarm_tools[0].tool_id, {
                "topology": "mesh",
                "max_agents": 6,
                "strategy": "balanced"
            })
            
            self.assertTrue(swarm_result.success)
            swarm_id = swarm_result.result_data["swarm_id"]
            
            # 2. Create session
            session_id = await manager.create_session("workflow_test", {
                "swarm_id": swarm_id,
                "task": "integration_test"
            })
            
            # 3. Store some memory
            memory_tools = [t for t in manager.tools.values() if t.name == "memory_store"]
            memory_result = await manager.execute_tool(memory_tools[0].tool_id, {
                "key": "swarm_config",
                "value": {"swarm_id": swarm_id, "topology": "mesh"},
                "namespace": session_id
            })
            
            self.assertTrue(memory_result.success)
            
            # 4. Analyze performance (mock data)
            perf_tools = [t for t in manager.tools.values() if t.name == "performance_analyze"]
            perf_result = await manager.execute_tool(perf_tools[0].tool_id, {
                "metrics": {
                    "agents_active": 6,
                    "tasks_completed": 10,
                    "avg_response_time": 2.3
                }
            })
            
            self.assertTrue(perf_result.success)
            
            # 5. Get tool status to verify all operations
            status = await manager.get_tool_status()
            
            self.assertGreaterEqual(status["execution_history_count"], 3)
            self.assertEqual(status["active_sessions"], 1)
            
            # 6. Clean up session
            await manager.close_session(session_id)
            
            # Verify workflow completed successfully
            final_status = await manager.get_tool_status()
            self.assertEqual(final_status["active_sessions"], 0)
        
        asyncio.run(test_workflow())

if __name__ == '__main__':
    unittest.main()