# Docker Agent for ONNX Inference & Fine-tuning

This Docker Agent orchestrates AI agents for ONNX model inference, benchmarking, and fine-tuning.

## Setup

### Prerequisites
- Docker Agent CLI installed (comes with Docker Desktop)
- `ANTHROPIC_API_KEY` environment variable set

### Set API Key (Windows PowerShell)

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

Or add to system environment variables permanently.

## Run the Agent

```bash
cd C:\AS\ONNX

# Interactive mode (recommended)
docker agent run agent.yaml

# Non-interactive (headless)
docker agent run agent.yaml --no-tui < commands.txt

# API server mode (hit via HTTP)
docker agent serve agent.yaml --port 8000
```

## Agent Architecture

**Coordinator (root agent)** routes tasks to three specialists:

1. **inference_specialist** — Model info, single inference
   - `Get model metadata for ./models/resnet.onnx`
   - `List all available models`
   - `Run inference on model X`

2. **benchmark_specialist** — Performance testing
   - `Benchmark model X with 100 iterations`
   - `Compare performance across models`
   - `Generate benchmark report`

3. **finetune_specialist** — Model training/tuning
   - `Fine-tune model on dataset`
   - `Run training with 10 epochs`
   - `Validate fine-tuned model`

## Example Prompts

### Inference
```
Get the metadata for models/model.onnx and explain the input/output shapes
```

### Benchmarking
```
Run a benchmark on models/model.onnx with 100 iterations and show throughput
```

### Fine-tuning
```
Fine-tune models/base.onnx using the dataset in datasets/train and save to models/finetuned.onnx
```

### Multi-step
```
1. Get info on models/model.onnx
2. Run 50 iterations of benchmarking
3. Compare with previous results
```

## What the Agent Can Do

- **Read/write files** in the project (filesystem toolset)
- **Execute shell commands** (dotnet, python, docker, git, etc.)
- **Reason through complex tasks** (think toolset)
- **Delegate to specialists** (multi-agent routing)

## Advanced: Run as API Server

```bash
docker agent serve agent.yaml --port 8000
```

Then call via HTTP:
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Benchmark models/model.onnx"}],
    "model": "root"
  }'
```

## Integrate with VS Code (MCP)

```bash
docker mcp client connect vscode --profile onnx-agent
```

Then in VS Code chat, switch to Agent mode and ask about ONNX models directly.

## Troubleshooting

### "Model not found"
- Check models/ directory exists: `ls models/`
- Ensure .onnx files are there: `dir models/`

### Agent can't run dotnet
- Make sure you're in C:\AS\ONNX: `cd C:\AS\ONNX`
- Build first: `dotnet build`

### Fine-tuning fails
- Check Python dependencies: `pip install -r finetuner/requirements-finetuning.txt`
- Verify dataset structure: `ls datasets/`

## Next Steps

1. **Add models to ./models/** — Copy real ONNX files
2. **Add datasets to ./datasets/** — For fine-tuning
3. **Ask the agent** — "Analyze models/my_model.onnx and suggest optimizations"
4. **Iterate** — The agent learns your workflow
