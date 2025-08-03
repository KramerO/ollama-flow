# 🗑️ Ollama Flow Uninstallation Guide

This guide explains how to completely remove Ollama Flow from your system using the provided uninstallation script.

## Quick Uninstall

```bash
# Interactive uninstall (recommended)
bash uninstall.sh

# Force uninstall (for automation)
bash uninstall.sh --force

# Show help
bash uninstall.sh --help
```

## What Gets Removed

### ✅ Framework Files
- `~/.ollama-flow/` - Complete framework directory
- All Python modules, agents, and components
- Enhanced AI orchestration tools

### ✅ CLI Wrapper  
- `~/.local/bin/ollama-flow` - Main CLI command
- Any backup CLI wrappers
- Symlinks if present

### ✅ Configuration
- `~/.config/ollama-flow/` - Configuration directory
- `config.yaml` and `.env` files
- User preferences and settings

### ✅ Shell Integration
- PATH entries in `~/.bashrc`
- PATH entries in `~/.zshrc`  
- PATH entries in `~/.profile`
- **Automatic backups created** for safety

### ✅ Data & Logs
- `ollama_flow_messages.db` - Message database
- `neural_intelligence.db` - AI learning data
- `monitoring.db`, `sessions.db` - System data
- All `*.log` files - Application logs
- Temporary files and caches

### ✅ Running Processes
- All `ollama-flow` processes
- All `enhanced_main.py` processes  
- Related Python component processes

## What is NOT Removed

### ❌ Preserved Components
- **Ollama itself** - Other projects may need it
- **Python dependencies** - Shared with other projects
- **Shell profile backups** - Safety preservation
- **User project files** - Your created content

## Usage Examples

### Interactive Uninstall (Recommended)
```bash
bash uninstall.sh
```
- Shows confirmation dialog
- Lists what will be removed
- Requires user confirmation
- Offers optional dependency removal

### Automated Uninstall
```bash
bash uninstall.sh --force
```
- Skips confirmation prompts
- Perfect for CI/CD pipelines
- Silent execution
- Keeps Python dependencies

### Dry Run Check
```bash
echo "n" | bash uninstall.sh
```
- See what would be removed
- Cancel before actual removal
- Useful for verification

## Safety Features

### 🛡️ Built-in Protections
- **Confirmation required** (unless `--force`)
- **Automatic shell profile backups** 
- **Graceful process termination**
- **Verification of complete removal**
- **Clear feedback on actions taken**
- **Error handling and recovery**

### 📋 Pre-Uninstall Checklist
1. ✅ Save any important project files
2. ✅ Stop running Ollama Flow tasks  
3. ✅ Close dashboards and CLI sessions
4. ✅ Consider Python dependency sharing

### 🔄 Post-Uninstall Steps
1. Restart terminal: `exec $SHELL`
2. Or reload profile: `source ~/.bashrc`
3. Verify removal: `ollama-flow` (should not work)

## Uninstall Process

The script follows this systematic approach:

1. **🛑 Process Termination**
   - Gracefully stop all Ollama Flow processes
   - Wait for clean shutdown
   - Force kill if necessary

2. **🗂️ File Removal**
   - Remove framework directory
   - Remove CLI wrapper
   - Remove configuration files

3. **📝 Profile Cleanup**
   - Backup shell profiles
   - Remove PATH entries
   - Clean installation traces

4. **🧹 Data Cleanup**
   - Remove databases
   - Clean log files
   - Remove temporary files

5. **🎯 Optional Cleanup**
   - Optionally remove Python dependencies
   - User confirmation required

6. **✅ Verification**
   - Verify complete removal
   - Report any issues
   - Confirm success

## Troubleshooting

### Script Won't Run
```bash
# Make executable
chmod +x uninstall.sh

# Run with bash
bash uninstall.sh
```

### Permission Issues
```bash
# Check permissions
ls -la uninstall.sh

# Fix if needed
chmod 755 uninstall.sh
```

### Partial Removal
If uninstall fails partway through:

```bash
# Force completion
bash uninstall.sh --force

# Manual cleanup if needed
rm -rf ~/.ollama-flow
rm -f ~/.local/bin/ollama-flow
rm -rf ~/.config/ollama-flow
```

### Verify Complete Removal
```bash
# Check framework
ls ~/.ollama-flow 2>/dev/null && echo "Still exists" || echo "Removed"

# Check CLI
which ollama-flow 2>/dev/null && echo "Still exists" || echo "Removed"

# Check config
ls ~/.config/ollama-flow 2>/dev/null && echo "Still exists" || echo "Removed"
```

## Reinstallation

After uninstalling, you can reinstall anytime:

```bash
# Reinstall latest version
curl -fsSL https://ollama-flow.ai/install.sh | sh

# Or use local installer
bash install.sh
```

## Support

If you encounter issues during uninstallation:

1. Check the uninstall log output
2. Try force mode: `bash uninstall.sh --force`
3. Report issues at: https://github.com/ruvnet/ollama-flow/issues
4. Manual cleanup instructions above

---

**Note:** This uninstaller is designed to be safe and thorough. It preserves system components that might be used by other projects while completely removing Ollama Flow.