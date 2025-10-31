// SPDX-License-Identifier: MIT
namespace ProHarp.Ingest.Models;

public class Alert
{
    public double Timestamp { get; set; }
    public string AnomalyType { get; set; } = "";
    public double Confidence { get; set; }
    public List<double>? BBox { get; set; }
    public Geo Geo { get; set; } = new();
}