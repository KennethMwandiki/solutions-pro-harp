// SPDX-License-Identifier: MIT
// Models/AlertEnvelope.cs
namespace ProHarp.Ingest.Models;

public class AlertEnvelope
{
    public required Payload payload { get; set; }
    public required string signature { get; set; }
}

public class Payload
{
    public required string topic { get; set; }
    public int count { get; set; }
    public required List<Alert> alerts { get; set; }
}

public class Alert
{
    public double timestamp { get; set; }
    public string anomaly_type { get; set; } = "";
    public double confidence { get; set; }
    public List<double>? bbox { get; set; }
    public Geo geo { get; set; } = new();
}

public class Geo
{
    public double? latitude { get; set; }
    public double? longitude { get; set; }
    public double? altitude { get; set; }
    public string? orbitId { get; set; }
    public string? facility_id { get; set; }
}
