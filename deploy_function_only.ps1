# Pro-Harp Function App Deployment Script
# Targeted deployment retry for Function App

$ResourceGroup = "RG-ProHarp"
$BaseName = "proharp"
$ScriptRoot = $PSScriptRoot

Write-Host "🚀 Retrying Function App Deployment..." -ForegroundColor Cyan

# Deploy Function App
Write-Host "`n⚡ Deploying Azure Function App..." -ForegroundColor Yellow
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$ScriptRoot/ops/deployment/azure/function-app.bicep" `
    --parameters baseName=$BaseName `
    --name function-app-retry

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Function App Deployed Successfully" -ForegroundColor Green
    Write-Host "Next Step: Deploy the Function code using:"
    Write-Host "cd solutions-pro-harp"
    Write-Host "az functionapp deployment source config-zip --resource-group $ResourceGroup --name ${BaseName}-func --src function_app.zip"
}
else {
    Write-Host "❌ Function App Deployment Failed" -ForegroundColor Red
}
