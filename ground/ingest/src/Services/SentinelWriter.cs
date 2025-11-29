// SPDX-License-Identifier: MIT
// Services/SentinelWriter.cs
using ProHarp.Ingest.Models;
using System.Text.Json;

namespace ProHarp.Ingest.Services;

public class SentinelWriter : ISink
{
    private const string LogFile = "sentinel_output.log";
    private readonly object _lock = new();

    public Task WriteAsync(IEnumerable<AlertRecord> records, CancellationToken ct)
    {
        lock (_lock)
        {
            foreach (var r in records)
            {
                var json = JsonSerializer.Serialize(r);
                File.AppendAllText(LogFile, json + Environment.NewLine);
            }
        }
        return Task.CompletedTask;
    }
}
