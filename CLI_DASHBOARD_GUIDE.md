# 📊 Enhanced CLI Dashboard - User Guide

## 🚀 Overview

Das Enhanced CLI Dashboard bietet eine vollständige, interaktive Monitoring-Lösung für das Ollama Flow Framework mit Echtzeit-Updates und benutzerfreundlicher Terminal-Oberfläche.

## ✨ Features

### 🔄 Real-time Task Monitoring
- Live Anzeige aller aktiven Tasks
- Task-Status: active, pending, completed, failed
- Progress-Tracking mit Prozentanzeige
- Worker-Zuordnung und Dependencies
- Estimated Duration und Priorities

### 💻 System Resource Monitoring
- Live CPU, Memory, Disk Usage mit Farbbalken
- Netzwerk I/O Statistiken  
- Aktive Prozesse und Ollama-Prozesse
- Agent-spezifische Ressourcennutzung
- Echtzeit-Updates alle 1 Sekunde

### 🏗️ Interactive Architecture Visualization
- **Hierarchical**: Queen → Sub-Queens → Workers
- **Centralized**: Queen im Zentrum, Workers rundherum  
- **Fully Connected**: Mesh-Netzwerk Darstellung
- Live Agent-Status (🔧 active, ⭕ idle)
- Visuelle Verbindungslinien

### ⚙️ Configuration Management
- Vollständige Konfigurationsanzeige
- Model, Worker Count, Architecture Type
- Security Settings, Features Status
- Environment Variables
- Dashboard Version Info

### 📄 Live Log Monitoring
- Echtzeit Log-Stream
- Farbkodierung nach Log-Level (ERROR, WARNING, INFO)
- Scrollbare Historie
- Automatische Updates

### ⌨️ Keyboard Navigation
- Intuitive Tastenkürzel
- 6-Panel System
- Responsive Interface

## 🎮 Usage

### Starting the Dashboard

```bash
# CLI Dashboard starten
ollama-flow cli-dashboard

# Alternative: Web Dashboard
ollama-flow dashboard

# Hilfe anzeigen
ollama-flow --help
```

### Navigation Controls

| Key | Action |
|-----|--------|
| `1` | Overview Panel |
| `2` | Tasks Panel |
| `3` | Resources Panel |
| `4` | Architecture Panel |
| `5` | Configuration Panel |
| `6` | Logs Panel |
| `Q` | Quit Dashboard |
| `R` | Force Refresh |
| `↑` | Navigate Up (future) |
| `↓` | Navigate Down (future) |

## 📋 Dashboard Panels

### 1. Overview Panel
**📊 SYSTEM OVERVIEW**
- Quick Stats: Active Tasks, Active Agents, Memory, CPU
- Current Model und Architecture Type
- Mini Architecture Preview
- System Status Summary

### 2. Tasks Panel  
**📋 ACTIVE TASKS**
- Task Table mit Columns:
  - ID: Unique Task Identifier
  - Status: active, pending, completed, failed
  - Content: Task Description (truncated)
  - Worker: Assigned Worker Agent
  - Progress: Completion Percentage
  - Duration: Estimated/Actual Duration
- Color-coded Status Indicators
- Real-time Updates

### 3. Resources Panel
**💻 SYSTEM RESOURCES**
- CPU Usage mit Progress Bar und Farbkodierung
- Memory Usage mit Progress Bar
- Disk Usage mit Progress Bar
- Network I/O Statistics (bytes sent/received)
- Process Counters (Total, Ollama-specific)
- Agent Resource Usage per Agent

**Color Coding:**
- 🟢 Green: < 50% Usage (Good)
- 🟡 Yellow: 50-80% Usage (Warning)  
- 🔴 Red: > 80% Usage (Critical)

### 4. Architecture Panel
**🏗️ ARCHITECTURE VISUALIZATION**

#### Hierarchical Mode
```
👑 Enhanced Queen
    │
👥 Sub Queen A   👥 Sub Queen B  
    │                  │
🔧 Worker 1      🔧 Worker 3
🔧 Worker 2      🔧 Worker 4
```

#### Centralized Mode
```
    🔧 Worker 1
         │
🔧 W4 ── 👑 Queen ── 🔧 W2
         │
    🔧 Worker 3
```

#### Fully Connected Mode
```
👑 Queen ── 🔧 W1 ── 🔧 W2
  │           │        │
🔧 W4 ────── 🔧 W3 ──┘
```

**Legend:**
- 👑 Queen Agent
- 👥 Sub-Queen Agent
- 🔧 Active Worker
- ⭕ Idle Worker

### 5. Configuration Panel
**⚙️ CONFIGURATION**
- Model: phi3:mini (default)
- Worker Count: 4 (default)
- Architecture: HIERARCHICAL
- Secure Mode: ✓ / ✗
- Parallel LLM: ✓ / ✗  
- Project Folder: Current directory
- Database Path: ollama_flow_messages.db
- Dashboard Version: v2.1.0

**Features:**
- ✓ auto-shutdown
- ✓ web-dashboard
- ✓ neural-intelligence
- ✓ extended-formats

### 6. Logs Panel
**📄 SYSTEM LOGS**
- Live log stream from ollama_flow_dashboard.log
- Color-coded by log level:
  - 🔴 ERROR: Critical errors
  - 🟡 WARNING: Warnings
  - 🟢 INFO: Information
  - ⚪ DEBUG: Debug information
- Last 100 lines displayed
- Auto-scrolling
- Real-time updates

## 🔧 Technical Details

### Architecture
- **EnhancedCLIDashboard**: Main class mit curses interface
- **Multi-threaded Updates**: 
  - Fast updates (1s): System metrics
  - Slow updates (5s): Tasks und agents
- **Async/await Pattern**: für database operations
- **Real-time Metrics**: via psutil

### Dependencies
- **curses**: Built-in Python module für terminal UI
- **psutil**: System und process utilities
- **asyncio**: Asynchronous programming
- **threading**: Background updates
- **sqlite3**: Database operations

### Performance
- **Update Intervals**:
  - System metrics: 1 second
  - Tasks/Agents: 5 seconds
  - Display refresh: 0.1 seconds
- **Memory efficient**: Threaded updates
- **CPU optimized**: Minimal overhead
- **Responsive**: Instant keyboard input

## 🐛 Troubleshooting

### Common Issues

**1. Import Error:**
```
❌ Could not import CLI dashboard
```
**Solution:**
- Ensure `cli_dashboard_enhanced.py` exists
- Check `curses` and `psutil` availability

**2. Terminal Too Small:**
```
Terminal too small for dashboard
```
**Solution:**
- Resize terminal to minimum 80x24
- Use fullscreen terminal

**3. Permission Errors:**
```
Cannot access database
```
**Solution:**
- Check file permissions
- Ensure write access to working directory

**4. Display Issues:**
```
Garbled characters
```
**Solution:**
- Use compatible terminal emulator
- Check UTF-8 encoding support

### Debug Mode

```bash
# Enable debug logging
export OLLAMA_LOG_LEVEL=DEBUG
ollama-flow cli-dashboard
```

### Log Files
- Dashboard logs: `ollama_flow_dashboard.log`
- Framework logs: `ollama_flow.log`
- Database: `ollama_flow_messages.db`

## 🚀 Advanced Usage

### Custom Configuration

```bash
# Custom worker count
export OLLAMA_WORKER_COUNT=8
ollama-flow cli-dashboard

# Custom model
export OLLAMA_MODEL=codellama:7b
ollama-flow cli-dashboard

# Custom architecture
export OLLAMA_ARCHITECTURE_TYPE=CENTRALIZED
ollama-flow cli-dashboard
```

### Integration with Tasks

```bash
# Start task in background, monitor with dashboard
ollama-flow run "Create Flask application" &
ollama-flow cli-dashboard
```

## 🔮 Future Enhancements

- Interactive task management
- Real-time configuration changes
- Export capabilities
- Custom themes
- Plugin system
- Remote monitoring

## 📞 Support

- Documentation: Siehe README.md
- Issues: GitHub Issues
- Examples: `/examples` directory

---

**🎯 CLI Dashboard v2.1.0 - Real-time Monitoring für Ollama Flow Framework**