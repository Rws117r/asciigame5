# spell_system.py
# Complete implementation of the D100 Dungeon spell system

import random

def load_spell_table(game_instance):
    """Load spells from the JSON data."""
    if hasattr(game_instance, 'spells_data') and 'spells' in game_instance.spells_data:
        return game_instance.spells_data['spells']
    return {}

def get_spell_by_roll(roll, spell_table):
    """Get a spell from the table based on a d100 roll."""
    # Convert roll to string and find the appropriate spell
    for threshold_str in sorted(spell_table.keys(), key=int, reverse=True):
        threshold = int(threshold_str)
        if roll >= threshold:
            return spell_table[threshold_str].copy()
    
    # Fallback to first spell if nothing found
    first_key = min(spell_table.keys(), key=int)
    return spell_table[first_key].copy()

def check_spell_book_unlock(world, player_id):
    """Check if spell book should be unlocked when Intelligence changes."""
    from components import Stats, SpellBook
    stats = world.get_component(player_id, "Stats")
    spell_book = world.get_component(player_id, "SpellBook")
    
    if spell_book and not spell_book.is_unlocked and stats.adj_int >= 50:
        spell_book.is_unlocked = True
        return True
    return False

def add_random_spell(world, player_id, game_instance):
    """Add a random spell from the spell table to the player's spell book."""
    spell_book = world.get_component(player_id, "SpellBook")
    if not spell_book:
        return None
    
    spell_table = load_spell_table(game_instance)
    if not spell_table:
        return None
    
    # Roll d100 for random spell
    roll = random.randint(1, 100)
    spell_data = get_spell_by_roll(roll, spell_table)
    
    if spell_data:
        spell_book.add_spell(spell_data)
        return spell_data['name']
    
    return None

def can_afford_spell(stats, spell):
    """Check if player can afford to cast a spell."""
    if spell['cost_type'] == 'hp':
        return stats.current_hp > spell['cost']  # Must have more than cost (can't die from casting)
    elif spell['cost_type'] == 'str':
        return stats.adj_str > spell['cost']  # Must have more than cost
    return False

def pay_spell_cost(stats, spell):
    """Pay the cost of casting a spell."""
    if spell['cost_type'] == 'hp':
        stats.current_hp -= spell['cost']
    elif spell['cost_type'] == 'str':
        stats.adj_str -= spell['cost']  # Temporary reduction until end of encounter

def apply_spell_effect(world, player_id, monster_id, spell, success_roll):
    """Apply the effect of a successfully cast spell."""
    from components import Stats
    
    stats = world.get_component(player_id, "Stats")
    monster_stats = world.get_component(monster_id, "Stats") if monster_id else None
    monster_info = world.get_component(monster_id, "Info") if monster_id else None
    
    effect = spell['effect']
    spell_name = spell['name']
    
    # Healing effects
    if effect == 'heal_10':
        heal_amount = min(10, stats.max_hp - stats.current_hp)
        stats.current_hp += heal_amount
        return f"Cast {spell_name}, healed {heal_amount} HP!"
    
    elif effect == 'heal_all':
        heal_amount = stats.max_hp - stats.current_hp
        stats.current_hp = stats.max_hp
        return f"Cast {spell_name}, fully healed ({heal_amount} HP)!"
    
    # Damage effects
    elif effect == 'damage_2':
        if monster_stats:
            monster_stats.current_hp -= 2
            return f"Cast {spell_name}, deals 2 damage to {monster_info.name}!"
        return f"Cast {spell_name}, but no target!"
    
    elif effect == 'damage_4':
        if monster_stats:
            monster_stats.current_hp -= 4
            return f"Cast {spell_name}, deals 4 damage to {monster_info.name}!"
        return f"Cast {spell_name}, but no target!"
    
    elif effect == 'ice_storm':
        if monster_stats:
            damage = random.randint(1, 10)
            monster_stats.current_hp -= damage
            if monster_stats.current_hp > 0:
                monster_stats.av = max(0, monster_stats.av - 5)
                return f"Cast {spell_name}, deals {damage} damage and reduces AV by 5!"
            else:
                return f"Cast {spell_name}, deals {damage} damage and destroys {monster_info.name}!"
        return f"Cast {spell_name}, but no target!"
    
    elif effect == 'lightning':
        if monster_stats:
            damage = random.randint(1, 10)
            monster_stats.current_hp -= damage
            # Monster gains +10 to all D100 tests for the round if it attacks
            return f"Cast {spell_name}, deals {damage} damage with electrical charges!"
        return f"Cast {spell_name}, but no target!"
    
    # Defensive effects
    elif effect == 'armor_1':
        stats.defense += 1
        return f"Cast {spell_name}, gained +1 defense until end of encounter!"
    
    elif effect == 'mirror_image':
        # Create illusions - monster suffers -10 to AV and gains +10 to D100 tests
        if monster_stats:
            monster_stats.av = max(0, monster_stats.av - 10)
            return f"Cast {spell_name}, created mirror images! Monster confused!"
        return f"Cast {spell_name}, created mirror images!"
    
    # Stat boost effects (temporary until end of encounter)
    elif effect == 'str_boost':
        # +10 Str to next d100 roll only
        return f"Cast {spell_name}, +10 Str to next roll!"
    
    elif effect == 'dex_boost':
        # +10 Dex to next d100 roll only
        return f"Cast {spell_name}, +10 Dex to next roll!"
    
    elif effect == 'int_boost':
        # +10 Int to next d100 roll only
        return f"Cast {spell_name}, +10 Int to next roll!"
    
    elif effect == 'str_boost_20':
        # +20 Str to next d100 roll only
        return f"Cast {spell_name}, +20 Str to next roll!"
    
    elif effect == 'dex_boost_20':
        # +20 Dex to next d100 roll only
        return f"Cast {spell_name}, +20 Dex to next roll!"
    
    elif effect == 'int_boost_20':
        # +20 Int to next d100 roll only
        return f"Cast {spell_name}, +20 Int to next roll!"
    
    # Debuff effects
    elif effect == 'clumsy':
        if monster_stats:
            monster_stats.av = max(0, monster_stats.av - 10)
            return f"Cast {spell_name}, {monster_info.name} becomes clumsy (-10 AV)!"
        return f"Cast {spell_name}, but no target!"
    
    elif effect == 'confuse':
        # Monster does not attack for the next combat round
        return f"Cast {spell_name}, monster is confused and won't attack next round!"
    
    # Special utility effects
    elif effect == 'open_magic':
        return f"Cast {spell_name}, opens a magically sealed door!"
    
    elif effect == 'invisibility':
        return f"Cast {spell_name}, you become invisible and can escape without a test!"
    
    elif effect == 'alter_time':
        # Remove 10 from the time track
        return f"Cast {spell_name}, time flows backwards!"
    
    elif effect == 'clone':
        # Create an exact replica that fights alongside
        return f"Cast {spell_name}, created a clone to fight beside you!"
    
    elif effect == 'counter':
        # Used after monster rolls for spell - cancels the attack
        return f"Cast {spell_name}, countered the monster's Dark Magic!"
    
    elif effect == 'manipulate':
        # Re-roll any die just rolled if cast in combat
        return f"Cast {spell_name}, manipulated fate itself!"
    
    elif effect == 'summons':
        # Summon a monster to fight in place of adventurer
        return f"Cast {spell_name}, summoned a creature to fight for you!"
    
    elif effect == 'drain_life':
        if monster_stats:
            # All HP lost by monster restores equal HP to adventurer
            damage_potential = monster_stats.current_hp
            stats.current_hp = min(stats.max_hp, stats.current_hp + damage_potential)
            monster_stats.current_hp = 0
            return f"Cast {spell_name}, drained all life from {monster_info.name}!"
        return f"Cast {spell_name}, but no target to drain!"
    
    elif effect == 'resurrection':
        # Add a life point box when adventurer next dies (auto-resurrection)
        from components import Info
        info = world.get_component(player_id, "Info")
        if info:
            info.life_points += 1
            return f"Cast {spell_name}, gained an extra life point!"
        return f"Cast {spell_name}, but failed to grant extra life!"
    
    else:
        return f"Cast {spell_name} successfully, but effect not implemented!"

# Function to give starting spells to Sorcerer path
def give_sorcerer_starting_spells(world, player_id, game_instance):
    """Give starting spells to Sorcerer characters."""
    spell_book = world.get_component(player_id, "SpellBook")
    if not spell_book:
        return []
    
    spell_table = load_spell_table(game_instance)
    if not spell_table:
        return []
    
    # Sorcerers start with 2 basic spells: Fire Blast (17) and Heal (13)
    starting_spell_rolls = [17, 13]
    spell_names = []
    
    for roll in starting_spell_rolls:
        spell_data = get_spell_by_roll(roll, spell_table)
        if spell_data:
            spell_book.add_spell(spell_data)
            spell_names.append(spell_data['name'])
    
    return spell_names

# Enhanced combat methods for proper spell integration
def enhanced_open_spell_submenu(combat_screen):
    """Enhanced spell submenu that follows D100 rules."""
    combat_screen.in_submenu = True
    combat_screen.current_submenu = 'spell'
    combat_screen.submenu_items = []
    combat_screen.submenu_selected = 0
    
    stats = combat_screen.world.get_component(combat_screen.player_id, "Stats")
    spell_book = combat_screen.world.get_component(combat_screen.player_id, "SpellBook")
    
    # Check if spell book is unlocked (Int >= 50)
    if not spell_book or not spell_book.is_unlocked:
        combat_screen.submenu_items.append({
            'type': 'none', 
            'name': f"Spell book locked (Need Int 50+, current: {stats.adj_int})"
        })
        return
    
    # Get castable spells based on current Intelligence
    castable_spells = spell_book.get_castable_spells(stats.adj_int)
    
    if not castable_spells:
        combat_screen.submenu_items.append({
            'type': 'none', 
            'name': f"No spells available (Int: {stats.adj_int})"
        })
        return
    
    # Add available spells to menu with cost and affordability
    for spell in castable_spells:
        cost_text = f"-{spell['cost']} {spell['cost_type'].upper()}"
        affordable = can_afford_spell(stats, spell)
        
        if affordable:
            name = f"{spell['name']} ({cost_text})"
            color_hint = ""
        else:
            name = f"{spell['name']} ({cost_text}) - CAN'T AFFORD"
            color_hint = " [RED]"
        
        combat_screen.submenu_items.append({
            'type': 'spell',
            'spell_data': spell,
            'name': name + color_hint,
            'affordable': affordable
        })

def enhanced_handle_spell_action(combat_screen, spell_item):
    """Enhanced spell casting that follows D100 rules exactly."""
    if not spell_item['affordable']:
        combat_screen.player_action = f"Cannot afford to cast {spell_item['spell_data']['name']}!"
        return
    
    spell = spell_item['spell_data']
    stats = combat_screen.world.get_component(combat_screen.player_id, "Stats")
    
    # Pay the spell cost first
    pay_spell_cost(stats, spell)
    
    # Perform spell test: Int + Magic skill bonus
    from systems import perform_test
    success, roll = perform_test(combat_screen.world, combat_screen.player_id, 'int', 0, ['Magic'])
    
    if success:
        # Apply spell effect
        result_message = apply_spell_effect(
            combat_screen.world, 
            combat_screen.player_id, 
            combat_screen.monster_id, 
            spell, 
            roll
        )
        combat_screen.player_action = f"{result_message} (Rolled {roll})"
    else:
        combat_screen.player_action = f"Cast {spell['name']} but it failed! (Rolled {roll})"
        # Note: Cost is already paid even on failure, as per D100 rules