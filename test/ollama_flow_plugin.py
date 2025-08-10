#!/usr/bin/env python3
"""
Ollama Flow Multi-Role Plugin
============================

Plugin für Integration in bestehende ollama-flow CLI

Verwendung:
    from ollama_flow_plugin import MultiRolePlugin
    
    plugin = MultiRolePlugin()
    result = await plugin.research_and_analyze("Ihre Anfrage")
"""

import asyncio
import sys
import os
from ollama_flow_coordinator import WorkflowCoordinator
from latex_report_generator import LaTeXReportGenerator

class MultiRolePlugin:
    def __init__(self, db_path: str = "ollama_flow_multi_role.db", enhanced_mode: bool = False):
        self.coordinator = WorkflowCoordinator(db_path, enhanced_mode=enhanced_mode)
        self.latex_generator = LaTeXReportGenerator()
        self.enhanced_mode = enhanced_mode
    
    async def research_and_analyze(self, query: str) -> dict:
        """Hauptfunktion für Recherche und Analyse"""
        return await self.coordinator.process_workflow(query)
    
    def get_status(self) -> dict:
        """Status aller Drohnen abrufen"""
        return self.coordinator.get_drone_status()
    
    async def quick_research(self, query: str) -> str:
        """Schnelle Recherche mit nur einer Zusammenfassung"""
        result = await self.research_and_analyze(query)
        
        if result["status"] == "completed":
            # Extrahiere wichtigste Erkenntnisse
            summary = []
            
            if result.get("analysis_result"):
                for analysis in result["analysis_result"]:
                    if "analysis_result" in analysis and "summary" in analysis["analysis_result"]:
                        summary.append(analysis["analysis_result"]["summary"])
            
            confidence = result.get("final_confidence_score", 0)
            
            return f"""
🔍 RECHERCHE ERGEBNIS für: {query}

📊 Vertrauenswert: {confidence:.1%}

📝 Zusammenfassung:
{chr(10).join(summary) if summary else "Keine Zusammenfassung verfügbar"}

🎯 Status: {result["status"]}
"""
        else:
            return f"❌ Recherche fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}"
    
    async def research_with_latex(self, query: str, filename: str = None) -> tuple[dict, str, str]:
        """Recherche mit LaTeX-Report-Generierung"""
        result = await self.research_and_analyze(query)
        
        if result["status"] == "completed":
            try:
                # Generate LaTeX content
                latex_content = self.latex_generator.generate_latex_report(result)
                
                if filename is None:
                    import re
                    from datetime import datetime
                    query_clean = re.sub(r'[^\w]', '_', result.get('original_query', 'report'))[:30]
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"research_report_{query_clean}_{timestamp}"
                
                latex_file = os.path.join(self.latex_generator.output_dir, f"{filename}.tex")
                
                # Write LaTeX file
                with open(latex_file, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Try PDF compilation, but don't fail if it doesn't work
                pdf_file = None
                try:
                    pdf_file = self.latex_generator.compile_pdf(latex_file)
                except Exception as pdf_error:
                    print(f"⚠️ PDF-Kompilierung fehlgeschlagen: {str(pdf_error)}")
                    print(f"💡 LaTeX-Datei verfügbar unter: {latex_file}")
                    print(f"💡 Manuell kompilieren mit: pdflatex {os.path.basename(latex_file)}")
                
                return result, latex_file, pdf_file
                
            except Exception as e:
                print(f"⚠️ LaTeX-Report konnte nicht erstellt werden: {str(e)}")
                return result, None, None
        else:
            return result, None, None

# CLI Wrapper Funktionen für einfache Integration
async def cli_research(query: str, enhanced: bool = False) -> None:
    """CLI Funktion für Recherche"""
    plugin = MultiRolePlugin(enhanced_mode=enhanced)
    result = await plugin.research_and_analyze(query)
    plugin.coordinator.print_workflow_summary(result)

async def cli_research_latex(query: str, filename: str = None, enhanced: bool = False) -> None:
    """CLI Funktion für Recherche mit LaTeX-Report"""
    plugin = MultiRolePlugin(enhanced_mode=enhanced)
    result, latex_file, pdf_file = await plugin.research_with_latex(query, filename)
    
    plugin.coordinator.print_workflow_summary(result)
    
    if latex_file:
        print(f"\n📄 LaTeX-Report erstellt: {latex_file}")
        if pdf_file:
            print(f"📑 PDF-Report erstellt: {pdf_file}")
        print(f"🎯 Report-Verzeichnis: {os.path.dirname(latex_file)}")
    else:
        print(f"⚠️ LaTeX-Report konnte nicht erstellt werden")

async def cli_quick_research(query: str, enhanced: bool = False) -> None:
    """CLI Funktion für schnelle Recherche"""
    plugin = MultiRolePlugin(enhanced_mode=enhanced)
    summary = await plugin.quick_research(query)
    print(summary)

def cli_status() -> None:
    """CLI Funktion für Status"""
    plugin = MultiRolePlugin()
    status = plugin.get_status()
    
    print("🤖 Drohnen Status:")
    print(f"📚 Recherche: {len(status['research_drones'])} Drohnen")
    print(f"🔍 Fact-Check: {len(status['fact_check_drones'])} Drohnen") 
    print(f"📊 Analyse: {len(status['analyst_drones'])} Drohnen")

# Kommandozeilen-Interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python ollama_flow_plugin.py research 'Ihre Anfrage'")
        print("  python ollama_flow_plugin.py enhanced 'Ihre Anfrage'")
        print("  python ollama_flow_plugin.py latex 'Ihre Anfrage'") 
        print("  python ollama_flow_plugin.py latex-enhanced 'Ihre Anfrage'")
        print("  python ollama_flow_plugin.py quick 'Ihre Anfrage'")
        print("  python ollama_flow_plugin.py status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "research" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        asyncio.run(cli_research(query))
    elif command == "enhanced" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        asyncio.run(cli_research(query, enhanced=True))
    elif command == "latex" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        asyncio.run(cli_research_latex(query))
    elif command == "latex-enhanced" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        asyncio.run(cli_research_latex(query, enhanced=True))
    elif command == "quick" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        asyncio.run(cli_quick_research(query))
    elif command == "status":
        cli_status()
    else:
        print("Ungültiger Befehl oder fehlende Anfrage")