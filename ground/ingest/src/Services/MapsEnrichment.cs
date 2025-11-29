// SPDX-License-Identifier: MIT
// Services/MapsEnrichment.cs
using System.Net.Http.Json;
using ProHarp.Ingest.Models;

namespace ProHarp.Ingest.Services;

public class MapsEnrichment
{
    private readonly HttpClient _http;
    private readonly IConfiguration _cfg;

    public MapsEnrichment(HttpClient http, IConfiguration cfg)
    {
        _http = http;
        _cfg = cfg;
    }

    public async Task<(string? address, string? admin, string? country)> ReverseAsync(double? lat, double? lon, CancellationToken ct)
    {
        if (lat is null || lon is null) return (null, null, null);

        var baseUrl = _cfg["AzureMaps:BaseUrl"]!;
        var key = _cfg["AzureMaps:SubscriptionKey"];

        if (string.IsNullOrEmpty(key) || key == "replace-or-use-managed-identity")
        {
            return (null, null, null);
        }

        var url = $"{baseUrl}?api-version=1.0&query={lat},{lon}&subscription-key={key}";

        var res = await _http.GetFromJsonAsync<AzureMapsReverseResponse>(url, ct);
        var result = res?.addresses?.FirstOrDefault();
        var address = result?.address?.freeformAddress;
        var admin = result?.address?.countrySubdivision;
        var country = result?.address?.countryCode;
        return (address, admin, country);
    }

    // Minimal DTO for Azure Maps response
    private class AzureMapsReverseResponse
    {
        public List<Item>? addresses { get; set; }
    }
    private class Item { public Address? address { get; set; } }
    private class Address
    {
        public string? freeformAddress { get; set; }
        public string? countrySubdivision { get; set; }
        public string? countryCode { get; set; }
    }
}
