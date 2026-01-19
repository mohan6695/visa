# Local Ollama Qwen Integration for KiloCode

This guide explains how to set up and use the local Ollama Qwen model with KiloCode.

## Prerequisites

1. **Ollama installed**: Download from https://ollama.ai
2. **Qwen model**: Downloaded to Ollama (see setup below)
3. **Python 3.8+**: For running the MCP server

## Setup Instructions

### Step 1: Install and Start Ollama

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Keep this terminal open
```

### Step 2: Download Qwen Model

```bash
# Download Qwen 7B model (recommended for local use)
ollama pull qwen:7b

# Or try smaller model for less memory
ollama pull qwen:3b

# Verify installation
ollama list
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

### Step 4: Start the MCP Server

```bash
# Make the startup script executable
chmod +x run_ollama_mcp.sh

# Start the MCP server
./run_ollama_mcp.sh
```

Or run directly:

```bash
pip install httpx mcp
python ollama_mcp_server.py
```

## Usage

Once the MCP server is running, KiloCode can use the local Qwen model for:

- **AI Chat**: Natural language conversations
- **Code Assistance**: Code generation and explanation
- **Text Analysis**: Summarization, sentiment analysis
- **Question Answering**: Answering questions based on context

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name to use | `qwen:7b` |
| `OLLAMA_EMBEDDING_MODEL` | Embedding model | `nomic-embed-text` |

## Testing

Test the connection:

```bash
curl http://localhost:11434/api/tags
```

Should return JSON with available models.

## Troubleshooting

### Ollama not starting
```bash
# Check if port is in use
lsof -i :11434

# Kill existing process
kill <PID>
```

### Model not found
```bash
# Re-download model
ollama pull qwen:7b

# Check available models
ollama list
```

### Connection refused
- Ensure Ollama is running: `ollama serve`
- Check URL is correct in `.env`

## API Reference

### Generate Text
```python
import httpx

response = httpx.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen:7b",
        "prompt": "Hello, how are you?",
        "stream": False
    }
)
print(response.json()["response"])
```

### Chat Completion
```python
response = httpx.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen:7b",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)
print(response.json()["message"]["content"])
```

## Models

Recommended models for different use cases:

| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| qwen:3b | ~2GB | ~4GB | Light tasks, testing |
| qwen:7b | ~7GB | ~8GB | General purpose (recommended) |
| qwen:14b | ~14GB | ~16GB | Complex reasoning |
| qwen:72b | ~72GB | ~80GB | High-quality responses |

## Performance Tips

1. **GPU Acceleration**: Ensure Metal (macOS) or CUDA is enabled
2. **Memory**: Close other applications when running large models
3. **Temperature**: Lower temperature (0.3-0.5) for more consistent outputs
4. **Context Length**: Adjust `num_ctx` for longer conversations
