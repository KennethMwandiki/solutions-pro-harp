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
    if (!sig.Validate(envelope.signature))
        return Results.Unauthorized();

    // Basic schema checks
    if (envelope.payload?.alerts is null || envelope.payload.alerts.Count == 0)
        return Results.BadRequest(new { error = "No alerts" });

    var records = new List<AlertRecord>();
    foreach (var a in envelope.payload.alerts)
    {
        var (address, admin, country) = await maps.ReverseAsync(a.geo.latitude, a.geo.longitude, ct);

        var rec = new AlertRecord
        {
            Timestamp = DateTimeOffset.FromUnixTimeSeconds((long)a.timestamp),
            Topic = envelope.payload.topic,
            AnomalyType = a.anomaly_type,
            Confidence = a.confidence,
            Lat = a.geo.latitude,
            Lon = a.geo.longitude,
            Alt = a.geo.altitude,
            OrbitId = a.geo.orbitId,
            FacilityId = a.geo.facility_id,
            Address = address,
            AdminRegion = admin,
            Country = country,
            BBox = a.bbox is null ? null : string.Join(",", a.bbox)
        };
        records.Add(rec);
    }

    await sink.WriteAsync(records, ct);
    return Results.Ok(new { accepted = records.Count });
});

app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));

app.Run();
