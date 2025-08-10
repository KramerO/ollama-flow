#!/usr/bin/env python3
"""
Code Generation Capability
Handles all code generation, validation, and file management tasks
"""

import os
import re
import ast
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CodeValidationResult:
    """Result of code validation"""
    is_valid: bool
    language: str
    filename: str
    issues: List[str]
    suggestions: List[str]
    complexity_score: int

class CodeGenerationCapability:
    """Advanced code generation with validation and optimization"""
    
    def __init__(self, agent, settings):
        self.agent = agent
        self.settings = settings
        self.supported_languages = {
            'python': {
                'extensions': ['.py'],
                'validator': self._validate_python_code,
                'formatter': self._format_python_code,
                'runner': self._run_python_code
            },
            'javascript': {
                'extensions': ['.js', '.ts'],
                'validator': self._validate_javascript_code,
                'formatter': self._format_javascript_code,
                'runner': self._run_javascript_code
            },
            'bash': {
                'extensions': ['.sh'],
                'validator': self._validate_bash_code,
                'formatter': self._format_bash_code,
                'runner': self._run_bash_code
            },
            'sql': {
                'extensions': ['.sql'],
                'validator': self._validate_sql_code,
                'formatter': self._format_sql_code,
                'runner': None
            }
        }
        
        # Code quality thresholds
        self.quality_thresholds = {
            'max_complexity': 10,
            'min_documentation_ratio': 0.1,
            'max_line_length': 120,
            'max_function_length': 50
        }
        
        logger.info(f"✅ Code generation capability initialized with {len(self.supported_languages)} languages")
    
    async def configure_for_role(self, role, is_priority: bool):
        """Configure code generation based on agent role"""
        role_configs = {
            'developer': {
                'focus_languages': ['python', 'javascript'],
                'quality_emphasis': 'functionality',
                'include_tests': True
            },
            'security_specialist': {
                'focus_languages': ['python', 'bash'],
                'quality_emphasis': 'security',
                'include_security_checks': True
            },
            'datascientist': {
                'focus_languages': ['python'],
                'quality_emphasis': 'performance',
                'include_data_validation': True
            },
            'it_architect': {
                'focus_languages': ['python', 'bash', 'sql'],
                'quality_emphasis': 'maintainability',
                'include_architecture_docs': True
            }
        }
        
        config = role_configs.get(role.value, {})
        self.role_config = config
        
        logger.info(f"🎯 Code generation configured for {role.value}: {config.get('quality_emphasis', 'general')} focus")
    
    async def should_execute(self, task: str, llm_response: str) -> bool:
        """Determine if code generation should be applied"""
        if not self.settings.agents.enable_code_generation:
            return False
        
        # Check for code generation indicators
        code_indicators = [
            'implement', 'create', 'build', 'develop', 'code', 'script', 'program',
            'function', 'class', 'module', 'application', 'write', 'generate'
        ]
        
        task_lower = task.lower()
        has_code_request = any(indicator in task_lower for indicator in code_indicators)
        
        # Check if LLM response contains code blocks
        has_code_blocks = bool(re.search(r'```\w*\n', llm_response))
        
        return has_code_request or has_code_blocks
    
    async def execute(self, task: str, llm_response: str) -> str:
        """Extract, validate, and save code from LLM response"""
        try:
            # Extract all code blocks
            code_blocks = self._extract_code_blocks(llm_response)
            
            if not code_blocks:
                logger.info("ℹ️ No code blocks found in response")
                return llm_response
            
            enhanced_response = llm_response
            execution_summary = []
            
            for i, code_block in enumerate(code_blocks):
                logger.info(f"🔍 Processing code block {i+1}/{len(code_blocks)} ({code_block['language']})")
                
                # Validate and process code
                validation_result = await self._validate_and_process_code(code_block, task)
                
                if validation_result.is_valid:
                    # Save code to file
                    file_path = await self._save_code_to_file(code_block, validation_result)
                    
                    # Optionally run code for testing
                    execution_result = await self._execute_code_safely(validation_result, file_path)
                    
                    execution_summary.append({
                        'language': validation_result.language,
                        'filename': validation_result.filename,
                        'file_path': file_path,
                        'validation': 'passed',
                        'execution': execution_result,
                        'complexity': validation_result.complexity_score,
                        'issues': validation_result.issues,
                        'suggestions': validation_result.suggestions
                    })
                else:
                    execution_summary.append({
                        'language': code_block['language'],
                        'validation': 'failed',
                        'issues': validation_result.issues
                    })
            
            # Add execution summary to response
            enhanced_response += self._generate_code_summary(execution_summary)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ Code generation execution failed: {e}")
            return llm_response + f"\n\n⚠️ Code generation error: {str(e)}"
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks with language detection"""
        code_blocks = []
        
        # Pattern for fenced code blocks
        pattern = r'```(\w*)\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match[0].lower() if match[0] else 'text'
            code = match[1].strip()
            
            if code and language != 'text':
                # Auto-detect language if not specified
                if not language or language == 'text':
                    language = self._detect_language(code)
                
                code_blocks.append({
                    'language': language,
                    'code': code,
                    'original_match': match
                })
        
        # Also extract inline code that looks like complete programs
        if not code_blocks:
            code_blocks.extend(self._extract_inline_code(text))
        
        return code_blocks
    
    def _detect_language(self, code: str) -> str:
        """Auto-detect programming language"""
        # Python indicators
        python_indicators = ['def ', 'import ', 'from ', 'class ', 'if __name__', 'print(']
        if any(indicator in code for indicator in python_indicators):
            return 'python'
        
        # JavaScript indicators  
        js_indicators = ['function ', 'const ', 'let ', 'var ', 'console.log', '=>']
        if any(indicator in code for indicator in js_indicators):
            return 'javascript'
        
        # Bash indicators
        bash_indicators = ['#!/bin/bash', '#!/bin/sh', 'echo ', '$', 'chmod ', 'mkdir ']
        if any(indicator in code for indicator in bash_indicators):
            return 'bash'
        
        # SQL indicators
        sql_indicators = ['SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'ALTER ']
        if any(indicator.lower() in code.lower() for indicator in sql_indicators):
            return 'sql'
        
        return 'text'
    
    def _extract_inline_code(self, text: str) -> List[Dict[str, str]]:
        """Extract potential code from inline text"""
        lines = text.split('\n')
        code_sections = []
        current_code = []
        in_code = False
        
        for line in lines:
            # Detect start of code section
            if (line.strip().startswith(('def ', 'class ', 'import ', 'from ', 'function ', '#!/')) 
                and not in_code):
                in_code = True
                current_code = [line]
            elif in_code:
                if line.strip() == '' or line.startswith((' ', '\t')):
                    current_code.append(line)
                else:
                    # End of code section
                    code = '\n'.join(current_code)
                    if len(code.strip()) > 20:  # Minimum code length
                        language = self._detect_language(code)
                        if language != 'text':
                            code_sections.append({
                                'language': language,
                                'code': code,
                                'original_match': None
                            })
                    in_code = False
                    current_code = []
        
        return code_sections
    
    async def _validate_and_process_code(self, code_block: Dict[str, str], task: str) -> CodeValidationResult:
        """Validate code and generate processing result"""
        language = code_block['language']
        code = code_block['code']
        
        # Generate appropriate filename
        filename = self._generate_filename(task, language)
        
        # Initialize result
        result = CodeValidationResult(
            is_valid=False,
            language=language,
            filename=filename,
            issues=[],
            suggestions=[],
            complexity_score=0
        )
        
        # Language-specific validation
        if language in self.supported_languages:
            validator = self.supported_languages[language]['validator']
            if validator:
                try:
                    validation_result = validator(code)
                    result.is_valid = validation_result['valid']
                    result.issues = validation_result.get('issues', [])
                    result.suggestions = validation_result.get('suggestions', [])
                    result.complexity_score = validation_result.get('complexity', 0)
                except Exception as e:
                    result.issues.append(f"Validation error: {str(e)}")
        else:
            result.is_valid = True  # Unknown language, assume valid
            result.suggestions.append(f"Language '{language}' not recognized, skipping validation")
        
        # Apply role-specific enhancements
        result = await self._apply_role_enhancements(result, code, task)
        
        return result
    
    def _generate_filename(self, task: str, language: str) -> str:
        """Generate appropriate filename based on task and language"""
        # Extract potential filename from task
        filename_patterns = [
            r'(?:create|write|implement)\s+(?:a\s+)?(?:file\s+)?(?:named\s+)?([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)',
            r'(?:save|write)\s+(?:to\s+)?([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)',
            r'([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)'
        ]
        
        for pattern in filename_patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generate filename from task content
        task_words = re.findall(r'\w+', task.lower())
        meaningful_words = [w for w in task_words if len(w) > 3 and w not in ['create', 'implement', 'build', 'make']]
        
        if meaningful_words:
            base_name = '_'.join(meaningful_words[:3])
        else:
            base_name = 'generated_code'
        
        # Add appropriate extension
        extensions = self.supported_languages.get(language, {}).get('extensions', ['.txt'])
        extension = extensions[0]
        
        return f"{base_name}{extension}"
    
    def _validate_python_code(self, code: str) -> Dict[str, Any]:
        """Validate Python code"""
        try:
            # Parse AST
            tree = ast.parse(code)
            
            issues = []
            suggestions = []
            complexity = 0
            
            # Basic syntax validation passed if we get here
            
            # Check for common issues
            code_lines = code.split('\n')
            
            # Check line length
            long_lines = [i+1 for i, line in enumerate(code_lines) 
                         if len(line) > self.quality_thresholds['max_line_length']]
            if long_lines:
                issues.append(f"Long lines detected (>{self.quality_thresholds['max_line_length']} chars): lines {long_lines}")
            
            # Check for documentation
            docstring_ratio = self._calculate_docstring_ratio(code)
            if docstring_ratio < self.quality_thresholds['min_documentation_ratio']:
                suggestions.append("Consider adding more documentation and comments")
            
            # Calculate complexity
            complexity = self._calculate_complexity(tree)
            if complexity > self.quality_thresholds['max_complexity']:
                issues.append(f"High complexity score: {complexity}")
                suggestions.append("Consider refactoring to reduce complexity")
            
            # Check for security issues
            security_issues = self._check_python_security(code)
            issues.extend(security_issues)
            
            return {
                'valid': True,
                'issues': issues,
                'suggestions': suggestions,
                'complexity': complexity,
                'ast': tree
            }
            
        except SyntaxError as e:
            return {
                'valid': False,
                'issues': [f"Syntax error: {str(e)}"],
                'suggestions': ["Fix syntax errors before proceeding"],
                'complexity': 0
            }
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Validation error: {str(e)}"],
                'suggestions': [],
                'complexity': 0
            }
    
    def _validate_javascript_code(self, code: str) -> Dict[str, Any]:
        """Validate JavaScript code (basic validation)"""
        issues = []
        suggestions = []
        
        # Basic checks
        if 'eval(' in code:
            issues.append("Use of eval() detected - security risk")
        
        if 'document.write(' in code:
            issues.append("Use of document.write() detected - consider safer alternatives")
        
        # Check for console.log (should be removed in production)
        if 'console.log(' in code:
            suggestions.append("Remove console.log statements for production code")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions,
            'complexity': self._estimate_js_complexity(code)
        }
    
    def _validate_bash_code(self, code: str) -> Dict[str, Any]:
        """Validate Bash script"""
        issues = []
        suggestions = []
        
        # Security checks
        dangerous_commands = ['rm -rf', 'chmod 777', 'sudo', 'su -']
        for cmd in dangerous_commands:
            if cmd in code:
                issues.append(f"Potentially dangerous command detected: {cmd}")
        
        # Best practices
        if not code.startswith('#!'):
            suggestions.append("Consider adding shebang line (#!/bin/bash)")
        
        if 'set -e' not in code:
            suggestions.append("Consider adding 'set -e' for better error handling")
        
        return {
            'valid': True,  # Bash is flexible, hard to determine invalid syntax
            'issues': issues,
            'suggestions': suggestions,
            'complexity': len(code.split('\n'))
        }
    
    def _validate_sql_code(self, code: str) -> Dict[str, Any]:
        """Validate SQL code"""
        issues = []
        suggestions = []
        
        # Security checks
        if re.search(r'DROP\s+TABLE', code, re.IGNORECASE):
            issues.append("DROP TABLE detected - potential data loss risk")
        
        if re.search(r'DELETE\s+FROM.*WHERE', code, re.IGNORECASE) is None and 'DELETE FROM' in code.upper():
            issues.append("DELETE without WHERE clause detected - potential data loss")
        
        # Best practices
        if not re.search(r';\s*$', code.strip()):
            suggestions.append("Consider ending SQL statements with semicolons")
        
        return {
            'valid': True,
            'issues': issues,
            'suggestions': suggestions,
            'complexity': len(re.findall(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b', code, re.IGNORECASE))
        }
    
    def _calculate_docstring_ratio(self, code: str) -> float:
        """Calculate ratio of documentation to code"""
        lines = code.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        doc_lines = len([line for line in lines if line.strip().startswith('#') or '"""' in line or "'''" in line])
        
        return doc_lines / max(total_lines, 1)
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Add complexity for control flow statements
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.BoolOp, ast.Compare)):
                complexity += 1
        
        return complexity
    
    def _estimate_js_complexity(self, code: str) -> int:
        """Estimate JavaScript complexity"""
        complexity_patterns = [
            r'\bif\b', r'\bwhile\b', r'\bfor\b', r'\bswitch\b',
            r'\bcatch\b', r'\b\?\s*:', r'\&\&', r'\|\|'
        ]
        
        complexity = 1
        for pattern in complexity_patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _check_python_security(self, code: str) -> List[str]:
        """Check for Python security issues"""
        security_issues = []
        
        # Dangerous functions
        dangerous_patterns = [
            (r'\beval\s*\(', "Use of eval() - code injection risk"),
            (r'\bexec\s*\(', "Use of exec() - code injection risk"),
            (r'\b__import__\s*\(', "Use of __import__() - potential security risk"),
            (r'subprocess\.call.*shell=True', "subprocess with shell=True - command injection risk"),
            (r'os\.system\s*\(', "Use of os.system() - command injection risk"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                security_issues.append(message)
        
        return security_issues
    
    async def _apply_role_enhancements(self, result: CodeValidationResult, code: str, task: str) -> CodeValidationResult:
        """Apply role-specific enhancements to validation result"""
        if not hasattr(self, 'role_config'):
            return result
        
        role_config = self.role_config
        
        # Security specialist enhancements
        if role_config.get('quality_emphasis') == 'security':
            if result.language == 'python':
                additional_security_checks = self._advanced_python_security_check(code)
                result.issues.extend(additional_security_checks)
        
        # Data scientist enhancements
        elif role_config.get('quality_emphasis') == 'performance':
            if result.language == 'python':
                performance_suggestions = self._get_python_performance_suggestions(code)
                result.suggestions.extend(performance_suggestions)
        
        # Architecture enhancements
        elif role_config.get('quality_emphasis') == 'maintainability':
            maintainability_suggestions = self._get_maintainability_suggestions(code, result.language)
            result.suggestions.extend(maintainability_suggestions)
        
        return result
    
    def _advanced_python_security_check(self, code: str) -> List[str]:
        """Advanced security checks for Python code"""
        issues = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'].+["\']', "Hardcoded password detected"),
            (r'api_key\s*=\s*["\'].+["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'].+["\']', "Hardcoded secret detected"),
        ]
        
        for pattern, message in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(message)
        
        return issues
    
    def _get_python_performance_suggestions(self, code: str) -> List[str]:
        """Get performance optimization suggestions for Python"""
        suggestions = []
        
        if 'for' in code and 'append(' in code:
            suggestions.append("Consider using list comprehensions for better performance")
        
        if 'pandas' in code and 'iterrows()' in code:
            suggestions.append("Avoid iterrows() in pandas - use vectorized operations")
        
        if '+=' in code and 'str' in str(type(code)):
            suggestions.append("For string concatenation in loops, consider using join()")
        
        return suggestions
    
    def _get_maintainability_suggestions(self, code: str, language: str) -> List[str]:
        """Get maintainability suggestions"""
        suggestions = []
        
        if language == 'python':
            if len(code.split('\n')) > 50:
                suggestions.append("Consider breaking large files into smaller modules")
            
            if 'class' in code and '__init__' in code:
                if len(re.findall(r'def\s+\w+', code)) > 10:
                    suggestions.append("Large class detected - consider decomposition")
        
        return suggestions
    
    async def _save_code_to_file(self, code_block: Dict[str, str], validation_result: CodeValidationResult) -> str:
        """Save validated code to file"""
        if not self.agent.project_folder_path:
            self.agent.project_folder_path = os.getcwd()
        
        file_path = os.path.join(self.agent.project_folder_path, validation_result.filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else self.agent.project_folder_path, 
                   exist_ok=True)
        
        # Format code if formatter available
        formatted_code = code_block['code']
        if validation_result.language in self.supported_languages:
            formatter = self.supported_languages[validation_result.language].get('formatter')
            if formatter:
                try:
                    formatted_code = formatter(formatted_code)
                except Exception as e:
                    logger.warning(f"Code formatting failed: {e}")
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_code)
        
        logger.info(f"✅ Code saved to {file_path}")
        return file_path
    
    async def _execute_code_safely(self, validation_result: CodeValidationResult, file_path: str) -> Dict[str, Any]:
        """Safely execute code for testing"""
        if not self.settings.agents.enable_command_execution:
            return {"executed": False, "reason": "Command execution disabled"}
        
        language = validation_result.language
        if language not in self.supported_languages:
            return {"executed": False, "reason": f"Execution not supported for {language}"}
        
        runner = self.supported_languages[language].get('runner')
        if not runner:
            return {"executed": False, "reason": f"No runner available for {language}"}
        
        try:
            result = runner(file_path)
            return {"executed": True, "result": result}
        except Exception as e:
            return {"executed": False, "error": str(e)}
    
    def _format_python_code(self, code: str) -> str:
        """Format Python code"""
        # Basic formatting - in production, use black or autopep8
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_javascript_code(self, code: str) -> str:
        """Format JavaScript code"""
        # Basic formatting
        return code.strip()
    
    def _format_bash_code(self, code: str) -> str:
        """Format Bash code"""
        # Ensure shebang if missing
        if not code.strip().startswith('#!'):
            code = '#!/bin/bash\n' + code
        return code
    
    def _format_sql_code(self, code: str) -> str:
        """Format SQL code"""
        # Convert to uppercase keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
        formatted = code
        for keyword in keywords:
            formatted = re.sub(f'\\b{keyword}\\b', keyword, formatted, flags=re.IGNORECASE)
        return formatted
    
    def _run_python_code(self, file_path: str) -> Dict[str, Any]:
        """Run Python code safely"""
        try:
            result = subprocess.run(
                ['python', '-c', f'exec(open("{file_path}").read())'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timeout'}
        except Exception as e:
            return {'error': str(e)}
    
    def _run_javascript_code(self, file_path: str) -> Dict[str, Any]:
        """Run JavaScript code safely"""
        try:
            result = subprocess.run(
                ['node', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timeout'}
        except Exception as e:
            return {'error': str(e)}
    
    def _run_bash_code(self, file_path: str) -> Dict[str, Any]:
        """Run Bash script safely"""
        try:
            # Make executable
            os.chmod(file_path, 0o755)
            result = subprocess.run(
                ['bash', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timeout'}
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_code_summary(self, execution_summary: List[Dict[str, Any]]) -> str:
        """Generate summary of code processing results"""
        if not execution_summary:
            return ""
        
        summary = "\n\n🚀 CODE GENERATION SUMMARY:\n" + "="*50 + "\n"
        
        total_files = len(execution_summary)
        successful_validations = sum(1 for item in execution_summary if item.get('validation') == 'passed')
        successful_executions = sum(1 for item in execution_summary if item.get('execution', {}).get('executed'))
        
        summary += f"📊 STATISTICS:\n"
        summary += f"• Total code blocks processed: {total_files}\n"
        summary += f"• Successful validations: {successful_validations}/{total_files}\n"
        summary += f"• Successful test runs: {successful_executions}/{total_files}\n\n"
        
        for i, item in enumerate(execution_summary, 1):
            summary += f"📁 CODE BLOCK {i}:\n"
            summary += f"• Language: {item['language']}\n"
            
            if item.get('filename'):
                summary += f"• File: {item['filename']}\n"
            
            if item.get('file_path'):
                summary += f"• Saved to: {item['file_path']}\n"
            
            summary += f"• Validation: {'✅ PASSED' if item.get('validation') == 'passed' else '❌ FAILED'}\n"
            
            if item.get('complexity'):
                summary += f"• Complexity Score: {item['complexity']}\n"
            
            if item.get('issues'):
                summary += f"• Issues Found: {len(item['issues'])}\n"
                for issue in item['issues'][:3]:  # Show first 3 issues
                    summary += f"  - {issue}\n"
            
            if item.get('suggestions'):
                summary += f"• Suggestions: {len(item['suggestions'])}\n"
                for suggestion in item['suggestions'][:2]:  # Show first 2 suggestions
                    summary += f"  - {suggestion}\n"
            
            execution_result = item.get('execution')
            if execution_result:
                if execution_result.get('executed'):
                    summary += f"• Test Execution: ✅ SUCCESS\n"
                    if execution_result.get('result', {}).get('stdout'):
                        stdout = execution_result['result']['stdout'][:200]  # Truncate long output
                        summary += f"• Output: {stdout}{'...' if len(stdout) == 200 else ''}\n"
                else:
                    summary += f"• Test Execution: ❌ FAILED ({execution_result.get('reason', 'Unknown error')})\n"
            
            summary += "\n" + "-"*30 + "\n"
        
        return summary