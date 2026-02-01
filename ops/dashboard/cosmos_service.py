import os
import streamlit as st
from azure.cosmos import CosmosClient, PartitionKey
import datetime

# Cache the connection to avoid recreating it on every rerun
@st.cache_resource
def get_cosmos_client():
    conn_str = os.environ.get("COSMOS_DB_CONNECTION_STRING")
    if not conn_str:
        return None
    try:
        return CosmosClient.from_connection_string(conn_str)
    except Exception as e:
        print(f"Cosmos Init Error: {e}")
        return None

class CosmosService:
    def __init__(self):
        self.client = get_cosmos_client()
        if self.client:
            self.database = self.client.get_database_client("ProHarpDB")
            self.container = self.database.get_container_client("Entities")

    def get_recent_incidents(self, limit=10):
        if not self.client:
            return []
            
        # Query for incidents, sorted by event_time desc
        query = """
        SELECT * FROM c 
        WHERE c.entity_type = 'incident' 
        ORDER BY c.event_time DESC
        OFFSET 0 LIMIT @limit
        """
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=[{"name": "@limit", "value": limit}],
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Query Error: {e}")
            return []

    def get_stats(self):
        # Quick aggregation example
        if not self.client:
            return {}
            
        stats = {
            "total_incidents": 0,
            "high_severity": 0
        }
        
        try:
            # Count incidents
            query_total = "SELECT VALUE COUNT(1) FROM c WHERE c.entity_type = 'incident'"
            total_res = list(self.container.query_items(query=query_total, enable_cross_partition_query=True))
            if total_res:
                stats["total_incidents"] = total_res[0]
                
            # Count high severity
            query_high = "SELECT VALUE COUNT(1) FROM c WHERE c.entity_type = 'incident' AND (c.severity = 'high' OR c.severity = 'critical')"
            high_res = list(self.container.query_items(query=query_high, enable_cross_partition_query=True))
            if high_res:
                stats["high_severity"] = high_res[0]
                
        except Exception as e:
            print(f"Stats Error: {e}")
            
        return stats
