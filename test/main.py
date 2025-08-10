#!/usr/bin/env python3
"""
Ollama Flow Multi-Role Drone System
====================================

Ein erweitertes System mit drei spezialisierten Drohnen-Teams:
- Recherche-Team: Sammelt Informationen und Daten
- Fact-Checking-Team: Validiert die Forschungsergebnisse
- Datenanalyse-Team: Analysiert und bewertet die Daten

Verwendung:
    python main.py "Ihre Suchanfrage hier"
    python main.py --interactive  # Interaktiver Modus
    python main.py --status       # Drohnen-Status anzeigen
"""

import asyncio
import sys
import argparse
import json
from ollama_flow_coordinator import WorkflowCoordinator

class OllamaFlowCLI:
    def __init__(self):
        self.coordinator = WorkflowCoordinator()
    
    async def run_query(self, query: str):
        """Führt eine komplette Workflow-Analyse für eine Anfrage durch."""
        print(f"🤖 Ollama Flow Multi-Role System gestartet")
        print(f"🎯 Verarbeite Anfrage: '{query}'")
        
        # Führe den Workflow aus
        result = await self.coordinator.process_workflow(query)
        
        # Zeige Zusammenfassung
        self.coordinator.print_workflow_summary(result)
        
        return result
    
    def show_drone_status(self):
        """Zeigt den aktuellen Status aller Drohnen an."""
        status = self.coordinator.get_drone_status()
        
        print("\n🤖 DROHNEN STATUS ÜBERSICHT")
        print("="*50)
        
        print(f"\n📚 Recherche-Drohnen ({len(status['research_drones'])})")
        for drone in status['research_drones']:
            task_status = f"Task: {drone['current_task']}" if drone['current_task'] else "Bereit"
            print(f"  {drone['id']}: {task_status} | Abgeschlossen: {drone['completed_tasks']}")
        
        print(f"\n🔍 Fact-Check-Drohnen ({len(status['fact_check_drones'])})")
        for drone in status['fact_check_drones']:
            task_status = f"Task: {drone['current_task']}" if drone['current_task'] else "Bereit"
            print(f"  {drone['id']}: {task_status} | Abgeschlossen: {drone['completed_tasks']}")
        
        print(f"\n📊 Analyse-Drohnen ({len(status['analyst_drones'])})")
        for drone in status['analyst_drones']:
            task_status = f"Task: {drone['current_task']}" if drone['current_task'] else "Bereit"
            print(f"  {drone['id']}: {task_status} | Abgeschlossen: {drone['completed_tasks']}")
        
        print("="*50)
    
    async def interactive_mode(self):
        """Startet den interaktiven Modus."""
        print("\n🚀 Willkommen im Ollama Flow Interactive Mode!")
        print("Geben Sie Ihre Anfragen ein oder 'quit' zum Beenden.")
        print("Verfügbare Befehle:")
        print("  status  - Drohnen-Status anzeigen")
        print("  quit    - Programm beenden")
        print("-" * 50)
        
        while True:
            try:
                query = input("\n🔍 Ihre Anfrage: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Auf Wiedersehen! 👋")
                    break
                elif query.lower() == 'status':
                    self.show_drone_status()
                elif query:
                    await self.run_query(query)
                else:
                    print("Bitte geben Sie eine Anfrage ein.")
                    
            except KeyboardInterrupt:
                print("\n\nProgramm unterbrochen. Auf Wiedersehen! 👋")
                break
            except Exception as e:
                print(f"❌ Fehler: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Ollama Flow Multi-Role Drone System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py "Klimawandel Auswirkungen Deutschland"
  python main.py --interactive
  python main.py --status
        """
    )
    
    parser.add_argument('query', nargs='?', help='Die Suchanfrage für das System')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Startet den interaktiven Modus')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Zeigt den Drohnen-Status an')
    
    args = parser.parse_args()
    
    cli = OllamaFlowCLI()
    
    try:
        if args.status:
            cli.show_drone_status()
        elif args.interactive:
            asyncio.run(cli.interactive_mode())
        elif args.query:
            asyncio.run(cli.run_query(args.query))
        else:
            parser.print_help()
            print("\n💡 Tipp: Verwenden Sie --interactive für den interaktiven Modus")
    
    except KeyboardInterrupt:
        print("\n\nProgramm unterbrochen. 👋")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()