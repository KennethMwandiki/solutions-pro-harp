// SPDX-License-Identifier: MIT
using System.Text.Json.Serialization;
namespace ProHarp.Ingest.Models;

public class Alert
{
    [JsonPropertyName("timestamp")]
    public double Timestamp { get; set; }
    [JsonPropertyName("anomaly_type")]
    public string AnomalyType { get; set; } = "";
    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }
    [JsonPropertyName("bbox")]
    public List<double>? BBox { get; set; }
    [JsonPropertyName("geo")]
    public Geo Geo { get; set; } = new();
}
