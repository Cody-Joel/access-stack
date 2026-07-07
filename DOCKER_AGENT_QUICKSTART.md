# Docker Agent Quick Start (Using Ollama - No API Key Needed)

## 1. Start Ollama & Pull a Model

**Start Ollama** (if not running):
```bash
# Ollama runs on http://localhost:11434
# It's already in your pgpt docker-compose setup
cd C:\pgpt
up.bat
```

**Make sure you have a model pulled**:
```bash
docker exec pgpt-ollama ollama pull mistral
# or use: hermes2, neural-chat, llama2, etc.
```

## 2. Run the Agent

### Option A: ONNX Only
```bash
cd C:\AS\ONNX
docker agent run agent.yaml
```

### Option B: Full Stack (Sentinel + Skill + ONNX)
```bash
cd C:\AS
docker agent run agent-full-stack.yaml
```

### Option C: Quick Menu
```bash
cd C:\AS\ONNX
.\run-agent.bat
```

## 3. Available Models (No API Key!)

**Ollama models** (local, free):
- `mistral` — Fast, good reasoning (default, recommended)
- `hermes2` — Creative, brainstorming
- `neural-chat` — Conversation optimized
- `llama2` — General purpose
- `dolphin-mixtral` — Advanced reasoning (slower)

Pull them:
```bash
docker exec pgpt-ollama ollama pull hermes2
docker exec pgpt-ollama ollama list
```

Change agent.yaml model:
```yaml
root:
  model: ollama/hermes2  # Change from mistral
```

## 4. Try These Prompts

```
List all files in C:\AS\ONNX\models and describe the project
```

```
Run the C# project: dotnet build and dotnet run
```

```
If any .onnx models exist, get their metadata
```

```
What's in the Python finetuner directory?
```

## 5. What It Can Do

✅ Read/write files  
✅ Execute dotnet (C#)  
✅ Execute Python  
✅ Run shell commands  
✅ Reason & delegate to specialists  
✅ Build and debug code  

## 6. Troubleshooting

### "Failed to connect to Ollama at http://localhost:11434"
```bash
cd C:\pgpt
up.bat  # Start containers
```

### "Model not found"
```bash
docker exec pgpt-ollama ollama pull mistral
```

### Models slow/not responding
Try a smaller model:
```bash
docker exec pgpt-ollama ollama pull neural-chat  # Faster
```

## 7. Next Steps

1. Add ONNX models to `C:\AS\ONNX\models\`
2. Ask the agent to analyze them
3. Run benchmarks
4. Integrate with VS Code (optional)
