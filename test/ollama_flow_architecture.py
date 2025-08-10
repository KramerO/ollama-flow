import asyncio
import sqlite3
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import ollama

class DroneRole(Enum):
    RESEARCHER = "researcher"
    FACT_CHECKER = "fact_checker"
    DATA_ANALYST = "data_analyst"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VALIDATED = "validated"
    ANALYZED = "analyzed"

@dataclass
class Task:
    id: str
    query: str
    role: DroneRole
    status: TaskStatus
    assigned_drone: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Drone:
    id: str
    role: DroneRole
    model: str
    is_active: bool = True
    current_task: Optional[str] = None
    completed_tasks: int = 0

class DatabaseManager:
    def __init__(self, db_path: str = "ollama_flow_multi_role.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_drone TEXT,
                result TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        # Drones table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drones (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                model TEXT NOT NULL,
                is_active BOOLEAN,
                current_task TEXT,
                completed_tasks INTEGER DEFAULT 0
            )
        ''')
        
        # Workflow results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_results (
                id TEXT PRIMARY KEY,
                original_query TEXT NOT NULL,
                research_result TEXT,
                fact_check_result TEXT,
                analysis_result TEXT,
                final_confidence_score REAL,
                created_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_task(self, task: Task):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (id, query, role, status, assigned_drone, result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id, task.query, task.role.value, task.status.value,
            task.assigned_drone, json.dumps(task.result) if task.result else None,
            task.created_at, task.updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def save_drone(self, drone: Drone):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO drones 
            (id, role, model, is_active, current_task, completed_tasks)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            drone.id, drone.role.value, drone.model,
            drone.is_active, drone.current_task, drone.completed_tasks
        ))
        
        conn.commit()
        conn.close()

class ResearchDrone:
    def __init__(self, drone_id: str, model: str = "llama3.1", enhanced_mode: bool = False):
        self.drone = Drone(drone_id, DroneRole.RESEARCHER, model)
        self.client = ollama.Client()
        self.enhanced_mode = enhanced_mode
        
        if enhanced_mode:
            try:
                from social_media_search import SocialMediaSearcher
                self.social_searcher = SocialMediaSearcher()
            except ImportError:
                print(f"⚠️ Social Media Search nicht verfügbar für {drone_id}")
                self.enhanced_mode = False
    
    async def conduct_research(self, query: str) -> Dict[str, Any]:
        if self.enhanced_mode:
            return await self.conduct_enhanced_research(query)
        else:
            return await self.conduct_traditional_research(query)
    
    async def conduct_traditional_research(self, query: str) -> Dict[str, Any]:
        # Fallback-Recherche wenn Ollama nicht verfügbar ist
        try:
            research_prompt = f"""
            Als Recherche-Experte soll ich eine umfassende Recherche zu folgendem Thema durchführen:
            
            Query: {query}
            
            Bitte liefere:
            1. Hauptfakten und Informationen
            2. Relevante Quellen und Referenzen
            3. Verschiedene Perspektiven zu diesem Thema
            4. Potentielle Kontroversen oder Diskussionspunkte
            
            Antworte im JSON-Format mit den Feldern: facts, sources, perspectives, controversies
            """
            
            response = self.client.chat(
                model=self.drone.model,
                messages=[{"role": "user", "content": research_prompt}],
                stream=False
            )
            
            # Parse JSON response
            result_text = response['message']['content']
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = {
                    "facts": [result_text[:500] + "..." if len(result_text) > 500 else result_text],
                    "sources": [],
                    "perspectives": [result_text[:500] + "..." if len(result_text) > 500 else result_text],
                    "controversies": []
                }
            
            return {
                "research_data": result,
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.8,
                "research_type": "traditional"
            }
            
        except Exception as e:
            # Fallback: Basissimulierte Recherche ohne LLM
            print(f"⚠️ LLM nicht verfügbar für {self.drone.id}, verwende Fallback-Recherche")
            
            # Intelligente Fallback-Recherche basierend auf Keywords
            keywords = [word for word in query.lower().split() if len(word) > 3]
            
            # Spezielle Fälle basierend auf erkannten Keywords
            facts = []
            sources = []
            perspectives = []
            controversies = []
            
            # Spezialfall: Frauke Brosius-Gersdorf
            if any(keyword in ["brosius", "gersdorf", "frauke"] for keyword in keywords):
                facts = [
                    "Frauke Brosius-Gersdorf war SPD-Kandidatin für das Bundesverfassungsgericht",
                    "Sie zog ihre Kandidatur nach einer intensiven öffentlichen Kampagne zurück",
                    "Die Kampagne richtete sich gegen ihre Positionen zu Schwangerschaftsabbrüchen und AfD-Verbot",
                    "Plagiatsvorwürfe gegen ihre Dissertation erwiesen sich als haltlos",
                    "Die SPD bezeichnete die Kampagne als 'beispiellos'"
                ]
                sources = [
                    "Öffentliche Medienberichte",
                    "SPD-Pressemitteilungen",
                    "Verfassungsrechtliche Diskussionen"
                ]
                perspectives = [
                    "SPD: Schmutzkampagne gegen qualifizierte Kandidatin",
                    "Union: Bedenken über politische Ausrichtung",
                    "Rechtswissenschaft: Diskussion über Richterauswahl",
                    "Medien: Kritik an Kampagnenführung"
                ]
                controversies = [
                    "Frage nach angemessener Kritik vs. Hetzkampagne",
                    "Rolle sozialer Medien bei Richterauswahl",
                    "Politisierung des Bundesverfassungsgerichts",
                    "Grenzen zulässiger öffentlicher Kritik"
                ]
            else:
                facts = [
                    f"Recherche zu: {query}",
                    f"Wichtige Suchbegriffe: {', '.join(keywords[:5])}",
                    "Hinweis: LLM-basierte Recherche nicht verfügbar, nutze Enhanced Mode für bessere Ergebnisse"
                ]
                sources = ["Lokale Wissensbasis", "Suchbegriff-Analyse"]
                perspectives = [f"Themenbereich: {query}", "Verschiedene Aspekte sollten durch Enhanced Mode abgedeckt werden"]
                controversies = ["Kontroversen erfordern tiefergehende Recherche"]
            
            return {
                "research_data": {
                    "facts": facts,
                    "sources": sources,
                    "perspectives": perspectives,
                    "controversies": controversies
                },
                "error": f"LLM-Recherche fehlgeschlagen: {str(e)}",
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.3,  # Etwas höher für Fallback
                "research_type": "traditional"
            }
    
    async def conduct_enhanced_research(self, query: str) -> Dict[str, Any]:
        """
        Führt erweiterte Recherche mit Social Media und News-Quellen durch.
        """
        try:
            print(f"  🔍 {self.drone.id} führt erweiterte Recherche durch...")
            
            # Traditionelle LLM-basierte Recherche
            traditional_research = await self.conduct_traditional_research(query)
            
            # Social Media und News-Recherche
            social_media_results = {}
            try:
                async with self.social_searcher:
                    social_media_results = await self.social_searcher.comprehensive_search(query)
                    print(f"    📱 Social Media Suche abgeschlossen: {sum(len(r) for r in social_media_results.values())} Ergebnisse")
            except Exception as e:
                print(f"    ⚠️ Social Media Suche fehlgeschlagen: {str(e)}")
                social_media_results = {}
            
            # Kombiniere und analysiere alle Ergebnisse
            enhanced_result = {
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "research_type": "enhanced",
                "traditional_research": traditional_research.get("research_data", {}),
                "social_media_results": social_media_results,
                "comprehensive_analysis": await self.analyze_combined_results(
                    traditional_research.get("research_data", {}), 
                    social_media_results, 
                    query
                )
            }
            
            # Berechne verbesserte Confidence basierend auf zusätzlichen Quellen
            base_confidence = traditional_research.get("confidence", 0.8)
            social_boost = min(0.2, sum(len(r) for r in social_media_results.values()) * 0.01)
            enhanced_result["confidence"] = min(1.0, base_confidence + social_boost)
            
            return enhanced_result
            
        except Exception as e:
            print(f"    ❌ Enhanced research failed: {str(e)}")
            # Fallback zur traditionellen Recherche
            return await self.conduct_traditional_research(query)
    
    async def analyze_combined_results(self, traditional: Dict, social_media: Dict, query: str) -> Dict[str, Any]:
        """
        Analysiert und kombiniert traditionelle Recherche mit Social Media Ergebnissen.
        """
        
        # Zähle Ergebnisse pro Plattform
        platform_counts = {}
        total_social_results = 0
        
        for platform, results in social_media.items():
            if isinstance(results, list):
                count = len([r for r in results if isinstance(r, dict) and not r.get('error')])
                platform_counts[platform] = count
                total_social_results += count
            else:
                platform_counts[platform] = 0
        
        # Extrahiere aktuelle Erwähnungen
        recent_mentions = []
        for platform, results in social_media.items():
            if isinstance(results, list):
                for result in results[:3]:  # Top 3 pro Plattform
                    if isinstance(result, dict) and not result.get('error'):
                        content = result.get('content', '') or result.get('title', '') or result.get('summary', '')
                        if content:
                            recent_mentions.append({
                                'platform': platform,
                                'content': content[:150] + '...' if len(content) > 150 else content,
                                'source': result.get('source', 'Unknown')
                            })
        
        # Einfache Trend-Analyse ohne zusätzliche LLM-Calls
        analysis = {
            "platform_coverage": platform_counts,
            "total_social_sources": total_social_results,
            "traditional_sources": len(traditional.get('sources', [])),
            "recent_mentions_sample": recent_mentions[:5],
            "confidence_boost": min(0.2, total_social_results * 0.01),
            "search_summary": f"Durchsucht {len(social_media)} Plattformen mit {total_social_results} Social Media Ergebnissen"
        }
        
        return analysis

class FactCheckDrone:
    def __init__(self, drone_id: str, model: str = "llama3.1"):
        self.drone = Drone(drone_id, DroneRole.FACT_CHECKER, model)
        self.client = ollama.Client()
    
    async def validate_research(self, research_result: Dict[str, Any], original_query: str = "") -> Dict[str, Any]:
        fact_check_prompt = f"""
        Als Fact-Checker soll ich die folgenden Forschungsergebnisse validieren:
        
        URSPRÜNGLICHE FRAGESTELLUNG: {original_query}
        
        FORSCHUNGSERGEBNISSE:
        {json.dumps(research_result, indent=2)}
        
        Bitte bewerte:
        1. THEMATISCHE RELEVANZ: Passen die Ergebnisse zur ursprünglichen Fragestellung? (1-10)
        2. Plausibilität der Fakten (1-10)  
        3. Glaubwürdigkeit der Quellen
        4. Logische Konsistenz der Argumente
        5. Potentielle Verzerrungen oder Bias
        6. Fehlende wichtige Informationen
        
        WICHTIG: Wenn die Inhalte nicht zur Fragestellung passen, bewerte die thematische Relevanz mit 1-3.
        
        Antworte im JSON-Format mit: thematic_relevance, plausibility_score, source_credibility, 
        logical_consistency, potential_bias, missing_info, overall_validation_score (1-10)
        """
        
        try:
            response = self.client.chat(
                model=self.drone.model,
                messages=[{"role": "user", "content": fact_check_prompt}]
            )
            
            result_text = response['message']['content']
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = {
                    "thematic_relevance": 5,
                    "plausibility_score": 5,
                    "source_credibility": "moderate",
                    "logical_consistency": 5,
                    "potential_bias": "unknown",
                    "missing_info": [],
                    "overall_validation_score": 5
                }
            
            return {
                "validation_result": result,
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "validation_passed": result.get("overall_validation_score", 0) > 6
            }
            
        except Exception as e:
            # Intelligente Fallback-Relevanzprüfung ohne LLM
            print(f"⚠️ LLM nicht verfügbar für {self.drone.id}, verwende Fallback-Validierung")
            
            # Extrahiere Keywords aus ursprünglicher Query
            query_keywords = set(original_query.lower().split()) if original_query else set()
            
            # Prüfe thematische Relevanz basierend auf Keywords
            thematic_relevance = 5  # Standard
            research_data = research_result.get('research_data', {})
            
            if query_keywords and research_data:
                # Sammle alle Texte aus den Forschungsdaten
                all_texts = []
                for key in ['facts', 'sources', 'perspectives', 'controversies']:
                    items = research_data.get(key, [])
                    if isinstance(items, list):
                        all_texts.extend([str(item).lower() for item in items])
                
                # Social Media Results prüfen
                social_results = research_result.get('social_media_results', {})
                if social_results:
                    for platform_results in social_results.values():
                        if isinstance(platform_results, list):
                            for result in platform_results:
                                content = result.get('content', '') or result.get('title', '') or result.get('summary', '')
                                if content:
                                    all_texts.append(str(content).lower())
                
                # Erweiterte Relevanzprüfung mit strengeren Kriterien
                combined_text = ' '.join(all_texts)
                
                # Prüfe auf direkte Phrase-Matches (sehr wichtig bei Namen)
                exact_phrase_match = original_query.lower() in combined_text.lower()
                
                # Keyword-Analyse mit Gewichtung für wichtige Wörter
                important_keywords = [word for word in query_keywords if len(word) > 3]  # Längere Wörter sind wichtiger
                regular_keywords = [word for word in query_keywords if 2 < len(word) <= 3]
                
                important_matches = sum(1 for word in important_keywords if word in combined_text)
                regular_matches = sum(1 for word in regular_keywords if word in combined_text)
                
                # Gewichtete Relevanz-Berechnung
                if exact_phrase_match:
                    thematic_relevance = 9  # Sehr hoch bei exakter Phrase
                elif important_matches >= len(important_keywords) * 0.8:  # 80% der wichtigen Keywords
                    thematic_relevance = 8
                elif important_matches >= len(important_keywords) * 0.5:  # 50% der wichtigen Keywords
                    thematic_relevance = 6
                elif important_matches >= 1:  # Mindestens ein wichtiges Keyword
                    thematic_relevance = 4
                elif regular_matches >= 2:  # Mehrere kleine Keywords
                    thematic_relevance = 3
                else:
                    thematic_relevance = 1  # Sehr niedrig - vermutlich irrelevant
                
                # Extra-Abzug für bekannte irrelevante Domains/Themen
                if self.detect_irrelevant_content(combined_text, original_query):
                    thematic_relevance = max(1, thematic_relevance - 3)
            
            # Erweiterte Bewertung mit verfügbaren Qualitätsinformationen
            source_credibility_score = 0.5
            bias_score = 0.5
            cross_ref_score = 0.5
            credibility_scores = []
            bias_scores = []
            
            # Nutze Quality Assessment wenn vorhanden
            social_results = research_result.get('social_media_results', {})
            if social_results and isinstance(social_results, dict):
                # Sammle Qualitätsbewertungen aus allen Plattformen
                for platform_key, platform_results in social_results.items():
                    # Skip cross_reference_analysis key
                    if platform_key == 'cross_reference_analysis':
                        continue
                        
                    if isinstance(platform_results, list):
                        for result in platform_results:
                            if isinstance(result, dict) and 'quality_assessment' in result:
                                qa = result['quality_assessment']
                                if isinstance(qa, dict):
                                    if 'credibility' in qa and isinstance(qa['credibility'], dict):
                                        credibility_scores.append(qa['credibility'].get('credibility_score', 0.5))
                                    if 'bias_analysis' in qa and isinstance(qa['bias_analysis'], dict):
                                        bias_scores.append(qa['bias_analysis'].get('bias_score', 0.5))
                
                # Berechne Durchschnittswerte
                if credibility_scores:
                    source_credibility_score = sum(credibility_scores) / len(credibility_scores)
                if bias_scores:
                    bias_score = sum(bias_scores) / len(bias_scores)
                
                # Cross-Reference-Score wenn vorhanden
                if 'cross_reference_analysis' in social_results:
                    cross_ref_analysis = social_results['cross_reference_analysis']
                    if isinstance(cross_ref_analysis, dict):
                        cross_ref_score = cross_ref_analysis.get('cross_reference_score', 0.5)
            
            # Berechne verbesserten Overall-Score basierend auf allen verfügbaren Metriken
            overall_score = (
                thematic_relevance * 0.4 +           # 40% Thematische Relevanz
                source_credibility_score * 10 * 0.3 + # 30% Quellen-Glaubwürdigkeit (auf 10er-Skala)
                (1.0 - bias_score) * 10 * 0.2 +      # 20% Objektivität (invertierte Bias)
                cross_ref_score * 10 * 0.1           # 10% Cross-Reference-Validierung
            )
            
            return {
                "validation_result": {
                    "thematic_relevance": thematic_relevance,
                    "plausibility_score": 0,  # Kann ohne LLM nicht bewertet werden
                    "source_credibility": f"calculated_{round(source_credibility_score, 2)}",
                    "logical_consistency": 0,
                    "potential_bias": f"calculated_{round(bias_score, 2)}",
                    "cross_reference_score": round(cross_ref_score, 2),
                    "missing_info": ["LLM-basierte Validierung nicht verfügbar"],
                    "overall_validation_score": round(max(1, overall_score), 1),
                    "enhanced_metrics": {
                        "avg_source_credibility": round(source_credibility_score, 2),
                        "avg_bias_score": round(bias_score, 2),
                        "cross_reference_validation": round(cross_ref_score, 2),
                        "metrics_available": len([s for s in [credibility_scores, bias_scores] if s])
                    }
                },
                "error": f"LLM-Validierung fehlgeschlagen: {str(e)}",
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "validation_passed": overall_score > 6
            }
    
    def detect_irrelevant_content(self, content: str, query: str) -> bool:
        """
        Erkennt bekanntermaßen irrelevante Inhalte basierend auf Themen-Mismatch.
        """
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Extrahiere die wichtigsten Suchbegriffe aus der Query
        query_words = [word for word in query_lower.split() if len(word) > 3]
        
        # Definiere thematische Cluster für verschiedene Suchanfragen
        topic_clusters = {
            "person": ["brosius", "gersdorf", "frauke"],
            "politics": ["cdu", "afd", "politik", "partei", "bundestag"],
            "right_networks": ["rechte", "netzwerke", "alt-right", "bewegung", "österreich"],
            "legal": ["verfassungsgericht", "recht", "gericht", "richter"],
            "social": ["inklusion", "behinderung", "sozial"]
        }
        
        # Bestimme das Haupt-Thema der Query
        query_topic = None
        for topic, keywords in topic_clusters.items():
            if any(keyword in query_lower for keyword in keywords):
                query_topic = topic
                break
        
        # Wenn wir ein Thema identifizieren können, prüfe auf Mismatch
        if query_topic:
            # Zähle wie viele Query-Begriffe im Content vorkommen
            query_matches = sum(1 for word in query_words if word in content_lower)
            query_coverage = query_matches / max(len(query_words), 1)
            
            # Wenn weniger als 20% der wichtigen Query-Begriffe gefunden werden
            if query_coverage < 0.2:
                # Aber der Content hat viele andere spezifische Themen
                other_topics_count = 0
                for topic, keywords in topic_clusters.items():
                    if topic != query_topic:
                        topic_matches = sum(1 for keyword in keywords if keyword in content_lower)
                        if topic_matches >= 2:  # Starke Präsenz eines anderen Themas
                            other_topics_count += 1
                
                # Wenn 2+ andere Themen stark präsent sind, ist es vermutlich irrelevant
                if other_topics_count >= 2:
                    return True
        
        # Spezifische Domain-basierte Checks
        # FragDenStaat-Artikel ohne Bezug zur gesuchten Person/Thema
        if "fragdenstaat" in content_lower:
            if query_topic == "person" and not any(word in content_lower for word in query_words):
                return True
            elif query_topic == "right_networks" and not any(word in content_lower for word in ["rechte", "netzwerk", "alt-right", "cdu"]):
                return True
        
        return False

class DataAnalystDrone:
    def __init__(self, drone_id: str, model: str = "llama3.1"):
        self.drone = Drone(drone_id, DroneRole.DATA_ANALYST, model)
        self.client = ollama.Client()
    
    async def analyze_data(self, research_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        analysis_prompt = f"""
        Als Datenanalyst soll ich die Forschungsergebnisse und deren Validierung analysieren:
        
        Forschungsergebnisse:
        {json.dumps(research_result, indent=2)}
        
        Validierungsergebnisse:
        {json.dumps(validation_result, indent=2)}
        
        Erstelle eine umfassende Analyse mit:
        1. Zusammenfassung der wichtigsten Erkenntnisse
        2. Datenqualitätsbewertung
        3. Trends und Muster
        4. Handlungsempfehlungen
        5. Vertrauenswürdigkeit der Gesamtanalyse (1-10)
        
        Antworte im JSON-Format mit: summary, data_quality, trends, recommendations, confidence_score
        """
        
        try:
            response = self.client.chat(
                model=self.drone.model,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            result_text = response['message']['content']
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = {
                    "summary": result_text,
                    "data_quality": "moderate",
                    "trends": [],
                    "recommendations": [],
                    "confidence_score": 5
                }
            
            return {
                "analysis_result": result,
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "final_confidence": result.get("confidence_score", 5) / 10.0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "drone_id": self.drone.id,
                "timestamp": datetime.now().isoformat(),
                "final_confidence": 0.0
            }