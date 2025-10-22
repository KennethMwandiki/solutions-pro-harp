// SPDX-License-Identifier: MIT
// Services/SignatureValidator.cs
using System.IdentityModel.Tokens.Jwt;
using Microsoft.IdentityModel.Tokens;
using System.Text;

namespace ProHarp.Ingest.Services;

public class SignatureValidator
{
    private readonly string _secret;
    private readonly TimeSpan _skew;

    public SignatureValidator(IConfiguration cfg)
    {
        _secret = cfg["Security:SigningSecret"] ?? throw new InvalidOperationException("Signing secret missing");
        _skew = TimeSpan.FromSeconds(int.Parse(cfg["Security:AllowedClockSkewSeconds"] ?? "120"));
    }

    public bool Validate(string jwt)
    {
        var handler = new JwtSecurityTokenHandler();
        var parameters = new TokenValidationParameters
        {
            ValidateIssuer = false,
            ValidateAudience = false,
            ValidateLifetime = false, // claims carry ts; enforce skew manually if desired
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_secret)),
            RequireSignedTokens = true
        };
        try
        {
            handler.ValidateToken(jwt, parameters, out var token);
            // Optional: inspect custom claims (ts, hash_hint) and enforce skew
            return true;
        }
        catch
        {
            return false;
        }
    }
}
