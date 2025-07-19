# dungeon.py
# This file contains classes related to the dungeon map structure and generation.

import random
from tables import MAPPING_TABLE, DOOR_TABLE
from room_templates import TEMPLATES
from config import YELLOW, RED, GREEN, BLUE, GREY

def d100():
    """Helper function for dice rolls."""
    return random.randint(1, 100)

class Door:
    """Represents a door with its properties."""
    def __init__(self, door_data):
        self.type = door_data['type']
        self.code = door_data['code']
        self.test = door_data['test']
        self.mod = door_data['mod']
        self.skills = door_data['skills']
        self.is_open = False

class Area:
    """Represents a single area (room/corridor) in the dungeon."""
    def __init__(self, x, y, area_data, template):
        self.x = x
        self.y = y
        self.type = area_data['type']
        self.layout = area_data['layout']
        self.color = {'Yellow': YELLOW, 'Red': RED, 'Green': GREEN, 'Blue': BLUE}.get(self.type, GREY)
        self.has_been_searched = False
        self.feature = None
        self.doors = {} 
        self.template = template
        self.room_data = self.template['map']

class DungeonMap:
    """Manages the collection of all discovered areas and procedural generation."""
    def __init__(self):
        self.areas = {}
        self.generate_area(0, 0, is_entrance=True)

    def get_area(self, x, y):
        """Safely retrieves an area at given coordinates, returning None if it doesn't exist."""
        return self.areas.get((x, y))

    def generate_area(self, x, y, is_entrance=False, required_exit=None):
        """
        Generates a new area, ensuring it has an exit that connects to the previous room.
        """
        if (x, y) in self.areas:
            return self.areas[(x, y)]

        if is_entrance:
            area_data = MAPPING_TABLE['entrance']
            template = TEMPLATES['start_room']
        else:
            roll = d100()
            valid_keys = [k for k in MAPPING_TABLE.keys() if isinstance(k, int)]
            closest_roll = min(valid_keys, key=lambda k: abs(k - roll))
            area_data = MAPPING_TABLE[closest_roll]
            
            # --- MODIFICATION START ---
            # Filter templates to find ones with the required connecting exit
            possible_templates = []
            if required_exit:
                for key, tmpl in TEMPLATES.items():
                    if key != 'start_room' and required_exit in tmpl['exits']:
                        possible_templates.append(key)
            
            # If no specific templates are found, fall back to any non-start room
            if not possible_templates:
                print(f"Warning: No room templates found with a '{required_exit}' exit. Picking a random room.")
                possible_templates = [k for k in TEMPLATES.keys() if k != 'start_room']

            template_key = random.choice(possible_templates)
            template = TEMPLATES[template_key]
            # --- MODIFICATION END ---
        
        new_area = Area(x, y, area_data, template)
        self.areas[(x, y)] = new_area
        
        # (Door creation logic remains the same)
        exit_map = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}
        for i, exit_type in enumerate(new_area.layout):
            if exit_type == 'D':
                roll = d100()
                valid_door_keys = [k for k in DOOR_TABLE.keys() if isinstance(k, int)]
                closest_door_roll = min(valid_door_keys, key=lambda k: abs(k - roll))
                door_data = DOOR_TABLE[closest_door_roll]
                dx, dy = exit_map[i]
                new_area.doors[(dx, dy)] = Door(door_data)
        
        return new_area
