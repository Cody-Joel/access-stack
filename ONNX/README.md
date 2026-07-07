# ONNX Inference & Benchmarking Tool

C# native inference engine with ONNX Runtime support for model inference and benchmarking.

## Quick Start (Native)

```bash
cd C:\AS\ONNX
dotnet build
dotnet run -- info -m path/to/model.onnx
dotnet run -- benchmark -m path/to/model.onnx -i 100
```

## Commands

- **info**: Display model metadata (inputs, outputs, shapes)
- **benchmark**: Run inference benchmark with warmup and iteration counts
- **infer**: Run single inference (extensible for custom logic)

## Docker

```bash
docker build -t onnx-inference .
docker compose up
```

## Project Structure

```
ONNX/
├── OnnxInference.csproj      # C# project file
├── OnnxEngine.cs             # Core inference engine
├── Program.cs                # CLI entry point
├── Dockerfile                # Multi-stage C# build
├── docker-compose.yml        # Compose with Python support
├── models/                   # ONNX model directory
├── results/                  # Benchmark output
└── finetuner/                # Python fine-tuning (coming)
```

## Requirements

- .NET 8 SDK (native)
- Docker (for containerized runs)
- ONNX models in `models/` directory

## Fine-tuning Setup

Python fine-tuning support coming in next phase.
