// SPDX-License-Identifier: MIT
// Program.cs
using Microsoft.AspNetCore.Mvc;
using ProHarp.Ingest.Models;
using ProHarp.Ingest.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<SignatureValidator>();
builder.Services.AddHttpClient<MapsEnrichment>();

if (builder.Environment.IsDevelopment())
{
    builder.Services.AddSingleton<ISink, MockSink>();
}
else
{
    builder.Services.AddSingleton<ISink, SentinelWriter>();
}

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.Logger.LogInformation("Using MockSink for development.");
    app.MapGet("/debug/logs", (ISink sink) =>
    {
        if (sink is MockSink mock)
        {
            return Results.Ok(mock.Records);
        }
        return Results.NotFound("Not in development mode");
    });
}


app.MapPost("/ingest", async (
    [FromBody] AlertEnvelope envelope,
    SignatureValidator sig,
    MapsEnrichment maps,
    ISink sink,
    IConfiguration cfg,
    ILogger<Program> logger, // Added ILogger
    CancellationToken ct) =>
{
    // Size guard
    var maxKb = cfg.GetValue<int>("Ingest:MaxPayloadKb", 64);
    var sizeKb = System.Text.Encoding.UTF8.GetByteCount(System.Text.Json.JsonSerializer.Serialize(envelope)) / 1024.0;
    if (sizeKb > maxKb) return Results.BadRequest(new { error = "Payload too large" });

    // Signature validation
    if (!sig.Validate(envelope.Signature))
        return Results.Unauthorized();

    // Basic schema checks
    if (envelope.Payload?.Alerts is null || envelope.Payload.Alerts.Count == 0)
        return Results.BadRequest(new { error = "No alerts" });

    var records = new List<AlertRecord>();
    try
    {
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
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Error processing ingest request");
        return Results.Problem("An error occurred while processing the request.");
    }
});

app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));

app.Run();
