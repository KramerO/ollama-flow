import ollama
import asyncio
import subprocess
from typing import Optional, Any, List
import re
import os
from enum import Enum
import logging

from agents.base_agent import BaseAgent, AgentMessage

# Import enhanced code generator
try:
    from enhanced_code_generator import create_code_generator
    ENHANCED_CODEGEN_AVAILABLE = True
except ImportError:
    ENHANCED_CODEGEN_AVAILABLE = False
    print("⚠️ Enhanced code generator not available, using fallback")

# Import LLM Chooser
try:
    from llm_chooser import get_llm_chooser, choose_model_for_role
    LLM_CHOOSER_AVAILABLE = True
except ImportError:
    LLM_CHOOSER_AVAILABLE = False
    print("⚠️ LLM Chooser not available, using default models")

logger = logging.getLogger(__name__)

class DroneRole(Enum):
    """Different roles a drone can take"""
    ANALYST = "analyst"
    DATA_SCIENTIST = "datascientist"
    IT_ARCHITECT = "it_architect"
    DEVELOPER = "developer"
    SECURITY_SPECIALIST = "security_specialist"

class DroneAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str = "llama3", project_folder_path: Optional[str] = None, role: DroneRole = DroneRole.DEVELOPER):
        super().__init__(agent_id, name)
        self.model = model  # Fallback model
        self.project_folder_path = project_folder_path
        self.role = role
        self.capabilities = self._get_role_capabilities()
        
        # Initialize LLM Chooser for dynamic model selection
        self.llm_chooser = None
        if LLM_CHOOSER_AVAILABLE:
            try:
                self.llm_chooser = get_llm_chooser()
                logger.info(f"✅ LLM Chooser initialized for {self.name} ({self.role.value})")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize LLM Chooser: {e}")
        
        # Initialize enhanced code generator if available
        self.code_generator = None
        if ENHANCED_CODEGEN_AVAILABLE:
            try:
                self.code_generator = create_code_generator()
                logger.info(f"✅ Enhanced code generator initialized for {self.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize enhanced code generator: {e}")

    async def _perform_task(self, prompt: str) -> str:
        try:
            # Wähle optimales LLM basierend auf Rolle und Task
            selected_model = self._choose_optimal_model(prompt)
            
            # Erweitere Prompt um rollenspezifische Kontexte
            enhanced_prompt = self._enhance_prompt_for_role(prompt)
            
            logger.info(f"🎯 {self.name} ({self.role.value}) uses model: {selected_model}")
            
            response = ollama.chat(
                model=selected_model,
                messages=[{"role": "user", "content": enhanced_prompt}],
            )
            
            # Post-processing basierend auf Rolle
            result = response["message"]["content"]
            if self.role == DroneRole.SECURITY_SPECIALIST:
                result = self._add_security_recommendations(result, prompt)
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Task execution failed for {self.name}: {e}")
            print(f"Error performing task: {e}")
            raise

    async def _run_command(self, command: str) -> str:
        print(f"[DroneAgent {self.name} ({self.role.value})] Executing command: {command}")
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

    async def _handle_file_saving(self, message_content: str, result: str) -> str:
        save_message = ""
        
        # Enhanced regex patterns for file saving with German and English support
        save_patterns = [
            r"(?:speichere sie (?:im Projektordner )?(?:unter|als))\s+([\w\.-]+)",
            r"(?:save it (?:to|as))\s+([\w\.-]+)",
            r"(?:erstelle|create).*?(?:als|as)\s+([\w\.-]+)",
            r"(?:datei|file).*?([\w\.-]+\.py)",
            r"(app\.py|[\w\.-]+\.py)"  # Match any .py file mentioned
        ]
        
        save_match = None
        for pattern in save_patterns:
            save_match = re.search(pattern, message_content, re.IGNORECASE)
            if save_match:
                break
        
        # Also check if this is a Flask app task specifically
        if not save_match and ("flask" in message_content.lower() or "hello world" in message_content.lower()):
            save_match = type('Match', (), {'group': lambda self, x: 'app.py'})()

        if save_match and self.project_folder_path:
            target_path = save_match.group(1).strip()
            full_path = os.path.join(self.project_folder_path, target_path)

            # Enhanced code extraction from result
            content_to_write = self._extract_code_content(result)

            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding='utf-8') as f:
                    f.write(content_to_write)
                save_message = f"\n✅ File saved to: {full_path}"
                print(save_message)
            except Exception as e:
                save_message = f"\n❌ Error saving file to {full_path}: {e}"
                print(save_message)
        
        return save_message
    
    def _extract_code_content(self, result: str) -> str:
        """Extract code content from LLM response"""
        # Try to extract code from markdown code blocks
        code_patterns = [
            r"```python\s*\n(.*?)\n```",
            r"```\s*\n(.*?)\n```",
            r"```(.+?)```"
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, result, re.DOTALL)
            if match:
                code_content = match.group(1).strip()
                if code_content and len(code_content) > 10:  # Reasonable code length
                    return code_content
        
        # If no code blocks found, check if result contains Flask-like code
        if "from flask import" in result.lower() or "app = flask" in result.lower() or "@app.route" in result.lower():
            # Extract everything that looks like Python code
            lines = result.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                stripped_line = line.strip()
                if (stripped_line.startswith(('from ', 'import ', 'def ', 'class ', 'if ', '@', 'app.')) or
                    '=' in stripped_line or 'return' in stripped_line):
                    in_code = True
                    code_lines.append(line)
                elif in_code and (stripped_line == '' or stripped_line.startswith(' ')):
                    code_lines.append(line)
                elif in_code and not stripped_line.startswith('#'):
                    # End of code block
                    break
            
            if code_lines:
                return '\n'.join(code_lines)
        
        # Fallback: use entire result but clean it up
        cleaned_result = result.strip()
        
        # Remove common LLM response prefixes/suffixes
        prefixes_to_remove = [
            "Here's the Flask application:",
            "Here is the Flask app:",
            "This is a simple Flask application:",
            "Here's a basic Flask app:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_result.lower().startswith(prefix.lower()):
                cleaned_result = cleaned_result[len(prefix):].strip()
                break
        
        return cleaned_result

    async def _handle_command_execution(self, message_content: str) -> str:
        command_output = ""
        command_match = re.search(r"(?:führe den befehl aus|execute command):\s*(.+)", message_content, re.IGNORECASE)
        if command_match:
            command_to_execute = command_match.group(1).strip()
            command_output = await self._run_command(command_to_execute)
        return command_output

    async def _analyze_and_execute_task(self, task: str) -> str:
        """Analyze task and decide whether to use LLM or direct command execution"""
        # Enhanced command execution prompts for better AI understanding
        enhanced_prompt = f"""
You are an AI assistant with command-line access. Analyze this task and provide the most efficient solution:

Task: {task}

You have the following capabilities:
1. Create files using standard commands (echo, cat, touch, etc.)
2. Execute Python scripts and install packages
3. Use any command-line tools available on the system
4. Generate code and save it to files

For this task, please:
1. First, analyze what needs to be done
2. Then provide the specific commands to execute
3. If code generation is needed, create the code and save it to the appropriate file

Be practical and use command-line tools effectively. Respond with clear steps and commands.
"""
        
        # Get AI response with enhanced prompt
        result = await self._perform_task(enhanced_prompt)
        
        # Parse and execute any commands found in the response
        await self._parse_and_execute_commands(result)
        
        # Extract and save any Python code found in the response using enhanced generator
        if "python" in task.lower() or ".py" in task.lower() or "opencv" in task.lower():
            if self.code_generator and self.project_folder_path:
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
                    
                    elif code_result['code']:
                        result += f"\n⚠️ Code validation failed: {', '.join(code_result['issues'])}"
                        result += f"\n💾 Saving code anyway for manual review..."
                        
                        file_path = os.path.join(self.project_folder_path, code_result['filename'])
                        with open(file_path, "w", encoding='utf-8') as f:
                            f.write(code_result['code'])
                        result += f"\n📝 Code saved to: {file_path}"
                    
                except Exception as e:
                    result += f"\n❌ Enhanced code generator failed: {e}"
                    # Fallback to original method
                    extracted_code = self._extract_complete_python_code(result)
                    if extracted_code:
                        filename = self._determine_filename(task)
                        file_path = os.path.join(self.project_folder_path, filename)
                        try:
                            with open(file_path, "w", encoding='utf-8') as f:
                                f.write(extracted_code)
                            result += f"\n✅ Fallback: Python code saved to: {file_path}"
                        except Exception as e2:
                            result += f"\n❌ Error saving Python code: {e2}"
            else:
                # Original fallback method
                extracted_code = self._extract_complete_python_code(result)
                if extracted_code and self.project_folder_path:
                    filename = self._determine_filename(task)
                    file_path = os.path.join(self.project_folder_path, filename)
                    try:
                        with open(file_path, "w", encoding='utf-8') as f:
                            f.write(extracted_code)
                        result += f"\n✅ Complete Python code saved to: {file_path}"
                    except Exception as e:
                        result += f"\n❌ Error saving Python code: {e}"
        
        return result

    def _get_role_capabilities(self) -> List[str]:
        """Get capabilities based on drone role"""
        capabilities_map = {
            DroneRole.ANALYST: [
                "data_analysis", "report_generation", "pattern_recognition",
                "statistical_analysis", "visualization", "documentation"
            ],
            DroneRole.DATA_SCIENTIST: [
                "machine_learning", "data_preprocessing", "model_training",
                "feature_engineering", "statistical_modeling", "python_analysis"
            ],
            DroneRole.IT_ARCHITECT: [
                "system_design", "infrastructure_planning", "scalability_design",
                "security_architecture", "technology_selection", "diagram_creation"
            ],
            DroneRole.DEVELOPER: [
                "coding", "debugging", "testing", "deployment",
                "version_control", "code_review", "problem_solving"
            ],
            DroneRole.SECURITY_SPECIALIST: [
                "security_audit", "vulnerability_assessment", "penetration_testing",
                "secure_coding", "threat_modeling", "compliance_check",
                "encryption_implementation", "authentication_design", "authorization_patterns",
                "security_architecture_review", "risk_assessment", "incident_response"
            ]
        }
        return capabilities_map.get(self.role, [])
    
    def _choose_optimal_model(self, task_context: str) -> str:
        """Wählt das optimale LLM basierend auf Rolle und Task-Kontext"""
        if self.llm_chooser:
            try:
                optimal_model = self.llm_chooser.choose_model_for_role(
                    self.role.value, 
                    task_context
                )
                logger.info(f"🎯 Model chosen for {self.role.value}: {optimal_model}")
                return optimal_model
            except Exception as e:
                logger.warning(f"⚠️ LLM selection failed, using fallback: {e}")
        
        return self.model  # Fallback to default
    
    def _enhance_prompt_for_role(self, prompt: str) -> str:
        """Erweitert den Prompt um rollenspezifische Kontexte und Anweisungen"""
        role_context = self._get_role_context()
        security_context = ""
        
        # Spezielle Security-Behandlung
        if self.role == DroneRole.SECURITY_SPECIALIST:
            security_context = self._get_security_context(prompt)
        
        enhanced_prompt = f"""{role_context}

TASK: {prompt}

{security_context}

IMPORTANT REQUIREMENTS:
1. CREATE ACTUAL CODE/FILES - Do not just describe what you would do
2. Use command-line tools to create real files (touch, echo, cat > file.py, etc.)
3. Write functional, complete code that actually works
4. Save all code to files in the project directory
5. Execute commands to validate your implementation

WORKING DIRECTORY: {self.project_folder_path if self.project_folder_path else '.'}

REQUIRED OUTPUT: Provide both:
- Working code/implementation (create actual files)
- Brief explanation of what you implemented

Execute commands and create files NOW, do not just plan or describe."""
        
        return enhanced_prompt
    
    def _get_security_context(self, task: str) -> str:
        """Erstellt Security-spezifischen Kontext"""
        security_frameworks = [
            "OWASP Top 10", "NIST Cybersecurity Framework", "ISO 27001",
            "SANS Top 25", "CWE (Common Weakness Enumeration)"
        ]
        
        task_lower = task.lower()
        context_parts = []
        
        # Erkenne Security-relevante Keywords
        if any(keyword in task_lower for keyword in ['web', 'api', 'application', 'app']):
            context_parts.append("""
SECURITY FOCUS - Web Application:
- Apply OWASP Top 10 principles (Injection, Broken Auth, Sensitive Data, XXE, etc.)
- Implement proper input validation and output encoding
- Use secure session management and CSRF protection
- Ensure proper authentication and authorization patterns""")
        
        if any(keyword in task_lower for keyword in ['database', 'sql', 'data']):
            context_parts.append("""
SECURITY FOCUS - Data Protection:
- Implement SQL injection prevention (parameterized queries)
- Use encryption for sensitive data at rest and in transit
- Apply principle of least privilege for database access
- Implement proper backup encryption and access controls""")
        
        if any(keyword in task_lower for keyword in ['authentication', 'login', 'user']):
            context_parts.append("""
SECURITY FOCUS - Authentication & Authorization:
- Implement multi-factor authentication (MFA)
- Use secure password policies and hashing (bcrypt, Argon2)
- Apply JWT security best practices
- Implement proper session timeout and management""")
        
        if any(keyword in task_lower for keyword in ['api', 'rest', 'microservice']):
            context_parts.append("""
SECURITY FOCUS - API Security:
- Implement proper API authentication (OAuth 2.0, JWT)
- Use rate limiting and throttling
- Apply input validation and sanitization
- Implement proper error handling (avoid information disclosure)""")
        
        if any(keyword in task_lower for keyword in ['architecture', 'design', 'system']):
            context_parts.append("""
SECURITY FOCUS - Architecture Security:
- Apply defense in depth principles
- Implement zero-trust architecture concepts
- Use secure communication protocols (TLS 1.3+)
- Design with security by default and privacy by design""")
        
        # Standard Security-Kontext wenn keine spezifischen Keywords gefunden
        if not context_parts:
            context_parts.append("""
GENERAL SECURITY PRINCIPLES:
- Follow secure coding practices
- Apply principle of least privilege
- Implement proper error handling and logging
- Use security-focused libraries and frameworks
- Consider threat modeling and risk assessment""")
        
        return "\n".join(context_parts) + f"""

SECURITY FRAMEWORKS TO CONSIDER: {', '.join(security_frameworks[:3])}

ALWAYS INCLUDE:
1. Specific security vulnerabilities to watch for
2. Concrete implementation recommendations
3. Security testing suggestions
4. Compliance considerations if applicable"""
    
    def _add_security_recommendations(self, result: str, original_task: str) -> str:
        """Fügt Security-Empfehlungen zum Ergebnis hinzu"""
        security_addendum = f"""

🔒 SECURITY SPECIALIST RECOMMENDATIONS:

IMMEDIATE ACTIONS:
• Code Review: Scan the above implementation for common vulnerabilities
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

NEXT STEPS:
1. Conduct threat modeling for this implementation
2. Set up automated security scanning (SAST/DAST)
3. Plan regular security reviews and updates
4. Document security architecture decisions

⚠️  SECURITY REMINDER: This analysis is based on the provided context. 
Always conduct thorough security reviews with qualified security professionals."""

        return result + security_addendum
    
    def _get_role_context(self) -> str:
        """Get role-specific context for enhanced prompts"""
        role_contexts = {
            DroneRole.ANALYST: """
🎯 ROLE: ANALYST DRONE - Data Intelligence Specialist

CORE EXPERTISE:
• Advanced statistical analysis and data interpretation
• Business intelligence and KPI development  
• Market research and competitive analysis
• Risk assessment and impact analysis
• Performance metrics and trend identification
• Report generation with actionable insights

WORKING STYLE:
• Data-driven decision making approach
• Systematic analysis with clear methodology
• Focus on patterns, anomalies, and correlations  
• Evidence-based recommendations
• Clear visualization of complex information

OUTPUT FORMAT:
1. Executive Summary (key findings)
2. Detailed Analysis (methodology & findings)
3. Visual Data Representation (when applicable)
4. Risk Assessment & Mitigation
5. Actionable Recommendations
6. Implementation Timeline

COLLABORATION: Share insights with architects for system optimization, work with developers on data integration requirements.
""",
            DroneRole.DATA_SCIENTIST: """
🎯 ROLE: DATA SCIENTIST DRONE - ML/AI Implementation Specialist  

CORE EXPERTISE:
• Machine Learning model design, training & optimization
• Computer Vision with OpenCV, TensorFlow, PyTorch
• Deep Learning architectures (CNN, RNN, Transformers)
• Statistical modeling and feature engineering
• Data pipeline architecture and ETL processes
• MLOps and model deployment strategies

EXECUTION COMMANDS YOU MUST USE:
• echo "import pandas as pd" > data_analysis.py (create Python files)
• pip install pandas numpy scikit-learn requests (install ML packages)
• python -c "import numpy; print('NumPy works')" (test installations)
• cat << 'EOF' > model.py (create multi-line ML code)
• mkdir data/ models/ (create project structure)

TECHNICAL STANDARDS:
• ALWAYS create working Python files with real ML code
• Include proper imports: pandas, numpy, requests, socket, etc.
• Create functional data collection and analysis scripts
• Add error handling and logging
• Generate requirements.txt with all dependencies

CRITICAL: You MUST create actual Python files with working code. No planning, only implementation.
""",
            DroneRole.IT_ARCHITECT: """
🎯 ROLE: IT ARCHITECT DRONE - Enterprise System Designer

CORE EXPERTISE:
• Enterprise architecture patterns and best practices
• Cloud-native design (AWS, Azure, GCP) 
• Microservices and distributed systems architecture
• API design and integration strategies
• Database architecture and data modeling
• Infrastructure as Code (IaC) and automation
• System scalability and performance optimization

WORKING STYLE:
• Architecture-first approach with clear documentation
• Technology-agnostic solution design
• Focus on maintainability, scalability, and reliability  
• Cost optimization and resource efficiency
• Future-proof design with evolution pathways

OUTPUT FORMAT:
1. Architecture Overview & Design Principles
2. System Components & Service Breakdown
3. Data Flow & Integration Diagrams
4. Technology Stack Recommendations
5. Scalability & Performance Considerations
6. Security & Compliance Framework
7. Implementation Roadmap & Milestones

TECHNICAL DELIVERABLES:
• System architecture diagrams (C4, UML)
• API specifications (OpenAPI/Swagger)
• Infrastructure definitions (Terraform, CloudFormation)
• Database schemas and migration scripts

COLLABORATION: Guide developers on implementation details, align with security specialists on secure design patterns.
""",
            DroneRole.DEVELOPER: """
🎯 ROLE: DEVELOPER DRONE - Software Implementation Expert

CORE EXPERTISE:
• Full-stack development (Python, JavaScript, TypeScript)
• Backend systems (FastAPI, Django, Flask)
• Frontend frameworks (React, Vue, Angular)
• Database design and optimization (SQL, NoSQL)
• DevOps and CI/CD pipeline implementation
• Test-driven development and quality assurance
• Version control and collaborative development

WORKING STYLE:
• Clean code principles with SOLID design patterns
• Test-first development with comprehensive coverage
• Performance optimization and code refactoring
• Documentation-driven development
• Agile methodologies and iterative delivery

EXECUTION COMMANDS YOU MUST USE:
• echo "code content" > filename.py (create Python files)
• cat << 'EOF' > filename.py (create multi-line files)
• touch filename.ext (create empty files)
• python -c "import module; print('test')" (validate code)
• pip install package_name (install dependencies)
• ls -la (verify files created)

TECHNICAL STANDARDS:
• ALWAYS create actual working files with real code
• Production-ready code with error handling
• Include proper imports, functions, and main execution
• Create requirements.txt for dependencies
• Add proper docstrings and comments

COLLABORATION: Implement architect designs, integrate with data scientist models, follow security specialist guidelines.

CRITICAL: You MUST execute commands to create actual files. Do not just describe or plan.
""",
            DroneRole.SECURITY_SPECIALIST: """
🎯 ROLE: SECURITY SPECIALIST DRONE - Cybersecurity & Compliance Expert

CORE EXPERTISE:
• Security architecture design and threat modeling
• Vulnerability assessment and penetration testing
• Secure coding practices and code review
• Identity & Access Management (IAM) systems
• Encryption, PKI, and cryptographic implementations
• Compliance frameworks (GDPR, SOC2, PCI-DSS, NIST)
• Incident response and forensic analysis
• Security automation and SIEM integration

WORKING STYLE:
• Zero-trust security model implementation
• Risk-based approach with quantified assessments
• Defense-in-depth strategy across all layers
• Continuous security monitoring and improvement
• Threat intelligence integration

OUTPUT FORMAT:
1. Threat Model & Risk Assessment
2. Security Requirements & Controls
3. Secure Implementation Guidelines
4. Security Testing & Validation Plan
5. Incident Response Procedures
6. Compliance Checklist & Audit Trail
7. Security Monitoring & Alerting Setup

SECURITY FRAMEWORKS:
• OWASP Top 10 and security testing methodology
• NIST Cybersecurity Framework implementation
• ISO 27001/27002 security controls
• SANS security architecture principles

COLLABORATION: Review all team outputs for security implications, provide secure design patterns to architects and developers.

SECURITY MINDSET: "Assume breach, verify everything, minimize attack surface, implement defense in depth."
"""
        }
        return role_contexts.get(self.role, "You are a specialized drone agent.")
    
    def _extract_complete_python_code(self, response: str) -> str:
        """Extract complete Python code from LLM response"""
        import re
        
        # Try to find Python code blocks
        python_patterns = [
            r'```python\n([\s\S]*?)```',
            r'```py\n([\s\S]*?)```',
            r'```([\s\S]*?)```',  # Generic code block
        ]
        
        for pattern in python_patterns:
            matches = re.findall(pattern, response, re.MULTILINE)
            if matches:
                # Take the largest code block (most complete)
                largest_match = max(matches, key=len)
                if len(largest_match.strip()) > 50:  # Must have substantial content
                    return largest_match.strip()
        
        # If no code blocks, look for Python imports and classes/functions
        lines = response.split('\n')
        python_lines = []
        in_python_section = False
        
        for line in lines:
            if any(keyword in line for keyword in ['import ', 'from ', 'def ', 'class ', 'if __name__']):
                in_python_section = True
            
            if in_python_section:
                python_lines.append(line)
                
            # Stop if we hit non-code content after starting
            if in_python_section and line.strip() and not line.startswith(' ') and not any(c in line for c in ['import', 'from', 'def', 'class', '#', 'if', 'for', 'while', 'try', 'with']):
                if not line.strip().replace(' ', '').replace('\t', '').isalnum():
                    break
        
        if python_lines and len('\n'.join(python_lines).strip()) > 50:
            return '\n'.join(python_lines).strip()
        
        return ""
    
    def _determine_filename(self, task: str) -> str:
        """Determine appropriate filename based on task"""
        task_lower = task.lower()
        
        if "opencv" in task_lower or "image" in task_lower or "bilderkennungs" in task_lower:
            return "image_recognition.py"
        elif "detect" in task_lower and "people" in task_lower:
            return "detect_people.py"
        elif "flask" in task_lower or "web" in task_lower:
            return "app.py"
        elif "ml" in task_lower or "machine learning" in task_lower:
            return "ml_model.py"
        elif "analysis" in task_lower or "analyze" in task_lower:
            return "data_analysis.py"
        else:
            return "main.py"

    def _get_role_specific_prompt(self, task: str) -> str:
        """Get role-specific enhanced prompt for task execution"""
        role_contexts = {
            DroneRole.ANALYST: f"""
You are an expert ANALYST drone. Your core competencies include:
- Data analysis and interpretation
- Report generation and documentation
- Pattern recognition and insights extraction
- Statistical analysis and metrics calculation
- Data visualization and presentation

Task: {task}

As an analyst, focus on:
1. Understanding the data or requirements thoroughly
2. Identifying patterns, trends, or insights
3. Providing clear, well-documented analysis
4. Creating comprehensive reports with actionable recommendations
5. Using appropriate analytical tools and methodologies
""",
            DroneRole.DATA_SCIENTIST: f"""
You are an expert DATA SCIENTIST drone. Your core competencies include:
- Machine learning model development and training
- Data preprocessing and feature engineering
- Statistical modeling and hypothesis testing
- Python-based data science workflows
- Model evaluation and optimization

Task: {task}

As a data scientist, focus on:
1. Data exploration and preprocessing
2. Feature selection and engineering
3. Model selection and training
4. Performance evaluation and validation
5. Creating reproducible analysis pipelines
""",
            DroneRole.IT_ARCHITECT: f"""
You are an expert IT ARCHITECT drone. Your core competencies include:
- System architecture design and planning
- Infrastructure design and scalability
- Security architecture and best practices
- Technology selection and evaluation
- Creating technical specifications and diagrams

Task: {task}

As an IT architect, focus on:
1. Designing scalable and maintainable systems
2. Considering security, performance, and reliability
3. Selecting appropriate technologies and patterns
4. Creating clear architectural documentation
5. Planning for future growth and changes
""",
            DroneRole.DEVELOPER: f"""
You are an expert DEVELOPER drone. Your core competencies include:
- Software development and programming
- Code debugging and optimization
- Testing and quality assurance
- Version control and collaboration
- Problem-solving and implementation

Task: {task}

As a developer, focus on:
1. Writing clean, efficient, and maintainable code
2. Following best practices and coding standards
3. Implementing proper error handling and testing
4. Optimizing performance and resource usage
5. Creating well-documented and reusable solutions
"""
        }
        return role_contexts.get(self.role, f"Task: {task}")

    async def _analyze_and_execute_task(self, task: str) -> str:
        """Analyze task and decide whether to use LLM or direct command execution with role-specific context"""
        # Get role-specific enhanced prompt
        enhanced_prompt = self._get_role_specific_prompt(task)
        
        # Add general capabilities context
        enhanced_prompt += f"""

Your available capabilities: {', '.join(self.capabilities)}

You have the following technical capabilities:
1. Create files using standard commands (echo, cat, touch, etc.)
2. Execute Python scripts and install packages
3. Use any command-line tools available on the system
4. Generate code and save it to files

For this task, please:
1. First, analyze what needs to be done from your role perspective
2. Then provide the specific commands to execute
3. If code generation is needed, create the code and save it to the appropriate file

Be practical and use command-line tools effectively while leveraging your role expertise.
"""
        
        # Get AI response with role-specific enhanced prompt
        result = await self._perform_task(enhanced_prompt)
        
        # Parse and execute any commands found in the response
        await self._parse_and_execute_commands(result)
        
        return result

    def get_role_info(self) -> dict:
        """Get information about drone's role and capabilities"""
        return {
            "role": self.role.value,
            "capabilities": self.capabilities,
            "agent_id": self.agent_id,
            "name": self.name
        }

    async def _parse_and_execute_commands(self, ai_response: str) -> str:
        """Parse AI response for commands and execute them"""
        command_output = ""
        
        # Look for command blocks in various formats
        command_patterns = [
            r"```bash\s*\n(.*?)\n```",
            r"```shell\s*\n(.*?)\n```", 
            r"```\s*\n(.*?)\n```",
            r"Command:\s*`([^`]+)`",
            r"Execute:\s*`([^`]+)`",
            r"Run:\s*`([^`]+)`"
        ]
        
        commands_found = []
        for pattern in command_patterns:
            matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split multi-line commands
                cmd_lines = [line.strip() for line in match.split('\n') if line.strip()]
                commands_found.extend(cmd_lines)
        
        # Execute found commands
        for command in commands_found:
            if command and not command.startswith('#'):  # Skip comments
                print(f"[DroneAgent {self.name} ({self.role.value})] Executing AI-suggested command: {command}")
                try:
                    cmd_result = await self._run_command(command)
                    command_output += f"\n--- Command: {command} ---\n{cmd_result}\n"
                except Exception as e:
                    command_output += f"\n--- Command: {command} (FAILED) ---\n{str(e)}\n"
        
        return command_output

    async def receive_message(self, message: AgentMessage):
        print(f"DroneAgent {self.name} ({self.agent_id}) with role {self.role.value} received message from {message.sender_id}: {message.content}")

        # Use AI analysis and command execution approach
        result = await self._analyze_and_execute_task(message.content)
        
        print(f"DroneAgent {self.name} ({self.agent_id}) with role {self.role.value} completed task analysis")

        # Handle file saving and additional command execution
        save_message = await self._handle_file_saving(message.content, result)
        command_output = await self._handle_command_execution(message.content)

        final_response = result + save_message
        if command_output:
            final_response += f"\nCommand Output:\n{command_output}"

        # Add role information to response
        role_info = f"\n[Completed by {self.role.value} drone: {self.name}]"
        final_response += role_info
        
        await self.send_message(message.sender_id, "response", final_response, message.request_id)