# Ollama Flow CLI Wrapper - Benutzerhandbuch

## 🚀 Übersicht

Der Ollama Flow CLI Wrapper bietet eine einheitliche Kommandozeilen-Schnittstelle für alle Funktionen des Enhanced Ollama Flow Frameworks. Nach der Installation können Sie alle Features über einfache `ollama-flow` Befehle nutzen.

## 📦 Installation

Der CLI Wrapper wird automatisch mit dem Installationsskript eingerichtet:

```cmd
install_windows.bat
```

### PATH Integration

Für globalen Zugriff auf `ollama-flow` von überall:

**Option 1: Automatisch während Installation**
```cmd
# Das Installationsskript fragt nach PATH-Integration
setup_path=j
```

**Option 2: Manuell über PowerShell (als Administrator)**
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Path\To\ollama-flow", "User")
```

**Option 3: Manuell über Command Prompt (als Administrator)**
```cmd
setx PATH "%PATH%;C:\Path\To\ollama-flow"
```

**Option 4: GUI (System Properties)**
1. Win+R → `sysdm.cpl`
2. Advanced → Environment Variables
3. PATH hinzufügen: `C:\Path\To\ollama-flow`

## 🎯 Hauptbefehle

### Task Execution
```cmd
# Einfache Task-Ausführung
ollama-flow run "Erstelle eine Flask Web-App"

# Mit erweiterten Optionen
ollama-flow run "Build a REST API" --workers 6 --arch HIERARCHICAL --secure

# Direkter Zugriff auf Enhanced Framework
ollama-flow enhanced --task "Complex project" --metrics --benchmark
```

### Dashboard Management
```cmd
# Web Dashboard starten
ollama-flow dashboard
# Läuft auf: http://localhost:5000

# CLI Dashboard (interaktiv)
ollama-flow cli

# Session Management Dashboard
ollama-flow sessions
```

### System Management
```cmd
# System Status anzeigen
ollama-flow status

# Gesundheitscheck
ollama-flow health

# Version anzeigen
ollama-flow version

# Konfiguration anzeigen
ollama-flow config
```

### Model Management
```cmd
# Verfügbare Modelle anzeigen
ollama-flow models
ollama-flow models list

# Modell herunterladen
ollama-flow models pull codellama:7b
ollama-flow models pull llama3

# Modell entfernen
ollama-flow models remove codellama:7b

# Empfohlene Modelle aktualisieren
ollama-flow models update
```

### Development Tools
```cmd
# Tests ausführen
ollama-flow test
ollama-flow test -v  # Verbose

# Performance Benchmarks
ollama-flow benchmark

# Abhängigkeiten installieren/aktualisieren
ollama-flow install
ollama-flow update

# System bereinigen
ollama-flow clean
```

### Logs und Debugging
```cmd
# System Logs anzeigen
ollama-flow logs

# Hilfe anzeigen
ollama-flow help
ollama-flow --help
ollama-flow -h
```

## 🔧 Erweiterte Parameter

### Enhanced Framework Optionen
```cmd
ollama-flow enhanced [OPTIONEN]

--task "beschreibung"      # Task-Beschreibung
--workers N                # Anzahl Worker-Agenten (2-12)
--arch TYPE               # Architektur: HIERARCHICAL/CENTRALIZED/FULLY_CONNECTED
--model NAME              # Ollama Modell (codellama:7b, llama3, etc.)
--project-folder PATH     # Ausgabe-Ordner für das Projekt
--secure                  # Sicherheitsmodus aktivieren
--metrics                 # Metriken-Sammlung aktivieren
--benchmark               # Benchmarking aktivieren
--interactive             # Interaktiver Modus
--verbose                 # Ausführliche Ausgabe
--debug                   # Debug-Modus
```

### Dashboard Optionen
```cmd
ollama-flow dashboard [OPTIONEN]

--port 5000               # Port für Web Dashboard
--host localhost          # Host-Adresse
--debug                   # Debug-Modus
```

## 📋 Praktische Beispiele

### Web Development
```cmd
# Vollständige Web-Anwendung erstellen
ollama-flow run "Erstelle eine E-Commerce Website mit React Frontend, Node.js Backend, MongoDB Datenbank und Tests" --workers 8 --arch HIERARCHICAL --project-folder "C:\Projekte\ECommerce" --secure --metrics

# API entwickeln
ollama-flow enhanced --task "Build REST API with authentication and database" --workers 4 --model codellama:7b
```

### Data Science
```cmd
# Datenanalyse-Pipeline
ollama-flow run "Analysiere Verkaufsdaten, erstelle ML-Modelle und Dashboard" --workers 6 --metrics --benchmark
```

### DevOps
```cmd
# CI/CD Pipeline setup
ollama-flow run "Setup Docker deployment with Kubernetes and monitoring" --workers 4 --secure
```

### Monitoring und Management
```cmd
# System überwachen
ollama-flow status
ollama-flow health

# Dashboards für verschiedene Zwecke
ollama-flow dashboard      # Web UI für Tasks
ollama-flow sessions       # Session Management
ollama-flow cli           # Command-line Interface
```

## 🔄 Workflow-Beispiele

### Typischer Entwicklungsworkflow
```cmd
# 1. System Status prüfen
ollama-flow status

# 2. Benötigte Modelle sicherstellen
ollama-flow models pull codellama:7b

# 3. Projekt starten
ollama-flow run "Build a microservice with Docker" --workers 4 --project-folder "C:\Projekte\Microservice"

# 4. Dashboard für Monitoring öffnen
ollama-flow sessions

# 5. Nach Abschluss: System bereinigen
ollama-flow clean
```

### Performance Optimization Workflow
```cmd
# 1. Benchmark erstellen
ollama-flow benchmark --task "Performance baseline"

# 2. Mit verschiedenen Konfigurationen testen
ollama-flow run "Optimize database queries" --workers 8 --metrics
ollama-flow run "Optimize database queries" --workers 4 --arch CENTRALIZED --metrics

# 3. Ergebnisse vergleichen
ollama-flow logs
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### CLI Wrapper nicht gefunden
```cmd
# Prüfen ob PATH gesetzt ist
echo %PATH%

# Manuell von Installationsverzeichnis ausführen
C:\Path\To\ollama-flow\ollama-flow.bat help
```

#### Virtual Environment Fehler
```cmd
# Installation reparieren
ollama-flow install

# Status prüfen
ollama-flow status
```

#### Ollama nicht verfügbar
```cmd
# Ollama Status prüfen
ollama --version
ollama serve

# Modelle prüfen
ollama-flow models list
```

#### Port bereits belegt
```cmd
# Anderen Port verwenden
ollama-flow dashboard --port 5001
```

### Debug-Modi

#### Verbose Output
```cmd
ollama-flow enhanced --task "Debug task" --verbose --debug
```

#### Logs anzeigen
```cmd
ollama-flow logs
```

#### Gesundheitscheck
```cmd
ollama-flow health
```

## ⚡ Performance Tipps

### Optimale Worker-Anzahl
- **Einfache Tasks**: 2-4 Workers
- **Mittlere Komplexität**: 4-6 Workers  
- **Komplexe Projekte**: 6-12 Workers

### Architektur-Wahl
- **HIERARCHICAL**: Beste für komplexe, strukturierte Tasks
- **CENTRALIZED**: Gut für koordinierte Tasks
- **FULLY_CONNECTED**: Optimal für kreative, offene Tasks

### Model-Empfehlungen
- **codellama:7b**: Beste Balance für Code-Tasks
- **llama3**: Gut für allgemeine Tasks
- **codellama:13b**: Für komplexe Code-Projekte (mehr RAM nötig)

## 🔗 Integration mit anderen Tools

### Git Integration
```cmd
# Nach Task-Ausführung
cd C:\Projekte\MeinProjekt
git init
git add .
git commit -m "Initial commit from ollama-flow"
```

### IDE Integration
```cmd
# Projekt in VS Code öffnen
ollama-flow run "Create React app" --project-folder "C:\Projekte\ReactApp"
code C:\Projekte\ReactApp
```

### Docker Integration
```cmd
# Docker-Setup einbeziehen
ollama-flow run "Build app with Docker deployment" --secure --workers 6
```

## 📈 Monitoring und Analytics

### Real-time Monitoring
```cmd
# Dashboard für Live-Monitoring
ollama-flow sessions

# Metrics aktivieren
ollama-flow enhanced --task "Monitor task" --metrics --benchmark
```

### Performance Tracking
```cmd
# Benchmark verschiedener Konfigurationen
ollama-flow benchmark --task "Performance test"
```

### Log Analysis
```cmd
# Alle Logs anzeigen
ollama-flow logs

# System Status
ollama-flow status
```

## 📚 Weitere Ressourcen

- **README_WINDOWS.md**: Vollständige Windows-Anleitung
- **ENHANCED_FEATURES.md**: Übersicht aller neuen Features
- **Installationslog**: `install.log` im Projektverzeichnis

---

**🎉 Der CLI Wrapper macht Ollama Flow noch einfacher zu nutzen!**

Mit einem einheitlichen `ollama-flow` Befehl haben Sie Zugriff auf alle Features des Enhanced Frameworks - von einfachen Tasks bis hin zu komplexen, multi-agenten KI-Orchestrierungen.