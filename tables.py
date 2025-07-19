# This file contains the data structures representing the tables from the D100 Dungeon rulebook.

# Reference: Page 55-58, Table M - Mapping
# Each entry represents an area layout. The numbers correspond to the d100 roll.
# 'type' is the color of the area.
# 'layout' is a simplified representation of exits (0: wall, 1: open).
# The order is [Top, Right, Bottom, Left]. A door is represented by 'D'.
MAPPING_TABLE = {
    1: {'type': 'Yellow', 'layout': [1, 0, 1, 0]},
    2: {'type': 'Red',    'layout': [1, 1, 1, 1]},
    # ... This would be populated with all 100 entries from the book.
    # For this example, we'll use a smaller, representative set.
    3: {'type': 'Yellow', 'layout': [0, 1, 0, 1]},
    4: {'type': 'Red',    'layout': [1, 'D', 1, 0]},
    5: {'type': 'Yellow', 'layout': [1, 1, 0, 1]},
    6: {'type': 'Green',  'layout': [0, 1, 1, 1]},
    7: {'type': 'Red',    'layout': [1, 'D', 1, 'D']},
    8: {'type': 'Yellow', 'layout': [1, 0, 1, 0]},
    9: {'type': 'Green',  'layout': [1, 'D', 1, 1]},
    10: {'type': 'Red',   'layout': [1, 0, 1, 0]},
    # A special layout for the entrance
    'entrance': {'type': 'Yellow', 'layout': [1, 0, 0, 0]} 
}

# --- NEW TABLE FOR MILESTONE 5 ---
# Reference: Page 40-41, Table D - Doors
DOOR_TABLE = {
    1: {'code': 'L1', 'type': 'Locked', 'test': 'Dex', 'mod': 0, 'skills': ['Locks']},
    32: {'code': 'TL1', 'type': 'Trap Locked', 'test': 'Dex', 'mod': 0, 'skills': ['Locks', 'Traps']},
    34: {'code': 'J1', 'type': 'Jammed', 'test': 'Str', 'mod': 0, 'skills': ['Strong']},
    # ... This would be populated with all entries from the book.
    # We'll use a representative sample for now.
    72: {'code': 'L4', 'type': 'Locked', 'test': 'Dex', 'mod': -15, 'skills': ['Locks']},
    96: {'code': 'M', 'type': 'Magic', 'test': 'Int', 'mod': 0, 'skills': ['Magic']}
}


# Reference: Page 45, Table G - Geographic
# A simplified version for demonstration.
GEOGRAPHIC_TABLE = {
    1: "PENDULUM TRAP: Test Dex-10 vs Trap.",
    12: "BARRELS: You find barrels. Open them?",
    19: "TRAPPED CHEST: Test Dex-20 vs Trap/Lock.",
    66: "FOUNTAIN: Drink from the glowing fountain?",
    98: "TREASURE TROVE: You find 5d100 gold and a treasure!"
}

# Reference: Page 44, Table F - Find
# A simplified version for demonstration.
FIND_TABLE = {
    1: "TRAP: You trigger a trap! Roll on Geographic Table.",
    6: "MONSTER: A monster was hiding here!",
    36: "ITEM: You find something of value. Roll on Items table.",
    71: "ARMOR: You find a piece of armor.",
    96: "SKELETON: You find a skeleton with a treasure."
}