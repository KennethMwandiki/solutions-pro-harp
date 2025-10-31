// SPDX-License-Identifier: MIT
// Services/SentinelWriter.cs
using ProHarp.Ingest.Models;
using System.Text.Json;

namespace ProHarp.Ingest.Services;

public class SentinelWriter : ISink
{
    // Replace with actual Event Hub / Log Analytics client
    public Task WriteAsync(IEnumerable<AlertRecord> records, CancellationToken ct)
    {
        foreach (var r in records)
        {
            Console.WriteLine(JsonSerializer.Serialize(r));
        }
        return Task.CompletedTask;
    }
}
