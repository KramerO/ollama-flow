# 🐳 Ollama Flow Docker Integration

Vollständige Docker-Unterstützung für container-basierte AI-Agent-Ausführung mit Skalierung und Orchestrierung.

## 🚀 Schnellstart

### Ein-Befehl-Setup
```bash
# Vollständiges Setup mit Docker
./scripts/docker_setup.sh setup

# Services starten
./scripts/docker_setup.sh start

# Dashboard öffnen: http://localhost:8080
```

### Manuelle Installation
```bash
# 1. Docker Images bauen
docker-compose build

# 2. Services starten
docker-compose up -d

# 3. Status prüfen
docker-compose ps
```

## 🏗️ Architektur

### Container-Übersicht
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main App      │    │     Redis       │    │   Monitoring    │
│ ollama-flow-app │◄──►│ollama-flow-redis│◄──►│ollama-flow-mon  │
│   Port: 8080    │    │   Port: 6379    │    │   Port: 9090    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent Worker 1  │    │ Agent Worker 2  │    │ Agent Worker N  │
│ollama-flow-w1   │    │ollama-flow-w2   │    │ollama-flow-wN   │
│ Role: ANALYST   │    │Role: DATA_SCI   │    │ Role: DYNAMIC   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Netzwerk-Konfiguration
- **Network**: `ollama-flow-net` (172.20.0.0/16)
- **Redis**: Zentrale Kommunikation und Datenpersistenz
- **Service Discovery**: Container-Namen als Hostnamen
- **Volumes**: Persistente Daten und Logs

## 📋 Verfügbare Services

### Produktions-Services (`docker-compose.yml`)
| Service | Port | Beschreibung |
|---------|------|--------------|
| `redis` | 6379 | Enhanced Database mit Persistenz |
| `ollama-flow` | 8080 | Haupt-Dashboard und API |
| `agent-worker-1` | - | Spezialisierter Agent (ANALYST) |
| `agent-worker-2` | - | Spezialisierter Agent (DATA_SCIENTIST) |
| `monitoring` | 9090 | System-Monitoring und Metriken |

### Entwicklungs-Services (`docker-compose.dev.yml`)
| Service | Port | Beschreibung |
|---------|------|--------------|
| `redis-dev` | 6380 | Development Redis mit Debug-Logs |
| `ollama-flow-dev` | 8081 | Development App mit Hot-Reload |
|  | 5678 | Debug-Port für Remote-Debugging |

## 🛠️ Verwendung

### Setup-Script verwenden
```bash
# Vollständiges Setup
./scripts/docker_setup.sh setup

# Produktions-Environment starten
./scripts/docker_setup.sh start

# Development-Environment starten  
./scripts/docker_setup.sh start-dev

# Services stoppen
./scripts/docker_setup.sh stop

# Worker skalieren
./scripts/docker_setup.sh scale 8

# Logs anzeigen
./scripts/docker_setup.sh logs ollama-flow

# Health-Check
./scripts/docker_setup.sh health

# Cleanup
./scripts/docker_setup.sh cleanup
```

### Docker Compose direkt verwenden
```bash
# Produktions-Environment
docker-compose up -d
docker-compose ps
docker-compose logs -f ollama-flow

# Development-Environment
docker-compose -f docker-compose.dev.yml up -d

# Skalierung
docker-compose up -d --scale agent-worker-1=4

# Stoppen
docker-compose down
```

### Individuelle Container
```bash
# Redis starten
docker run -d --name ollama-redis \
  -p 6379:6379 \
  -v ollama-redis-data:/data \
  redis:7.2-alpine redis-server --appendonly yes

# Ollama Flow starten
docker run -d --name ollama-flow \
  -p 8080:8080 \
  -e REDIS_HOST=ollama-redis \
  -v $(pwd)/output:/app/output \
  ollama-flow:latest

# Agent Worker starten
docker run -d --name ollama-worker-1 \
  -e REDIS_HOST=ollama-redis \
  -e WORKER_ID=1 \
  -v $(pwd)/data:/app/data \
  ollama-flow:latest python3 agents/docker_agent_worker.py
```

## ⚙️ Konfiguration

### Umgebungsvariablen
```bash
# Redis-Verbindung
REDIS_HOST=redis                    # Redis Hostname
REDIS_PORT=6379                     # Redis Port

# Ollama-Verbindung
OLLAMA_HOST=host.docker.internal:11434  # Ollama API Endpoint

# Docker-Spezifisch
DOCKER_MODE=true                    # Container-Modus aktivieren
DEBUG_MODE=false                    # Debug-Modus (nur Development)

# Agent-Konfiguration
WORKER_ID=1                         # Eindeutige Worker-ID
AGENT_MODE=worker                   # Agent-Modus (worker/queen/sub-queen)

# Logging
LOG_LEVEL=INFO                      # Log-Level (DEBUG/INFO/WARNING/ERROR)
PYTHONUNBUFFERED=1                  # Python Output Buffering deaktivieren
```

### Volume-Konfiguration
```yaml
volumes:
  redis_data:           # Redis Datenpersistenz
    driver: local
  
  # Bind Mounts für Development
  ./data:/app/data      # Arbeits-Dateien
  ./logs:/app/logs      # Log-Dateien  
  ./output:/app/output  # Generierte Ausgaben
```

### Netzwerk-Konfiguration
```yaml
networks:
  ollama-flow-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🔧 Agent-Worker-System

### Spezialisierte Rollen
```python
# Worker-Rollen basierend auf Worker-ID
roles = [
    DroneRole.ANALYST,        # Worker 1
    DroneRole.DATA_SCIENTIST, # Worker 2  
    DroneRole.IT_ARCHITECT,   # Worker 3
    DroneRole.DEVELOPER       # Worker 4
]
role = roles[worker_id % len(roles)]
```

### Worker-Skalierung
```bash
# Mehr Worker starten (horizontal scaling)
./scripts/docker_setup.sh scale 8

# Oder mit docker-compose
docker-compose up -d --scale agent-worker-1=4 --scale agent-worker-2=4
```

### Worker-Management
```python
# Worker-Registrierung
worker_info = {
    'worker_id': worker_id,
    'role': agent.role.value,
    'status': 'available',
    'container_id': os.getenv('HOSTNAME'),
    'last_seen': time.time()
}

# Heartbeat-System
heartbeat_data = {
    'worker_id': worker_id,
    'timestamp': time.time(),
    'status': 'active'
}
```

## 📊 Monitoring und Debugging

### Container-Status prüfen
```bash
# Alle Services
docker-compose ps

# Einzelner Service
docker-compose ps ollama-flow

# Resource-Nutzung
docker stats $(docker-compose ps -q)
```

### Logs analysieren
```bash
# Live-Logs
docker-compose logs -f

# Spezifische Services
docker-compose logs -f ollama-flow redis agent-worker-1

# Log-Timestamps
docker-compose logs -t --since="1h" ollama-flow

# Letzte 100 Zeilen
docker-compose logs --tail=100 ollama-flow
```

### Health-Checks
```bash
# Automatische Health-Checks
curl -f http://localhost:8080/health

# Redis Health-Check
docker exec ollama-flow-redis redis-cli ping

# Worker Health-Check
./scripts/docker_setup.sh health
```

### Performance-Monitoring
```bash
# Container-Performance
docker stats --no-stream

# Netzwerk-Traffic
docker exec ollama-flow-app netstat -tuln

# Disk-Usage
docker system df
docker volume ls
```

## 🧪 Testing

### Unit-Tests für Docker-Integration
```bash
# Alle Docker-Tests
python -m pytest tests/test_docker_integration.py -v

# Spezifische Test-Kategorien
python -m pytest tests/test_docker_integration.py::TestDockerManager -v
python -m pytest tests/test_docker_integration.py::TestDockerAgentWorker -v

# Integration-Tests (benötigt Docker)
python -m pytest tests/test_docker_integration.py -m integration -v
```

### Manual Testing
```bash
# Setup-Script testen
./scripts/docker_setup.sh test

# Container-Funktionalität testen
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🔒 Sicherheit

### Security Best Practices
- **Non-Root User**: Container laufen als `ollama`-User
- **Read-Only Filesystems**: Wo möglich
- **Resource-Limits**: Memory und CPU-Beschränkungen
- **Network-Isolation**: Eigenes Docker-Netzwerk
- **Secret-Management**: Keine Secrets in Images

### Resource-Limits
```yaml
services:
  ollama-flow:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Security-Scanning
```bash
# Image-Vulnerabilities scannen
docker scout cves ollama-flow:latest

# Container-Security prüfen
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/project \
  securecodewarrior/docker-security-scanning
```

## 🚀 Performance-Optimierungen

### Multi-Stage Build
```dockerfile
# Build Stage - nur für Kompilierung
FROM python:3.11-slim AS builder
# ... build dependencies

# Runtime Stage - minimal für Ausführung  
FROM python:3.11-slim AS runtime
COPY --from=builder /app /app
```

### Caching-Strategien
```bash
# Build-Cache nutzen
docker-compose build --parallel

# Layer-Caching optimieren
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # Code-Änderungen invalidieren nicht pip install
```

### Resource-Monitoring
```python
# Container-Metriken sammeln
def get_container_stats():
    stats = {}
    for container in docker_client.containers.list():
        stats[container.name] = container.stats(stream=False)
    return stats
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
name: Docker Build and Test
on: [push, pull_request]
jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and test
        run: |
          ./scripts/docker_setup.sh build
          ./scripts/docker_setup.sh test
```

### Automated Deployment
```bash
# Production Deployment
docker-compose -f docker-compose.prod.yml up -d

# Blue-Green Deployment
docker-compose -f docker-compose.blue.yml up -d
# Test new version...
docker-compose -f docker-compose.green.yml down
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### 1. Container startet nicht
```bash
# Logs prüfen
docker-compose logs ollama-flow

# Container-Status
docker-compose ps

# Image neu bauen
docker-compose build --no-cache ollama-flow
```

#### 2. Redis-Verbindungsfehler
```bash
# Redis-Container prüfen
docker-compose logs redis

# Netzwerk-Verbindung testen
docker-compose exec ollama-flow ping redis

# Redis direkt testen
docker-compose exec redis redis-cli ping
```

#### 3. Worker registrieren sich nicht
```bash
# Worker-Logs prüfen
docker-compose logs agent-worker-1

# Umgebungsvariablen prüfen
docker-compose exec agent-worker-1 env | grep -E "(REDIS|WORKER)"

# Datenbank-Verbindung testen
docker-compose exec ollama-flow python3 -c "
from enhanced_db_manager import EnhancedDBManager
db = EnhancedDBManager()
print(db.get_stats())
"
```

#### 4. Ollama nicht erreichbar
```bash
# Host-Verbindung prüfen
docker-compose exec ollama-flow curl -s http://host.docker.internal:11434/api/tags

# Alternative Ollama-Container
docker run -d --name ollama \
  -p 11434:11434 \
  -v ollama-data:/root/.ollama \
  ollama/ollama
```

### Debug-Modus aktivieren
```bash
# Development-Environment mit Debugging
docker-compose -f docker-compose.dev.yml up -d

# Remote-Debugger verbinden (Port 5678)
# VS Code: Python Remote Attach to localhost:5678
```

### Performance-Probleme
```bash
# Resource-Nutzung prüfen
docker stats --no-stream

# Container-Limits erhöhen
docker-compose -f docker-compose.yml up -d \
  --scale agent-worker-1=2 \
  --scale agent-worker-2=2
```

## 📚 Weiterführende Dokumentationen

- **[Docker Compose Reference](https://docs.docker.com/compose/)**
- **[Docker Networking](https://docs.docker.com/network/)**  
- **[Redis Docker Image](https://hub.docker.com/_/redis)**
- **[Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)**

---

## 🤝 Support

**Probleme mit Docker-Integration?**

1. **Check-Liste durchgehen**: Requirements, Images, Netzwerk
2. **Logs analysieren**: `./scripts/docker_setup.sh logs`
3. **Health-Check**: `./scripts/docker_setup.sh health`
4. **GitHub Issues**: Erstelle detailliertes Issue mit Logs

**Entwicklungs-Support:**
- Development-Environment: `./scripts/docker_setup.sh start-dev`
- Remote-Debugging: Port 5678
- Hot-Reload: Code-Änderungen werden automatisch übernommen