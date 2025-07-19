# ecs.py
# This file contains the core Entity-Component-System World class.

class World:
    """Manages all entities, components, and systems."""
    def __init__(self):
        self.entities = {}
        self.components = {}
        self.entity_id_counter = 0

    def create_entity(self):
        """Creates a new entity ID."""
        entity_id = self.entity_id_counter
        self.entities[entity_id] = {}
        self.entity_id_counter += 1
        return entity_id

    def add_component(self, entity_id, component):
        """Adds a component to a given entity."""
        component_name = component.__class__.__name__
        self.entities[entity_id][component_name] = component
        if component_name not in self.components:
            self.components[component_name] = set()
        self.components[component_name].add(entity_id)

    def get_component(self, entity_id, component_name):
        """Retrieves a component from an entity."""
        return self.entities.get(entity_id, {}).get(component_name)

    def get_entities_with(self, *component_names):
        """Returns a set of entity IDs that have all the specified components."""
        try:
            return set.intersection(*(self.components[name] for name in component_names))
        except (KeyError, TypeError):
            return set()
    
    def remove_entity(self, entity_id):
        """Removes an entity and all its components from the world."""
        if entity_id in self.entities:
            for component_name in list(self.entities[entity_id]):
                if component_name in self.components:
                    self.components[component_name].discard(entity_id)
            del self.entities[entity_id]
