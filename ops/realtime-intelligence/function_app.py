import azure.functions as func
import logging
import json
import os
import uuid
from azure.cosmos import CosmosClient, PartitionKey

app = func.FunctionApp()

def get_cosmos_container():
    """Helper to get Cosmos DB container client."""
    conn_str = os.environ.get("COSMOS_DB_CONNECTION_STRING")
    if not conn_str:
        logging.error("COSMOS_DB_CONNECTION_STRING not set.")
        return None
    
    try:
        client = CosmosClient.from_connection_string(conn_str)
        # Using the same database and container as the rest of the app
        database = client.get_database_client("ProHarpDB")
        container = database.get_container_client("Entities")
        return container
    except Exception as e:
        logging.error(f"Failed to connect to Cosmos DB: {e}")
        return None

@app.event_grid_trigger(arg_name="event")
def proharp_process_anomaly(event: func.EventGridEvent):
    """
    Process Orbital Anomaly events and save to Cosmos DB.
    """
    logging.info(f"Received Event Grid event: {event.id}, type: {event.event_type}")
    
    data = event.get_json()
    
    # Construct Incident Entity
    # We map the event to a persisted entity format (Incident/ThreatEvent)
    incident_id = str(uuid.uuid4())
    
    incident_doc = {
        "id": incident_id,
        "tenant_id": "default_tenant", # Could extract from subject if encoded
        "entity_type": "incident",     # Differentiator from objects/areas
        "event_id": event.id,
        "event_time": event.event_time.isoformat() if event.event_time else None,
        "subject": event.subject,
        "topic": event.topic,
        "data_version": event.data_version,
        "severity": data.get("severity", "unknown"),
        "confidence": data.get("confidence", 0.0),
        "message": data.get("message", ""),
        "coordinates": data.get("coordinates", {}),
        "raw_data": data,
        "processed_at": str(datetime.datetime.utcnow())
    }

    # Save to Cosmos DB
    container = get_cosmos_container()
    if container:
        try:
            container.upsert_item(incident_doc)
            logging.info(f"Saved incident {incident_id} to Cosmos DB.")
        except Exception as e:
            logging.error(f"Failed to upsert incident: {e}")
    else:
        logging.warning("Skipping Cosmos DB save (client not available).")

    logging.info("Successfully processed anomaly event.")
