# dungeon.py
# This file contains classes related to the dungeon map structure and generation.

import random
from tables import MAPPING_TABLE, DOOR_TABLE
from room_templates import TEMPLATES, WALKABLE_TILES
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
        
        # Store actual world position for each tile
        self.world_tiles = {}
        self._calculate_world_positions()
    
    def _calculate_world_positions(self):
        """Calculate the world coordinates for each tile in this room."""
        room_width = len(self.room_data[0])
        room_height = len(self.room_data)
        
        # Calculate world offset for this room (rooms overlap by 1 tile at doors)
        world_offset_x = self.x * (room_width - 1)
        world_offset_y = self.y * (room_height - 1)
        
        for local_y, row in enumerate(self.room_data):
            for local_x, char in enumerate(row):
                world_x = world_offset_x + local_x
                world_y = world_offset_y + local_y
                self.world_tiles[(world_x, world_y)] = {
                    'char': char,
                    'local_pos': (local_x, local_y),
                    'room_coords': (self.x, self.y)
                }

class DungeonMap:
    """Manages the collection of all discovered areas and procedural generation."""
    def __init__(self):
        self.areas = {}
        self.world_tiles = {}  # Global tile map for rendering
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
        
        new_area = Area(x, y, area_data, template)
        self.areas[(x, y)] = new_area
        
        # Add this room's tiles to the global world map
        self._add_area_to_world_map(new_area)
        
        # Generate doors
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
    
    def _add_area_to_world_map(self, area):
        """Add an area's tiles to the global world tile map."""
        for world_pos, tile_data in area.world_tiles.items():
            # Only add if not already occupied, or if this is a door connection
            if world_pos not in self.world_tiles or tile_data['char'] == 'D':
                self.world_tiles[world_pos] = tile_data
    
    def get_world_tile(self, world_x, world_y):
        """Get the tile character at world coordinates."""
        tile_data = self.world_tiles.get((world_x, world_y))
        return tile_data['char'] if tile_data else None
    
    def get_tile_room_coords(self, world_x, world_y):
        """Get the room coordinates for a world tile."""
        tile_data = self.world_tiles.get((world_x, world_y))
        return tile_data['room_coords'] if tile_data else None
    
    def world_to_local_coords(self, world_x, world_y):
        """Convert world coordinates to room-local coordinates."""
        tile_data = self.world_tiles.get((world_x, world_y))
        if tile_data:
            return tile_data['room_coords'], tile_data['local_pos']
        return None, None
    
    def local_to_world_coords(self, room_x, room_y, local_x, local_y):
        """Convert room-local coordinates to world coordinates."""
        area = self.get_area(room_x, room_y)
        if not area:
            return None, None
        
        room_width = len(area.room_data[0])
        room_height = len(area.room_data)
        
        world_offset_x = room_x * (room_width - 1)
        world_offset_y = room_y * (room_height - 1)
        
        return world_offset_x + local_x, world_offset_y + local_y
    
    def get_world_bounds(self):
        """Get the bounds of the current world map."""
        if not self.world_tiles:
            return 0, 0, 0, 0
        
        x_coords = [pos[0] for pos in self.world_tiles.keys()]
        y_coords = [pos[1] for pos in self.world_tiles.keys()]
        
        return min(x_coords), min(y_coords), max(x_coords), max(y_coords)