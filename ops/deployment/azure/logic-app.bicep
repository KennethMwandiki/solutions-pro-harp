@description('Location for all resources.')
param location string = resourceGroup().location

@description('Prefix for resource names.')
param baseName string

resource lockdownLogicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: '${baseName}-lockdown-playbook'
  location: location
  properties: {
    state: 'Enabled'
    definition: {
        '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
        'contentVersion': '1.0.0.0'
        'triggers': {
            'manual': {
                'type': 'Request'
                'kind': 'Http'
                'inputs': {
                    'schema': {
                        'properties': {
                            'AlertId': { 'type': 'string' }
                            'AnomalyType': { 'type': 'string' }
                            'Confidence': { 'type': 'number' }
                            'FacilityId': { 'type': 'string' }
                        }
                        'type': 'object'
                    }
                }
            }
        }
        'actions': {
            'Condition': {
                'type': 'If'
                'expression': {
                    'and': [
                        {
                            'greater': [
                                '@triggerBody()?[\'Confidence\']'
                                0.9
                            ]
                        }
                    ]
                }
                'actions': {
                    'IoT_Action': {
                        'type': 'Http'
                        'inputs': {
                            'method': 'POST'
                            'uri': 'https://api.facility-iot.local/lockdown'
                            'body': {
                                'facility': '@triggerBody()?[\'FacilityId\']'
                            }
                        }
                    }
                }
            }
        }
    }
  }
}
