@description('The base name for the Function App resources.')
param baseName string

@description('The location for resources.')
param location string = resourceGroup().location

@description('The runtime stack for the Function App.')
param runtime string = 'python'

@description('The storage account connection string.')
// In a real scenario we'd create storage or pass keys, but for simplicity we create one here.
// param storageAccountConnectionString string 

var functionAppName = '${baseName}-func'
var hostingPlanName = '${baseName}-plan'
// Storage names must be < 24 chars. Base 7 + fnst 4 + unique 13 = 24.
var storageAccountName = toLower('${take(baseName, 7)}fnst${take(uniqueString(resourceGroup().id), 11)}')

resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

resource hostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: hostingPlanName
  location: location
  sku: {
    name: 'Y1' // Consumption plan
    tier: 'Dynamic'
  }
  properties: {}
}

resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.10'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: runtime
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          // Ideally we link to existing App Insights
          value: '' 
        }
      ]
    }
    httpsOnly: true
  }
}

output functionAppName string = functionApp.name
output defaultHostName string = functionApp.properties.defaultHostName
