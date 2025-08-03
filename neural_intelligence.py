"""
Neural Intelligence System for Ollama Flow Framework
Implements pattern recognition, learning, and cognitive analysis
"""

import asyncio
import json
import logging
import sqlite3
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import pickle
import os

logger = logging.getLogger(__name__)

@dataclass
class NeuralPattern:
    """Represents a learned neural pattern"""
    pattern_id: str
    pattern_type: str  # task_decomposition, worker_selection, error_handling
    input_features: Dict[str, Any]
    output_result: Dict[str, Any]
    success_rate: float
    usage_count: int
    last_used: str
    created_at: str
    confidence_score: float
    metadata: Dict[str, Any]

@dataclass
class CognitiveInsight:
    """Cognitive analysis result"""
    insight_type: str
    description: str
    impact_score: float
    recommendations: List[str]
    evidence: Dict[str, Any]
    timestamp: str

class NeuralIntelligenceEngine:
    """Advanced neural intelligence system for pattern recognition and learning"""
    
    def __init__(self, db_path: str = "neural_intelligence.db"):
        self.db_path = db_path
        self.patterns: Dict[str, NeuralPattern] = {}
        self.cognitive_models: Dict[str, Any] = {}
        self.learning_rate = 0.1
        self.confidence_threshold = 0.7
        self.pattern_cache = {}
        
        # Initialize database
        self._init_database()
        self._load_patterns()
        self._init_cognitive_models()

    def _init_database(self):
        """Initialize neural intelligence database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Neural patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS neural_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                input_features TEXT NOT NULL,
                output_result TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                metadata TEXT
            )
        """)
        
        # Cognitive insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cognitive_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT NOT NULL,
                description TEXT NOT NULL,
                impact_score REAL NOT NULL,
                recommendations TEXT NOT NULL,
                evidence TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                context TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Learning sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                session_id TEXT PRIMARY KEY,
                session_type TEXT NOT NULL,
                input_data TEXT NOT NULL,
                output_data TEXT NOT NULL,
                performance_score REAL,
                learned_patterns INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()

    def _load_patterns(self):
        """Load existing patterns from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM neural_patterns")
        rows = cursor.fetchall()
        
        for row in rows:
            pattern = NeuralPattern(
                pattern_id=row[0],
                pattern_type=row[1],
                input_features=json.loads(row[2]),
                output_result=json.loads(row[3]),
                success_rate=row[4],
                usage_count=row[5],
                last_used=row[6],
                created_at=row[7],
                confidence_score=row[8],
                metadata=json.loads(row[9]) if row[9] else {}
            )
            self.patterns[pattern.pattern_id] = pattern
            
        conn.close()
        logger.info(f"Loaded {len(self.patterns)} neural patterns")

    def _init_cognitive_models(self):
        """Initialize cognitive analysis models"""
        self.cognitive_models = {
            'task_complexity_analyzer': self._analyze_task_complexity,
            'worker_performance_predictor': self._predict_worker_performance,
            'error_pattern_detector': self._detect_error_patterns,
            'optimization_recommender': self._recommend_optimizations,
            'success_probability_calculator': self._calculate_success_probability
        }
        logger.info(f"Initialized {len(self.cognitive_models)} cognitive models")

    def _generate_pattern_id(self, pattern_type: str, input_features: Dict[str, Any]) -> str:
        """Generate unique pattern ID"""
        content = f"{pattern_type}_{json.dumps(input_features, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def learn_from_execution(self, execution_data: Dict[str, Any]) -> List[NeuralPattern]:
        """Learn patterns from task execution data"""
        learned_patterns = []
        
        try:
            # Extract learning opportunities
            learning_ops = self._extract_learning_opportunities(execution_data)
            
            for op in learning_ops:
                pattern = await self._create_or_update_pattern(op)
                if pattern:
                    learned_patterns.append(pattern)
                    
            # Store learning session
            await self._store_learning_session(execution_data, learned_patterns)
            
            logger.info(f"Learned {len(learned_patterns)} patterns from execution")
            return learned_patterns
            
        except Exception as e:
            logger.error(f"Error in neural learning: {e}")
            return []

    def _extract_learning_opportunities(self, execution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract learning opportunities from execution data"""
        opportunities = []
        
        # Task decomposition patterns
        if 'task_decomposition' in execution_data:
            opportunities.append({
                'pattern_type': 'task_decomposition',
                'input_features': {
                    'original_task': execution_data.get('original_task', ''),
                    'worker_count': execution_data.get('worker_count', 0),
                    'architecture': execution_data.get('architecture', ''),
                    'task_complexity': self._estimate_task_complexity(execution_data.get('original_task', ''))
                },
                'output_result': {
                    'subtasks': execution_data['task_decomposition'].get('subtasks', []),
                    'execution_time': execution_data.get('execution_time', 0),
                    'success_rate': execution_data.get('success_rate', 0),
                    'parallel_efficiency': execution_data.get('parallel_efficiency', 0)
                }
            })
        
        # Worker selection patterns
        if 'worker_assignments' in execution_data:
            for assignment in execution_data['worker_assignments']:
                opportunities.append({
                    'pattern_type': 'worker_selection',
                    'input_features': {
                        'task_requirements': assignment.get('task_requirements', {}),
                        'worker_skills': assignment.get('worker_skills', []),
                        'worker_load': assignment.get('worker_load', 0),
                        'task_priority': assignment.get('task_priority', 'medium')
                    },
                    'output_result': {
                        'selected_worker': assignment.get('worker_id', ''),
                        'execution_success': assignment.get('success', False),
                        'execution_time': assignment.get('execution_time', 0),
                        'quality_score': assignment.get('quality_score', 0)
                    }
                })
        
        # Error handling patterns
        if 'errors' in execution_data:
            for error in execution_data['errors']:
                opportunities.append({
                    'pattern_type': 'error_handling',
                    'input_features': {
                        'error_type': error.get('type', ''),
                        'error_context': error.get('context', {}),
                        'system_state': error.get('system_state', {}),
                        'task_complexity': error.get('task_complexity', 0)
                    },
                    'output_result': {
                        'recovery_action': error.get('recovery_action', ''),
                        'recovery_success': error.get('recovery_success', False),
                        'recovery_time': error.get('recovery_time', 0),
                        'prevention_strategy': error.get('prevention_strategy', '')
                    }
                })
        
        return opportunities

    async def _create_or_update_pattern(self, opportunity: Dict[str, Any]) -> Optional[NeuralPattern]:
        """Create new pattern or update existing one"""
        try:
            pattern_id = self._generate_pattern_id(
                opportunity['pattern_type'], 
                opportunity['input_features']
            )
            
            if pattern_id in self.patterns:
                # Update existing pattern
                pattern = self.patterns[pattern_id]
                pattern.usage_count += 1
                pattern.last_used = datetime.now().isoformat()
                
                # Update success rate with exponential moving average
                current_success = self._calculate_opportunity_success(opportunity)
                pattern.success_rate = (
                    pattern.success_rate * (1 - self.learning_rate) + 
                    current_success * self.learning_rate
                )
                
                # Update confidence score
                pattern.confidence_score = min(1.0, pattern.confidence_score + 0.1)
                
            else:
                # Create new pattern
                pattern = NeuralPattern(
                    pattern_id=pattern_id,
                    pattern_type=opportunity['pattern_type'],
                    input_features=opportunity['input_features'],
                    output_result=opportunity['output_result'],
                    success_rate=self._calculate_opportunity_success(opportunity),
                    usage_count=1,
                    last_used=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat(),
                    confidence_score=0.5,
                    metadata={}
                )
                self.patterns[pattern_id] = pattern
            
            # Save to database
            await self._save_pattern(pattern)
            return pattern
            
        except Exception as e:
            logger.error(f"Error creating/updating pattern: {e}")
            return None

    def _calculate_opportunity_success(self, opportunity: Dict[str, Any]) -> float:
        """Calculate success score for a learning opportunity"""
        output = opportunity['output_result']
        
        if opportunity['pattern_type'] == 'task_decomposition':
            return min(1.0, (
                output.get('success_rate', 0) * 0.4 +
                (1.0 - min(1.0, output.get('execution_time', 60) / 60)) * 0.3 +
                output.get('parallel_efficiency', 0) * 0.3
            ))
        elif opportunity['pattern_type'] == 'worker_selection':
            return min(1.0, (
                (1.0 if output.get('execution_success', False) else 0.0) * 0.5 +
                (1.0 - min(1.0, output.get('execution_time', 30) / 30)) * 0.3 +
                output.get('quality_score', 0) * 0.2
            ))
        elif opportunity['pattern_type'] == 'error_handling':
            return min(1.0, (
                (1.0 if output.get('recovery_success', False) else 0.0) * 0.6 +
                (1.0 - min(1.0, output.get('recovery_time', 10) / 10)) * 0.4
            ))
        
        return 0.5  # Default neutral score

    async def _save_pattern(self, pattern: NeuralPattern):
        """Save pattern to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO neural_patterns 
            (pattern_id, pattern_type, input_features, output_result, success_rate, 
             usage_count, last_used, created_at, confidence_score, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.pattern_type,
            json.dumps(pattern.input_features),
            json.dumps(pattern.output_result),
            pattern.success_rate,
            pattern.usage_count,
            pattern.last_used,
            pattern.created_at,
            pattern.confidence_score,
            json.dumps(pattern.metadata)
        ))
        
        conn.commit()
        conn.close()

    async def predict_optimal_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal strategy based on learned patterns"""
        try:
            predictions = {}
            
            # Task decomposition prediction
            if 'task' in context:
                decomp_prediction = await self._predict_task_decomposition(context)
                predictions['task_decomposition'] = decomp_prediction
            
            # Worker selection prediction
            if 'available_workers' in context:
                worker_prediction = await self._predict_worker_selection(context)
                predictions['worker_selection'] = worker_prediction
            
            # Performance prediction
            performance_prediction = await self._predict_performance(context)
            predictions['performance'] = performance_prediction
            
            # Risk assessment
            risk_assessment = await self._assess_risks(context)
            predictions['risk_assessment'] = risk_assessment
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in strategy prediction: {e}")
            return {}

    async def _predict_task_decomposition(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal task decomposition strategy"""
        task = context.get('task', '')
        worker_count = context.get('worker_count', 4)
        
        # Find similar patterns
        similar_patterns = self._find_similar_patterns(
            'task_decomposition', 
            {
                'task_complexity': self._estimate_task_complexity(task),
                'worker_count': worker_count,
                'architecture': context.get('architecture', 'HIERARCHICAL')
            }
        )
        
        if similar_patterns:
            # Weighted average based on confidence and success rate
            total_weight = 0
            weighted_subtask_count = 0
            weighted_execution_time = 0
            
            for pattern in similar_patterns:
                weight = pattern.confidence_score * pattern.success_rate
                total_weight += weight
                
                subtask_count = len(pattern.output_result.get('subtasks', []))
                execution_time = pattern.output_result.get('execution_time', 60)
                
                weighted_subtask_count += subtask_count * weight
                weighted_execution_time += execution_time * weight
            
            if total_weight > 0:
                return {
                    'recommended_subtask_count': int(weighted_subtask_count / total_weight),
                    'estimated_execution_time': weighted_execution_time / total_weight,
                    'confidence': min(1.0, total_weight / len(similar_patterns)),
                    'based_on_patterns': len(similar_patterns)
                }
        
        # Fallback to heuristic
        estimated_complexity = self._estimate_task_complexity(task)
        return {
            'recommended_subtask_count': min(worker_count, max(2, int(estimated_complexity * 3))),
            'estimated_execution_time': estimated_complexity * 30,
            'confidence': 0.3,
            'based_on_patterns': 0
        }

    async def _predict_worker_selection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal worker selection"""
        available_workers = context.get('available_workers', [])
        task_requirements = context.get('task_requirements', {})
        
        worker_scores = {}
        
        for worker in available_workers:
            # Find patterns for this worker type
            similar_patterns = self._find_similar_patterns(
                'worker_selection',
                {
                    'worker_skills': worker.get('skills', []),
                    'task_priority': task_requirements.get('priority', 'medium')
                }
            )
            
            if similar_patterns:
                avg_success = sum(p.success_rate for p in similar_patterns) / len(similar_patterns)
                avg_confidence = sum(p.confidence_score for p in similar_patterns) / len(similar_patterns)
                worker_scores[worker['id']] = avg_success * avg_confidence
            else:
                # Heuristic scoring
                skill_match = len(set(worker.get('skills', [])) & set(task_requirements.get('required_skills', [])))
                load_factor = 1.0 - (worker.get('current_load', 0) / 10.0)
                worker_scores[worker['id']] = skill_match * 0.6 + load_factor * 0.4
        
        # Sort by score
        sorted_workers = sorted(worker_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'recommended_worker': sorted_workers[0][0] if sorted_workers else None,
            'worker_scores': dict(sorted_workers),
            'confidence': 0.8 if similar_patterns else 0.4
        }

    async def _predict_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict expected performance metrics"""
        # Analyze historical performance data
        similar_contexts = self._find_similar_execution_contexts(context)
        
        if similar_contexts:
            avg_execution_time = sum(c.get('execution_time', 60) for c in similar_contexts) / len(similar_contexts)
            avg_success_rate = sum(c.get('success_rate', 0.5) for c in similar_contexts) / len(similar_contexts)
            avg_parallel_efficiency = sum(c.get('parallel_efficiency', 0.5) for c in similar_contexts) / len(similar_contexts)
            
            return {
                'estimated_execution_time': avg_execution_time,
                'estimated_success_rate': avg_success_rate,
                'estimated_parallel_efficiency': avg_parallel_efficiency,
                'confidence': min(1.0, len(similar_contexts) / 10.0)
            }
        
        # Fallback estimates
        task_complexity = self._estimate_task_complexity(context.get('task', ''))
        worker_count = context.get('worker_count', 4)
        
        return {
            'estimated_execution_time': task_complexity * 20 + (60 / max(1, worker_count)),
            'estimated_success_rate': max(0.3, 1.0 - task_complexity * 0.3),
            'estimated_parallel_efficiency': min(0.9, worker_count * 0.2),
            'confidence': 0.3
        }

    async def _assess_risks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential risks and provide mitigation strategies"""
        risks = []
        
        # Task complexity risk
        task_complexity = self._estimate_task_complexity(context.get('task', ''))
        if task_complexity > 0.7:
            risks.append({
                'type': 'high_complexity',
                'severity': task_complexity,
                'description': 'Task complexity is high, may lead to decomposition issues',
                'mitigation': 'Consider breaking into smaller phases or adding more workers'
            })
        
        # Worker availability risk
        worker_count = context.get('worker_count', 4)
        if worker_count < 3:
            risks.append({
                'type': 'low_worker_count',
                'severity': 0.6,
                'description': 'Low worker count may limit parallel processing efficiency',
                'mitigation': 'Consider increasing worker count or using simpler decomposition'
            })
        
        # Historical failure patterns
        error_patterns = self._find_similar_patterns('error_handling', context)
        if error_patterns:
            failure_rate = 1.0 - (sum(p.success_rate for p in error_patterns) / len(error_patterns))
            if failure_rate > 0.3:
                risks.append({
                    'type': 'historical_failures',
                    'severity': failure_rate,
                    'description': f'Similar contexts have {failure_rate:.1%} failure rate',
                    'mitigation': 'Implement additional error handling and monitoring'
                })
        
        return {
            'risk_level': 'high' if any(r['severity'] > 0.7 for r in risks) else 'medium' if risks else 'low',
            'identified_risks': risks,
            'overall_risk_score': sum(r['severity'] for r in risks) / max(1, len(risks))
        }

    def _find_similar_patterns(self, pattern_type: str, features: Dict[str, Any], limit: int = 10) -> List[NeuralPattern]:
        """Find similar patterns based on feature similarity"""
        similar_patterns = []
        
        for pattern in self.patterns.values():
            if pattern.pattern_type == pattern_type and pattern.confidence_score >= self.confidence_threshold:
                similarity = self._calculate_feature_similarity(features, pattern.input_features)
                if similarity > 0.5:
                    similar_patterns.append((pattern, similarity))
        
        # Sort by similarity and return top matches
        similar_patterns.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in similar_patterns[:limit]]

    def _calculate_feature_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between two feature sets"""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
        
        similarity_scores = []
        
        for key in common_keys:
            val1, val2 = features1[key], features2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric similarity
                max_val = max(abs(val1), abs(val2), 1)
                similarity = 1.0 - abs(val1 - val2) / max_val
            elif isinstance(val1, str) and isinstance(val2, str):
                # String similarity (simple)
                similarity = 1.0 if val1 == val2 else 0.0
            elif isinstance(val1, list) and isinstance(val2, list):
                # List similarity (Jaccard)
                set1, set2 = set(val1), set(val2)
                similarity = len(set1 & set2) / max(len(set1 | set2), 1)
            else:
                similarity = 1.0 if val1 == val2 else 0.0
            
            similarity_scores.append(similarity)
        
        return sum(similarity_scores) / len(similarity_scores)

    def _estimate_task_complexity(self, task: str) -> float:
        """Estimate task complexity (0.0 to 1.0)"""
        if not task:
            return 0.5
        
        complexity_indicators = {
            'complex': 0.3, 'difficult': 0.3, 'advanced': 0.2, 'comprehensive': 0.2,
            'multiple': 0.1, 'integrate': 0.1, 'optimize': 0.1, 'analyze': 0.1,
            'implement': 0.05, 'create': 0.05, 'build': 0.05, 'develop': 0.05
        }
        
        task_lower = task.lower()
        complexity = 0.3  # Base complexity
        
        for indicator, weight in complexity_indicators.items():
            if indicator in task_lower:
                complexity += weight
        
        # Adjust for length
        complexity += min(0.2, len(task.split()) / 50)
        
        return min(1.0, complexity)

    def _find_similar_execution_contexts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar execution contexts from history"""
        # This would typically query a performance history database
        # For now, return empty list as placeholder
        return []

    async def generate_cognitive_insights(self, analysis_window_hours: int = 24) -> List[CognitiveInsight]:
        """Generate cognitive insights from recent patterns and performance"""
        insights = []
        
        try:
            # Analyze pattern effectiveness
            pattern_insights = await self._analyze_pattern_effectiveness()
            insights.extend(pattern_insights)
            
            # Analyze performance trends
            performance_insights = await self._analyze_performance_trends(analysis_window_hours)
            insights.extend(performance_insights)
            
            # Identify optimization opportunities
            optimization_insights = await self._identify_optimization_opportunities()
            insights.extend(optimization_insights)
            
            # Store insights
            for insight in insights:
                await self._store_cognitive_insight(insight)
            
            logger.info(f"Generated {len(insights)} cognitive insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating cognitive insights: {e}")
            return []

    async def _analyze_pattern_effectiveness(self) -> List[CognitiveInsight]:
        """Analyze effectiveness of learned patterns"""
        insights = []
        
        # Group patterns by type
        pattern_groups = defaultdict(list)
        for pattern in self.patterns.values():
            pattern_groups[pattern.pattern_type].append(pattern)
        
        for pattern_type, patterns in pattern_groups.items():
            if len(patterns) >= 3:  # Need minimum patterns for analysis
                avg_success = sum(p.success_rate for p in patterns) / len(patterns)
                avg_confidence = sum(p.confidence_score for p in patterns) / len(patterns)
                total_usage = sum(p.usage_count for p in patterns)
                
                if avg_success < 0.6:
                    insights.append(CognitiveInsight(
                        insight_type=f"{pattern_type}_effectiveness",
                        description=f"Low success rate ({avg_success:.1%}) for {pattern_type} patterns",
                        impact_score=0.8,
                        recommendations=[
                            f"Review and refine {pattern_type} strategy",
                            "Collect more training data for better patterns",
                            "Consider alternative approaches"
                        ],
                        evidence={
                            'pattern_count': len(patterns),
                            'avg_success_rate': avg_success,
                            'total_usage': total_usage
                        },
                        timestamp=datetime.now().isoformat()
                    ))
                
                elif avg_success > 0.8 and total_usage > 10:
                    insights.append(CognitiveInsight(
                        insight_type=f"{pattern_type}_success",
                        description=f"High success rate ({avg_success:.1%}) for {pattern_type} patterns",
                        impact_score=0.6,
                        recommendations=[
                            f"Continue leveraging {pattern_type} patterns",
                            "Share successful patterns with similar contexts",
                            "Use as template for other pattern types"
                        ],
                        evidence={
                            'pattern_count': len(patterns),
                            'avg_success_rate': avg_success,
                            'total_usage': total_usage
                        },
                        timestamp=datetime.now().isoformat()
                    ))
        
        return insights

    async def _analyze_performance_trends(self, hours: int) -> List[CognitiveInsight]:
        """Analyze performance trends"""
        insights = []
        
        # This would analyze performance metrics from the database
        # For now, return placeholder insights
        insights.append(CognitiveInsight(
            insight_type="performance_trend",
            description="Performance analysis requires more historical data",
            impact_score=0.3,
            recommendations=[
                "Continue collecting performance metrics",
                "Run more tasks to build performance baseline"
            ],
            evidence={'data_points': 0},
            timestamp=datetime.now().isoformat()
        ))
        
        return insights

    async def _identify_optimization_opportunities(self) -> List[CognitiveInsight]:
        """Identify optimization opportunities"""
        insights = []
        
        # Analyze pattern distribution
        pattern_types = defaultdict(int)
        for pattern in self.patterns.values():
            pattern_types[pattern.pattern_type] += 1
        
        if pattern_types['task_decomposition'] < 5:
            insights.append(CognitiveInsight(
                insight_type="learning_opportunity",
                description="Limited task decomposition patterns available",
                impact_score=0.7,
                recommendations=[
                    "Run more diverse tasks to learn decomposition patterns",
                    "Experiment with different worker counts and architectures",
                    "Focus on complex tasks for better pattern learning"
                ],
                evidence={'task_decomposition_patterns': pattern_types['task_decomposition']},
                timestamp=datetime.now().isoformat()
            ))
        
        return insights

    async def _store_cognitive_insight(self, insight: CognitiveInsight):
        """Store cognitive insight in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cognitive_insights 
            (insight_type, description, impact_score, recommendations, evidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            insight.insight_type,
            insight.description,
            insight.impact_score,
            json.dumps(insight.recommendations),
            json.dumps(insight.evidence),
            insight.timestamp
        ))
        
        conn.commit()
        conn.close()

    async def _store_learning_session(self, execution_data: Dict[str, Any], learned_patterns: List[NeuralPattern]):
        """Store learning session data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = hashlib.sha256(f"{datetime.now().isoformat()}_{execution_data}".encode()).hexdigest()[:16]
        
        cursor.execute("""
            INSERT INTO learning_sessions 
            (session_id, session_type, input_data, output_data, performance_score, learned_patterns, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            'task_execution',
            json.dumps(execution_data),
            json.dumps([asdict(p) for p in learned_patterns]),
            execution_data.get('success_rate', 0),
            len(learned_patterns),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()

    # Cognitive model implementations
    async def _analyze_task_complexity(self, task: str) -> Dict[str, Any]:
        """Cognitive model for task complexity analysis"""
        complexity_score = self._estimate_task_complexity(task)
        
        return {
            'complexity_score': complexity_score,
            'complexity_level': 'high' if complexity_score > 0.7 else 'medium' if complexity_score > 0.4 else 'low',
            'recommended_workers': min(8, max(2, int(complexity_score * 6) + 1)),
            'estimated_subtasks': min(10, max(2, int(complexity_score * 5) + 1)),
            'risk_factors': self._identify_complexity_risk_factors(task)
        }

    async def _predict_worker_performance(self, worker_context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict worker performance based on historical patterns"""
        worker_id = worker_context.get('worker_id', '')
        task_type = worker_context.get('task_type', '')
        
        # Find relevant patterns
        relevant_patterns = [
            p for p in self.patterns.values() 
            if p.pattern_type == 'worker_selection' and 
            worker_id in str(p.output_result)
        ]
        
        if relevant_patterns:
            avg_success = sum(p.success_rate for p in relevant_patterns) / len(relevant_patterns)
            return {
                'predicted_success_rate': avg_success,
                'confidence': min(1.0, len(relevant_patterns) / 5.0),
                'based_on_executions': len(relevant_patterns)
            }
        
        return {
            'predicted_success_rate': 0.7,  # Default assumption
            'confidence': 0.3,
            'based_on_executions': 0
        }

    async def _detect_error_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential error patterns"""
        error_patterns = [p for p in self.patterns.values() if p.pattern_type == 'error_handling']
        
        risk_score = 0.0
        potential_errors = []
        
        for pattern in error_patterns:
            similarity = self._calculate_feature_similarity(context, pattern.input_features)
            if similarity > 0.6:
                risk_score = max(risk_score, 1.0 - pattern.success_rate)
                potential_errors.append({
                    'error_type': pattern.input_features.get('error_type', 'unknown'),
                    'probability': 1.0 - pattern.success_rate,
                    'similarity': similarity
                })
        
        return {
            'risk_score': risk_score,
            'potential_errors': potential_errors,
            'recommendations': self._generate_error_prevention_recommendations(potential_errors)
        }

    async def _recommend_optimizations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimizations based on learned patterns"""
        recommendations = []
        
        # Worker count optimization
        task_complexity = self._estimate_task_complexity(context.get('task', ''))
        current_workers = context.get('worker_count', 4)
        optimal_workers = min(8, max(2, int(task_complexity * 6) + 1))
        
        if abs(current_workers - optimal_workers) > 1:
            recommendations.append({
                'type': 'worker_count',
                'current': current_workers,
                'recommended': optimal_workers,
                'reason': f'Task complexity ({task_complexity:.2f}) suggests {optimal_workers} workers',
                'impact': 'performance'
            })
        
        # Architecture optimization
        if task_complexity > 0.6 and context.get('architecture') != 'HIERARCHICAL':
            recommendations.append({
                'type': 'architecture',
                'current': context.get('architecture', 'CENTRALIZED'),
                'recommended': 'HIERARCHICAL',
                'reason': 'Complex tasks benefit from hierarchical coordination',
                'impact': 'coordination'
            })
        
        return {
            'recommendations': recommendations,
            'priority': 'high' if len(recommendations) > 2 else 'medium' if recommendations else 'low'
        }

    async def _calculate_success_probability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate probability of successful execution"""
        base_probability = 0.7  # Base assumption
        
        # Adjust based on task complexity
        task_complexity = self._estimate_task_complexity(context.get('task', ''))
        complexity_penalty = task_complexity * 0.3
        
        # Adjust based on worker count
        worker_count = context.get('worker_count', 4)
        worker_bonus = min(0.2, (worker_count - 2) * 0.05)
        
        # Adjust based on historical patterns
        similar_patterns = self._find_similar_patterns('task_decomposition', context)
        if similar_patterns:
            historical_success = sum(p.success_rate for p in similar_patterns) / len(similar_patterns)
            history_weight = min(0.3, len(similar_patterns) * 0.05)
            base_probability = base_probability * (1 - history_weight) + historical_success * history_weight
        
        final_probability = max(0.1, min(0.95, base_probability - complexity_penalty + worker_bonus))
        
        return {
            'success_probability': final_probability,
            'confidence': 0.8 if similar_patterns else 0.5,
            'factors': {
                'task_complexity_penalty': complexity_penalty,
                'worker_count_bonus': worker_bonus,
                'historical_patterns': len(similar_patterns)
            }
        }

    def _identify_complexity_risk_factors(self, task: str) -> List[str]:
        """Identify risk factors that contribute to task complexity"""
        risk_factors = []
        task_lower = task.lower()
        
        risk_keywords = {
            'integration': 'Multiple system integration required',
            'api': 'API development/integration complexity',
            'database': 'Database design and management complexity',
            'security': 'Security implementation requirements',
            'performance': 'Performance optimization challenges',
            'scalability': 'Scalability considerations',
            'testing': 'Comprehensive testing requirements',
            'deployment': 'Deployment and DevOps complexity'
        }
        
        for keyword, description in risk_keywords.items():
            if keyword in task_lower:
                risk_factors.append(description)
        
        return risk_factors

    def _generate_error_prevention_recommendations(self, potential_errors: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations to prevent potential errors"""
        recommendations = []
        
        for error in potential_errors:
            error_type = error['error_type']
            
            if 'timeout' in error_type.lower():
                recommendations.append("Implement timeout handling and retry mechanisms")
            elif 'memory' in error_type.lower():
                recommendations.append("Monitor memory usage and implement resource limits")
            elif 'connection' in error_type.lower():
                recommendations.append("Add connection pooling and error recovery")
            elif 'validation' in error_type.lower():
                recommendations.append("Strengthen input validation and sanitization")
            else:
                recommendations.append(f"Add specific error handling for {error_type}")
        
        return list(set(recommendations))  # Remove duplicates

    def get_neural_status(self) -> Dict[str, Any]:
        """Get current neural intelligence status"""
        pattern_stats = defaultdict(int)
        for pattern in self.patterns.values():
            pattern_stats[pattern.pattern_type] += 1
        
        avg_confidence = sum(p.confidence_score for p in self.patterns.values()) / max(1, len(self.patterns))
        avg_success = sum(p.success_rate for p in self.patterns.values()) / max(1, len(self.patterns))
        
        return {
            'total_patterns': len(self.patterns),
            'pattern_distribution': dict(pattern_stats),
            'average_confidence': avg_confidence,
            'average_success_rate': avg_success,
            'cognitive_models': list(self.cognitive_models.keys()),
            'learning_active': True,
            'database_path': self.db_path
        }

    async def initialize(self) -> bool:
        """Initialize the neural intelligence engine"""
        try:
            # Database is already initialized in __init__
            # Load any additional patterns or perform setup
            logger.info("Neural Intelligence Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Neural Intelligence Engine: {e}")
            return False

    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all learned patterns"""
        patterns_list = []
        for pattern in self.patterns.values():
            patterns_list.append({
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'input_features': pattern.input_features,
                'output_result': pattern.output_result,
                'success_rate': pattern.success_rate,
                'usage_count': pattern.usage_count,
                'last_used': pattern.last_used,
                'created_at': pattern.created_at,
                'confidence_score': pattern.confidence_score,
                'metadata': pattern.metadata
            })
        return patterns_list

    def get_status(self) -> Dict[str, Any]:
        """Get neural intelligence status (alias for get_neural_status)"""
        return self.get_neural_status()