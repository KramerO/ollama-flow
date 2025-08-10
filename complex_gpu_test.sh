#!/bin/bash

# 🚀 Komplexer GPU Stress Test für ollama-flow
# 8 Worker Hierarchische Architektur - Maximale GPU Auslastung

set -e

echo "🚀 KOMPLEXER GPU STRESS TEST"
echo "============================="
echo "Architektur: HIERARCHICAL"
echo "Worker: 8 (2 Sub-Queens mit je 4 Workers)"
echo "GPU: AMD RX 6650 XT"
echo "============================="

# GPU Optimierungen laden
export OLLAMA_NUM_PARALLEL=8
export OLLAMA_MAX_LOADED_MODELS=4
export OLLAMA_GPU_LAYERS=35
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KEEP_ALIVE=15m
export OLLAMA_MAX_QUEUE=50

# AMD GPU Settings
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export GPU_MAX_HEAP_SIZE=100
export GPU_MAX_ALLOC_PERCENT=95

# Komplexe Task die alle 8 Worker voll ausnutzt
COMPLEX_TASK="Entwickle ein vollständiges Python-Projekt für ein intelligentes Code-Analyse-System mit folgenden Komponenten: 

1. HAUPTMODUL: Ein AST-Parser der Python-Code analysiert und Komplexitätsmetriken berechnet (Cyclomatic Complexity, Halstead Metrics, Lines of Code, Technical Debt Ratio)

2. DATABASE-SCHICHT: SQLAlchemy-basierte Datenbank mit Tabellen für Projects, Files, Functions, Classes, Metrics und Reports - inklusive Migrations und Relationship-Definitionen

3. API-SERVER: FastAPI-Server mit Endpoints für Upload, Analyse, Reporting und Dashboard - mit Authentication, Rate Limiting und async Processing

4. WORKER-SYSTEM: Celery-basierte Background-Worker für asynchrone Code-Analyse mit Redis als Broker und Result Backend

5. WEB-DASHBOARD: React-Frontend mit TypeScript, Charts (Chart.js), File-Explorer, Metric-Visualisierung und Real-time Updates via WebSockets  

6. CLI-TOOL: Click-basiertes Command-Line Interface für Batch-Processing, CI/CD Integration und Report-Generation

7. DOCKER-DEPLOYMENT: Multi-Container Setup mit Docker-Compose für alle Services, Nginx Reverse Proxy und Production-ready Configuration

8. TESTING-SUITE: Pytest-basierte Tests mit mindestens 90% Coverage, Integration Tests, Performance Tests und Mock-Strategien

Jede Komponente soll vollständig implementiert werden mit Error Handling, Logging, Documentation (Docstrings + README), Type Hints, und production-ready Code Quality. Das System soll skalierbar, wartbar und erweiterbar sein."

echo ""
echo "🧪 Starte komplexen Test mit 8 Workern..."
echo "Task: Vollständiges Python Code-Analyse-System"
echo ""

# GPU Monitoring im Hintergrund starten
if command -v radeontop >/dev/null 2>&1; then
    echo "📊 Starte GPU Monitoring..."
    timeout 300 radeontop -d - > gpu_usage_during_test.log 2>&1 &
    GPU_PID=$!
else
    echo "⚠️  radeontop nicht installiert - kein GPU Monitoring"
fi

# Performance Monitoring
echo "⏱️  Start Time: $(date)"
START_TIME=$(date +%s)

# Komplexer Test ausführen
echo ""
echo "🚀 Führe GPU-optimierten Test aus..."
./ollama-flow-gpu run "$COMPLEX_TASK" --workers 8

# End Time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "✅ Test abgeschlossen!"
echo "⏱️  Gesamtdauer: ${DURATION} Sekunden"

# GPU Monitoring beenden
if [ ! -z "$GPU_PID" ]; then
    kill $GPU_PID 2>/dev/null || true
    echo "📊 GPU Usage Log: gpu_usage_during_test.log"
fi

echo ""
echo "📈 Performance Summary:"
echo "  - Worker: 8 (Hierarchisch)"
echo "  - Dauer: ${DURATION}s"
echo "  - GPU Layers: 35"
echo "  - Parallel Requests: 8"
echo "  - Task Komplexität: Sehr hoch (8 Komponenten)"

echo ""
echo "🔍 Analysiere GPU Usage..."
if [ -f "gpu_usage_during_test.log" ]; then
    echo "GPU Peak Usage:"
    grep "gpu" gpu_usage_during_test.log | head -5
    
    echo ""
    echo "VRAM Usage:"
    grep "vram" gpu_usage_during_test.log | tail -3
fi

echo ""
echo "🎉 GPU Stress Test komplett!"