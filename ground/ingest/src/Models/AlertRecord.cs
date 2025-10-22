// SPDX-License-Identifier: MIT
// Models/AlertRecord.cs
namespace ProHarp.Ingest.Models;

public class AlertRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public DateTimeOffset Timestamp { get; set; }
    public string Topic { get; set; } = "";
    public string AnomalyType { get; set; } = "";
    public double Confidence { get; set; }
    public double? Lat { get; set; }
    public double? Lon { get; set; }
    public double? Alt { get; set; }
    public string? OrbitId { get; set; }
    public string? FacilityId { get; set; }
    public string? Address { get; set; }
    public string? AdminRegion { get; set; }
    public string? Country { get; set; }
    public string? BBox { get; set; } // serialized if present
}
