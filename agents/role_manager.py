#!/usr/bin/env python3
"""
Enhanced Role Manager for Dynamic Role Assignment
Centralized role management with performance optimization
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

class DroneRole(Enum):
    """Different roles a drone can take"""
    ANALYST = "analyst"
    DATA_SCIENTIST = "datascientist" 
    IT_ARCHITECT = "it_architect"
    DEVELOPER = "developer"
    SECURITY_SPECIALIST = "security_specialist"

class RoleManager:
    """Centralized role management system"""
    
    def __init__(self):
        self.role_assignments: Dict[str, DroneRole] = {}
        self.assignment_history: List[Dict] = []
        self.role_keywords = self._initialize_role_keywords()
        self.capabilities_map = self._initialize_capabilities_map()
        
    def _initialize_role_keywords(self) -> Dict[DroneRole, List[str]]:
        """Initialize comprehensive role keyword mappings"""
        return {
            DroneRole.DATA_SCIENTIST: [
                'machine learning', 'ml', 'model', 'train', 'predict', 'dataset',
                'pandas', 'numpy', 'scikit', 'tensorflow', 'pytorch', 'analysis',
                'statistics', 'correlation', 'regression', 'classification',
                'opencv', 'cv2', 'image recognition', 'computer vision', 'bildverarbeitung',
                'bilderkennungs', 'bilderkennung', 'image processing', 'drone perspective',
                'pattern recognition', 'feature detection', 'object detection',
                'neural network', 'deep learning', 'artificial intelligence',
                'data mining', 'predictive analytics', 'supervised learning',
                'unsupervised learning', 'reinforcement learning', 'ai', 'ki'
            ],
            DroneRole.ANALYST: [
                'analyze', 'report', 'document', 'review', 'assess', 'evaluate',
                'metrics', 'dashboard', 'visualization', 'chart', 'graph',
                'insights', 'trends', 'patterns', 'summary', 'daten', 'data',
                'analytics', 'business intelligence', 'kpi', 'performance',
                'monitoring', 'reporting', 'analysis', 'interpretation'
            ],
            DroneRole.IT_ARCHITECT: [
                'architecture', 'design', 'system', 'infrastructure', 'scalability',
                'microservices', 'api', 'database', 'deployment', 'architektur',
                'cloud', 'docker', 'kubernetes', 'projekt', 'project structure',
                'enterprise', 'solution design', 'integration', 'platform',
                'distributed systems', 'service mesh', 'container orchestration'
            ],
            DroneRole.DEVELOPER: [
                'code', 'develop', 'implement', 'build', 'create', 'program',
                'function', 'class', 'script', 'application', 'web', 'frontend',
                'backend', 'debug', 'test', 'fix', 'python', 'erstelle', 'baust',
                'programming', 'coding', 'software development', 'programming language',
                'framework', 'library', 'development tools', 'ide'
            ],
            DroneRole.SECURITY_SPECIALIST: [
                'security', 'secure', 'vulnerability', 'audit', 'penetration', 'encrypt',
                'authenticate', 'authorize', 'compliance', 'threat', 'attack', 'defense',
                'owasp', 'csrf', 'xss', 'injection', 'authentication', 'authorization',
                'ssl', 'tls', 'firewall', 'intrusion', 'malware', 'breach', 'privacy',
                'sicherheit', 'verschlüsselung', 'angriff', 'schutz', 'bedrohung',
                'risks', 'risk assessment', 'cyber', 'cybersecurity', 'hacking', 'exploit',
                'penetration testing', 'security assessment', 'security audit',
                'vulnerability assessment', 'security compliance', 'gdpr', 'pci-dss'
            ]
        }
    
    def _initialize_capabilities_map(self) -> Dict[DroneRole, List[str]]:
        """Initialize role-specific capabilities"""
        return {
            DroneRole.ANALYST: [
                "data_analysis", "report_generation", "pattern_recognition",
                "statistical_analysis", "visualization", "documentation",
                "business_intelligence", "kpi_development", "performance_monitoring"
            ],
            DroneRole.DATA_SCIENTIST: [
                "machine_learning", "data_preprocessing", "model_training",
                "feature_engineering", "statistical_modeling", "python_analysis",
                "deep_learning", "neural_networks", "computer_vision", "nlp"
            ],
            DroneRole.IT_ARCHITECT: [
                "system_design", "infrastructure_planning", "scalability_design",
                "security_architecture", "technology_selection", "diagram_creation",
                "microservices_design", "cloud_architecture", "integration_patterns"
            ],
            DroneRole.DEVELOPER: [
                "coding", "debugging", "testing", "deployment",
                "version_control", "code_review", "problem_solving",
                "software_architecture", "api_development", "database_design"
            ],
            DroneRole.SECURITY_SPECIALIST: [
                "security_audit", "vulnerability_assessment", "penetration_testing",
                "secure_coding", "threat_modeling", "compliance_check",
                "encryption_implementation", "authentication_design", "authorization_patterns",
                "security_architecture_review", "risk_assessment", "incident_response",
                "security_monitoring", "forensic_analysis", "security_awareness"
            ]
        }
    
    def assign_role(self, drone_id: str, drone_name: str, task: str) -> Tuple[DroneRole, List[str]]:
        """
        Assign optimal role based on sophisticated task analysis
        
        Returns:
            Tuple of (assigned_role, capabilities)
        """
        task_lower = task.lower()
        role_scores = {}
        
        # Score each role based on keyword matches with weighted scoring
        for role, keywords in self.role_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in task_lower:
                    # Weight longer keywords higher (more specific)
                    weight = len(keyword.split()) * 2 if len(keyword.split()) > 1 else 1
                    score += weight
            role_scores[role] = score
        
        # Apply contextual boosts for complex scenarios
        role_scores = self._apply_contextual_scoring(task_lower, role_scores)
        
        # Select role with highest score, default to DEVELOPER
        best_role = max(role_scores.items(), key=lambda x: x[1])
        assigned_role = best_role[0] if best_role[1] > 0 else DroneRole.DEVELOPER
        
        # Get capabilities for the assigned role
        capabilities = self.capabilities_map.get(assigned_role, [])
        
        # Record assignment
        self._record_assignment(drone_id, drone_name, assigned_role, task, best_role[1])
        
        logger.info(f"🎯 Role Manager: {drone_name} assigned {assigned_role.value} (score: {best_role[1]})")
        
        return assigned_role, capabilities
    
    def _apply_contextual_scoring(self, task_lower: str, role_scores: Dict[DroneRole, int]) -> Dict[DroneRole, int]:
        """Apply contextual scoring boosts based on task complexity"""
        
        # Boost security role for fintech/finance tasks
        if any(term in task_lower for term in ['fintech', 'finance', 'payment', 'blockchain', 'banking']):
            role_scores[DroneRole.SECURITY_SPECIALIST] += 5
            
        # Boost architect role for platform/system tasks
        if any(term in task_lower for term in ['platform', 'system', 'architecture', 'infrastructure']):
            role_scores[DroneRole.IT_ARCHITECT] += 3
            
        # Boost data scientist for AI/ML tasks
        if any(term in task_lower for term in ['ai', 'artificial intelligence', 'ml', 'algorithm']):
            role_scores[DroneRole.DATA_SCIENTIST] += 4
            
        # Boost analyst for dashboard/reporting tasks  
        if any(term in task_lower for term in ['dashboard', 'analytics', 'monitoring', 'report']):
            role_scores[DroneRole.ANALYST] += 3
            
        return role_scores
    
    def _record_assignment(self, drone_id: str, drone_name: str, role: DroneRole, 
                          task: str, score: int) -> None:
        """Record role assignment for tracking and analytics"""
        assignment_record = {
            'drone_id': drone_id,
            'drone_name': drone_name,
            'role': role.value,
            'task': task[:100],  # Truncate for storage
            'score': score,
            'timestamp': time.time()
        }
        
        self.assignment_history.append(assignment_record)
        self.role_assignments[drone_id] = role
        
        # Update role monitor if available
        try:
            import role_monitor
            role_monitor.update_role(
                drone_id, drone_name, "None", role.value, task[:100]
            )
        except ImportError:
            pass  # Role monitor not available
    
    def get_role_statistics(self) -> Dict[str, int]:
        """Get statistics about role assignments"""
        stats = {}
        for record in self.assignment_history:
            role = record['role']
            stats[role] = stats.get(role, 0) + 1
        return stats
    
    def get_drone_role(self, drone_id: str) -> Optional[DroneRole]:
        """Get current role for a specific drone"""
        return self.role_assignments.get(drone_id)
    
    def clear_assignments(self) -> None:
        """Clear all role assignments (useful for testing)"""
        self.role_assignments.clear()
        self.assignment_history.clear()
        logger.info("🔄 Role Manager: All assignments cleared")

# Global instance for shared usage
_role_manager_instance = None

def get_role_manager() -> RoleManager:
    """Get singleton role manager instance"""
    global _role_manager_instance
    if _role_manager_instance is None:
        _role_manager_instance = RoleManager()
        logger.info("✅ Role Manager initialized")
    return _role_manager_instance