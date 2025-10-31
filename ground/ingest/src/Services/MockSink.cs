// SPDX-License-Identifier: MIT
using ProHarp.Ingest.Models;
using System.Collections.Concurrent;

namespace ProHarp.Ingest.Services;

public class MockSink : ISink
{
    private readonly ILogger<MockSink> _logger;
    public readonly ConcurrentQueue<AlertRecord> Records = new();

    public MockSink(ILogger<MockSink> logger)
    {
        _logger = logger;
    }

    public Task WriteAsync(IEnumerable<AlertRecord> records, CancellationToken ct)
    {
        foreach (var rec in records)
        {
            Records.Enqueue(rec);
            _logger.LogInformation("MockSink received record: {recordJson}", System.Text.Json.JsonSerializer.Serialize(rec));
        }
        return Task.CompletedTask;
    }
}
