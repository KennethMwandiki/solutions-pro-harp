// SPDX-License-Identifier: MIT
// Services/SignatureValidator.cs
using Microsoft.IdentityModel.JsonWebTokens;
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
        _skew = TimeSpan.FromSeconds(cfg.GetValue<int>("Security:AllowedClockSkewSeconds", 120));
    }

    public bool Validate(string jwt)
    {
        var handler = new JsonWebTokenHandler();
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
            var result = handler.ValidateToken(jwt, parameters);
            return result.IsValid;
        }
        catch
        {
            return false;
        }
    }
}
