#!/usr/bin/env python3
"""
Unified Agent System - Consolidates all agent functionality
Replaces multiple agent classes with a single, configurable agent
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

from agents.base_agent import BaseAgent, AgentMessage
from agents.role_manager import get_role_manager, DroneRole
from llm_chooser import get_llm_chooser
from config.settings import get_settings

# Import capabilities
from agents.capabilities.code_generation import CodeGenerationCapability
from agents.capabilities.command_execution import CommandExecutionCapability
from agents.capabilities.security_analysis import SecurityAnalysisCapability

logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Agent performance and usage metrics"""
    tasks_completed: int = 0
    total_execution_time: float = 0.0
    errors_encountered: int = 0
    model_switches: int = 0
    last_active: Optional[float] = None
    role_changes: int = 0
    
    @property
    def average_execution_time(self) -> float:
        return self.total_execution_time / max(self.tasks_completed, 1)

class AgentState(Enum):
    """Agent operational states"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class UnifiedAgent(BaseAgent):
    """
    Unified agent that consolidates functionality from all previous agent types
    Uses capability pattern for extensibility and role-based optimization
    """
    
    def __init__(self, 
                 agent_id: str, 
                 name: str, 
                 model: Optional[str] = None,
                 capabilities: Optional[List[str]] = None,
                 project_folder_path: Optional[str] = None):
        super().__init__(agent_id, name)
        
        # Configuration
        self.settings = get_settings()
        self.model = model or self.settings.llm.default_model
        self.project_folder_path = project_folder_path or self.settings.agents.project_folder
        
        # Core components
        self.role_manager = get_role_manager()
        self.llm_chooser = get_llm_chooser()
        
        # Agent state
        self.state = AgentState.IDLE
        self.current_role: Optional[DroneRole] = None
        self.role_capabilities: List[str] = []
        self.metrics = AgentMetrics()
        
        # Capability system
        self.capabilities: Dict[str, Any] = {}
        self._initialize_capabilities(capabilities or [])
        
        # Performance optimization
        self._response_cache: Dict[str, Any] = {}
        self._cache_ttl = self.settings.llm.cache_ttl
        
        logger.info(f"✅ UnifiedAgent {self.name} initialized with {len(self.capabilities)} capabilities")
    
    def _initialize_capabilities(self, requested_capabilities: List[str]) -> None:
        """Initialize agent capabilities based on configuration and requests"""
        available_capabilities = {
            'code_generation': CodeGenerationCapability,
            'command_execution': CommandExecutionCapability,
            'security_analysis': SecurityAnalysisCapability,
        }
        
        # Enable all capabilities by default, or only requested ones
        if not requested_capabilities:
            requested_capabilities = list(available_capabilities.keys())
        
        for cap_name in requested_capabilities:
            if cap_name in available_capabilities:
                try:
                    self.capabilities[cap_name] = available_capabilities[cap_name](
                        agent=self,
                        settings=self.settings
                    )
                    logger.info(f"✅ Capability '{cap_name}' enabled for {self.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize capability '{cap_name}': {e}")
    
    async def assign_dynamic_role(self, task: str) -> DroneRole:
        """Assign optimal role based on task analysis"""
        try:
            self.state = AgentState.PROCESSING
            start_time = time.time()
            
            # Get previous role for comparison
            old_role = self.current_role.value if self.current_role else "None"
            
            # Use centralized role manager
            assigned_role, capabilities = self.role_manager.assign_role(
                self.agent_id, self.name, task
            )
            
            # Update agent state
            if self.current_role != assigned_role:
                self.current_role = assigned_role
                self.role_capabilities = capabilities
                self.metrics.role_changes += 1
                
                logger.info(f"🎭 {self.name}: Role change {old_role} → {assigned_role.value}")
                
                # Optimize capabilities based on new role
                await self._optimize_capabilities_for_role(assigned_role)
            
            self.metrics.last_active = time.time()
            execution_time = time.time() - start_time
            logger.debug(f"⏱️ Role assignment took {execution_time:.2f}s")
            
            return assigned_role
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.metrics.errors_encountered += 1
            logger.error(f"❌ Role assignment failed for {self.name}: {e}")
            
            # Fallback to developer role
            self.current_role = DroneRole.DEVELOPER
            self.role_capabilities = ["coding", "debugging", "testing"]
            return self.current_role
        finally:
            if self.state != AgentState.ERROR:
                self.state = AgentState.IDLE
    
    async def _optimize_capabilities_for_role(self, role: DroneRole) -> None:
        """Optimize agent capabilities based on assigned role"""
        role_capability_priority = {
            DroneRole.DEVELOPER: ['code_generation', 'command_execution'],
            DroneRole.SECURITY_SPECIALIST: ['security_analysis', 'code_generation'],
            DroneRole.DATA_SCIENTIST: ['code_generation', 'command_execution'],
            DroneRole.IT_ARCHITECT: ['code_generation', 'security_analysis'],
            DroneRole.ANALYST: ['command_execution', 'security_analysis']
        }
        
        priority_caps = role_capability_priority.get(role, [])
        
        # Configure capabilities for optimal performance based on role
        for cap_name, capability in self.capabilities.items():
            if hasattr(capability, 'configure_for_role'):
                await capability.configure_for_role(role, cap_name in priority_caps)
    
    def _choose_optimal_model(self, task_context: str) -> str:
        """Choose optimal LLM model with caching and fallback"""
        try:
            if self.current_role:
                optimal_model = self.llm_chooser.choose_model_for_role(
                    self.current_role.value, task_context
                )
                
                if optimal_model != self.model:
                    self.metrics.model_switches += 1
                    logger.info(f"🔄 {self.name}: Model switch {self.model} → {optimal_model}")
                    
                return optimal_model
            
        except Exception as e:
            logger.warning(f"⚠️ Model selection failed, using fallback: {e}")
        
        return self.model
    
    async def _execute_with_capabilities(self, task: str, llm_response: str) -> str:
        """Execute task using available capabilities"""
        enhanced_response = llm_response
        
        # Apply capabilities in priority order based on role
        capability_order = self._get_capability_execution_order()
        
        for cap_name in capability_order:
            if cap_name in self.capabilities:
                try:
                    capability = self.capabilities[cap_name]
                    if await capability.should_execute(task, enhanced_response):
                        result = await capability.execute(task, enhanced_response)
                        enhanced_response = result
                        logger.debug(f"✅ Applied capability '{cap_name}' in {self.name}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Capability '{cap_name}' failed: {e}")
                    continue
        
        return enhanced_response
    
    def _get_capability_execution_order(self) -> List[str]:
        """Get capability execution order based on current role"""
        role_orders = {
            DroneRole.DEVELOPER: ['code_generation', 'command_execution', 'security_analysis'],
            DroneRole.SECURITY_SPECIALIST: ['security_analysis', 'code_generation', 'command_execution'],
            DroneRole.DATA_SCIENTIST: ['code_generation', 'command_execution', 'security_analysis'],
            DroneRole.IT_ARCHITECT: ['code_generation', 'security_analysis', 'command_execution'],
            DroneRole.ANALYST: ['command_execution', 'security_analysis', 'code_generation']
        }
        
        return role_orders.get(self.current_role, ['code_generation', 'command_execution', 'security_analysis'])
    
    def _cache_key(self, task: str, model: str) -> str:
        """Generate cache key for response caching"""
        return f"{model}:{hash(task):x}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if not self.settings.llm.enable_caching:
            return None
            
        cached = self._response_cache.get(cache_key)
        if cached and time.time() - cached['timestamp'] < self._cache_ttl:
            return cached
        
        # Remove expired cache entry
        if cached:
            del self._response_cache[cache_key]
        
        return None
    
    def _cache_response(self, cache_key: str, response: str) -> None:
        """Cache LLM response"""
        if self.settings.llm.enable_caching:
            self._response_cache[cache_key] = {
                'response': response,
                'timestamp': time.time()
            }
    
    async def _perform_task(self, task: str) -> str:
        """Execute task with full optimization and capability support"""
        start_time = time.time()
        
        try:
            self.state = AgentState.PROCESSING
            
            # Ensure role is assigned
            if not self.current_role:
                await self.assign_dynamic_role(task)
            
            # Choose optimal model
            selected_model = self._choose_optimal_model(task)
            
            # Check cache first
            cache_key = self._cache_key(task, selected_model)
            cached_response = self._get_cached_response(cache_key)
            
            if cached_response:
                logger.info(f"💾 Cache hit for {self.name}")
                llm_response = cached_response['response']
            else:
                # Create role-enhanced prompt
                enhanced_prompt = self._create_role_enhanced_prompt(task)
                
                # Execute LLM request
                logger.info(f"🎯 {self.name} ({self.current_role.value}) using {selected_model}")
                
                import ollama
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: ollama.chat(
                        model=selected_model,
                        messages=[{"role": "user", "content": enhanced_prompt}],
                    )
                )
                
                llm_response = response["message"]["content"]
                self._cache_response(cache_key, llm_response)
            
            # Apply capabilities
            final_response = await self._execute_with_capabilities(task, llm_response)
            
            # Add role-specific enhancements
            final_response = self._apply_role_specific_processing(final_response, task)
            
            # Update metrics
            execution_time = time.time() - start_time
            self.metrics.tasks_completed += 1
            self.metrics.total_execution_time += execution_time
            self.metrics.last_active = time.time()
            
            logger.info(f"✅ {self.name} completed task in {execution_time:.2f}s")
            
            return final_response
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.metrics.errors_encountered += 1
            error_msg = f"❌ Task execution failed in {self.name}: {e}"
            logger.error(error_msg)
            raise
            
        finally:
            if self.state != AgentState.ERROR:
                self.state = AgentState.IDLE
    
    def _create_role_enhanced_prompt(self, task: str) -> str:
        """Create optimized prompt with role context and capabilities"""
        if not self.current_role:
            return task
        
        role_context = self._get_role_context()
        capabilities_list = ", ".join(self.role_capabilities)
        
        enhanced_prompt = f"""{role_context}

TASK: {task}

SPECIALIZED CAPABILITIES: {capabilities_list}
AVAILABLE TOOLS: {list(self.capabilities.keys())}
WORKING DIRECTORY: {self.project_folder_path or '.'}

EXECUTION REQUIREMENTS:
• Provide functional, production-ready implementations
• Use appropriate error handling and validation
• Follow role-specific best practices and standards
• Leverage available capabilities for optimal results
• Consider performance and security implications

RESPONSE FORMAT:
• Clear, actionable results with proper structure
• Include implementation details and reasoning
• Provide next steps or recommendations where applicable"""

        return enhanced_prompt
    
    def _get_role_context(self) -> str:
        """Get detailed, role-specific context"""
        role_contexts = {
            DroneRole.ANALYST: """
🎯 ROLE: SENIOR DATA ANALYST - Business Intelligence & Analytics Expert

CORE EXPERTISE:
• Advanced statistical analysis and data interpretation
• Business intelligence dashboard creation and KPI development  
• Market research, competitive analysis, and trend identification
• Risk assessment, impact analysis, and strategic recommendations
• Performance metrics optimization and reporting automation
• Data visualization with actionable insights and storytelling""",
            
            DroneRole.DATA_SCIENTIST: """
🎯 ROLE: SENIOR DATA SCIENTIST - ML/AI Implementation Specialist

CORE EXPERTISE:
• Machine Learning model design, training, validation, and deployment
• Deep Learning architectures (CNN, RNN, Transformers, GANs)
• Computer Vision with OpenCV, TensorFlow, PyTorch, and scikit-learn
• Natural Language Processing and text analytics
• Statistical modeling, feature engineering, and data pipeline architecture
• MLOps, model monitoring, A/B testing, and performance optimization""",
            
            DroneRole.IT_ARCHITECT: """
🎯 ROLE: ENTERPRISE IT ARCHITECT - System Design & Infrastructure Expert

CORE EXPERTISE:
• Enterprise architecture patterns, microservices, and distributed systems
• Cloud-native design with AWS, Azure, GCP, and hybrid architectures
• API design, integration patterns, and service mesh implementations
• Database architecture, data modeling, and performance optimization
• Infrastructure as Code (Terraform, Ansible), CI/CD, and DevOps practices
• Security architecture, compliance frameworks, and scalability planning""",
            
            DroneRole.DEVELOPER: """
🎯 ROLE: SENIOR FULL-STACK DEVELOPER - Software Implementation Expert

CORE EXPERTISE:
• Full-stack development with Python, JavaScript, TypeScript, and modern frameworks
• Backend systems: FastAPI, Django, Flask, Node.js, and microservices
• Frontend frameworks: React, Vue, Angular, and responsive design
• Database design and optimization (PostgreSQL, MongoDB, Redis)
• DevOps: Docker, Kubernetes, CI/CD pipelines, and cloud deployment
• Test-driven development, code quality, and performance optimization""",
            
            DroneRole.SECURITY_SPECIALIST: """
🎯 ROLE: CYBERSECURITY ARCHITECT - Security & Compliance Expert

CORE EXPERTISE:
• Security architecture design, threat modeling, and risk assessment
• Vulnerability assessment, penetration testing, and security auditing
• Secure coding practices, code review, and security by design
• Identity & Access Management (IAM), Zero Trust, and authentication systems
• Encryption, PKI, cryptographic implementations, and data protection
• Compliance frameworks (GDPR, SOC2, PCI-DSS, NIST, ISO 27001)"""
        }
        
        return role_contexts.get(
            self.current_role, 
            f"🎯 ROLE: SPECIALIZED {self.current_role.value.upper()} AGENT"
        )
    
    def _apply_role_specific_processing(self, result: str, original_task: str) -> str:
        """Apply role-specific post-processing and recommendations"""
        if not self.current_role:
            return result
        
        role_processors = {
            DroneRole.SECURITY_SPECIALIST: self._add_security_analysis,
            DroneRole.ANALYST: self._add_business_insights,
            DroneRole.DATA_SCIENTIST: self._add_ml_recommendations,
            DroneRole.IT_ARCHITECT: self._add_architecture_considerations,
            DroneRole.DEVELOPER: self._add_development_notes
        }
        
        processor = role_processors.get(self.current_role)
        if processor:
            return processor(result, original_task)
        
        return result
    
    def _add_security_analysis(self, result: str, task: str) -> str:
        """Add comprehensive security analysis and recommendations"""
        return result + f"""

🔒 SECURITY SPECIALIST ANALYSIS:

SECURITY ASSESSMENT:
• Threat Model: Analyzed potential attack vectors and vulnerabilities
• Risk Level: {self._assess_security_risk(task)}
• Compliance: Reviewed against OWASP Top 10 and industry standards

IMMEDIATE SECURITY ACTIONS:
• Code Review: Static analysis for security vulnerabilities required
• Dependency Audit: Verify all dependencies for known CVEs  
• Access Control: Implement proper authentication and authorization
• Data Protection: Ensure sensitive data encryption and secure handling

SECURITY CHECKLIST:
□ Input validation and sanitization implemented
□ Output encoding and XSS protection applied
□ SQL injection prevention measures in place
□ CSRF protection and secure session management
□ Security headers configured (HSTS, CSP, etc.)
□ Error handling doesn't leak sensitive information
□ Comprehensive logging and monitoring enabled
□ Regular security testing scheduled

COMPLIANCE VERIFICATION:
• GDPR: Data protection and privacy requirements
• SOC2: Security controls and audit readiness  
• Industry Standards: Sector-specific security requirements

⚠️ CRITICAL: This implementation requires professional security review before production deployment."""
    
    def _add_business_insights(self, result: str, task: str) -> str:
        """Add business analysis and strategic insights"""
        return result + f"""

📊 BUSINESS ANALYST INSIGHTS:

STRATEGIC ANALYSIS:
• Business Impact: {self._assess_business_impact(task)}
• ROI Potential: Estimated positive impact on key business metrics
• Risk Assessment: Low to moderate implementation risk identified

KEY PERFORMANCE INDICATORS:
• Efficiency Metrics: Implementation should improve operational efficiency
• Quality Metrics: Enhanced accuracy and consistency expected
• User Experience: Improved usability and satisfaction anticipated

ACTIONABLE RECOMMENDATIONS:
• Stakeholder Engagement: Identify key stakeholders for feedback and buy-in
• Change Management: Plan phased rollout with training and support
• Success Metrics: Define measurable outcomes and monitoring processes
• Continuous Improvement: Establish feedback loops and optimization cycles

BUSINESS VALUE PROPOSITION:
• Cost Reduction: Automation and efficiency improvements
• Revenue Enhancement: Better decision-making and customer experience
• Competitive Advantage: Innovation and market differentiation
• Risk Mitigation: Improved compliance and operational reliability"""
    
    def _add_ml_recommendations(self, result: str, task: str) -> str:
        """Add machine learning and data science insights"""
        return result + f"""

🧠 DATA SCIENTIST RECOMMENDATIONS:

ML/AI OPTIMIZATION OPPORTUNITIES:
• Model Performance: Consider ensemble methods and hyperparameter tuning
• Feature Engineering: Identify additional features for improved accuracy
• Data Quality: Implement data validation and anomaly detection
• Scalability: Plan for distributed training and inference

TECHNICAL IMPLEMENTATION:
• Framework Selection: Optimized for performance and maintainability
• Model Validation: Cross-validation and statistical significance testing
• Monitoring: Real-time model performance and drift detection
• A/B Testing: Experimental design for model comparison

DATA PIPELINE CONSIDERATIONS:
• ETL Processes: Robust data extraction, transformation, and loading
• Data Versioning: Track data lineage and reproducibility
• Feature Store: Centralized feature management and serving
• Model Registry: Version control and deployment management

PERFORMANCE METRICS:
• Accuracy Metrics: Precision, recall, F1-score, and domain-specific KPIs
• Operational Metrics: Latency, throughput, and resource utilization
• Business Metrics: ROI, conversion rates, and user engagement"""
    
    def _add_architecture_considerations(self, result: str, task: str) -> str:
        """Add architectural design considerations"""
        return result + f"""

🏗️ IT ARCHITECT DESIGN CONSIDERATIONS:

ARCHITECTURE PRINCIPLES:
• Scalability: Horizontal and vertical scaling strategies
• Reliability: High availability and disaster recovery planning
• Maintainability: Modular design and clean code practices
• Security: Defense in depth and security by design

TECHNICAL RECOMMENDATIONS:
• Microservices: Service decomposition and API design
• Cloud Strategy: Multi-cloud or hybrid deployment options
• Data Architecture: Database selection and data modeling
• Integration Patterns: API management and event-driven architecture

OPERATIONAL EXCELLENCE:
• Monitoring: Comprehensive observability and alerting
• CI/CD: Automated testing and deployment pipelines
• Infrastructure: Infrastructure as Code and configuration management
• Performance: Load testing and capacity planning

GOVERNANCE FRAMEWORK:
• Standards: Technical standards and best practices
• Documentation: Architecture decision records and documentation
• Review Process: Architecture review board and approval workflows
• Compliance: Regulatory and organizational requirements"""
    
    def _add_development_notes(self, result: str, task: str) -> str:
        """Add development best practices and notes"""
        return result + f"""

💻 DEVELOPMENT IMPLEMENTATION NOTES:

CODE QUALITY STANDARDS:
• Testing: Unit tests, integration tests, and test coverage > 80%
• Documentation: Inline comments, docstrings, and README updates
• Code Style: Follow PEP8, ESLint rules, and consistent formatting
• Version Control: Meaningful commit messages and branching strategy

TECHNICAL DEBT MANAGEMENT:
• Refactoring: Identify areas for code improvement and optimization
• Dependencies: Keep dependencies updated and secure
• Performance: Profile code and optimize bottlenecks
• Monitoring: Add logging, metrics, and error tracking

DEVELOPMENT WORKFLOW:
• Environment Setup: Docker containers and development environments
• IDE Configuration: Linting, formatting, and debugging setup
• Code Review: Pull request templates and review checklists
• Deployment: Staging environments and rollback procedures

NEXT STEPS:
• Implementation Planning: Break down into manageable tasks
• Resource Requirements: Estimate time, effort, and dependencies
• Risk Mitigation: Identify potential issues and contingency plans
• Success Criteria: Define completion criteria and acceptance tests"""
    
    def _assess_security_risk(self, task: str) -> str:
        """Assess security risk level based on task content"""
        high_risk_keywords = ['admin', 'root', 'password', 'token', 'secret', 'api_key', 'database', 'sql']
        medium_risk_keywords = ['user', 'login', 'auth', 'permission', 'access', 'data', 'file']
        
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in high_risk_keywords):
            return "HIGH - Requires immediate security review"
        elif any(keyword in task_lower for keyword in medium_risk_keywords):
            return "MEDIUM - Security considerations required"
        else:
            return "LOW - Standard security practices apply"
    
    def _assess_business_impact(self, task: str) -> str:
        """Assess potential business impact"""
        high_impact_keywords = ['revenue', 'customer', 'production', 'critical', 'urgent']
        medium_impact_keywords = ['efficiency', 'process', 'workflow', 'automation', 'optimization']
        
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in high_impact_keywords):
            return "HIGH - Direct impact on business operations or revenue"
        elif any(keyword in task_lower for keyword in medium_impact_keywords):
            return "MEDIUM - Operational efficiency improvements expected"
        else:
            return "LOW - Limited business impact, mostly technical enhancement"
    
    async def receive_message(self, message: AgentMessage):
        """Process incoming message with full capability support"""
        try:
            role_name = self.current_role.value if self.current_role else "dynamic"
            logger.info(f"📨 {self.name} ({role_name}) received task from {message.sender_id}")
            
            # Assign role if needed
            if not self.current_role:
                await self.assign_dynamic_role(message.content)
            
            # Execute task
            result = await self._perform_task(message.content)
            
            # Add execution metadata
            metadata = f"\n\n[✅ Completed by {self.current_role.value} agent: {self.name}]"
            metadata += f"\n[⏱️ Execution time: {self.metrics.average_execution_time:.2f}s avg]"
            metadata += f"\n[🎯 Success rate: {self._calculate_success_rate():.1%}]"
            
            final_response = result + metadata
            
            # Send response
            await self.send_message(message.sender_id, "response", final_response, message.request_id)
            
        except Exception as e:
            error_msg = f"❌ Error in unified agent {self.name}: {e}"
            logger.error(error_msg)
            await self.send_message(message.sender_id, "error", error_msg, message.request_id)
    
    def _calculate_success_rate(self) -> float:
        """Calculate agent success rate"""
        total_tasks = self.metrics.tasks_completed + self.metrics.errors_encountered
        if total_tasks == 0:
            return 1.0
        return self.metrics.tasks_completed / total_tasks
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status and metrics"""
        return {
            "agent_info": {
                "id": self.agent_id,
                "name": self.name,
                "state": self.state.value,
                "current_role": self.current_role.value if self.current_role else None,
                "model": self.model
            },
            "capabilities": {
                "active_capabilities": list(self.capabilities.keys()),
                "role_capabilities": self.role_capabilities,
                "project_folder": self.project_folder_path
            },
            "performance_metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "success_rate": self._calculate_success_rate(),
                "average_execution_time": self.metrics.average_execution_time,
                "total_execution_time": self.metrics.total_execution_time,
                "errors_encountered": self.metrics.errors_encountered,
                "model_switches": self.metrics.model_switches,
                "role_changes": self.metrics.role_changes,
                "last_active": self.metrics.last_active,
                "cache_hit_rate": len(self._response_cache) / max(self.metrics.tasks_completed, 1)
            },
            "configuration": {
                "caching_enabled": self.settings.llm.enable_caching,
                "max_model_size": self.settings.llm.max_model_size_gb,
                "command_execution_enabled": self.settings.agents.enable_command_execution,
                "code_generation_enabled": self.settings.agents.enable_code_generation
            }
        }
    
    def __str__(self) -> str:
        role = self.current_role.value if self.current_role else "dynamic"
        return f"UnifiedAgent({self.name}, role={role}, state={self.state.value})"