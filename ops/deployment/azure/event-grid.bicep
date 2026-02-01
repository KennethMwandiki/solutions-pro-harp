@description('The base name for the Event Grid Topic.')
param baseName string

@description('The location for the Event Grid Topic.')
param location string = resourceGroup().location

resource eventGridTopic 'Microsoft.EventGrid/topics@2022-06-15' = {
  name: '${baseName}-events'
  location: location
  properties: {
    inputSchema: 'EventGridSchema'
    publicNetworkAccess: 'Enabled'
  }
}

output topicEndpoint string = eventGridTopic.properties.endpoint
output topicName string = eventGridTopic.name 

@description('The name of the Logic App to trigger.')
param logicAppName string = ''

resource logicAppSubscription 'Microsoft.EventGrid/topics/eventSubscriptions@2022-06-15' = if (!empty(logicAppName)) {
  parent: eventGridTopic
  name: 'to-logic-app'
  properties: {
    destination: {
      endpointType: 'WebHook'
      properties: {
        endpointUrl: listCallbackUrl(resourceId('Microsoft.Logic/workflows/triggers', logicAppName, 'manual'), '2016-06-01').value
      }
    }
    eventDeliverySchema: 'EventGridSchema'
    filter: {
      isSubjectCaseSensitive: false
      enableAdvancedFilteringOnArrays: true
    }
  }
}
