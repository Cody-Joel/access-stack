using OnnxInference;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

class Program
{
    static async Task Main(string[] args)
    {
        if (args.Length == 0)
        {
            PrintUsage();
            return;
        }

        try
        {
            string command = args[0];
            string[] commandArgs = args.Skip(1).ToArray();

            switch (command.ToLower())
            {
                case "info":
                    HandleInfo(commandArgs);
                    break;
                case "benchmark":
                    HandleBenchmark(commandArgs);
                    break;
                case "infer":
                    HandleInfer(commandArgs);
                    break;
                default:
                    Console.WriteLine($"Unknown command: {command}");
                    PrintUsage();
                    break;
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            Environment.Exit(1);
        }
    }

    static void HandleInfo(string[] args)
    {
        string? modelPath = null;
        for (int i = 0; i < args.Length; i++)
        {
            if ((args[i] == "-m" || args[i] == "--model") && i + 1 < args.Length)
                modelPath = args[i + 1];
        }

        if (string.IsNullOrEmpty(modelPath))
        {
            Console.Error.WriteLine("Usage: onnx info -m <model_path>");
            Environment.Exit(1);
        }

        using var engine = new OnnxEngine(modelPath);
        var metadata = engine.GetMetadata();

        Console.WriteLine("\n=== Model Information ===");
        Console.WriteLine($"Model: {metadata.ModelPath}");
        Console.WriteLine($"\nInputs:");
        foreach (var input in metadata.InputNodes)
        {
            var shape = string.Join(", ", metadata.InputShapes[input]);
            Console.WriteLine($"  └─ {input}: [{shape}]");
        }
        Console.WriteLine($"\nOutputs:");
        foreach (var output in metadata.OutputNodes)
        {
            Console.WriteLine($"  └─ {output}");
        }
    }

    static void HandleBenchmark(string[] args)
    {
        string? modelPath = null;
        int iterations = 100;
        int warmup = 10;

        for (int i = 0; i < args.Length; i++)
        {
            if ((args[i] == "-m" || args[i] == "--model") && i + 1 < args.Length)
                modelPath = args[i + 1];
            else if ((args[i] == "-i" || args[i] == "--iterations") && i + 1 < args.Length)
                int.TryParse(args[i + 1], out iterations);
            else if ((args[i] == "-w" || args[i] == "--warmup") && i + 1 < args.Length)
                int.TryParse(args[i + 1], out warmup);
        }

        if (string.IsNullOrEmpty(modelPath))
        {
            Console.Error.WriteLine("Usage: onnx benchmark -m <model_path> [-i iterations] [-w warmup]");
            Environment.Exit(1);
        }

        using var engine = new OnnxEngine(modelPath);
        var metadata = engine.GetMetadata();

        Console.WriteLine($"\n=== Benchmarking {modelPath} ===");
        Console.WriteLine($"Creating dummy input tensors based on model shapes...");

        var inputs = new List<NamedOnnxValue>();

        foreach (var (inputName, shape) in metadata.InputShapes)
        {
            var dimensions = shape.Select(x => (int)x).ToArray();
            var tensor = new DenseTensor<float>(dimensions);
            var random = new Random(42);
            for (int i = 0; i < tensor.Length; i++)
                tensor.SetValue(i, (float)random.NextDouble());

            inputs.Add(NamedOnnxValue.CreateFromTensor(inputName, tensor));
        }

        var result = engine.Benchmark(inputs, iterations, warmup);
        Console.WriteLine(result);
    }

    static void HandleInfer(string[] args)
    {
        string? modelPath = null;
        for (int i = 0; i < args.Length; i++)
        {
            if ((args[i] == "-m" || args[i] == "--model") && i + 1 < args.Length)
                modelPath = args[i + 1];
        }

        if (string.IsNullOrEmpty(modelPath))
        {
            Console.Error.WriteLine("Usage: onnx infer -m <model_path>");
            Environment.Exit(1);
        }

        Console.WriteLine($"Inference endpoint would run on: {modelPath}");
        Console.WriteLine("(Implement custom inference logic here)");
    }

    static void PrintUsage()
    {
        Console.WriteLine("""
            ONNX Inference & Benchmarking Tool
            
            Commands:
              info      Display model metadata
              benchmark Run inference benchmark
              infer     Run single inference
            
            Examples:
              onnx info -m model.onnx
              onnx benchmark -m model.onnx -i 100 -w 10
              onnx infer -m model.onnx
            """);
    }
}
