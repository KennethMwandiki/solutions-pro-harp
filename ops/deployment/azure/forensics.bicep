@description('Location for all resources.')
param location string = resourceGroup().location

@description('Prefix for resource names.')
param baseName string

// Forensics Storage Account
resource forensicsStorage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: '${baseName}forensics'
  location: location
  sku: {
    name: 'Standard_GRS' // Geo-redundant for high durability
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    isVersioningEnabled: true
  }
}

// Blob Service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2021-09-01' = {
  parent: forensicsStorage
  name: 'default'
  properties: {
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 30
    }
  }
}

// Immutable Container (WORM)
resource evidenceContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-09-01' = {
  parent: blobService
  name: 'evidence-locker'
  properties: {
    publicAccess: 'None'
    immutableStorageWithVersioning: {
      enabled: true
    }
  }
}

// Time-based retention policy (WORM)
// Note: Locked policy requires careful handling (cannot be deleted). 
// using Unlocked for initial deployment to allow testing/deletion.
resource retentionPolicy 'Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies@2021-09-01' = {
  parent: evidenceContainer
  name: 'default'
  properties: {
    immutabilityPeriodSinceCreationInDays: 365
    allowProtectedAppendWrites: true // Allow new blocks, no overwrite
    state: 'Unlocked' // Switch to 'Locked' for production WORM compliance
  }
}

output storageAccountName string = forensicsStorage.name
output containerName string = evidenceContainer.name
