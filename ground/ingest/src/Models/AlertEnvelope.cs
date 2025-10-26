// SPDX-License-Identifier: MIT
// Models/AlertEnvelope.cs
using System.Text.Json.Serialization;
namespace ProHarp.Ingest.Models;

public class AlertEnvelope
{
    [JsonPropertyName("payload")]
    public required Payload Payload { get; set; }
    [JsonPropertyName("signature")]
    public required string Signature { get; set; }
}

public class Payload
{
    [JsonPropertyName("topic")]
    public required string Topic { get; set; }
    [JsonPropertyName("count")]
    public int Count { get; set; }
    [JsonPropertyName("alerts")]
    public required List<Alert> Alerts { get; set; }
}
