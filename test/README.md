# Ollama Flow Multi-Role Drone System

Ein erweiteres System, das eine Architektur mit drei spezialisierten Drohnen-Teams spawnt:

## 🤖 Drohnen-Teams

### 📚 Recherche-Team (3 Drohnen)
- Sammeln umfassende Informationen zu Anfragen
- Verschiedene Recherche-Winkel und Perspektiven
- Identifizierung von Fakten, Quellen und Kontroversen

### 🔍 Fact-Checking-Team (2 Drohnen)
- Validierung der Forschungsergebnisse
- Bewertung der Plausibilität und Glaubwürdigkeit
- Identifizierung von Bias und fehlenden Informationen

### 📊 Datenanalyse-Team (2 Drohnen)
- Analyse und Auswertung der validierten Daten
- Erstellung von Zusammenfassungen und Trends
- Berechnung von Vertrauenswerten und Empfehlungen

## 🚀 Installation

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# System testen
python test_system.py
```

## 📋 Verwendung

### Einzelne Anfrage
```bash
python main.py "Klimawandel Auswirkungen auf Deutschland"
```

### Interaktiver Modus
```bash
python main.py --interactive
```

### Drohnen-Status anzeigen
```bash
python main.py --status
```

## 🏗️ Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Recherche-Team  │───▶│ Fact-Check-Team │───▶│ Analyse-Team    │
│ (3 Drohnen)     │    │ (2 Drohnen)     │    │ (2 Drohnen)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Coordinator                        │
│              • Task Verteilung                                │
│              • Status Überwachung                             │
│              • Ergebnis Aggregation                           │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Manager                             │
│              • Tasks, Drohnen, Workflows                      │
│              • SQLite Backend                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Workflow-Phasen

1. **Recherche-Phase**: Parallele Informationssammlung durch mehrere Drohnen
2. **Validierungs-Phase**: Fact-Checking der Recherche-Ergebnisse
3. **Analyse-Phase**: Datenauswertung und Bewertung
4. **Aggregation**: Berechnung des finalen Vertrauenswertes

## 📊 Ausgabe-Format

Jeder Workflow liefert:
- Ursprüngliche Anfrage
- Detaillierte Forschungsergebnisse
- Validierungs-Berichte
- Analyse-Zusammenfassungen
- Finaler Vertrauenswert (0-1.0)

## 🧪 Testing

```bash
python test_system.py
```

Das Test-System validiert:
- Drohnen-Initialisierung
- Datenbank-Operationen
- Workflow-Ausführung
- Ergebnis-Validierung

## ⚙️ Konfiguration

- **Ollama Model**: Standard `llama3.1` (änderbar in der Architektur)
- **Datenbank**: SQLite (`ollama_flow_multi_role.db`)
- **Drohnen-Anzahl**: Anpassbar in `initialize_drone_fleets()`