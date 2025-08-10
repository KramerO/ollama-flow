#!/usr/bin/env python3
"""
LLM Chooser System für Ollama Flow
Dynamische LLM-Auswahl basierend auf Drohnen-Rollen und Task-Typen
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum
import ollama

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Verschiedene Task-Typen für spezielle LLM-Auswahl"""
    CODE_DEVELOPMENT = "code_development"
    ARCHITECTURE_DESIGN = "architecture_design"
    DATA_ANALYSIS = "data_analysis"
    SECURITY_AUDIT = "security_audit"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"

class LLMChooser:
    """
    Intelligente LLM-Auswahl basierend auf Rollen und Tasks
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "llm_models.json"
        self.available_models = []
        self.role_model_mapping = {}
        self.task_model_mapping = {}
        self.default_model = "llama3"
        
        self._load_config()
        self._detect_available_models()
    
    def _load_config(self):
        """Lädt die LLM-Konfiguration aus JSON-Datei"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.role_model_mapping = config.get('role_mapping', {})
                self.task_model_mapping = config.get('task_mapping', {})
                self.default_model = config.get('default_model', 'llama3')
                
                logger.info(f"✅ LLM-Konfiguration geladen: {config_file}")
            else:
                self._create_default_config()
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der LLM-Konfiguration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Erstellt Standard-LLM-Konfiguration"""
        default_config = {
            "default_model": "llama3",
            "role_mapping": {
                "developer": {
                    "primary": "codegemma:7b",
                    "fallback": ["codellama:7b", "llama3", "phi3:mini"]
                },
                "it_architect": {
                    "primary": "llama3:70b", 
                    "fallback": ["mixtral:8x7b", "llama3", "phi3:medium"]
                },
                "analyst": {
                    "primary": "mixtral:8x7b",
                    "fallback": ["llama3", "phi3:medium"]
                },
                "datascientist": {
                    "primary": "llama3:70b",
                    "fallback": ["codellama:13b", "llama3", "mixtral:8x7b"]
                },
                "security_specialist": {
                    "primary": "llama3:70b",
                    "fallback": ["mixtral:8x7b", "codellama:13b", "llama3"]
                }
            },
            "task_mapping": {
                "code_development": {
                    "preferred_models": ["codegemma:7b", "codellama:7b", "codellama:13b"],
                    "avoid_models": ["phi3:mini"]
                },
                "architecture_design": {
                    "preferred_models": ["llama3:70b", "mixtral:8x7b", "llama3"],
                    "avoid_models": ["phi3:mini"]
                },
                "security_audit": {
                    "preferred_models": ["llama3:70b", "mixtral:8x7b", "codellama:13b"],
                    "avoid_models": ["phi3:mini"]
                },
                "data_analysis": {
                    "preferred_models": ["llama3:70b", "mixtral:8x7b", "llama3"],
                    "avoid_models": []
                },
                "documentation": {
                    "preferred_models": ["llama3", "mixtral:8x7b", "phi3:medium"],
                    "avoid_models": []
                }
            },
            "model_capabilities": {
                "codegemma:7b": {
                    "strengths": ["code_generation", "debugging", "code_review"],
                    "languages": ["python", "javascript", "java", "cpp", "go", "rust"],
                    "context_size": 8192
                },
                "codellama:7b": {
                    "strengths": ["code_generation", "code_explanation", "refactoring"],
                    "languages": ["python", "javascript", "java", "cpp", "c", "php"],
                    "context_size": 4096
                },
                "codellama:13b": {
                    "strengths": ["complex_code", "architecture", "debugging"],
                    "languages": ["python", "javascript", "java", "cpp", "c", "go"],
                    "context_size": 4096
                },
                "llama3": {
                    "strengths": ["general_purpose", "analysis", "documentation"],
                    "languages": ["all"],
                    "context_size": 4096
                },
                "llama3:70b": {
                    "strengths": ["complex_reasoning", "architecture", "security"],
                    "languages": ["all"],
                    "context_size": 8192
                },
                "mixtral:8x7b": {
                    "strengths": ["analysis", "architecture", "complex_tasks"],
                    "languages": ["all"],
                    "context_size": 32768
                },
                "phi3:mini": {
                    "strengths": ["simple_tasks", "fast_responses"],
                    "languages": ["basic"],
                    "context_size": 4096
                },
                "phi3:medium": {
                    "strengths": ["balanced_performance", "documentation"],
                    "languages": ["most"],
                    "context_size": 4096
                }
            }
        }
        
        # Speichere Standard-Konfiguration
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            self.role_model_mapping = default_config['role_mapping']
            self.task_model_mapping = default_config['task_mapping']
            self.default_model = default_config['default_model']
            
            logger.info(f"✅ Standard-LLM-Konfiguration erstellt: {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Standard-Konfiguration: {e}")
    
    def _detect_available_models(self):
        """Erkennt verfügbare Ollama-Modelle"""
        try:
            # Verwende ollama list Kommando
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                self.available_models = []
                
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]  # First column is model name
                        self.available_models.append(model_name)
                
                logger.info(f"✅ Verfügbare Modelle erkannt: {len(self.available_models)} Modelle")
                logger.debug(f"Modelle: {self.available_models}")
            else:
                logger.warning("⚠️ Konnte Ollama-Modelle nicht auflisten")
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei der Modellerkennung: {e}")
            # Fallback auf häufige Modelle
            self.available_models = ["llama3", "phi3:mini", "codellama:7b"]
    
    def choose_model_for_role(self, role: str, task_context: Optional[str] = None) -> str:
        """
        Wählt das beste LLM basierend auf der Drohnen-Rolle
        
        Args:
            role: Drohnen-Rolle (z.B. 'developer', 'security_specialist')
            task_context: Zusätzlicher Kontext über den Task
        
        Returns:
            Name des gewählten LLM-Modells
        """
        role_lower = role.lower()
        
        # Prüfe Rollen-spezifische Zuordnung
        if role_lower in self.role_model_mapping:
            role_config = self.role_model_mapping[role_lower]
            
            # Versuche primäres Modell
            primary_model = role_config.get('primary')
            if primary_model and self._is_model_available(primary_model):
                logger.info(f"🎯 Gewähltes Modell für {role}: {primary_model} (primär)")
                return primary_model
            
            # Versuche Fallback-Modelle
            fallback_models = role_config.get('fallback', [])
            for model in fallback_models:
                if self._is_model_available(model):
                    logger.info(f"🎯 Gewähltes Modell für {role}: {model} (fallback)")
                    return model
        
        # Task-basierte Auswahl wenn verfügbar
        if task_context:
            task_model = self._choose_by_task_context(task_context)
            if task_model:
                logger.info(f"🎯 Gewähltes Modell für {role} (task-based): {task_model}")
                return task_model
        
        # Standard-Modell als letzter Fallback
        if self._is_model_available(self.default_model):
            logger.info(f"🎯 Gewähltes Modell für {role}: {self.default_model} (default)")
            return self.default_model
        
        # Notfall: Erstes verfügbares Modell
        if self.available_models:
            fallback = self.available_models[0]
            logger.warning(f"⚠️ Gewähltes Modell für {role}: {fallback} (emergency fallback)")
            return fallback
        
        # Absoluter Notfall
        logger.error(f"❌ Kein verfügbares Modell für {role} gefunden, verwende llama3")
        return "llama3"
    
    def _choose_by_task_context(self, task_context: str) -> Optional[str]:
        """Wählt Modell basierend auf Task-Kontext"""
        task_lower = task_context.lower()
        
        # Erkenne Task-Type basierend auf Keywords
        task_type = None
        
        if any(keyword in task_lower for keyword in ['code', 'implement', 'programming', 'function', 'class']):
            task_type = TaskType.CODE_DEVELOPMENT
        elif any(keyword in task_lower for keyword in ['architecture', 'design', 'structure', 'pattern']):
            task_type = TaskType.ARCHITECTURE_DESIGN
        elif any(keyword in task_lower for keyword in ['security', 'vulnerability', 'secure', 'attack', 'defense']):
            task_type = TaskType.SECURITY_AUDIT
        elif any(keyword in task_lower for keyword in ['analyze', 'data', 'statistics', 'metrics']):
            task_type = TaskType.DATA_ANALYSIS
        elif any(keyword in task_lower for keyword in ['document', 'readme', 'explanation', 'guide']):
            task_type = TaskType.DOCUMENTATION
        
        if task_type:
            task_key = task_type.value
            if task_key in self.task_model_mapping:
                preferred_models = self.task_model_mapping[task_key].get('preferred_models', [])
                
                for model in preferred_models:
                    if self._is_model_available(model):
                        return model
        
        return None
    
    def _is_model_available(self, model_name: str, auto_download: bool = True) -> bool:
        """Prüft ob ein Modell verfügbar ist und lädt es ggf. herunter"""
        if model_name in self.available_models:
            return True
        
        if auto_download:
            logger.info(f"📥 Modell {model_name} nicht gefunden, starte Download...")
            if self._download_model(model_name):
                self._detect_available_models()  # Aktualisiere Liste
                return model_name in self.available_models
        
        return False
    
    def _download_model(self, model_name: str) -> bool:
        """Lädt ein Ollama-Modell herunter"""
        try:
            import subprocess
            import time
            
            print(f"🔄 Downloading {model_name}... (Das kann einige Minuten dauern)")
            
            # Starte ollama pull in einem separaten Prozess
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Zeige Fortschritt
            while process.poll() is None:
                time.sleep(2)
                print(".", end="", flush=True)
            
            print()  # Neue Zeile
            
            if process.returncode == 0:
                logger.info(f"✅ Modell {model_name} erfolgreich heruntergeladen")
                return True
            else:
                stderr = process.stderr.read()
                logger.error(f"❌ Download von {model_name} fehlgeschlagen: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Download von {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Dict:
        """Gibt Informationen über ein Modell zurück"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            model_capabilities = config.get('model_capabilities', {})
            return model_capabilities.get(model_name, {
                "strengths": ["general_purpose"],
                "languages": ["all"],
                "context_size": 4096
            })
        except:
            return {"strengths": ["unknown"], "languages": ["all"], "context_size": 4096}
    
    def suggest_models_for_task(self, task_description: str) -> List[str]:
        """Schlägt die besten Modelle für einen Task vor"""
        suggested = []
        
        # Task-basierte Vorschläge
        task_model = self._choose_by_task_context(task_description)
        if task_model and task_model not in suggested:
            suggested.append(task_model)
        
        # Fallback zu guten Allround-Modellen
        good_models = ["llama3:70b", "mixtral:8x7b", "llama3", "codellama:13b"]
        for model in good_models:
            if self._is_model_available(model) and model not in suggested:
                suggested.append(model)
        
        return suggested[:3]  # Top 3 Vorschläge
    
    def update_role_mapping(self, role: str, primary_model: str, fallback_models: List[str] = None):
        """Aktualisiert die Rollen-Zuordnung"""
        if fallback_models is None:
            fallback_models = [self.default_model]
        
        self.role_model_mapping[role.lower()] = {
            "primary": primary_model,
            "fallback": fallback_models
        }
        
        # Speichere aktualisierte Konfiguration
        self._save_config()
        logger.info(f"✅ Rollen-Zuordnung aktualisiert: {role} -> {primary_model}")
    
    def _save_config(self):
        """Speichert aktuelle Konfiguration"""
        try:
            config = {
                "default_model": self.default_model,
                "role_mapping": self.role_model_mapping,
                "task_mapping": self.task_model_mapping
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Konfiguration: {e}")

# Globale Instanz für einfache Nutzung
_global_chooser = None

def get_llm_chooser() -> LLMChooser:
    """Gibt globale LLMChooser-Instanz zurück"""
    global _global_chooser
    if _global_chooser is None:
        _global_chooser = LLMChooser()
    return _global_chooser

def choose_model_for_role(role: str, task_context: Optional[str] = None) -> str:
    """Convenience-Funktion für Modell-Auswahl"""
    return get_llm_chooser().choose_model_for_role(role, task_context)

if __name__ == "__main__":
    # Test der LLM-Auswahl
    chooser = LLMChooser()
    
    print("🧪 Testing LLM Chooser...")
    
    roles = ["developer", "security_specialist", "it_architect", "analyst", "datascientist"]
    tasks = [
        "Implement a secure authentication system",
        "Design microservices architecture",
        "Analyze security vulnerabilities",
        "Create documentation for API",
        "Review code for performance issues"
    ]
    
    for role in roles:
        model = chooser.choose_model_for_role(role)
        print(f"👤 {role.capitalize()}: {model}")
    
    for task in tasks:
        suggested = chooser.suggest_models_for_task(task)
        print(f"📋 '{task[:30]}...': {suggested}")