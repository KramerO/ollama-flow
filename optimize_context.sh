#!/bin/bash

# Ollama Context Size Optimization Script

echo "🔧 Ollama Context Size Optimization"
echo "=================================="

# Check current Ollama status
echo "📊 Current Ollama Models:"
ollama list

# Create models with different context sizes
echo ""
echo "🚀 Creating optimized models..."

# Small context model (4K) - fast for simple tasks
cat << 'EOF' > /tmp/small-context-model
FROM phi3:mini
PARAMETER num_ctx 4096
PARAMETER temperature 0.7
SYSTEM """You are a focused code generation assistant for simple tasks."""
EOF

# Medium context model (8K) - balanced
cat << 'EOF' > /tmp/medium-context-model
FROM phi3:mini
PARAMETER num_ctx 8192
PARAMETER temperature 0.7
SYSTEM """You are a code generation assistant with access to moderate project context."""
EOF

# Large context model (16K) - for complex projects
cat << 'EOF' > /tmp/large-context-model
FROM phi3:mini
PARAMETER num_ctx 16384
PARAMETER temperature 0.7
SYSTEM """You are an advanced code generation assistant with extensive project context awareness."""
EOF

# Create the models
echo "Creating phi3-small-context (4K tokens)..."
ollama create phi3-small-context -f /tmp/small-context-model 2>/dev/null

echo "Creating phi3-medium-context (8K tokens)..."
ollama create phi3-medium-context -f /tmp/medium-context-model 2>/dev/null

echo "Creating phi3-large-context (16K tokens)..."
ollama create phi3-large-context -f /tmp/large-context-model 2>/dev/null

# Cleanup temp files
rm -f /tmp/*-context-model

echo ""
echo "✅ Available optimized models:"
echo "   • phi3-small-context  (4K context)  - Fast, simple tasks"
echo "   • phi3-medium-context (8K context)  - Balanced performance"
echo "   • phi3-large-context  (16K context) - Large project context"

echo ""
echo "💡 Usage examples:"
echo "   ollama-flow run 'simple task' --model phi3-small-context"
echo "   ollama-flow run 'complex project task' --model phi3-large-context"

echo ""
echo "🎯 Optimization complete!"