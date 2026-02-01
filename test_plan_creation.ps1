# Test script to isolate Plan creation failure and suppress warnings
$env:PYTHONWARNINGS = "ignore"

$ResourceGroup = "RG-ProHarp"
$Location = "eastus"
$BaseName = "proharp"
$PlanName = "$BaseName-plan-test"

Write-Host "Testing SKU 'Y1' for Linux Plan..."
az functionapp plan create `
    --name $PlanName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Y1 `
    --is-linux `
    --debug 2>&1 | Select-String "Invalid sku" -Context 0, 5

Write-Host "Test Complete."
