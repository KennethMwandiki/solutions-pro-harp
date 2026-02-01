# Pro-Harp Function App Deployment (Imperative)
# Usage: ./deploy_function_imperative.ps1

# Suppress Python warnings from Azure CLI
$env:PYTHONWARNINGS = "ignore"

$ResourceGroup = "RG-ProHarp"
$Location = "eastus"
$BaseName = "proharp"

# Generate unique storage name (alphanumeric, <24 chars)
$RandomSuffix = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
$StorageName = "proharpfn$RandomSuffix"
$AppName = "$BaseName-func-app"

Write-Host "🚀 Starting Imperative Function App Deployment..." -ForegroundColor Cyan
Write-Host "Resource Group: $ResourceGroup"
Write-Host "Storage Account: $StorageName"
Write-Host "Function App: $AppName"

# 1. Create Storage Account
Write-Host "`n📦 Creating Storage Account ($StorageName)..." -ForegroundColor Yellow
az storage account create `
    --name $StorageName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2

if ($LASTEXITCODE -ne 0) { Write-Error "Storage creation failed"; exit 1 }

# 2. Create Function App (With Implicit Consumption Plan)
# We use --consumption-plan-location to let Azure create the plan implicitly
Write-Host "`n⚡ Creating Function App ($AppName)..." -ForegroundColor Yellow
az functionapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --storage-account $StorageName `
    --consumption-plan-location $Location `
    --runtime python `
    --runtime-version 3.10 `
    --functions-version 4 `
    --os-type Linux 2>&1 | Out-String | Write-Host

if ($LASTEXITCODE -ne 0) { Write-Error "Function App creation failed"; exit 1 }

Write-Host "`n✅ Function App Infrastructure Deployed!" -ForegroundColor Green

# 3. Deploy Code
Write-Host "`n📤 Deploying Function Code..." -ForegroundColor Yellow
# Ensure we are in the right directory or use absolute path to zip
$ScriptPath = $PSScriptRoot
$ZipPath = Join-Path $ScriptPath "function_app.zip"

if (Test-Path $ZipPath) {
    az functionapp deployment source config-zip `
        --resource-group $ResourceGroup `
        --name $AppName `
        --src $ZipPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Code Deployed Successfully!" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Code Deployment Failed" -ForegroundColor Red
    }
}
else {
    Write-Host "⚠️ function_app.zip not found at $ZipPath. Please zip and deploy manually." -ForegroundColor Yellow
}
