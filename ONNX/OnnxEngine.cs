using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;
using System.Diagnostics;

namespace OnnxInference;

public class OnnxEngine : IDisposable
{
    private readonly InferenceSession _session;
    private readonly string _modelPath;

    public OnnxEngine(string modelPath)
    {
        if (!File.Exists(modelPath))
            throw new FileNotFoundException($"ONNX model not found: {modelPath}");

        _modelPath = modelPath;
        var sessionOptions = new SessionOptions();
        sessionOptions.GraphOptimizationLevel = GraphOptimizationLevel.ORT_ENABLE_ALL;
        _session = new InferenceSession(modelPath, sessionOptions);
    }

    public ModelMetadata GetMetadata()
    {
        var inputShapes = new Dictionary<string, List<long>>();
        foreach (var (key, nodeMetadata) in _session.InputMetadata)
        {
            inputShapes[key] = nodeMetadata.Dimensions.Cast<long>().ToList();
        }

        return new ModelMetadata
        {
            ModelPath = _modelPath,
            InputNodes = _session.InputNames.ToList(),
            OutputNodes = _session.OutputNames.ToList(),
            InputShapes = inputShapes
        };
    }

    public IReadOnlyList<DisposableNamedOnnxValue> Infer(IReadOnlyCollection<NamedOnnxValue> inputs)
    {
        return _session.Run(inputs);
    }

    public BenchmarkResult Benchmark(IReadOnlyCollection<NamedOnnxValue> inputs, int iterations = 100, int warmupRuns = 10)
    {
        // Warmup
        for (int i = 0; i < warmupRuns; i++)
        {
            var results = Infer(inputs);
            foreach (var r in results)
                r.Dispose();
        }

        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            var results = Infer(inputs);
            foreach (var r in results)
                r.Dispose();
        }
        sw.Stop();

        return new BenchmarkResult
        {
            TotalMs = sw.ElapsedMilliseconds,
            IterationCount = iterations,
            AverageMs = (double)sw.ElapsedMilliseconds / iterations,
            ThroughputPerSec = iterations / (sw.ElapsedMilliseconds / 1000.0)
        };
    }

    public void Dispose()
    {
        _session?.Dispose();
    }
}

public class ModelMetadata
{
    public string ModelPath { get; set; } = string.Empty;
    public List<string> InputNodes { get; set; } = new();
    public List<string> OutputNodes { get; set; } = new();
    public Dictionary<string, List<long>> InputShapes { get; set; } = new();
}

public class BenchmarkResult
{
    public long TotalMs { get; set; }
    public int IterationCount { get; set; }
    public double AverageMs { get; set; }
    public double ThroughputPerSec { get; set; }

    public override string ToString()
    {
        return $"""
            Benchmark Results:
            ├─ Iterations: {IterationCount}
            ├─ Total Time: {TotalMs}ms
            ├─ Average: {AverageMs:F4}ms per inference
            └─ Throughput: {ThroughputPerSec:F2} inferences/sec
            """;
    }
}
