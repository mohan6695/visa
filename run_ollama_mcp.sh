#!/bin/bash
# Startup script for Ollama MCP Server
# This script starts the MCP server that allows KiloCode to use local Ollama Qwen model

# Set environment variables
export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen:7b}"

echo "=============================================="
echo "Ollama MCP Server for KiloCode"
echo "=============================================="
echo "Ollama URL: $OLLAMA_URL"
echo "Model: $OLLAMA_MODEL"
echo "=============================================="

# Check if Ollama is running
if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
    echo "Warning: Ollama doesn't seem to be running at $OLLAMA_URL"
    echo "Make sure Ollama is installed and running before starting this server."
    echo "You can start Ollama with: ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies if needed
pip install -q httpx mcp

# Start the MCP server
echo "Starting Ollama MCP Server..."
python ollama_mcp_server.py
