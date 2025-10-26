// SPDX-License-Identifier: MIT
using System.Text.Json.Serialization;
namespace ProHarp.Ingest.Models;

public class Geo
{
    // Auto telemetry (from orbital SDK)
    [JsonPropertyName("latitude")]
    public double? Latitude { get; set; }
    [JsonPropertyName("longitude")]
    public double? Longitude { get; set; }
    [JsonPropertyName("altitude")]
    public double? Altitude { get; set; }
    [JsonPropertyName("orbitId")]
    public string? OrbitId { get; set; }
    [JsonPropertyName("facility_id")]
    public string? FacilityId { get; set; }

    // Provenance
    [JsonPropertyName("telemetry_source")]
    public string TelemetrySource { get; set; } = "auto"; // "auto" or "manual"

    // Manual override (optional)
    [JsonPropertyName("manual_override")]
    public ManualOverride? ManualOverride { get; set; }
}

public class ManualOverride
{
    [JsonPropertyName("enabled")]
    public bool Enabled { get; set; }
    [JsonPropertyName("latitude")]
    public double? Latitude { get; set; }
    [JsonPropertyName("longitude")]
    public double? Longitude { get; set; }
    [JsonPropertyName("reason")]
    public string? Reason { get; set; }
}
