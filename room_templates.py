# room_templates.py
# This file stores pre-designed ASCII room layouts.

# Each key is a unique name for the template.
# 'map' is a list of strings representing the room's layout.
# 'exits' is a dictionary where keys are 'north', 'south', 'east', 'west'
# and values are the (x, y) coordinates of the entrance tile in that room.
# 'walkable' is a string of characters the player can move onto.

TEMPLATES = {
    'start_room': {
        'map': [
            "#########D##########",
            "#..................#",
            "#..................#",
            "#..................#",
            "#..................#",
            "#..................#",
            "#..................#",
            "#..................#",
            "####################"
        ],
        'exits': {'north': (9, 0)},
        'start_pos': (9, 4)
    },
    'corridor_ns': {
        'map': [
            "#######D###########",
            "#######.###########",
            "#######.###########",
            "#######.###########",
            "#######.###########",
            "#######.###########",
            "#######.###########",
            "#######D###########"
        ],
        'exits': {'north': (7, 0), 'south': (7, 7)}
    },
    'four_way_room': {
        'map': [
            "#########D#########",
            "#.................#",
            "#.................#",
            "#.................#",
            "D.................D",
            "#.................#",
            "#.................#",
            "#.................#",
            "#########D#########"
        ],
        'exits': {'north': (9, 0), 'south': (9, 8), 'east': (18, 4), 'west': (0, 4)}
    }
}

# Define which characters are considered walkable.
WALKABLE_TILES = "D."
