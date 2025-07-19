# systems.py
# This file contains game logic functions (systems) that operate on components.

import pygame
import random
from config import FONT_NAME

def d100():
    """Helper function for dice rolls."""
    return random.randint(1, 100)

def load_font(name, size):
    """Safely loads a font, falling back to the default if not found."""
    try:
        return pygame.font.Font(name, size)
    except pygame.error:
        print(f"Warning: Font '{name}' not found. Falling back to default.")
        return pygame.font.Font(None, size)

def draw_text(surface, text, x, y, font, color, center=False):
    """Renders and draws text onto a surface."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def update_player_stats(world, player_id):
    """Recalculates a player's adjusted stats based on their equipped items."""
    player_stats = world.get_component(player_id, "Stats")
    equipment = world.get_component(player_id, "Equipment")
    if not player_stats or not equipment: return

    # Reset adjusted stats to their base primary values
    player_stats.adj_str = player_stats.primary_str
    player_stats.adj_dex = player_stats.primary_dex
    player_stats.adj_int = player_stats.primary_int
    player_stats.max_hp = player_stats.primary_hp
    player_stats.defense = 0
    player_stats.damage_mod = 0
    
    # Apply bonuses from each equipped item
    for item_id in equipment.slots.values():
        if item_id:
            item = world.get_component(item_id, "Item")
            if item and item.bonuses:
                player_stats.adj_str += item.bonuses.get("str", 0)
                player_stats.adj_dex += item.bonuses.get("dex", 0)
                player_stats.adj_int += item.bonuses.get("int", 0)
                player_stats.max_hp += item.bonuses.get("hp", 0)
                player_stats.defense += item.bonuses.get("def", 0)
                player_stats.damage_mod += item.bonuses.get("dmg", 0)
    
    # Ensure current HP does not exceed the new max HP
    player_stats.current_hp = min(player_stats.current_hp, player_stats.max_hp)

def award_experience(world, player_id, name, pips_to_add=1):
    """Adds experience pips to a stat or skill and handles leveling up."""
    stats = world.get_component(player_id, "Stats")
    skills = world.get_component(player_id, "Skills")
    name_lower = name.lower()
    
    if name_lower in stats.xp_pips:
        # Awarding XP to a Stat
        if name_lower in stats.attuned_stats: pips_to_add *= 2
        track = stats.xp_pips[name_lower]
        for _ in range(pips_to_add):
            if 0 in track: track[track.index(0)] = 1
        
        if 0 not in track: # Level up!
            setattr(stats, f"primary_{name_lower}", getattr(stats, f"primary_{name_lower}") + 5)
            stats.xp_pips[name_lower] = [0] * 10
            update_player_stats(world, player_id)
            print(f"{name.upper()} increased by 5!")

    elif name in skills.skills:
        # Awarding XP to a Skill
        skill_data = skills.skills[name]
        if skill_data['attuned']: pips_to_add *= 2
        track = skill_data['xp_pips']
        for _ in range(pips_to_add * 2): # Rule: 2 pips for assisted skills
            if 0 in track: track[track.index(0)] = 1

        if 0 not in track: # Level up!
            skill_data['bonus'] += 5
            skill_data['xp_pips'] = [0] * 10
            print(f"Skill {name} increased by 5!")

def perform_test(world, player_id, characteristic, modifier, assisting_skills):
    """Performs a d100 test, handles XP gain, and returns the result."""
    stats = world.get_component(player_id, "Stats")
    skills = world.get_component(player_id, "Skills")
    char_lower = characteristic.lower()

    target_value = getattr(stats, f"adj_{char_lower}") + modifier
    for skill_name in assisting_skills:
        if skill_name in skills.skills:
            target_value += skills.skills[skill_name]['bonus']
    
    roll = d100()
    
    if roll <= 10:
        award_experience(world, player_id, char_lower, 1)
        for skill_name in assisting_skills:
            award_experience(world, player_id, skill_name, 1)

    if roll == 1: return True, roll
    if roll == 100: return False, roll
    
    return roll <= target_value, roll
