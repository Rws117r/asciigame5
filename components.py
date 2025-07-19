# components.py
# This file contains all the component classes for the ECS.
# Components are simple data containers.

class Position:
    """Represents an entity's position, including world and local coordinates."""
    def __init__(self, world_x, world_y, local_x, local_y):
        self.world_x = world_x
        self.world_y = world_y
        self.local_x = local_x
        self.local_y = local_y

class Renderable:
    """Gives an entity a character and color for drawing."""
    def __init__(self, char, color):
        self.char, self.color = char, color

class Player:
    """A tag component to identify the player entity."""
    pass

class Combatant:
    """A tag component for any entity that can participate in combat."""
    pass

class Stats:
    """Holds all numerical combat and progression stats for an entity."""
    def __init__(self, strength, dexterity, intelligence, hp, av=0, defense=0, damage_mod=0):
        self.primary_str = strength
        self.primary_dex = dexterity
        self.primary_int = intelligence
        self.primary_hp = hp
        
        self.adj_str = strength
        self.adj_dex = dexterity
        self.adj_int = intelligence
        
        self.max_hp = hp
        self.current_hp = hp

        self.av = av 
        self.defense = defense
        self.damage_mod = damage_mod
        
        self.xp_pips = {
            "str": [0] * 10,
            "dex": [0] * 10,
            "int": [0] * 10
        }
        self.attuned_stats = []

class Info:
    """Holds non-stat information about an entity (names, types, etc.)."""
    def __init__(self, name, race=None, hero_path=None, life_points=3, rep=1, fate=3):
        self.name = name
        self.race = race
        self.hero_path = hero_path
        self.life_points = life_points
        self.rep = rep
        self.fate = fate

class Item:
    """Component for items with stats and properties."""
    def __init__(self, name, value, slot, bonuses):
        self.name = name
        self.value = value
        self.slot = slot
        self.bonuses = bonuses

class Inventory:
    """Component to hold a list of item entity IDs."""
    def __init__(self):
        self.items = []

class Equipment:
    """Component to manage equipped items in their designated slots."""
    def __init__(self):
        self.slots = {
            "head": None, "torso": None, "main_hand": None, "off_hand": None,
            "back": None, "arms": None, "hands": None, "waist": None,
            "legs": None, "feet": None, "neck": None, "ring1": None, "ring2": None
        }

class Skills:
    """Holds all skills and their progression for an entity."""
    def __init__(self):
        skill_names = [
            'Agility', 'Aware', 'Bravery', 'Dodge', 'Escape', 'Locks', 
            'Lucky', 'Magic', 'Strong', 'Traps'
        ]
        self.skills = {s: {'bonus': 0, 'xp_pips': [0]*10, 'attuned': False} for s in skill_names}

class SpellBook:
    """Component to track known spells for spell casters."""
    def __init__(self):
        self.spells = []  # List of spell dictionaries
        self.is_unlocked = False  # Unlocked when Int >= 50
    
    def add_spell(self, spell_data):
        """Add a spell to the spell book."""
        if spell_data not in self.spells:
            self.spells.append(spell_data)
    
    def can_cast_spell(self, spell, current_int):
        """Check if a spell can be cast based on current Intelligence."""
        return spell in self.spells and current_int >= spell['int_requirement']
    
    def get_castable_spells(self, current_int):
        """Get all spells that can be cast with current Intelligence."""
        return [spell for spell in self.spells if current_int >= spell['int_requirement']]

class TimeManager:
    """A component for the game manager entity to track in-game time."""
    def __init__(self):
        self.ticks = 0
        self.time_track_markers = {
            3: 'oil', 6: 'food', 9: 'monster', 12: 'oil', 15: 'food', 18: 'monster',
            21: 'oil', 24: 'food', 27: 'monster', 30: 'oil', 33: 'food', 36: 'end'
        }

class MessageLog:
    """A component for the game manager to store and manage game messages."""
    def __init__(self, max_lines=5):
        self.messages = []
        self.max_lines = max_lines

    def add_message(self, text, color):
        if len(self.messages) >= self.max_lines:
            self.messages.pop(0)
        self.messages.append((text, color))

class Resources:
    """A component for the player to track consumable items."""
    def __init__(self, oil=20, food=10, picks=15):
        self.oil = oil
        self.food = food
        self.picks = picks
        self.key_pips = 0
        self.lever_pips = 0