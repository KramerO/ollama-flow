import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from ollama_flow_architecture import (
    DroneRole, TaskStatus, Task, Drone, DatabaseManager,
    ResearchDrone, FactCheckDrone, DataAnalystDrone
)

class WorkflowCoordinator:
    def __init__(self, db_path: str = "ollama_flow_multi_role.db", enhanced_mode: bool = False):
        self.db_manager = DatabaseManager(db_path)
        self.enhanced_mode = enhanced_mode
        self.research_drones: List[ResearchDrone] = []
        self.fact_check_drones: List[FactCheckDrone] = []
        self.analyst_drones: List[DataAnalystDrone] = []
        
        # Initialize drone fleets
        self.initialize_drone_fleets()
    
    def initialize_drone_fleets(self):
        # Create research team (3 drones)
        for i in range(3):
            # Mix enhanced and traditional drones
            enhanced = self.enhanced_mode and (i < 2)  # First 2 drones enhanced, last one traditional
            drone_name = f"researcher_{i+1}" + ("_enhanced" if enhanced else "")
            drone = ResearchDrone(drone_name, enhanced_mode=enhanced)
            self.research_drones.append(drone)
            self.db_manager.save_drone(drone.drone)
        
        # Create fact-checking team (2 drones)
        for i in range(2):
            drone = FactCheckDrone(f"factchecker_{i+1}")
            self.fact_check_drones.append(drone)
            self.db_manager.save_drone(drone.drone)
        
        # Create data analyst team (2 drones)
        for i in range(2):
            drone = DataAnalystDrone(f"analyst_{i+1}")
            self.analyst_drones.append(drone)
            self.db_manager.save_drone(drone.drone)
        
        mode_info = " (Enhanced Mode)" if self.enhanced_mode else ""
        print(f"Initialized drone fleets{mode_info}:")
        enhanced_count = sum(1 for drone in self.research_drones if drone.enhanced_mode)
        print(f"- {len(self.research_drones)} Research Drones ({enhanced_count} enhanced)")
        print(f"- {len(self.fact_check_drones)} Fact-Check Drones")
        print(f"- {len(self.analyst_drones)} Data Analyst Drones")
    
    def get_available_drone(self, role: DroneRole):
        if role == DroneRole.RESEARCHER:
            return next((drone for drone in self.research_drones 
                        if drone.drone.current_task is None), None)
        elif role == DroneRole.FACT_CHECKER:
            return next((drone for drone in self.fact_check_drones 
                        if drone.drone.current_task is None), None)
        elif role == DroneRole.DATA_ANALYST:
            return next((drone for drone in self.analyst_drones 
                        if drone.drone.current_task is None), None)
        return None
    
    async def process_workflow(self, query: str) -> Dict[str, Any]:
        workflow_id = str(uuid.uuid4())
        print(f"\n🚀 Starting workflow {workflow_id} for query: '{query}'")
        
        workflow_result = {
            "id": workflow_id,
            "original_query": query,
            "research_result": None,
            "fact_check_result": None,
            "analysis_result": None,
            "final_confidence_score": 0.0,
            "created_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        try:
            # Phase 1: Research
            print("\n📚 Phase 1: Research Phase")
            research_tasks = await self.execute_research_phase(query)
            workflow_result["research_result"] = research_tasks
            
            # Phase 2: Fact-Checking
            print("\n🔍 Phase 2: Fact-Checking Phase")
            fact_check_results = await self.execute_fact_check_phase(research_tasks, query)
            workflow_result["fact_check_result"] = fact_check_results
            
            # Phase 3: Data Analysis
            print("\n📊 Phase 3: Data Analysis Phase")
            analysis_results = await self.execute_analysis_phase(research_tasks, fact_check_results)
            workflow_result["analysis_result"] = analysis_results
            
            # Calculate final confidence score
            workflow_result["final_confidence_score"] = self.calculate_final_confidence(
                research_tasks, fact_check_results, analysis_results
            )
            
            workflow_result["status"] = "completed"
            
            # Save workflow result to database
            self.save_workflow_result(workflow_result)
            
            print(f"\n✅ Workflow {workflow_id} completed with confidence score: {workflow_result['final_confidence_score']:.2f}")
            
            return workflow_result
            
        except Exception as e:
            workflow_result["status"] = "failed"
            workflow_result["error"] = str(e)
            print(f"❌ Workflow {workflow_id} failed: {str(e)}")
            return workflow_result
    
    async def execute_research_phase(self, query: str) -> List[Dict[str, Any]]:
        research_tasks = []
        
        # Distribute research to multiple drones
        research_angles = [
            f"Grundlegende Fakten und Informationen zu: {query}",
            f"Historischer Kontext und Entwicklung von: {query}",
            f"Aktuelle Trends und Zukunftsperspektiven zu: {query}"
        ]
        
        tasks = []
        for i, angle in enumerate(research_angles):
            drone = self.get_available_drone(DroneRole.RESEARCHER)
            if drone:
                drone.drone.current_task = f"research_task_{i}"
                task = asyncio.create_task(drone.conduct_research(angle))
                tasks.append(task)
                print(f"  📋 Assigned research task to {drone.drone.id}: {angle[:50]}...")
        
        # Wait for all research tasks to complete
        research_results = await asyncio.gather(*tasks)
        
        # Update drone status
        for drone in self.research_drones:
            if drone.drone.current_task:
                drone.drone.current_task = None
                drone.drone.completed_tasks += 1
                self.db_manager.save_drone(drone.drone)
        
        return research_results
    
    async def execute_fact_check_phase(self, research_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        fact_check_tasks = []
        
        tasks = []
        for i, research_result in enumerate(research_results):
            drone = self.get_available_drone(DroneRole.FACT_CHECKER)
            if drone:
                drone.drone.current_task = f"fact_check_task_{i}"
                task = asyncio.create_task(drone.validate_research(research_result, query))
                tasks.append(task)
                print(f"  🔍 Assigned fact-check task to {drone.drone.id}")
        
        # Wait for all fact-checking tasks to complete
        fact_check_results = await asyncio.gather(*tasks)
        
        # Update drone status
        for drone in self.fact_check_drones:
            if drone.drone.current_task:
                drone.drone.current_task = None
                drone.drone.completed_tasks += 1
                self.db_manager.save_drone(drone.drone)
        
        return fact_check_results
    
    async def execute_analysis_phase(self, research_results: List[Dict[str, Any]], 
                                   fact_check_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        analysis_tasks = []
        
        tasks = []
        # Pair research and fact-check results for analysis
        for i, (research, fact_check) in enumerate(zip(research_results, fact_check_results)):
            drone = self.get_available_drone(DroneRole.DATA_ANALYST)
            if drone:
                drone.drone.current_task = f"analysis_task_{i}"
                task = asyncio.create_task(drone.analyze_data(research, fact_check))
                tasks.append(task)
                print(f"  📊 Assigned analysis task to {drone.drone.id}")
        
        # Wait for all analysis tasks to complete
        analysis_results = await asyncio.gather(*tasks)
        
        # Update drone status
        for drone in self.analyst_drones:
            if drone.drone.current_task:
                drone.drone.current_task = None
                drone.drone.completed_tasks += 1
                self.db_manager.save_drone(drone.drone)
        
        return analysis_results
    
    def calculate_final_confidence(self, research_results: List[Dict[str, Any]], 
                                 fact_check_results: List[Dict[str, Any]], 
                                 analysis_results: List[Dict[str, Any]]) -> float:
        total_confidence = 0.0
        total_weight = 0.0
        
        # Weight research confidence
        for result in research_results:
            confidence = result.get("confidence", 0.5)
            total_confidence += confidence * 0.3
            total_weight += 0.3
        
        # Weight fact-check validation
        for result in fact_check_results:
            validation_score = result.get("validation_result", {}).get("overall_validation_score", 5)
            total_confidence += (validation_score / 10.0) * 0.4
            total_weight += 0.4
        
        # Weight analysis confidence
        for result in analysis_results:
            confidence = result.get("final_confidence", 0.5)
            total_confidence += confidence * 0.3
            total_weight += 0.3
        
        return total_confidence / total_weight if total_weight > 0 else 0.0
    
    def save_workflow_result(self, workflow_result: Dict[str, Any]):
        import sqlite3
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflow_results 
            (id, original_query, research_result, fact_check_result, analysis_result, 
             final_confidence_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_result["id"],
            workflow_result["original_query"],
            json.dumps(workflow_result["research_result"]),
            json.dumps(workflow_result["fact_check_result"]),
            json.dumps(workflow_result["analysis_result"]),
            workflow_result["final_confidence_score"],
            workflow_result["created_at"]
        ))
        
        conn.commit()
        conn.close()
    
    def get_drone_status(self) -> Dict[str, Any]:
        status = {
            "research_drones": [],
            "fact_check_drones": [],
            "analyst_drones": []
        }
        
        for drone in self.research_drones:
            status["research_drones"].append({
                "id": drone.drone.id,
                "active": drone.drone.is_active,
                "current_task": drone.drone.current_task,
                "completed_tasks": drone.drone.completed_tasks
            })
        
        for drone in self.fact_check_drones:
            status["fact_check_drones"].append({
                "id": drone.drone.id,
                "active": drone.drone.is_active,
                "current_task": drone.drone.current_task,
                "completed_tasks": drone.drone.completed_tasks
            })
        
        for drone in self.analyst_drones:
            status["analyst_drones"].append({
                "id": drone.drone.id,
                "active": drone.drone.is_active,
                "current_task": drone.drone.current_task,
                "completed_tasks": drone.drone.completed_tasks
            })
        
        return status
    
    def print_workflow_summary(self, workflow_result: Dict[str, Any]):
        print("\n" + "="*80)
        print(f"📋 WORKFLOW SUMMARY - ID: {workflow_result['id']}")
        print("="*80)
        print(f"Query: {workflow_result['original_query']}")
        print(f"Status: {workflow_result['status']}")
        print(f"Final Confidence Score: {workflow_result['final_confidence_score']:.2f}/1.0")
        print(f"Created: {workflow_result['created_at']}")
        
        if workflow_result.get('research_result'):
            print(f"\n📚 Research Results: {len(workflow_result['research_result'])} completed")
            # Show enhanced research info if available
            enhanced_count = sum(1 for r in workflow_result['research_result'] 
                               if r.get('research_type') == 'enhanced')
            if enhanced_count > 0:
                print(f"   🚀 Enhanced Research: {enhanced_count}/{len(workflow_result['research_result'])} drones")
        
        if workflow_result.get('fact_check_result'):
            print(f"🔍 Fact-Check Results: {len(workflow_result['fact_check_result'])} completed")
            validated_count = sum(1 for r in workflow_result['fact_check_result'] 
                                if r.get('validation_passed', False))
            print(f"   ✅ Validated: {validated_count}/{len(workflow_result['fact_check_result'])}")
        
        if workflow_result.get('analysis_result'):
            print(f"📊 Analysis Results: {len(workflow_result['analysis_result'])} completed")
        
        # Auto-generate text report for enhanced mode
        if self.enhanced_mode or any(r.get('research_type') == 'enhanced' 
                                   for r in workflow_result.get('research_result', [])):
            report_file = self.generate_text_report(workflow_result)
            if report_file:
                print(f"📄 Enhanced Report erstellt: {report_file}")
        
        print("="*80)
    
    def generate_text_report(self, workflow_result: Dict[str, Any]) -> str:
        """Generiert automatisch einen Textreport für Enhanced Research."""
        import os
        import re
        from datetime import datetime
        
        # Erstelle reports Verzeichnis falls nicht vorhanden
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Erstelle Dateiname
        query_clean = re.sub(r'[^\w]', '_', workflow_result.get('original_query', 'report'))[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"enhanced_research_{query_clean}_{timestamp}.txt"
        filepath = os.path.join(reports_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("OLLAMA FLOW ENHANCED RESEARCH REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Anfrage: {workflow_result.get('original_query', 'Unknown')}\n")
                f.write(f"Workflow ID: {workflow_result.get('id', 'Unknown')}\n")
                f.write(f"Status: {workflow_result.get('status', 'Unknown')}\n")
                f.write(f"Vertrauenswert: {workflow_result.get('final_confidence_score', 0):.2f}/1.0\n")
                f.write(f"Erstellt: {workflow_result.get('created_at', 'Unknown')}\n\n")
                
                # Research Results
                research_results = workflow_result.get('research_result', [])
                if research_results:
                    f.write("RECHERCHE-ERGEBNISSE\n")
                    f.write("-" * 40 + "\n\n")
                    
                    for i, result in enumerate(research_results, 1):
                        f.write(f"Drohne {i}: {result.get('drone_id', 'Unknown')}\n")
                        f.write(f"Typ: {result.get('research_type', 'traditional')}\n")
                        f.write(f"Vertrauen: {result.get('confidence', 0):.2f}\n")
                        
                        # Traditional research data
                        if 'research_data' in result:
                            data = result['research_data']
                            if isinstance(data, dict):
                                facts = data.get('facts', [])
                                if facts:
                                    f.write("Fakten:\n")
                                    for fact in facts[:3]:  # Top 3
                                        f.write(f"  • {fact}\n")
                                
                                perspectives = data.get('perspectives', [])
                                if perspectives:
                                    f.write("Perspektiven:\n")
                                    for perspective in perspectives[:2]:  # Top 2
                                        f.write(f"  • {perspective}\n")
                        
                        # Enhanced research data
                        if 'social_media_results' in result:
                            social_results = result['social_media_results']
                            total_social = sum(len(r) for r in social_results.values())
                            f.write(f"Social Media Quellen: {total_social}\n")
                            
                            for platform, results in social_results.items():
                                if results and not any(r.get('error') for r in results):
                                    f.write(f"  • {platform.capitalize()}: {len(results)} Ergebnisse\n")
                        
                        if 'comprehensive_analysis' in result:
                            analysis = result['comprehensive_analysis']
                            if 'search_summary' in analysis:
                                f.write(f"Suche: {analysis['search_summary']}\n")
                        
                        f.write("\n")
                
                # Fact-Check Results
                factcheck_results = workflow_result.get('fact_check_result', [])
                if factcheck_results:
                    f.write("FACT-CHECK ERGEBNISSE\n")
                    f.write("-" * 40 + "\n\n")
                    
                    validated_count = sum(1 for r in factcheck_results if r.get('validation_passed', False))
                    f.write(f"Validiert: {validated_count}/{len(factcheck_results)}\n\n")
                    
                    for i, result in enumerate(factcheck_results, 1):
                        f.write(f"Fact-Check {i}: {result.get('drone_id', 'Unknown')}\n")
                        f.write(f"Status: {'✓ Bestanden' if result.get('validation_passed') else '✗ Nicht bestanden'}\n")
                        
                        validation_result = result.get('validation_result', {})
                        if isinstance(validation_result, dict):
                            overall_score = validation_result.get('overall_validation_score', 0)
                            f.write(f"Bewertung: {overall_score}/10\n")
                        
                        f.write("\n")
                
                # Analysis Results
                analysis_results = workflow_result.get('analysis_result', [])
                if analysis_results:
                    f.write("ANALYSE-ERGEBNISSE\n")
                    f.write("-" * 40 + "\n\n")
                    
                    for i, result in enumerate(analysis_results, 1):
                        f.write(f"Analyse {i}: {result.get('drone_id', 'Unknown')}\n")
                        f.write(f"Vertrauen: {result.get('final_confidence', 0):.2f}\n")
                        
                        analysis_result = result.get('analysis_result', {})
                        if isinstance(analysis_result, dict):
                            summary = analysis_result.get('summary', '')
                            if summary:
                                f.write(f"Zusammenfassung: {summary}\n")
                            
                            recommendations = analysis_result.get('recommendations', [])
                            if recommendations:
                                f.write("Empfehlungen:\n")
                                for rec in recommendations[:3]:  # Top 3
                                    if isinstance(rec, str):
                                        f.write(f"  • {rec}\n")
                        
                        f.write("\n")
                
                # Footer
                f.write("-" * 80 + "\n")
                f.write("Erstellt mit Ollama Flow Multi-Role System\n")
                f.write(f"Enhanced Mode: {self.enhanced_mode}\n")
                f.write("-" * 80 + "\n")
            
            return filepath
            
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen des Reports: {str(e)}")
            return None