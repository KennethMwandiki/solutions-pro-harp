// SPDX-License-Identifier: MIT
using ProHarp.Ingest.Models;

namespace ProHarp.Ingest.Services;

public interface ISink
{
    Task WriteAsync(IEnumerable<AlertRecord> records, CancellationToken ct);
}
