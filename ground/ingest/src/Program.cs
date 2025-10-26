// SPDX-License-Identifier: MIT
// Program.cs
using Microsoft.AspNetCore.Mvc;
using ProHarp.Ingest.Models;
using ProHarp.Ingest.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<SignatureValidator>();
builder.Services.AddHttpClient<MapsEnrichment>();
builder.Services.AddSingleton<SentinelWriter>();

var app = builder.Build();

app.MapPost("/ingest", async (
    [FromBody] AlertEnvelope envelope,
    SignatureValidator sig,
    MapsEnrichment maps,
    SentinelWriter sink,
    IConfiguration cfg,
    CancellationToken ct) =>
{
    // Size guard
    var maxKb = int.Parse(cfg["Ingest:MaxPayloadKb"] ?? "64");
    var sizeKb = System.Text.Encoding.UTF8.GetByteCount(System.Text.Json.JsonSerializer.Serialize(envelope)) / 1024.0;
    if (sizeKb > maxKb) return Results.BadRequest(new { error = "Payload too large" });

    // Signature validation
    if (!sig.Validate(envelope.Signature))
        return Results.Unauthorized();

    // Basic schema checks
    if (envelope.Payload?.Alerts is null || envelope.Payload.Alerts.Count == 0)
        return Results.BadRequest(new { error = "No alerts" });

    var records = new List<AlertRecord>();
    foreach (var a in envelope.Payload.Alerts)
    {
        var (address, admin, country) = await maps.ReverseAsync(a.Geo.Latitude, a.Geo.Longitude, ct);

        var rec = new AlertRecord
        {
            Timestamp = DateTimeOffset.FromUnixTimeSeconds((long)a.Timestamp),
            Topic = envelope.Payload.Topic,
            AnomalyType = a.AnomalyType,
            Confidence = a.Confidence,
            Lat = a.Geo.Latitude,
            Lon = a.Geo.Longitude,
            Alt = a.Geo.Altitude,
            OrbitId = a.Geo.OrbitId,
            FacilityId = a.Geo.FacilityId,
            TelemetrySource = a.Geo.TelemetrySource,
            ManualLat = a.Geo.ManualOverride?.Latitude,
            ManualLon = a.Geo.ManualOverride?.Longitude,
            ManualReason = a.Geo.ManualOverride?.Reason,
            BBox = a.BBox is null ? null : string.Join(",", a.BBox)
        };
        records.Add(rec);
    }

    await sink.WriteAsync(records, ct);
    return Results.Ok(new { accepted = records.Count });
});

app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));

app.Run();
