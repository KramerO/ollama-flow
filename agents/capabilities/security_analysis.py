#!/usr/bin/env python3
"""
Security Analysis Capability
Provides comprehensive security analysis and recommendations
"""

import re
import hashlib
import secrets
import json
from typing import Dict, Any, List, Optional, Set, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    """A security finding with details"""
    severity: str  # critical, high, medium, low, info
    category: str  # vulnerability type
    title: str
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class SecurityReport:
    """Comprehensive security analysis report"""
    risk_score: int  # 0-100
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings: List[SecurityFinding]
    recommendations: List[str]
    compliance_status: Dict[str, str]

class SecurityAnalysisCapability:
    """Advanced security analysis for code, configurations, and systems"""
    
    def __init__(self, agent, settings):
        self.agent = agent
        self.settings = settings
        
        # Security patterns and rules
        self.vulnerability_patterns = self._initialize_vulnerability_patterns()
        self.secure_coding_rules = self._initialize_secure_coding_rules()
        self.compliance_frameworks = self._initialize_compliance_frameworks()
        
        # Threat intelligence
        self.known_vulnerabilities = self._load_vulnerability_database()
        self.security_wordlist = self._load_security_wordlist()
        
        logger.info("✅ Security analysis capability initialized with comprehensive rule sets")
    
    def _initialize_vulnerability_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize vulnerability detection patterns"""
        return {
            "sql_injection": {
                "patterns": [
                    r"(?i)(?:(?:union(?:\s+all)?)|(?:select|insert|update|delete|drop|create)\s+.*(?:from|into|where|set))",
                    r"(?i)(?:\'\s*;\s*(?:drop|delete|update|insert))",
                    r"(?i)(?:\'\s*(?:or|and)\s+\d+\s*=\s*\d+)",
                    r"(?i)(?:query\s*\+?\=\s*[\"\']\s*(?:select|insert|update|delete))"
                ],
                "severity": "critical",
                "description": "Potential SQL injection vulnerability",
                "recommendation": "Use parameterized queries and input validation"
            },
            "xss": {
                "patterns": [
                    r"(?i)(?:<script[^>]*>.*?</script>)",
                    r"(?i)(?:javascript:)",
                    r"(?i)(?:on(?:load|error|click|focus|blur)\s*=)",
                    r"(?i)(?:innerHTML\s*=\s*[\"\''].*?[\"\''])"
                ],
                "severity": "high",
                "description": "Potential Cross-Site Scripting (XSS) vulnerability",
                "recommendation": "Sanitize user input and encode output"
            },
            "command_injection": {
                "patterns": [
                    r"(?i)(?:(?:system|exec|shell_exec|passthru|eval)\s*\()",
                    r"(?i)(?:\|\s*(?:sh|bash|cmd|powershell))",
                    r"(?i)(?:subprocess\.(?:call|run|Popen).*shell=True)",
                    r"(?i)(?:os\.system\s*\()"
                ],
                "severity": "critical",
                "description": "Potential command injection vulnerability",
                "recommendation": "Avoid dynamic command construction, use safe APIs"
            },
            "hardcoded_secrets": {
                "patterns": [
                    r"(?i)(?:password|pwd|pass)\s*[=:]\s*[\"'][^\"']{8,}[\"']",
                    r"(?i)(?:api[_-]?key|apikey)\s*[=:]\s*[\"'][^\"']{16,}[\"']",
                    r"(?i)(?:secret|token)\s*[=:]\s*[\"'][^\"']{16,}[\"']",
                    r"(?i)(?:private[_-]?key|privatekey)\s*[=:]\s*[\"'][^\"']{32,}[\"']",
                    r"(?:[A-Za-z0-9+/]{40,}={0,2})"  # Base64 encoded secrets
                ],
                "severity": "critical",
                "description": "Hardcoded credentials or secrets detected",
                "recommendation": "Use environment variables or secure key management"
            },
            "insecure_crypto": {
                "patterns": [
                    r"(?i)(?:md5|sha1)(?:\(\)|Hash|Digest)",
                    r"(?i)(?:DES|RC4|MD5|SHA1)(?:\s*\(|\s+)",
                    r"(?i)(?:random\.random\(\))",
                    r"(?i)(?:Math\.random\(\))"
                ],
                "severity": "medium",
                "description": "Insecure cryptographic practice",
                "recommendation": "Use strong cryptographic algorithms (SHA-256+, AES)"
            },
            "path_traversal": {
                "patterns": [
                    r"(?i)(?:\.\.\/|\.\.\\)",
                    r"(?i)(?:\/etc\/passwd|\/windows\/system32)",
                    r"(?i)(?:\.\.%2f|\.\.%5c)"
                ],
                "severity": "high",
                "description": "Potential path traversal vulnerability",
                "recommendation": "Validate and sanitize file paths"
            },
            "insecure_deserialization": {
                "patterns": [
                    r"(?i)(?:pickle\.loads?|yaml\.load|eval\s*\()",
                    r"(?i)(?:JSON\.parse.*user|unserialize\s*\()",
                    r"(?i)(?:ObjectInputStream|readObject)"
                ],
                "severity": "high",
                "description": "Insecure deserialization detected",
                "recommendation": "Use safe deserialization methods"
            },
            "weak_authentication": {
                "patterns": [
                    r"(?i)(?:password\s*==?\s*[\"'].*[\"'])",
                    r"(?i)(?:auth\s*=\s*[\"'].*[\"'])",
                    r"(?i)(?:login.*without.*password)",
                    r"(?i)(?:bypass.*auth)"
                ],
                "severity": "high",
                "description": "Weak authentication mechanism",
                "recommendation": "Implement strong authentication controls"
            }
        }
    
    def _initialize_secure_coding_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize secure coding best practices"""
        return {
            "input_validation": {
                "description": "Validate all user inputs",
                "checks": [
                    "Length validation",
                    "Type validation", 
                    "Format validation",
                    "Range validation"
                ]
            },
            "output_encoding": {
                "description": "Encode outputs to prevent injection attacks",
                "checks": [
                    "HTML encoding",
                    "URL encoding",
                    "SQL parameter binding",
                    "Command escaping"
                ]
            },
            "error_handling": {
                "description": "Secure error handling practices",
                "checks": [
                    "No sensitive information in errors",
                    "Generic error messages",
                    "Proper logging without secrets",
                    "Fail securely"
                ]
            },
            "access_control": {
                "description": "Implement proper access controls",
                "checks": [
                    "Authentication required",
                    "Authorization checks",
                    "Principle of least privilege",
                    "Session management"
                ]
            }
        }
    
    def _initialize_compliance_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance framework requirements"""
        return {
            "owasp_top_10": {
                "name": "OWASP Top 10 2021",
                "categories": [
                    "A01:2021-Broken Access Control",
                    "A02:2021-Cryptographic Failures", 
                    "A03:2021-Injection",
                    "A04:2021-Insecure Design",
                    "A05:2021-Security Misconfiguration",
                    "A06:2021-Vulnerable and Outdated Components",
                    "A07:2021-Identification and Authentication Failures",
                    "A08:2021-Software and Data Integrity Failures",
                    "A09:2021-Security Logging and Monitoring Failures",
                    "A10:2021-Server-Side Request Forgery"
                ]
            },
            "gdpr": {
                "name": "General Data Protection Regulation",
                "requirements": [
                    "Data encryption at rest and in transit",
                    "Data minimization principle",
                    "Right to be forgotten implementation",
                    "Consent management",
                    "Data breach notification procedures"
                ]
            },
            "pci_dss": {
                "name": "Payment Card Industry Data Security Standard",
                "requirements": [
                    "Secure network architecture",
                    "Strong access controls",
                    "Encryption of cardholder data",
                    "Regular security testing",
                    "Security monitoring and logging"
                ]
            }
        }
    
    def _load_vulnerability_database(self) -> Dict[str, Any]:
        """Load known vulnerability patterns and CVEs"""
        # In a real implementation, this would load from a CVE database
        return {
            "common_vulnerabilities": [
                {"id": "CWE-79", "name": "Cross-site Scripting", "severity": "high"},
                {"id": "CWE-89", "name": "SQL Injection", "severity": "critical"},
                {"id": "CWE-78", "name": "OS Command Injection", "severity": "critical"},
                {"id": "CWE-22", "name": "Path Traversal", "severity": "high"},
                {"id": "CWE-502", "name": "Deserialization", "severity": "high"}
            ]
        }
    
    def _load_security_wordlist(self) -> Set[str]:
        """Load security-related keywords for analysis"""
        return {
            'password', 'secret', 'key', 'token', 'auth', 'login', 'admin',
            'root', 'user', 'encrypt', 'decrypt', 'hash', 'salt', 'session',
            'cookie', 'cors', 'csrf', 'xss', 'sql', 'injection', 'vulnerability',
            'security', 'exploit', 'malware', 'virus', 'backdoor', 'trojan'
        }
    
    async def configure_for_role(self, role, is_priority: bool):
        """Configure security analysis based on agent role"""
        role_focus = {
            'security_specialist': {
                'focus_areas': ['vulnerability_assessment', 'threat_modeling', 'compliance'],
                'severity_threshold': 'low',
                'include_advanced_analysis': True
            },
            'developer': {
                'focus_areas': ['secure_coding', 'input_validation', 'authentication'],
                'severity_threshold': 'medium',
                'include_code_analysis': True
            },
            'it_architect': {
                'focus_areas': ['security_architecture', 'infrastructure', 'compliance'],
                'severity_threshold': 'medium',
                'include_architecture_review': True
            },
            'analyst': {
                'focus_areas': ['risk_assessment', 'compliance', 'reporting'],
                'severity_threshold': 'high',
                'include_risk_analysis': True
            }
        }
        
        self.role_config = role_focus.get(role.value, role_focus['developer'])
        logger.info(f"🔒 Security analysis configured for {role.value}: {self.role_config['focus_areas']}")
    
    async def should_execute(self, task: str, llm_response: str) -> bool:
        """Determine if security analysis should be applied"""
        # Always run for security specialist
        if hasattr(self, 'agent') and hasattr(self.agent, 'current_role'):
            if self.agent.current_role and self.agent.current_role.value == 'security_specialist':
                return True
        
        # Check for security-related keywords
        security_indicators = [
            'security', 'secure', 'vulnerability', 'audit', 'review',
            'authentication', 'authorization', 'encryption', 'password',
            'token', 'key', 'certificate', 'ssl', 'tls', 'https',
            'inject', 'xss', 'csrf', 'sql', 'command', 'path',
            'access', 'permission', 'privilege', 'compliance'
        ]
        
        text_to_check = (task + ' ' + llm_response).lower()
        
        # Check for security keywords
        has_security_content = any(indicator in text_to_check for indicator in security_indicators)
        
        # Check for code that might need security review
        has_code_blocks = bool(re.search(r'```\w*\n', llm_response))
        
        # Check for configuration or infrastructure content
        has_config_content = any(term in text_to_check for term in [
            'config', 'deploy', 'server', 'database', 'api', 'service'
        ])
        
        return has_security_content or (has_code_blocks and has_config_content)
    
    async def execute(self, task: str, llm_response: str) -> str:
        """Perform comprehensive security analysis"""
        try:
            logger.info("🔒 Starting comprehensive security analysis...")
            
            # Perform different types of analysis
            findings = []
            
            # 1. Code security analysis
            code_findings = await self._analyze_code_security(llm_response)
            findings.extend(code_findings)
            
            # 2. Configuration security analysis  
            config_findings = await self._analyze_configuration_security(llm_response)
            findings.extend(config_findings)
            
            # 3. Architecture security analysis
            arch_findings = await self._analyze_architecture_security(task, llm_response)
            findings.extend(arch_findings)
            
            # 4. Compliance analysis
            compliance_status = await self._analyze_compliance(findings)
            
            # Generate comprehensive security report
            security_report = self._generate_security_report(findings, compliance_status)
            
            # Add security analysis to response
            enhanced_response = llm_response + self._format_security_analysis(security_report)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ Security analysis failed: {e}")
            return llm_response + f"\n\n⚠️ Security analysis error: {str(e)}"
    
    async def _analyze_code_security(self, code_content: str) -> List[SecurityFinding]:
        """Analyze code for security vulnerabilities"""
        findings = []
        
        # Extract code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', code_content, re.DOTALL)
        all_code = '\n'.join(code_blocks) if code_blocks else code_content
        
        # Check each vulnerability pattern
        for vuln_type, vuln_info in self.vulnerability_patterns.items():
            for pattern in vuln_info["patterns"]:
                matches = re.finditer(pattern, all_code, re.MULTILINE | re.IGNORECASE)
                
                for match in matches:
                    # Find line number
                    line_num = all_code[:match.start()].count('\n') + 1
                    
                    finding = SecurityFinding(
                        severity=vuln_info["severity"],
                        category=vuln_type,
                        title=f"{vuln_type.replace('_', ' ').title()} Detected",
                        description=vuln_info["description"],
                        recommendation=vuln_info["recommendation"],
                        code_snippet=match.group(0)[:100],
                        line_number=line_num
                    )
                    findings.append(finding)
        
        # Additional code-specific checks
        if 'password' in all_code.lower() and '=' in all_code:
            findings.append(SecurityFinding(
                severity="medium",
                category="credential_management",
                title="Password Handling Detected",
                description="Password-related code requires security review",
                recommendation="Ensure passwords are properly hashed and never logged"
            ))
        
        return findings
    
    async def _analyze_configuration_security(self, content: str) -> List[SecurityFinding]:
        """Analyze configuration for security issues"""
        findings = []
        
        # Check for insecure configurations
        insecure_configs = {
            r"(?i)debug\s*=\s*true": {
                "severity": "medium",
                "title": "Debug Mode Enabled",
                "description": "Debug mode should not be enabled in production",
                "recommendation": "Disable debug mode in production environments"
            },
            r"(?i)ssl\s*=\s*false": {
                "severity": "high", 
                "title": "SSL/TLS Disabled",
                "description": "SSL/TLS should be enabled for secure communication",
                "recommendation": "Enable SSL/TLS encryption"
            },
            r"(?i)cors\s*=\s*\*": {
                "severity": "medium",
                "title": "Permissive CORS Policy",
                "description": "Wildcard CORS policy may be too permissive",
                "recommendation": "Restrict CORS to specific domains"
            },
            r"(?i)(?:0\.0\.0\.0|127\.0\.0\.1):\d+": {
                "severity": "low",
                "title": "Network Binding Configuration",
                "description": "Review network binding configuration",
                "recommendation": "Ensure appropriate network access controls"
            }
        }
        
        for pattern, config in insecure_configs.items():
            if re.search(pattern, content):
                findings.append(SecurityFinding(
                    severity=config["severity"],
                    category="configuration",
                    title=config["title"],
                    description=config["description"],
                    recommendation=config["recommendation"]
                ))
        
        return findings
    
    async def _analyze_architecture_security(self, task: str, content: str) -> List[SecurityFinding]:
        """Analyze architectural security considerations"""
        findings = []
        
        # Check for architectural security patterns
        if any(term in content.lower() for term in ['microservice', 'api', 'service']):
            findings.append(SecurityFinding(
                severity="info",
                category="architecture",
                title="Microservices Security Considerations",
                description="Microservices architecture requires additional security measures",
                recommendation="Implement service mesh, API gateway, and inter-service authentication"
            ))
        
        if any(term in content.lower() for term in ['database', 'db', 'sql']):
            findings.append(SecurityFinding(
                severity="info", 
                category="data_security",
                title="Database Security Review Required",
                description="Database implementations require security review",
                recommendation="Implement encryption at rest, access controls, and audit logging"
            ))
        
        if any(term in content.lower() for term in ['cloud', 'aws', 'azure', 'gcp']):
            findings.append(SecurityFinding(
                severity="info",
                category="cloud_security",
                title="Cloud Security Best Practices",
                description="Cloud deployments require specific security considerations",
                recommendation="Follow cloud security frameworks and implement identity management"
            ))
        
        return findings
    
    async def _analyze_compliance(self, findings: List[SecurityFinding]) -> Dict[str, str]:
        """Analyze compliance status against frameworks"""
        compliance_status = {}
        
        # OWASP Top 10 compliance check
        owasp_issues = [f for f in findings if f.category in [
            'sql_injection', 'xss', 'command_injection', 'insecure_crypto',
            'weak_authentication', 'path_traversal', 'insecure_deserialization'
        ]]
        
        if owasp_issues:
            high_severity_count = len([f for f in owasp_issues if f.severity in ['critical', 'high']])
            if high_severity_count > 0:
                compliance_status['owasp_top_10'] = f"Non-compliant - {high_severity_count} high/critical issues"
            else:
                compliance_status['owasp_top_10'] = "Partially compliant - minor issues detected"
        else:
            compliance_status['owasp_top_10'] = "Compliant - no major issues detected"
        
        # GDPR compliance (basic check)
        has_data_handling = any(term in str(findings).lower() for term in [
            'personal', 'data', 'user', 'customer', 'privacy'
        ])
        
        if has_data_handling:
            compliance_status['gdpr'] = "Review required - data handling detected"
        else:
            compliance_status['gdpr'] = "Not applicable - no personal data handling detected"
        
        return compliance_status
    
    def _generate_security_report(self, findings: List[SecurityFinding], compliance_status: Dict[str, str]) -> SecurityReport:
        """Generate comprehensive security report"""
        findings_by_severity = {
            'critical': len([f for f in findings if f.severity == 'critical']),
            'high': len([f for f in findings if f.severity == 'high']),
            'medium': len([f for f in findings if f.severity == 'medium']),
            'low': len([f for f in findings if f.severity == 'low']),
            'info': len([f for f in findings if f.severity == 'info'])
        }
        
        # Calculate risk score (0-100)
        risk_score = min(100, (
            findings_by_severity['critical'] * 25 +
            findings_by_severity['high'] * 15 +
            findings_by_severity['medium'] * 8 +
            findings_by_severity['low'] * 3 +
            findings_by_severity['info'] * 1
        ))
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(findings)
        
        return SecurityReport(
            risk_score=risk_score,
            total_findings=len(findings),
            findings_by_severity=findings_by_severity,
            findings=findings,
            recommendations=recommendations,
            compliance_status=compliance_status
        )
    
    def _generate_security_recommendations(self, findings: List[SecurityFinding]) -> List[str]:
        """Generate prioritized security recommendations"""
        recommendations = []
        
        # Group findings by category
        categories = set(f.category for f in findings)
        
        if 'hardcoded_secrets' in categories:
            recommendations.append("URGENT: Remove hardcoded credentials and implement secure secret management")
        
        if 'sql_injection' in categories or 'command_injection' in categories:
            recommendations.append("CRITICAL: Implement input validation and parameterized queries")
        
        if 'xss' in categories:
            recommendations.append("HIGH: Implement output encoding and Content Security Policy")
        
        if 'insecure_crypto' in categories:
            recommendations.append("MEDIUM: Upgrade to secure cryptographic algorithms")
        
        # Generic recommendations based on findings
        if any(f.severity in ['critical', 'high'] for f in findings):
            recommendations.append("Conduct immediate security review before production deployment")
        
        if len(findings) > 10:
            recommendations.append("Consider comprehensive security testing and code audit")
        
        recommendations.append("Implement security monitoring and logging")
        recommendations.append("Regular security training for development team")
        recommendations.append("Establish secure development lifecycle (SDL)")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _format_security_analysis(self, report: SecurityReport) -> str:
        """Format security analysis for output"""
        analysis = f"\n\n🔒 COMPREHENSIVE SECURITY ANALYSIS:\n" + "="*60 + "\n"
        
        # Risk assessment
        risk_level = "LOW"
        if report.risk_score >= 80:
            risk_level = "CRITICAL"
        elif report.risk_score >= 60:
            risk_level = "HIGH"
        elif report.risk_score >= 40:
            risk_level = "MEDIUM"
        
        analysis += f"📊 SECURITY RISK ASSESSMENT:\n"
        analysis += f"• Overall Risk Score: {report.risk_score}/100 ({risk_level})\n"
        analysis += f"• Total Security Findings: {report.total_findings}\n"
        analysis += f"• Critical Issues: {report.findings_by_severity['critical']}\n"
        analysis += f"• High Priority Issues: {report.findings_by_severity['high']}\n"
        analysis += f"• Medium Priority Issues: {report.findings_by_severity['medium']}\n"
        analysis += f"• Low Priority Issues: {report.findings_by_severity['low']}\n"
        analysis += f"• Informational: {report.findings_by_severity['info']}\n\n"
        
        # Detailed findings
        if report.findings:
            analysis += "🚨 SECURITY FINDINGS:\n" + "-"*30 + "\n"
            
            # Group by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                severity_findings = [f for f in report.findings if f.severity == severity]
                if severity_findings:
                    analysis += f"\n{severity.upper()} SEVERITY:\n"
                    for finding in severity_findings[:5]:  # Limit to 5 per severity
                        analysis += f"• {finding.title}\n"
                        analysis += f"  Category: {finding.category}\n"
                        analysis += f"  Description: {finding.description}\n"
                        analysis += f"  Recommendation: {finding.recommendation}\n"
                        if finding.code_snippet:
                            analysis += f"  Code: {finding.code_snippet}...\n"
                        analysis += "\n"
        
        # Compliance status
        if report.compliance_status:
            analysis += "📋 COMPLIANCE STATUS:\n" + "-"*30 + "\n"
            for framework, status in report.compliance_status.items():
                analysis += f"• {framework.upper()}: {status}\n"
            analysis += "\n"
        
        # Recommendations
        if report.recommendations:
            analysis += "🎯 PRIORITY RECOMMENDATIONS:\n" + "-"*30 + "\n"
            for i, rec in enumerate(report.recommendations[:8], 1):
                analysis += f"{i}. {rec}\n"
            analysis += "\n"
        
        # Security checklist
        analysis += "✅ SECURITY VERIFICATION CHECKLIST:\n" + "-"*30 + "\n"
        checklist_items = [
            "Input validation implemented for all user inputs",
            "Output encoding applied to prevent XSS attacks",
            "Authentication and authorization properly configured",
            "Sensitive data encrypted at rest and in transit",
            "Error messages don't reveal sensitive information",
            "Security headers configured (HTTPS, CSP, etc.)",
            "Dependencies scanned for known vulnerabilities",
            "Security logging and monitoring implemented",
            "Access controls follow principle of least privilege",
            "Regular security testing scheduled"
        ]
        
        for item in checklist_items:
            analysis += f"□ {item}\n"
        
        analysis += "\n⚠️ IMPORTANT: This automated analysis should be supplemented with manual security review.\n"
        analysis += "Consider engaging security professionals for production systems.\n"
        
        return analysis
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security analysis metrics and statistics"""
        return {
            "vulnerability_patterns": len(self.vulnerability_patterns),
            "secure_coding_rules": len(self.secure_coding_rules),
            "compliance_frameworks": len(self.compliance_frameworks),
            "known_vulnerabilities": len(self.known_vulnerabilities.get("common_vulnerabilities", [])),
            "security_wordlist_size": len(self.security_wordlist),
            "analysis_capabilities": [
                "Static code analysis",
                "Configuration security review", 
                "Architecture security assessment",
                "Compliance checking",
                "Vulnerability pattern matching",
                "Risk scoring and prioritization"
            ]
        }