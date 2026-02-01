#disable-next-line outputs-should-not-contain-secrets
@description('The base name for the Cosmos DB account.')
param baseName string

@description('The location for the Cosmos DB account.')
param location string = resourceGroup().location

@description('The name of the database.')
param databaseName string = 'ProHarpDB'

@description('The name of the container.')
param containerName string = 'Entities'

resource account 'Microsoft.DocumentDB/databaseAccounts@2022-05-15' = {
  name: '${baseName}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2022-05-15' = {
  parent: account
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2022-05-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          '/tenant_id'
        ]
        kind: 'Hash'
      }
    }
  }
}

output connectionString string = account.listConnectionStrings().connectionStrings[0].connectionString
output accountName string = account.name
