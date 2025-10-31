// SPDX-License-Identifier: MIT
namespace ProHarp.Ingest.Models;

public class Geo
{
    // Auto telemetry (from orbital SDK)
    public double? Latitude { get; set; }
    public double? Longitude { get; set; }
    public double? Altitude { get; set; }
    public string? OrbitId { get; set; }
    public string? FacilityId { get; set; }

    // Provenance
    public string TelemetrySource { get; set; } = "auto"; // "auto" or "manual"

    // Manual override (optional)
    public ManualOverride? ManualOverride { get; set; }
}

public class ManualOverride
{
    public bool Enabled { get; set; }
    public double? Latitude { get; set; }
    public double? Longitude { get; set; }
    public string? Reason { get; set; }
}