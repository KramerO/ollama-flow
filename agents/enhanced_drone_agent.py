#!/usr/bin/env python3
"""
Enhanced Drone Agent with Refactored Role Management
Optimized performance and cleaner architecture
"""

import ollama
import asyncio
import os
from typing import Optional, List
import logging
from agents.base_agent import BaseAgent, AgentMessage
from agents.role_manager import get_role_manager, DroneRole

# Import enhanced components with fallbacks
try:
    from enhanced_code_generator import create_code_generator
    ENHANCED_CODEGEN_AVAILABLE = True
except ImportError:
    ENHANCED_CODEGEN_AVAILABLE = False
    logging.warning("⚠️ Enhanced code generator not available, using fallback")

try:
    from llm_chooser import get_llm_chooser
    LLM_CHOOSER_AVAILABLE = True
except ImportError:
    LLM_CHOOSER_AVAILABLE = False
    logging.warning("⚠️ LLM Chooser not available, using default models")

logger = logging.getLogger(__name__)

class EnhancedDroneAgent(BaseAgent):
    """Enhanced drone agent with optimized role management"""
    
    def __init__(self, agent_id: str, name: str, model: str = "llama3", 
                 project_folder_path: Optional[str] = None):
        super().__init__(agent_id, name)
        self.model = model
        self.project_folder_path = project_folder_path
        
        # Role management
        self.role_manager = get_role_manager()
        self.role: Optional[DroneRole] = None
        self.capabilities: List[str] = []
        
        # Enhanced components
        self._initialize_llm_chooser()
        self._initialize_code_generator()
        
    def _initialize_llm_chooser(self) -> None:
        """Initialize LLM chooser with error handling"""
        self.llm_chooser = None
        if LLM_CHOOSER_AVAILABLE:
            try:
                self.llm_chooser = get_llm_chooser()
                logger.info(f"✅ LLM Chooser initialized for {self.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize LLM Chooser: {e}")
    
    def _initialize_code_generator(self) -> None:
        """Initialize enhanced code generator with error handling"""
        self.code_generator = None
        if ENHANCED_CODEGEN_AVAILABLE:
            try:
                self.code_generator = create_code_generator()
                logger.info(f"✅ Enhanced code generator initialized for {self.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize enhanced code generator: {e}")
    
    def assign_dynamic_role(self, task: str) -> DroneRole:
        """Assign role using centralized role manager"""
        try:
            old_role = self.role.value if self.role else "None"
            
            # Use role manager for assignment
            assigned_role, capabilities = self.role_manager.assign_role(
                self.agent_id, self.name, task
            )
            
            # Update agent state
            self.role = assigned_role
            self.capabilities = capabilities
            
            # Enhanced role assignment output
            print(f"🎭 [EnhancedDroneAgent {self.name}] Dynamic role assignment: {old_role} -> {assigned_role.value}")
            print(f"🎯 [EnhancedDroneAgent {self.name}] Now specialized as: {assigned_role.value.upper()}")
            print(f"💪 [EnhancedDroneAgent {self.name}] Capabilities: {', '.join(capabilities)}")
            
            return assigned_role
            
        except Exception as e:
            logger.error(f"❌ Role assignment failed for {self.name}: {e}")
            # Fallback to developer role
            self.role = DroneRole.DEVELOPER
            self.capabilities = ["coding", "debugging", "testing"]
            print(f"🔄 [EnhancedDroneAgent {self.name}] Fallback to DEVELOPER role")
            return self.role
    
    async def _perform_task(self, prompt: str) -> str:
        """Perform task with enhanced error handling and role safety"""
        try:
            # Ensure role is assigned
            if not self.role:
                logger.warning(f"⚠️ [EnhancedDroneAgent {self.name}] No role assigned, using fallback")
                self.role = DroneRole.DEVELOPER
                self.capabilities = ["coding", "debugging", "testing"]
            
            # Choose optimal model
            selected_model = self._choose_optimal_model(prompt)
            
            role_name = self.role.value
            logger.info(f"🎯 {self.name} ({role_name}) uses model: {selected_model}")
            
            # Execute LLM call
            response = ollama.chat(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Process result based on role
            result = response["message"]["content"]
            result = self._apply_role_specific_processing(result, prompt)
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error in agent {self.name} ({self.agent_id}) task execution: {e}"
            logger.error(error_msg)
            print(error_msg)
            raise
    
    def _choose_optimal_model(self, task_context: str) -> str:
        """Choose optimal LLM model based on role and task context"""
        if self.llm_chooser and self.role:
            try:
                optimal_model = self.llm_chooser.choose_model_for_role(
                    self.role.value, task_context
                )
                logger.info(f"🎯 Model chosen for {self.role.value}: {optimal_model}")
                return optimal_model
            except Exception as e:
                logger.warning(f"⚠️ LLM selection failed, using fallback: {e}")
        
        return self.model  # Fallback to default
    
    def _apply_role_specific_processing(self, result: str, original_task: str) -> str:
        """Apply role-specific post-processing to results"""
        if not self.role:
            return result
        
        if self.role == DroneRole.SECURITY_SPECIALIST:
            return self._add_security_recommendations(result, original_task)
        elif self.role == DroneRole.ANALYST:
            return self._add_analysis_summary(result)
        elif self.role == DroneRole.DATA_SCIENTIST:
            return self._add_ml_insights(result)
        
        return result
    
    def _add_security_recommendations(self, result: str, original_task: str) -> str:
        """Add security specialist recommendations"""
        security_addendum = f"""

🔒 SECURITY SPECIALIST RECOMMENDATIONS:

IMMEDIATE ACTIONS:
• Code Review: Scan implementation for common vulnerabilities
• Security Testing: Plan penetration testing and security audits
• Dependency Check: Verify all dependencies for known vulnerabilities
• Access Control: Implement proper authentication and authorization

SECURITY CHECKLIST:
□ Input validation implemented
□ Output encoding applied
□ SQL injection prevention in place
□ XSS protection implemented
□ CSRF tokens used where applicable
□ Secure headers configured
□ Error handling doesn't leak sensitive information
□ Logging and monitoring configured

COMPLIANCE FRAMEWORK:
• OWASP Top 10 compliance verification
• GDPR data protection requirements
• Industry-specific security standards
• Regular security assessments planned

⚠️ SECURITY REMINDER: This analysis requires professional security review."""
        
        return result + security_addendum
    
    def _add_analysis_summary(self, result: str) -> str:
        """Add analyst-specific summary"""
        return result + f"""

📊 ANALYST INSIGHTS:
• Data-driven decision making applied
• Key performance indicators identified  
• Actionable recommendations provided
• Risk assessment included"""
    
    def _add_ml_insights(self, result: str) -> str:
        """Add data scientist ML insights"""
        return result + f"""

🧠 ML/AI INSIGHTS:
• Model validation strategies recommended
• Feature engineering opportunities identified
• Performance optimization suggestions included
• Scalability considerations addressed"""
    
    async def _analyze_and_execute_task(self, task: str) -> str:
        """Analyze task, assign role, and execute with enhanced processing"""
        # Ensure role assignment
        if not self.role:
            try:
                assigned_role = self.assign_dynamic_role(task)
                logger.info(f"✅ [EnhancedDroneAgent {self.name}] Role assigned: {assigned_role.value}")
            except Exception as e:
                logger.error(f"❌ [EnhancedDroneAgent {self.name}] Role assignment failed: {e}")
                # Set fallback role
                self.role = DroneRole.DEVELOPER
                self.capabilities = ["coding", "debugging", "testing"]
                logger.info(f"🔄 [EnhancedDroneAgent {self.name}] Using fallback DEVELOPER role")
        
        # Create enhanced prompt
        enhanced_prompt = self._create_role_enhanced_prompt(task)
        
        # Execute task
        result = await self._perform_task(enhanced_prompt)
        
        # Parse and execute commands
        command_output = await self._extract_and_execute_commands(result)
        if command_output:
            result += f"\n\n=== COMMAND EXECUTION RESULTS ===\n{command_output}"
        
        # Handle code generation if applicable
        if self._should_generate_code(task):
            result = await self._handle_code_generation(result, task)
        
        return result
    
    def _create_role_enhanced_prompt(self, task: str) -> str:
        """Create role-enhanced prompt with specialized context"""
        if not self.role:
            return task
        
        role_context = self._get_role_context()
        
        enhanced_prompt = f"""{role_context}

TASK: {task}

CAPABILITIES: {', '.join(self.capabilities)}

WORKING DIRECTORY: {self.project_folder_path or '.'}

EXECUTION REQUIREMENTS:
• Create functional implementations, not placeholders
• Use proper error handling and validation
• Follow role-specific best practices
• Provide clear, actionable results"""
        
        return enhanced_prompt
    
    def _get_role_context(self) -> str:
        """Get detailed role-specific context"""
        if not self.role:
            return "🎯 ROLE: DYNAMIC ASSIGNMENT - Analyzing task to determine optimal role"
        
        role_contexts = {
            DroneRole.ANALYST: """
🎯 ROLE: ANALYST DRONE - Data Intelligence Specialist

CORE EXPERTISE:
• Advanced statistical analysis and data interpretation
• Business intelligence and KPI development
• Market research and competitive analysis  
• Risk assessment and impact analysis
• Performance metrics and trend identification
• Report generation with actionable insights""",
            
            DroneRole.DATA_SCIENTIST: """
🎯 ROLE: DATA SCIENTIST DRONE - ML/AI Implementation Specialist

CORE EXPERTISE:
• Machine Learning model design, training & optimization
• Computer Vision with OpenCV, TensorFlow, PyTorch
• Deep Learning architectures (CNN, RNN, Transformers)
• Statistical modeling and feature engineering
• Data pipeline architecture and ETL processes
• MLOps and model deployment strategies""",
            
            DroneRole.IT_ARCHITECT: """
🎯 ROLE: IT ARCHITECT DRONE - Enterprise System Designer

CORE EXPERTISE:
• Enterprise architecture patterns and best practices
• Cloud-native design (AWS, Azure, GCP)
• Microservices and distributed systems architecture
• API design and integration strategies
• Database architecture and data modeling
• Infrastructure as Code (IaC) and automation""",
            
            DroneRole.DEVELOPER: """
🎯 ROLE: DEVELOPER DRONE - Software Implementation Expert

CORE EXPERTISE:
• Full-stack development (Python, JavaScript, TypeScript)
• Backend systems (FastAPI, Django, Flask)
• Frontend frameworks (React, Vue, Angular)
• Database design and optimization (SQL, NoSQL)
• DevOps and CI/CD pipeline implementation
• Test-driven development and quality assurance""",
            
            DroneRole.SECURITY_SPECIALIST: """
🎯 ROLE: SECURITY SPECIALIST DRONE - Cybersecurity & Compliance Expert

CORE EXPERTISE:
• Security architecture design and threat modeling
• Vulnerability assessment and penetration testing
• Secure coding practices and code review
• Identity & Access Management (IAM) systems
• Encryption, PKI, and cryptographic implementations
• Compliance frameworks (GDPR, SOC2, PCI-DSS, NIST)"""
        }
        
        return role_contexts.get(self.role, f"You are a specialized {self.role.value} drone agent.")
    
    def _should_generate_code(self, task: str) -> bool:
        """Determine if task requires code generation"""
        code_indicators = ["python", ".py", "script", "code", "program", "implement", "build"]
        return any(indicator in task.lower() for indicator in code_indicators)
    
    async def _handle_code_generation(self, result: str, task: str) -> str:
        """Handle enhanced code generation with validation"""
        if not self.code_generator or not self.project_folder_path:
            return result
        
        try:
            # Use enhanced code generator
            code_result = self.code_generator.extract_and_validate_code(result, task)
            
            if code_result['code'] and code_result['is_valid']:
                file_path = os.path.join(self.project_folder_path, code_result['filename'])
                
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(code_result['code'])
                
                result += f"\n\n✅ Enhanced code validation passed"
                result += f"\n✅ {code_result['language'].upper()} code saved to: {file_path}"
                
                if code_result['issues']:
                    result += f"\n⚠️ Code issues detected: {', '.join(code_result['issues'])}"
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Code generation failed: {e}")
            return result
    
    async def _extract_and_execute_commands(self, llm_response: str) -> str:
        """Extract and execute shell commands from LLM response"""
        import re
        
        command_patterns = [
            r'```bash\n(.*?)\n```',
            r'```shell\n(.*?)\n```',
            r'```\n(.*?)\n```'
        ]
        
        commands_executed = []
        
        for pattern in command_patterns:
            matches = re.findall(pattern, llm_response, re.MULTILINE | re.DOTALL)
            for match in matches:
                command_lines = [line.strip() for line in match.split('\n') if line.strip()]
                for command in command_lines:
                    if command and not command.startswith('#'):
                        try:
                            role_name = self.role.value if self.role else "dynamic"
                            print(f"[EnhancedDroneAgent {self.name} ({role_name})] Executing: {command}")
                            result = await self._run_command(command)
                            commands_executed.append(f"Command: {command}\nResult: {result}")
                        except Exception as e:
                            commands_executed.append(f"Command: {command}\nError: {str(e)}")
        
        return "\n\n".join(commands_executed) if commands_executed else ""
    
    async def _run_command(self, command: str) -> str:
        """Execute shell command with proper error handling"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_folder_path if self.project_folder_path else None
        )
        stdout, stderr = await process.communicate()

        output = ""
        if stdout:
            output += f"Stdout:\n{stdout.decode().strip()}\n"
        if stderr:
            output += f"Stderr:\n{stderr.decode().strip()}\n"
        if process.returncode != 0:
            output += f"Error: Command exited with code {process.returncode}\n"
        
        return output.strip()
    
    async def receive_message(self, message: AgentMessage):
        """Enhanced message processing with comprehensive error handling"""
        role_name = self.role.value if self.role else "dynamic"
        print(f"EnhancedDroneAgent {self.name} ({self.agent_id}) with role {role_name} received message from {message.sender_id}: {message.content}")

        try:
            # Process task with role assignment and execution
            result = await self._analyze_and_execute_task(message.content)
            
            # Add role information to response
            final_role = self.role.value if self.role else "dynamic"
            role_info = f"\n[Completed by {final_role} drone: {self.name}]"
            final_response = result + role_info
            
            # Send response
            await self.send_message(message.sender_id, "response", final_response, message.request_id)
            
        except Exception as e:
            error_msg = f"❌ Error in enhanced agent {self.name}: {e}"
            logger.error(error_msg)
            await self.send_message(message.sender_id, "error", error_msg, message.request_id)
    
    def get_role_info(self) -> dict:
        """Get comprehensive role information"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value if self.role else "dynamic",
            "capabilities": self.capabilities,
            "model": self.model,
            "enhanced_features": {
                "llm_chooser": LLM_CHOOSER_AVAILABLE,
                "code_generator": ENHANCED_CODEGEN_AVAILABLE,
                "role_manager": True
            }
        }