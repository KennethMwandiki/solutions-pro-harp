// SPDX-License-Identifier: MIT
namespace ProHarp.Ingest.Models;

public class AlertRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public DateTimeOffset Timestamp { get; set; }
    public string Topic { get; set; } = "";
    public string AnomalyType { get; set; } = "";
    public double Confidence { get; set; }

    // Auto telemetry
    public double? Lat { get; set; }
    public double? Lon { get; set; }
    public double? Alt { get; set; }
    public string? OrbitId { get; set; }
    public string? FacilityId { get; set; }

    // Provenance
    public string TelemetrySource { get; set; } = "auto";

    // Manual override (if any)
    public double? ManualLat { get; set; }
    public double? ManualLon { get; set; }
    public string? ManualReason { get; set; }

    // Optional bounding box
    public string? BBox { get; set; }
}
