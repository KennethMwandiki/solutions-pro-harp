"""
Cosmos DB Repository for Pro-Harp Entity Management.
Handles persistence of TrackedObjects, Personnel, and Areas to Azure Cosmos DB.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from .data_models import EntityRepository, TrackedObject, Personnel, AreaOfInterest, EntityType, GeoLocation, CriticalityLevel

logger = logging.getLogger(__name__)

class CosmosEntityRepository:
    """Repository implementation using Azure Cosmos DB."""
    
    def __init__(self, connection_string: str, database_name: str = "ProHarpDB", container_name: str = "Entities"):
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database_name = database_name
        self.container_name = container_name
        self._initialize_db()

    def _initialize_db(self):
        """Ensure database and container exist."""
        try:
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/tenant_id"),
                offer_throughput=400 
            )
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise

    def save_entity(self, entity: Any) -> None:
        """Save a single entity (Object, Personnel, or Area) to Cosmos DB."""
        # Convert entity to dictionary suitable for JSON serialization
        # We start with the GeoJSON representation which is our standard interchange format
        # But for Cosmos, we might want a flatter structure or just store the properties + geometry
        
        # Adaptation: Use the GeoJSON properties and add geometry explicitly if needed, 
        # or store exactly the GeoJSON as the document. 
        # Storing GeoJSON directly (Feature format)
        
        if hasattr(entity, 'to_geojson'):
            data = entity.to_geojson()
            # Ensure 'id' and 'tenant_id' are at the root for Cosmos DB indexing/partitioning
            doc = {
                "id": entity.id,
                "tenant_id": entity.tenant_id,
                "entity_type": data["properties"]["entity_type"], # Lift type for easy querying
                **data # Store full GeoJSON structure
            }
            try:
                self.container.upsert_item(doc)
                logger.info(f"Saved entity {entity.id} to Cosmos DB.")
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to save entity {entity.id}: {e}")
                raise
        else:
            raise ValueError("Entity must support to_geojson method")

    def get_entities_by_tenant(self, tenant_id: str) -> EntityRepository:
        """
        Retrieve all entities for a specific tenant and return an EntityRepository instance.
        """
        query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id"
        parameters = [{"name": "@tenant_id", "value": tenant_id}]
        
        repo = EntityRepository()
        
        try:
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False # Targeted query
            )
            
            for item in items:
                self._hydrate_entity(repo, item)
                
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to query entities for tenant {tenant_id}: {e}")
            
        return repo

    def _hydrate_entity(self, repo: EntityRepository, doc: Dict[str, Any]):
        """Convert a Cosmos DB document back to a domain entity and add to repo."""
        # The document is essentially the GeoJSON Feature with some extra root keys
        # We need to reconstruct the objects based on 'entity_type'
        
        props = doc["properties"]
        geom = doc["geometry"]
        entity_type = props.get("entity_type")
        
        try:
            if entity_type == EntityType.OBJECT.value:
                coords = geom["coordinates"]
                loc = GeoLocation(lat=coords[1], lon=coords[0], alt=coords[2] if len(coords) > 2 else None)
                obj = TrackedObject(
                    id=props["id"],
                    name=props["name"],
                    location=loc,
                    criticality=CriticalityLevel[props["criticality"]],
                    vulnerability_score=props["vulnerability_score"],
                    asset_value=props["asset_value"],
                    dependencies=props.get("dependencies", []),
                    tenant_id=props.get("tenant_id", "default_tenant")
                )
                repo.add_object(obj)
                
            elif entity_type == EntityType.PERSONNEL.value:
                coords = geom["coordinates"]
                loc = GeoLocation(lat=coords[1], lon=coords[0], alt=coords[2] if len(coords) > 2 else None)
                person = Personnel(
                    id=props["id"],
                    name=props["name"],
                    role=props["role"],
                    location=loc,
                    criticality=CriticalityLevel[props["criticality"]],
                    on_duty=props["on_duty"],
                    safety_clearances=props.get("safety_clearances", []),
                    contact_phone=props.get("contact_phone"),
                    contact_email=props.get("contact_email"),
                    tenant_id=props.get("tenant_id", "default_tenant")
                )
                repo.add_personnel(person)

            elif entity_type == EntityType.AREA.value:
                # Area logic
                area = AreaOfInterest(
                    id=props["id"],
                    name=props["name"],
                    polygon_coords=geom["coordinates"][0], # Polygon coords are nested [[x,y],...]
                    population_density=props["population_density"],
                    historical_incident_count=props["historical_incident_count"],
                    strategic_importance=CriticalityLevel[props["strategic_importance"]],
                    available_resources=props.get("available_resources", []),
                    tenant_id=props.get("tenant_id", "default_tenant")
                )
                repo.add_area(area)
                
        except Exception as e:
            logger.warning(f"Failed to hydrate entity {doc.get('id')}: {e}")

