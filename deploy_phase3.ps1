# Pro-Harp Phase 2 & 3 Deployment Script
# Deploys Cosmos DB, Event Grid, and Azure Functions

$ResourceGroup = "RG-ProHarp"
$Location = "eastus"
$BaseName = "proharp"
$ScriptRoot = $PSScriptRoot

Write-Host "🚀 Starting Pro-Harp Advanced Features Deployment..." -ForegroundColor Cyan
Write-Host "📂 Working Directory: $ScriptRoot" -ForegroundColor DarkGray

# Helper function for retries
function Invoke-AzDeploymentWithRetry {
    param (
        [string]$ResourceGroup,
        [string]$TemplateFile,
        [string]$Name,
        [string]$Parameters,
        [int]$MaxRetries = 3
    )

    $retryCount = 0
    $success = $false

    while (-not $success -and $retryCount -lt $MaxRetries) {
        try {
            Write-Host "Attempting deployment '$Name' (Try $($retryCount + 1)/$MaxRetries)..." -ForegroundColor Yellow
            
            # Using Invoke-Expression or direct execution handling
            az deployment group create `
                --resource-group $ResourceGroup `
                --template-file $TemplateFile `
                --parameters $Parameters `
                --name $Name 2>&1 | Out-String | Write-Host

            if ($LASTEXITCODE -eq 0) {
                $success = $true
                Write-Host "✅ Deployment '$Name' Succeeded!" -ForegroundColor Green
            }
            else {
                throw "Deployment failed with exit code $LASTEXITCODE"
            }
        }
        catch {
            Write-Host "⚠️ Error during deployment: $_" -ForegroundColor Red
            $retryCount++
            if ($retryCount -lt $MaxRetries) {
                Write-Host "Waiting 10 seconds before retry..." -ForegroundColor Gray
                Start-Sleep -Seconds 10
            }
        }
    }

    if (-not $success) {
        Write-Host "❌ Deployment '$Name' failed after $MaxRetries attempts." -ForegroundColor Red
        return $false
    }
    return $true
}

# 0. Connectivity Check
Write-Host "`n🔍 Checking Azure Connectivity..." -ForegroundColor Cyan
try {
    az account show --query name -o tsv | Out-Null
    Write-Host "✅ Connected to Azure." -ForegroundColor Green
}
catch {
    Write-Host "❌ Unable to connect to Azure. Please run 'az login' and check your internet connection." -ForegroundColor Red
    exit 1
}

# 1. Deploy Cosmos DB
Write-Host "`n� Deploying Cosmos DB (Entity Repository)..." -ForegroundColor Cyan
$cosmosSuccess = Invoke-AzDeploymentWithRetry -ResourceGroup $ResourceGroup -TemplateFile "$ScriptRoot/ops/deployment/azure/cosmos-db.bicep" -Name "cosmos-db" -Parameters "baseName=$BaseName"

if ($cosmosSuccess) {
    # Get Connection String
    $CosmosConn = az deployment group show --resource-group $ResourceGroup --name cosmos-db --query properties.outputs.connectionString.value -o tsv
    Write-Host "🔑 Connection String retrieved."
    Write-Host "⚠️ Please update ops/emergency/.env manually if needed." -ForegroundColor Magenta
}
else {
    exit 1
}

# 2. Deploy Event Grid
Write-Host "`n📡 Deploying Event Grid Topic..." -ForegroundColor Cyan
Invoke-AzDeploymentWithRetry -ResourceGroup $ResourceGroup -TemplateFile "$ScriptRoot/ops/deployment/azure/event-grid.bicep" -Name "event-grid" -Parameters "baseName=$BaseName"

# 3. Deploy Function App
Write-Host "`n⚡ Deploying Azure Function App (Real-Time Handlers)..." -ForegroundColor Cyan
Invoke-AzDeploymentWithRetry -ResourceGroup $ResourceGroup -TemplateFile "$ScriptRoot/ops/deployment/azure/function-app.bicep" -Name "function-app" -Parameters "baseName=$BaseName"

Write-Host "`n🎉 Deployment Sequence Complete!" -ForegroundColor Cyan
Write-Host "Next Steps:"
Write-Host "1. Update .env with Cosmos DB Connection String"
Write-Host "2. Deploy Function Code to the new Function App"
