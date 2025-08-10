# Auto-Scaling System Guide für Ollama Flow

## Übersicht

Das Auto-Scaling System für Ollama Flow ermöglicht die automatische Skalierung von KI-Agenten basierend auf verfügbarem GPU-Speicher und Workload-Metriken. Das System optimiert die Agent-Anzahl dynamisch, um eine optimale Ressourcennutzung und Performance zu gewährleisten.

## 🔧 Hauptkomponenten

### 1. GPU Auto-Scaler (`gpu_autoscaler.py`)
- **Funktion**: Überwacht GPU-Status und trifft speicherbasierte Scaling-Entscheidungen
- **Features**:
  - Erkennung von NVIDIA, AMD und Intel GPUs
  - Modell-spezifische Memory-Anforderungen
  - Automatische Berechnung der max. Agent-Anzahl
  - Cooldown-Mechanismus für stabile Scaling-Entscheidungen

### 2. Workload Metrics Collector (`workload_metrics.py`)
- **Funktion**: Sammelt und analysiert Systemmetriken für workload-basierte Entscheidungen
- **Features**:
  - Task-Lifecycle-Tracking
  - Agent-Performance-Überwachung  
  - Workload-Severity-Bewertung
  - Scaling-Empfehlungen basierend auf Queue-Länge und Auslastung

### 3. Auto-Scaling Engine (`auto_scaling_engine.py`)
- **Funktion**: Koordiniert verschiedene Scaling-Strategien und trifft finale Entscheidungen
- **Strategien**:
  - `GPU_MEMORY_BASED`: Reine GPU-Speicher-Orientierung
  - `WORKLOAD_BASED`: Queue- und Auslastungsbasiert
  - `HYBRID`: Kombiniert GPU und Workload-Metriken
  - `CONSERVATIVE`: Vorsichtige Scaling-Entscheidungen
  - `AGGRESSIVE`: Proaktive Scaling-Entscheidungen

### 4. Dynamic Agent Manager (`dynamic_agent_manager.py`)
- **Funktion**: Verwaltet Lebenszyklus von dynamisch erstellten Agenten
- **Features**:
  - Agent-Erstellung und -Terminierung
  - Lifecycle-State-Tracking
  - Queue-Management für Batch-Operationen
  - Graceful Shutdown-Mechanismen

## 🚀 Verwendung

### Basis-Konfiguration

```python
from enhanced_framework import EnhancedOllamaFlow

# Auto-Scaling aktivieren
system = EnhancedOllamaFlow(
    auto_scaling=True,
    scaling_strategy="GPU_MEMORY_BASED",  # oder WORKLOAD_BASED, HYBRID, etc.
    model="phi3:mini"
)

# System initialisieren
await system.initialize()
```

### CLI-Verwendung

```bash
# Mit Auto-Scaling aktivieren
python enhanced_framework.py run "Create a Python web app" --auto-scaling --strategy HYBRID

# Interaktiver Modus mit Auto-Scaling
python enhanced_framework.py interactive --auto-scaling --strategy GPU_MEMORY_BASED
```

## ⚙️ Konfiguration

### GPU-Scaling-Parameter

```python
scaling_config = {
    'min_agents': 1,                      # Minimum Agent-Anzahl
    'max_agents': 8,                      # Maximum Agent-Anzahl (wird automatisch berechnet)
    'memory_buffer_mb': 1024,             # Reserve-Speicher
    'memory_safety_margin': 0.15,         # 15% Sicherheitsspielraum
    'scale_up_threshold': 0.75,           # Scale up bei >75% Memory-Nutzung
    'scale_down_threshold': 0.40,         # Scale down bei <40% Memory-Nutzung
    'scale_check_interval': 15.0,         # Prüfintervall in Sekunden
    'cooldown_period': 30.0,              # Cooldown zwischen Scaling-Aktionen
}
```

### Workload-Schwellenwerte

```python
workload_thresholds = {
    'high_queue_length': 10,              # Hohe Queue-Länge
    'high_wait_time': 30.0,               # Hohe Wartezeit (Sekunden)
    'high_cpu_usage': 80.0,               # Hohe CPU-Nutzung (%)
    'high_memory_usage': 85.0,            # Hohe System-Memory-Nutzung (%)
    'low_idle_agents': 0.2,               # Min. 20% idle Agents
    'agent_overload_threshold': 0.8,      # 80% agents busy = overload
    'scale_up_cooldown': 60.0,            # Scale-up Cooldown
    'scale_down_cooldown': 120.0,         # Scale-down Cooldown
}
```

## 🔍 Monitoring und Status

### Status-Informationen abrufen

```python
# GPU-Status
gpu_status = auto_scaler.get_gpu_status()
print(f"GPU Memory: {gpu_status['available_memory_mb']}MB verfügbar")
print(f"GPU Auslastung: {gpu_status['average_gpu_utilization']}%")

# Auto-Scaling Status
scaling_status = engine.get_scaling_status()
print(f"Aktuelle Strategie: {scaling_status['strategy']}")
print(f"Aktive Agents: {scaling_status['active_agents']}")

# Workload-Metriken
metrics = collector.get_current_metrics()
print(f"Queue-Länge: {metrics.queue_length}")
print(f"Durchschnittliche Wartezeit: {metrics.average_wait_time}s")
```

### Scaling-Empfehlungen

```python
# GPU-basierte Empfehlungen
gpu_recommendations = gpu_scaler.get_scaling_recommendations()

# Workload-basierte Empfehlungen  
workload_recommendations = metrics_collector.get_scaling_recommendations()

# Engine-Empfehlungen (alle Strategien kombiniert)
combined_recommendations = engine.get_recommendations()
```

## 📊 Scaling-Strategien im Detail

### 1. GPU_MEMORY_BASED
**Beste Verwendung**: Systeme mit begrenztem GPU-Speicher
- Skaliert basierend auf verfügbarem GPU-Memory
- Berücksichtigt modellspezifische Memory-Anforderungen
- Verhindert Out-of-Memory-Fehler

### 2. WORKLOAD_BASED  
**Beste Verwendung**: Queue-intensive Anwendungen
- Skaliert basierend auf Task-Queue-Länge und Wartezeiten
- Berücksichtigt Agent-Auslastung und Throughput
- Reagiert schnell auf Workload-Spitzen

### 3. HYBRID (Empfohlen)
**Beste Verwendung**: Ausgewogene Systeme
- Kombiniert GPU- und Workload-Metriken
- Konsens-Algorithmus für stabile Entscheidungen
- GPU-Memory hat Vorrang bei Konflikten

### 4. CONSERVATIVE
**Beste Verwendung**: Produktive Umgebungen
- Vorsichtige Scaling-Entscheidungen
- Höhere Schwellenwerte für Scale-up
- Längere Cooldown-Perioden

### 5. AGGRESSIVE
**Beste Verwendung**: Entwicklung/Testing
- Proaktives Scaling bei verfügbaren Ressourcen
- Batch-Scaling (mehrere Agents gleichzeitig)
- Schnelle Reaktion auf Workload-Änderungen

## 🛠️ Erweiterte Konfiguration

### Custom Scaling-Callbacks

```python
async def custom_scaling_notification(event):
    """Custom handler für Scaling-Events"""
    print(f"Scaling Event: {event.action} {event.from_count}→{event.to_count}")
    # Custom Logic hier...

# Callback registrieren
engine.set_callbacks(
    notification_callback=custom_scaling_notification
)
```

### Custom Agent-Rollen

```python
# Optimale Rolle für neuen Agent bestimmen
def determine_optimal_role():
    # Custom Logic basierend auf aktuellen Anforderungen
    return DroneRole.DEVELOPER

# Agent mit spezifischer Rolle erstellen
agent = await dynamic_manager.create_agent(
    role=determine_optimal_role(),
    model="codellama:7b",
    reason="custom_scaling"
)
```

### Lifecycle-Callbacks

```python
async def on_agent_created(lifecycle_info):
    print(f"Agent {lifecycle_info.agent_id} erstellt: {lifecycle_info.role}")

async def on_agent_terminated(lifecycle_info):
    print(f"Agent {lifecycle_info.agent_id} beendet nach {lifecycle_info.lifetime_seconds}s")

# Callbacks registrieren
dynamic_manager.add_lifecycle_callback(AgentLifecycleState.ACTIVE, on_agent_created)
dynamic_manager.add_lifecycle_callback(AgentLifecycleState.TERMINATED, on_agent_terminated)
```

## 🔧 Troubleshooting

### Häufige Probleme

#### 1. Agents werden nicht skaliert
```bash
# GPU-Status prüfen
python -c "from gpu_autoscaler import GPUMonitor; print(GPUMonitor().get_gpu_status())"

# Scaling-Empfehlungen prüfen
python -c "from gpu_autoscaler import GPUAutoScaler; print(GPUAutoScaler().get_scaling_recommendations())"
```

#### 2. Hohe Memory-Nutzung
```python
# Memory-Anforderungen verschiedener Modelle prüfen
gpu_monitor = GPUMonitor()
for model_name, req in gpu_monitor.model_requirements.items():
    print(f"{model_name}: {req.recommended_memory_mb}MB")
```

#### 3. Scaling zu aggressiv/konservativ
```python
# Strategie anpassen
engine.update_strategy(ScalingStrategy.CONSERVATIVE)  # Weniger aggressiv
# oder
engine.update_strategy(ScalingStrategy.AGGRESSIVE)    # Aggressiver
```

### Debug-Modi

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detaillierte Logs für alle Auto-Scaling-Komponenten
logger = logging.getLogger("gpu_autoscaler")
logger.setLevel(logging.DEBUG)

logger = logging.getLogger("auto_scaling_engine") 
logger.setLevel(logging.DEBUG)

logger = logging.getLogger("dynamic_agent_manager")
logger.setLevel(logging.DEBUG)
```

## 📈 Performance-Optimierung

### GPU-Memory-Optimierung

1. **Modell-Auswahl**: Kleinere Modelle für mehr parallele Agents
   ```python
   # Statt llama3:70b (40GB) → llama3:8b (5GB) für mehr Agents
   system = EnhancedOllamaFlow(model="llama3:8b")
   ```

2. **Memory-Buffer anpassen**:
   ```python
   gpu_scaler.scaling_config['memory_buffer_mb'] = 2048  # Mehr Reserve
   gpu_scaler.scaling_config['memory_safety_margin'] = 0.20  # 20% Spielraum
   ```

### Workload-Optimierung

1. **Queue-Management**:
   ```python
   # Batch-Processing aktivieren
   dynamic_manager.config['batch_creation_size'] = 5  # 5 Agents parallel erstellen
   ```

2. **Cooldown-Tuning**:
   ```python
   # Schnelleres Scaling in Entwicklung
   engine.config['scaling_check_interval'] = 10.0  # 10s statt 20s
   engine.config['cooldown_period'] = 15.0         # 15s statt 30s
   ```

## 🔄 Integration mit bestehenden Systemen

### Docker-Integration

```yaml
# docker-compose.yml
services:
  ollama-flow:
    environment:
      - AUTO_SCALING=true
      - SCALING_STRATEGY=HYBRID
      - GPU_LAYERS=35
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### API-Integration

```python
from enhanced_framework import EnhancedOllamaFlow

class AutoScalingAPI:
    def __init__(self):
        self.system = EnhancedOllamaFlow(auto_scaling=True)
    
    async def get_status(self):
        return {
            'gpu_status': self.system.auto_scaling_engine.get_scaling_status(),
            'agent_count': len(self.system.dynamic_agent_manager.active_agents),
            'recommendations': self.system.auto_scaling_engine.get_recommendations()
        }
    
    async def set_strategy(self, strategy: str):
        strategy_enum = getattr(ScalingStrategy, strategy.upper())
        self.system.auto_scaling_engine.update_strategy(strategy_enum)
        return {"status": "updated", "strategy": strategy}
```

## 📝 Best Practices

### 1. Strategie-Auswahl
- **Entwicklung**: `AGGRESSIVE` für schnelle Iteration
- **Testing**: `HYBRID` für ausgewogene Performance  
- **Produktion**: `CONSERVATIVE` für Stabilität

### 2. Resource Planning
- **GPU-Memory**: 20-30% Reserve für System-Overhead
- **Agent-Limits**: Max 1 Agent pro 4-6GB GPU-Memory
- **Cooldown**: Min 30s in Produktion, 10-15s in Entwicklung

### 3. Monitoring
- GPU-Utilization: Ziel 60-80% für optimale Auslastung
- Queue-Length: Unter 10 für gute Response-Times
- Agent-Idle-Time: 10-20% idle Agents für Burst-Capacity

### 4. Fehlerbehebung
- Logs regelmäßig überwachen
- Scaling-Events tracken  
- Performance-Metriken sammeln
- Resource-Limits testen

---

*Das Auto-Scaling System wurde entwickelt, um die Komplexität der manuellen Agent-Verwaltung zu eliminieren und eine optimale Ressourcennutzung in verschiedenen Einsatzszenarien zu gewährleisten.*