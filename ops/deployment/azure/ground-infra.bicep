@description('Location for all resources.')
param location string = resourceGroup().location

@description('Prefix for resource names.')
param baseName string = 'proharp-${uniqueString(resourceGroup().id)}'

// 1. Log Analytics Workspace (Sentinel)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: '${baseName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

// 2. Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2021-09-01' = {
  name: replace('${baseName}acr', '-', '')
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// 3. Azure Maps Account
resource maps 'Microsoft.Maps/accounts@2021-02-01' = {
  name: '${baseName}-maps'
  location: location
  sku: {
    name: 'G2'
  }
  kind: 'Gen2'
}

// 4. Key Vault
resource kv 'Microsoft.KeyVault/vaults@2021-10-01' = {
  name: '${baseName}-kv'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
  }
}

// 5. Container Apps Environment
resource caEnv 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: '${baseName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// 6. Ground Ingest Container App
resource groundApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: 'ground-ingest'
  location: location
  properties: {
    managedEnvironmentId: caEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
      }
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'ground-ingest'
          image: '${acr.properties.loginServer}/ground-ingest:latest'
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'AzureMaps:SubscriptionKey'
              value: maps.listKeys().primaryKey // In 'prod', use Key Vault reference
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
    }
  }
}

output ingestUrl string = groundApp.properties.configuration.ingress.fqdn
