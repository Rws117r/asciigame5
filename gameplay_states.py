# gameplay_states.py
# This file contains the main gameplay states (exploration, inventory, doors)

import pygame
import random
from config import *
from ecs import World
from components import *
from systems import *
from dungeon import DungeonMap
from room_templates import WALKABLE_TILES
from menu_states import BaseState

class GameplayScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.world = World()
        self.font = load_font(FONT_NAME, FONT_SIZE)
        self.ui_font = load_font(FONT_NAME, UI_FONT_SIZE)
        
        self.dungeon_map = DungeonMap()
        self.manager_id = self.create_manager()  # Create manager first to initialize message_log
        self.player_id = self.create_player()
        self.message_log.add_message("Welcome to the dungeon!", YELLOW)

    def auto_equip_starting_gear(self, world, player_id, starting_items):
        """Automatically equip starting weapons and armor."""
        equipment = world.get_component(player_id, "Equipment")
        inventory = world.get_component(player_id, "Inventory")
        resources = world.get_component(player_id, "Resources")
        
        for item_info in starting_items:
            # Create the item entity
            item_id = world.create_entity()
            item_data = item_info['data']
            
            # Create the item component
            world.add_component(item_id, Item(
                name=item_data['name'], 
                value=item_data['value'], 
                slot=item_data['slot'], 
                bonuses=item_data.get('bonuses', {})
            ))
            
            # Auto-equip weapons and armor, add consumables to inventory
            if item_info['type'] in ['weapon', 'armor']:
                slot = item_data['slot']
                if slot in equipment.slots and equipment.slots[slot] is None:
                    equipment.slots[slot] = item_id
                    print(f"Auto-equipped: {item_data['name']}")
                else:
                    # If slot is occupied or item is two-handed, add to inventory
                    inventory.items.append(item_id)
            elif item_info['type'] == 'consumable':
                # Handle consumables - add resources or potions to inventory
                if 'oil' in item_data['name'].lower():
                    resources.oil += 1
                elif 'food' in item_data['name'].lower():
                    resources.food += 1
                elif 'pick' in item_data['name'].lower():
                    resources.picks += 1
                else:
                    # Add potions to inventory
                    inventory.items.append(item_id)

    def create_player(self):
        player_id = self.world.create_entity()
        p_data = self.game.player_data
        
        # Player starts in world (0,0) at the designated start pos of the room template
        start_area = self.dungeon_map.get_area(0, 0)
        start_pos_local = start_area.template.get('start_pos', (1, 1))
        self.world.add_component(player_id, Position(0, 0, start_pos_local[0], start_pos_local[1]))

        self.world.add_component(player_id, Renderable('@', YELLOW))
        self.world.add_component(player_id, Player())
        self.world.add_component(player_id, Info(p_data['name'], p_data['race'], p_data['hero_path'], p_data['info']['life']))
        self.world.add_component(player_id, Inventory())
        self.world.add_component(player_id, Equipment())
        
        # Add spell book component
        self.world.add_component(player_id, SpellBook())
        
        # Start with the specified resources (some will be added by starting equipment)
        self.world.add_component(player_id, Resources(oil=0, food=0, picks=0))

        stats_comp = Stats(p_data['stats']['str'], p_data['stats']['dex'], p_data['stats']['int'], p_data['stats']['hp'])
        skills_comp = Skills()
        
        path, race = p_data['hero_path'], p_data['race']
        if path == 'Warrior': skills_comp.skills['Bravery']['bonus'] = 5; skills_comp.skills['Escape']['bonus'] = 5
        if path == 'Rogue': skills_comp.skills['Locks']['bonus'] = 5; skills_comp.skills['Traps']['bonus'] = 5
        if path == 'Sorcerer': skills_comp.skills['Magic']['bonus'] = 5; skills_comp.skills['Lucky']['bonus'] = 5
        if race == 'Dwarf': skills_comp.skills['Strong']['bonus'] = 5
        if race == 'Elf': skills_comp.skills['Dodge']['bonus'] = 5
        if race == 'Human': skills_comp.skills['Aware']['bonus'] = 5
        for skill_name in p_data.get('skills_choice', []):
            if skill_name in skills_comp.skills: skills_comp.skills[skill_name]['bonus'] += 5

        self.world.add_component(player_id, stats_comp)
        self.world.add_component(player_id, skills_comp)
        
        # Auto-equip starting equipment
        if 'starting_equipment' in p_data:
            self.auto_equip_starting_gear(self.world, player_id, p_data['starting_equipment'])
            # Update stats after equipping gear
            update_player_stats(self.world, player_id)
            
            # Check if spell book should be unlocked
            from spell_system import check_spell_book_unlock, give_sorcerer_starting_spells
            spell_book = self.world.get_component(player_id, "SpellBook")
            stats = self.world.get_component(player_id, "Stats")
            
            if stats.adj_int >= 50:
                spell_book.is_unlocked = True
                self.message_log.add_message("Spell book unlocked! (Intelligence 50+)", GREEN)
                
                # Give starting spells to Sorcerers
                if path == 'Sorcerer':
                    starting_spells = give_sorcerer_starting_spells(self.world, player_id, self.game)
                    if starting_spells:
                        self.message_log.add_message(f"Starting spells: {', '.join(starting_spells)}", BLUE)
            
            # Log starting equipment
            equipment = self.world.get_component(player_id, "Equipment")
            resources = self.world.get_component(player_id, "Resources")
            equipped_items = []
            for slot, item_id in equipment.slots.items():
                if item_id:
                    item = self.world.get_component(item_id, "Item")
                    equipped_items.append(f"{item.name} ({slot})")
            
            if equipped_items:
                self.message_log.add_message("Starting equipment equipped:", GREEN)
                for item_desc in equipped_items:
                    self.message_log.add_message(f"  {item_desc}", WHITE)
            
            self.message_log.add_message(f"Resources: Oil:{resources.oil} Food:{resources.food} Picks:{resources.picks}", ORANGE)
        
        return player_id

    def create_manager(self):
        manager_id = self.world.create_entity()
        self.world.add_component(manager_id, TimeManager())
        self.message_log = MessageLog()
        self.world.add_component(manager_id, self.message_log)
        return manager_id

    def advance_turn(self, ticks=1):
        time_manager = self.world.get_component(self.manager_id, "TimeManager")
        resources = self.world.get_component(self.player_id, "Resources")
        
        time_manager.ticks += ticks
        self.message_log.add_message(f"Time advances... ({time_manager.ticks})", GREY)

        event = time_manager.time_track_markers.get(time_manager.ticks)
        if event == 'oil':
            if resources.oil > 0:
                resources.oil -= 1
                self.message_log.add_message("You use a flask of oil.", ORANGE)
            else:
                self.message_log.add_message("You are out of oil! It's getting dark...", RED)
        elif event == 'food':
            if resources.food > 0:
                resources.food -= 1
                self.message_log.add_message("You eat some rations.", ORANGE)
            else:
                self.message_log.add_message("You are hungry and weak!", RED)
        elif event == 'monster':
            self.message_log.add_message("A wandering monster appears!", RED)
            self.start_combat()
        elif event == 'end':
            time_manager.ticks = 0

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                self.move_player(event.key)
            elif event.key == pygame.K_s:
                player_pos = self.world.get_component(self.player_id, "Position")
                current_area = self.dungeon_map.get_area(player_pos.world_x, player_pos.world_y)
                if not current_area.has_been_searched:
                    self.advance_turn(5)
                    self.message_log.add_message("You search the area...", YELLOW)
                    current_area.has_been_searched = True
                else:
                    self.message_log.add_message("You've already searched here.", GREY)
            elif event.key == pygame.K_i:
                self.game.push_state(InventoryScreen(self.game, self.world, self.player_id))
            elif event.key == pygame.K_f:
                self.game.toggle_fullscreen()

    def move_player(self, key):
        """Handles player movement using the enhanced world coordinate system."""
        player_pos = self.world.get_component(self.player_id, "Position")
        current_area = self.dungeon_map.get_area(player_pos.world_x, player_pos.world_y)
        
        dx, dy = 0, 0
        if key == pygame.K_UP: dy = -1
        elif key == pygame.K_DOWN: dy = 1
        elif key == pygame.K_LEFT: dx = -1
        elif key == pygame.K_RIGHT: dx = 1

        new_local_x = player_pos.local_x + dx
        new_local_y = player_pos.local_y + dy

        # Check bounds of current room first
        if (0 <= new_local_x < len(current_area.room_data[0]) and 
            0 <= new_local_y < len(current_area.room_data)):
            
            target_tile = current_area.room_data[new_local_y][new_local_x]
            
            if target_tile in WALKABLE_TILES:
                # Check if this is an exit to another room
                is_exit = False
                exit_direction = None
                for direction, coords in current_area.template['exits'].items():
                    if coords == (new_local_x, new_local_y):
                        is_exit = True
                        exit_direction = direction
                        break
                
                if is_exit:
                    # Moving to another room
                    world_dx, world_dy = {'north':(0,-1), 'south':(0,1), 'east':(1,0), 'west':(-1,0)}[exit_direction]
                    player_pos.world_x += world_dx
                    player_pos.world_y += world_dy
                    
                    # Generate the new area if it doesn't exist
                    opposite_dir = {'north':'south', 'south':'north', 'east':'west', 'west':'east'}[exit_direction]
                    new_area = self.dungeon_map.generate_area(player_pos.world_x, player_pos.world_y, required_exit=opposite_dir)
                    
                    # Set player position to the entrance of the new room
                    entry_coords = new_area.template['exits'][opposite_dir]
                    player_pos.local_x, player_pos.local_y = entry_coords
                    
                    self.message_log.add_message("You enter a new area.", YELLOW)
                    self.advance_turn()
                else:
                    # Normal movement within the room
                    player_pos.local_x = new_local_x
                    player_pos.local_y = new_local_y
                    self.advance_turn()

    def start_combat(self):
        player_pos = self.world.get_component(self.player_id, "Position")
        current_area = self.dungeon_map.get_area(player_pos.world_x, player_pos.world_y)

        monster_key = random.choice(list(self.game.monsters_data.keys()))
        m_data = self.game.monsters_data[monster_key]
        monster_id = self.world.create_entity()
        self.world.add_component(monster_id, Combatant())
        self.world.add_component(monster_id, Info(name=m_data['name']))
        hp = m_data['hp'][0] if isinstance(m_data['hp'], list) else m_data['hp']
        self.world.add_component(monster_id, Stats(0, 0, 0, hp, m_data['av'], m_data['def'], m_data['dmg']))
        self.world.add_component(monster_id, Renderable(m_data['char'], m_data['color']))
        
        from combat_states import CombatScreen
        self.game.push_state(CombatScreen(self.game, self.world, self.player_id, monster_id, monster_key, current_area))

    def update(self): pass

    def draw(self, screen):
        """Enhanced draw method that shows multiple connected rooms."""
        screen.fill(BLACK)
        player_pos = self.world.get_component(self.player_id, "Position")
        char_w, char_h = self.font.size(' ')

        # Calculate player's world position
        player_world_x, player_world_y = self.dungeon_map.local_to_world_coords(
            player_pos.world_x, player_pos.world_y, player_pos.local_x, player_pos.local_y)
        
        if player_world_x is None or player_world_y is None:
            return  # Safety check
        
        # Center camera on player
        screen_center_x = GRID_WIDTH // 2
        screen_center_y = GRID_HEIGHT // 2
        cam_world_x = player_world_x - screen_center_x
        cam_world_y = player_world_y - screen_center_y
        
        # Draw all visible tiles from the world map
        for screen_y in range(GRID_HEIGHT):
            for screen_x in range(GRID_WIDTH):
                world_x = cam_world_x + screen_x
                world_y = cam_world_y + screen_y
                
                char = self.dungeon_map.get_world_tile(world_x, world_y)
                if char:
                    color = GREY if char == '#' else DARK_GREY
                    if char in WALKABLE_TILES:
                        color = DARK_GREY
                    draw_text(screen, char, screen_x * char_w, screen_y * char_h, self.font, color)
        
        # Draw player
        player_render = self.world.get_component(self.player_id, "Renderable")
        draw_text(screen, player_render.char, screen_center_x * char_w, screen_center_y * char_h, self.font, player_render.color)
        
        # Draw UI elements (messages, stats, etc.)
        log_y = screen.get_height() - (self.message_log.max_lines * 20) - 10
        for msg, color in self.message_log.messages:
            draw_text(screen, msg, 10, log_y, self.ui_font, color)
            log_y += 20
        
        stats = self.world.get_component(self.player_id, "Stats")
        resources = self.world.get_component(self.player_id, "Resources")
        hp_text = f"HP: {stats.current_hp}/{stats.max_hp}"
        draw_text(screen, hp_text, 10, 10, self.ui_font, GREEN)
        draw_text(screen, f"Oil: {resources.oil} Food: {resources.food} Picks: {resources.picks}", 10, 35, self.ui_font, ORANGE)

class InventoryScreen(BaseState):
    def __init__(self, game, world, player_id):
        super().__init__(game)
        self.world = world
        self.player_id = player_id
        self.font = load_font(FONT_NAME, 20)
        self.header_font = load_font(FONT_NAME, 30)
        self.inventory_items = []
        self.refresh_lists()
        self.selected_index = 0

    def refresh_lists(self):
        inventory_comp = self.world.get_component(self.player_id, "Inventory")
        self.inventory_items = inventory_comp.items

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self.game.pop_state()
            elif event.key == pygame.K_UP:
                if self.inventory_items: self.selected_index = (self.selected_index - 1) % len(self.inventory_items)
            elif event.key == pygame.K_DOWN:
                 if self.inventory_items: self.selected_index = (self.selected_index + 1) % len(self.inventory_items)
            elif event.key == pygame.K_e: self.equip_item()

    def update(self): pass

    def equip_item(self):
        if not self.inventory_items: return
        item_id = self.inventory_items[self.selected_index]
        item = self.world.get_component(item_id, "Item")
        slot_to_equip = item.slot
        if slot_to_equip == "junk": return
        equipment = self.world.get_component(self.player_id, "Equipment")
        inventory = self.world.get_component(self.player_id, "Inventory")
        if equipment.slots.get(slot_to_equip) is not None:
            unequipped_item_id = equipment.slots[slot_to_equip]
            inventory.items.append(unequipped_item_id)
        equipment.slots[slot_to_equip] = item_id
        inventory.items.pop(self.selected_index)
        update_player_stats(self.world, self.player_id)
        self.refresh_lists()
        if self.inventory_items and self.selected_index >= len(self.inventory_items):
            self.selected_index = len(self.inventory_items) - 1

    def draw(self, screen):
        screen.fill(BLACK)
        width, height = screen.get_size()
        col1, col2, col3 = width * 0.05, width * 0.4, width * 0.75

        draw_text(screen, "Equipped", col1, 20, self.header_font, YELLOW)
        equipment = self.world.get_component(self.player_id, "Equipment")
        y_pos = 70
        for slot, item_id in equipment.slots.items():
            item_name = "Empty"
            if item_id: item_name = self.world.get_component(item_id, "Item").name
            draw_text(screen, f"{slot.replace('_', ' ').title():<10}: {item_name}", col1, y_pos, self.font, WHITE)
            y_pos += 25

        draw_text(screen, "Character", col2, 20, self.header_font, YELLOW)
        stats = self.world.get_component(self.player_id, "Stats")
        skills = self.world.get_component(self.player_id, "Skills")
        y_pos = 70
        draw_text(screen, f"STR: {stats.primary_str} ({stats.adj_str})", col2, y_pos, self.font, WHITE)
        y_pos += 25
        draw_text(screen, f"DEX: {stats.primary_dex} ({stats.adj_dex})", col2, y_pos, self.font, WHITE)
        y_pos += 25
        draw_text(screen, f"INT: {stats.primary_int} ({stats.adj_int})", col2, y_pos, self.font, WHITE)
        y_pos += 40
        for name, data in skills.skills.items():
            draw_text(screen, f"{name:<8}: {data['bonus']:>2}", col2, y_pos, self.font, WHITE)
            for i, pip in enumerate(data['xp_pips']):
                pip_char, pip_color = ('■', BLUE) if pip else ('□', GREY)
                draw_text(screen, pip_char, col2 + 150 + (i*12), y_pos, self.font, pip_color)
            y_pos += 25
        
        draw_text(screen, "Inventory", col3, 20, self.header_font, YELLOW)
        y_pos = 70
        if not self.inventory_items:
            draw_text(screen, "Backpack is empty.", col3, y_pos, self.font, GREY)
        else:
            for i, item_id in enumerate(self.inventory_items):
                item = self.world.get_component(item_id, "Item")
                color = YELLOW if i == self.selected_index else WHITE
                draw_text(screen, item.name, col3, y_pos, self.font, color)
                y_pos += 25

        draw_text(screen, "UP/DOWN: Navigate | E: Equip | ESC: Close", width//2, height - 40, self.font, WHITE, center=True)

class DoorScreen(BaseState):
    def __init__(self, game, world, player_id, door):
        super().__init__(game)
        self.world = world
        self.player_id = player_id
        self.door = door
        self.font = load_font(FONT_NAME, 28)
        self.options = self.get_options()
        self.selected_index = 0

    def get_options(self):
        options = []
        if self.door.type in ['Locked', 'Trap Locked']:
            options.append("Use Key")
            options.append("Pick Lock")
        if self.door.type == 'Jammed':
            options.append("Force Open")
        if self.door.type == 'Magic':
            options.append("Use Magic")
        options.append("Leave")
        return options
    
    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN: self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key == pygame.K_RETURN: self.select_option()
            elif event.key == pygame.K_ESCAPE: self.game.pop_state()

    def select_option(self):
        option = self.options[self.selected_index]
        # Find the gameplay screen that's below this door screen
        gameplay_screen = None
        for state in reversed(self.game.states):
            if isinstance(state, GameplayScreen):
                gameplay_screen = state
                break
        
        if not gameplay_screen:
            self.game.pop_state()
            return
            
        message_log = self.world.get_component(gameplay_screen.manager_id, "MessageLog")
        resources = self.world.get_component(self.player_id, "Resources")

        if option == "Leave":
            self.game.pop_state()
            return

        success, roll = perform_test(self.world, self.player_id, self.door.test, self.door.mod, self.door.skills)
        
        if success:
            message_log.add_message(f"Success! The door opens. (Rolled {roll})", GREEN)
            self.door.is_open = True
            self.game.pop_state()
        else:
            message_log.add_message(f"Failure! The door remains shut. (Rolled {roll})", RED)
            if self.door.type in ['Locked', 'Trap Locked']:
                resources.picks -= 1
                message_log.add_message("You lost a pick.", ORANGE)
            self.game.pop_state()

    def update(self): pass

    def draw(self, screen):
        s = pygame.Surface(screen.get_size())
        s.set_alpha(128)
        s.fill(BLACK)
        screen.blit(s, (0,0))

        width, height = screen.get_size()
        box_w, box_h = 400, 200
        box_x, box_y = (width - box_w)//2, (height - box_h)//2
        pygame.draw.rect(screen, DARK_GREY, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), 2)
        
        draw_text(screen, f"{self.door.type} Door", box_x + box_w//2, box_y + 30, self.font, YELLOW, center=True)
        
        for i, option in enumerate(self.options):
            y_pos = box_y + 80 + i * 35
            color = YELLOW if i == self.selected_index else WHITE
            draw_text(screen, option, box_x + box_w//2, y_pos, self.font, color, center=True)