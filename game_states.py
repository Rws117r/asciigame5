# game_states.py
# This file contains all the classes for the different game screens/states.

import pygame
import random
import json 
# Import the module itself to allow states to reference other states within the same file.
import game_states 
from config import *
from ecs import World
from components import *
from systems import *
from dungeon import DungeonMap
from room_templates import WALKABLE_TILES

class BaseState:
    """A base class for all game states to inherit from."""
    def __init__(self, game):
        self.game = game
    def handle_events(self, event):
        raise NotImplementedError
    def update(self):
        raise NotImplementedError
    def draw(self, screen):
        raise NotImplementedError

class TitleScreen(BaseState):
    """The main menu screen."""
    def __init__(self, game):
        super().__init__(game)
        self.menu_options = ['New Game', 'Continue', 'Quit']
        self.selected_index = 0
        self.title_font = load_font(FONT_NAME, 100)
        self.menu_font = load_font(FONT_NAME, 50)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.selected_index = (self.selected_index - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN: self.selected_index = (self.selected_index + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN: self.select_option()
            elif event.key == pygame.K_f: self.game.toggle_fullscreen()

    def select_option(self):
        option = self.menu_options[self.selected_index]
        if option == 'New Game': self.game.change_state(game_states.CharCreationScreen(self.game))
        elif option == 'Continue': print("Continue selected (not implemented)")
        elif option == 'Quit': self.game.quit()

    def update(self): pass

    def draw(self, screen):
        screen.fill(BLACK)
        draw_text(screen, "ASCII RPG", screen.get_width()//2, screen.get_height()//4, self.title_font, WHITE, center=True)
        for i, option in enumerate(self.menu_options):
            y_pos = screen.get_height() // 2 + i * 60
            color = YELLOW if i == self.selected_index else WHITE
            draw_text(screen, option, screen.get_width()//2, y_pos, self.menu_font, color, center=True)

class CharCreationScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.font = load_font(FONT_NAME, 32)
        self.header_font = load_font(FONT_NAME, 42)
        self.step = 0
        self.stats = {'Str': 30, 'Dex': 30, 'Int': 30}
        self.points_to_assign = [50, 40, 30]
        self.assigned_stats = []
        self.races = ['Human', 'Elf', 'Dwarf']
        self.paths = ['Warrior', 'Rogue', 'Sorcerer']
        self.all_skills = ['Agility', 'Aware', 'Bravery', 'Dodge', 'Escape', 'Locks', 'Lucky', 'Magic', 'Strong', 'Traps']
        self.chosen_skills = []
        self.selections = {0: 0, 1: 0, 2: 0, 3:0, 4:0}
        self.current_selection_index = 0

    def get_current_options(self):
        if self.step == 0: return list(self.stats.keys())
        if self.step == 1: return self.races
        if self.step == 2: return self.paths
        if self.step == 3: 
            pre_bonus_skills = self.get_pre_bonus_skills()
            return [s for s in self.all_skills if s not in pre_bonus_skills and s not in self.chosen_skills]
        if self.step == 4: return ["Begin Adventure"]
        return []
    
    def get_pre_bonus_skills(self):
        skills_with_bonuses = set()
        path = self.paths[self.selections[2]]
        race = self.races[self.selections[1]]
        if path == 'Warrior': skills_with_bonuses.update(['Bravery', 'Escape'])
        if path == 'Rogue': skills_with_bonuses.update(['Locks', 'Traps'])
        if path == 'Sorcerer': skills_with_bonuses.update(['Magic', 'Lucky'])
        if race == 'Dwarf': skills_with_bonuses.add('Strong')
        if race == 'Elf': skills_with_bonuses.add('Dodge')
        if race == 'Human': skills_with_bonuses.add('Aware')
        return list(skills_with_bonuses)

    def make_selection(self):
        if self.step == 0:
            stat_key = self.get_current_options()[self.current_selection_index]
            if stat_key not in self.assigned_stats:
                point_val = self.points_to_assign[len(self.assigned_stats)]
                self.stats[stat_key] = point_val
                self.assigned_stats.append(stat_key)
                if len(self.assigned_stats) == len(self.points_to_assign):
                    self.step += 1; self.current_selection_index = 0
        elif self.step == 1:
            self.selections[1] = self.current_selection_index
            self.step += 1; self.current_selection_index = 0
        elif self.step == 2:
            self.selections[2] = self.current_selection_index
            self.step += 1; self.current_selection_index = 0
        elif self.step == 3:
            skill_to_add = self.get_current_options()[self.current_selection_index]
            self.chosen_skills.append(skill_to_add)
            if len(self.chosen_skills) == 2:
                self.step += 1; self.current_selection_index = 0
        elif self.step == 4:
            self.finish_creation()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            options = self.get_current_options()
            if not options: return
            if event.key == pygame.K_UP: self.current_selection_index = (self.current_selection_index - 1) % len(options)
            elif event.key == pygame.K_DOWN: self.current_selection_index = (self.current_selection_index + 1) % len(options)
            elif event.key == pygame.K_RETURN: self.make_selection()
            elif event.key == pygame.K_f: self.game.toggle_fullscreen()

    def finish_creation(self):
        race = self.races[self.selections[1]]
        path = self.paths[self.selections[2]]
        
        if path == 'Warrior': self.stats['Str'] += 10; self.stats['Dex'] -= 5; self.stats['Int'] -= 5
        elif path == 'Rogue': self.stats['Dex'] += 10; self.stats['Int'] -= 5; self.stats['Str'] -= 5
        elif path == 'Sorcerer': self.stats['Int'] += 10; self.stats['Dex'] -= 5; self.stats['Str'] -= 5
        
        if race == 'Dwarf': self.stats['Str'] += 5; self.stats['Int'] -= 5
        elif race == 'Elf': self.stats['Dex'] += 5; self.stats['Str'] -= 5
        elif race == 'Human': self.stats['Int'] += 5; self.stats['Dex'] -= 5
            
        self.game.player_data = {
            "name": "Adventurer", "race": race, "hero_path": path,
            "stats": {"str": self.stats['Str'], "dex": self.stats['Dex'], "int": self.stats['Int'], "hp": 20},
            "info": {"life": 3, "rep": 1, "fate": 3}, "equipment": {}, "inventory": [],
            "skills_choice": self.chosen_skills
        }
        try:
            with open("player.json", "w") as f:
                json.dump(self.game.player_data, f, indent=4)
            print("Player data saved to player.json")
        except Exception as e:
            print(f"Could not save player data: {e}")
        self.game.change_state(game_states.GameplayScreen(self.game))

    def update(self): pass

    def draw(self, screen):
        screen.fill(BLACK)
        w, h = screen.get_size()
        draw_text(screen, "Create Your Adventurer", w//2, 50, self.header_font, WHITE, center=True)
        
        y_pos = 120
        draw_text(screen, "1. Characteristics", w//2, y_pos, self.font, GREY if self.step > 0 else WHITE, center=True)
        points_left = len(self.points_to_assign) - len(self.assigned_stats)
        if points_left > 0:
            draw_text(screen, f"Assign: {self.points_to_assign[len(self.assigned_stats)]}", w//2, y_pos + 30, self.font, WHITE, center=True)
        for i, (key, value) in enumerate(self.stats.items()):
            color = WHITE
            if self.step == 0 and i == self.current_selection_index: color = YELLOW
            if key in self.assigned_stats: color = GREEN
            draw_text(screen, f"{key}: {value}", w//2, y_pos + 60 + i * 30, self.font, color, center=True)
        
        y_pos += 160
        draw_text(screen, "2. Race", w//2, y_pos, self.font, GREY if self.step > 1 else WHITE, center=True)
        for i, race in enumerate(self.races):
            color = GREY
            if self.step == 1 and i == self.current_selection_index: color = YELLOW
            if self.step > 1 and i == self.selections[1]: color = GREEN
            draw_text(screen, race, w//2, y_pos + 30 + i * 30, self.font, color, center=True)

        y_pos += 130
        draw_text(screen, "3. Hero Path", w//2, y_pos, self.font, GREY if self.step > 2 else WHITE, center=True)
        for i, path in enumerate(self.paths):
            color = GREY
            if self.step == 2 and i == self.current_selection_index: color = YELLOW
            if self.step > 2 and i == self.selections[2]: color = GREEN
            draw_text(screen, path, w//2, y_pos + 30 + i * 30, self.font, color, center=True)

        y_pos += 130
        draw_text(screen, "4. Skill Bonus (+5 to two skills)", w//2, y_pos, self.font, GREY if self.step > 3 else WHITE, center=True)
        if self.step == 3:
            options = self.get_current_options()
            for i, skill in enumerate(options):
                color = YELLOW if i == self.current_selection_index else WHITE
                draw_text(screen, skill, w//2, y_pos + 30 + i * 25, load_font(FONT_NAME, 20), color, center=True)
        elif self.step > 3:
            for i, skill in enumerate(self.chosen_skills):
                 draw_text(screen, f"+5 {skill}", w//2, y_pos + 30 + i * 25, load_font(FONT_NAME, 20), GREEN, center=True)

        if self.step == 4:
            draw_text(screen, "Begin Adventure", w//2, h - 70, self.header_font, YELLOW, center=True)

class GameplayScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.world = World()
        self.font = load_font(FONT_NAME, FONT_SIZE)
        self.ui_font = load_font(FONT_NAME, UI_FONT_SIZE)
        
        self.dungeon_map = DungeonMap()
        self.player_id = self.create_player()
        self.manager_id = self.create_manager()
        self.message_log.add_message("Welcome to the dungeon!", YELLOW)

    def create_player(self):
        player_id = self.world.create_entity()
        p_data = self.game.player_data
        
        # --- FIX START ---
        # Player starts in world (0,0) at the designated start pos of the room template
        start_area = self.dungeon_map.get_area(0, 0)
        start_pos_local = start_area.template.get('start_pos', (1, 1))
        self.world.add_component(player_id, Position(0, 0, start_pos_local[0], start_pos_local[1]))
        # --- FIX END ---

        self.world.add_component(player_id, Renderable('@', YELLOW))
        self.world.add_component(player_id, Player())
        self.world.add_component(player_id, Info(p_data['name'], p_data['race'], p_data['hero_path'], p_data['info']['life']))
        self.world.add_component(player_id, Inventory())
        self.world.add_component(player_id, Equipment())
        self.world.add_component(player_id, Resources())

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
                self.game.push_state(game_states.InventoryScreen(self.game, self.world, self.player_id))
            elif event.key == pygame.K_f:
                self.game.toggle_fullscreen()

    def move_player(self, key):
        """Handles player movement, collision, and room transitions."""
        player_pos = self.world.get_component(self.player_id, "Position")
        current_area = self.dungeon_map.get_area(player_pos.world_x, player_pos.world_y)
        
        dx, dy = 0, 0
        if key == pygame.K_UP: dy = -1
        elif key == pygame.K_DOWN: dy = 1
        elif key == pygame.K_LEFT: dx = -1
        elif key == pygame.K_RIGHT: dx = 1

        new_local_x = player_pos.local_x + dx
        new_local_y = player_pos.local_y + dy

        target_tile = current_area.room_data[new_local_y][new_local_x]

        if target_tile in WALKABLE_TILES:
            is_exit = False
            exit_direction = None
            for direction, coords in current_area.template['exits'].items():
                if coords == (new_local_x, new_local_y):
                    is_exit = True
                    exit_direction = direction
                    break
            
            if is_exit:
                world_dx, world_dy = {'north':(0,-1), 'south':(0,1), 'east':(1,0), 'west':(-1,0)}[exit_direction]
                player_pos.world_x += world_dx
                player_pos.world_y += world_dy
                
                # Tell the generator what kind of entrance is needed
                opposite_dir = {'north':'south', 'south':'north', 'east':'west', 'west':'east'}[exit_direction]
                new_area = self.dungeon_map.generate_area(player_pos.world_x, player_pos.world_y, required_exit=opposite_dir)
                # --- MODIFICATION END ---
                entry_coords = new_area.template['exits'][opposite_dir]
                player_pos.local_x, player_pos.local_y = entry_coords
                
                self.message_log.add_message("You enter a new area.", YELLOW)
                self.advance_turn()
            else:
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
        self.game.push_state(game_states.CombatScreen(self.game, self.world, self.player_id, monster_id, monster_key, current_area))

    def update(self): pass

    def draw(self, screen):
        screen.fill(BLACK)
        player_pos = self.world.get_component(self.player_id, "Position")
        current_area = self.dungeon_map.get_area(player_pos.world_x, player_pos.world_y)
        char_w, char_h = self.font.size(' ')

        screen_center_x = (GRID_WIDTH // 2)
        screen_center_y = (GRID_HEIGHT // 2)

        cam_local_x = player_pos.local_x - screen_center_x
        cam_local_y = player_pos.local_y - screen_center_y

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                map_x = cam_local_x + x
                map_y = cam_local_y + y

                if 0 <= map_y < len(current_area.room_data) and 0 <= map_x < len(current_area.room_data[map_y]):
                    char = current_area.room_data[map_y][map_x]
                    color = GREY if char == '#' else DARK_GREY
                    if char in WALKABLE_TILES: color = DARK_GREY
                    draw_text(screen, char, x * char_w, y * char_h, self.font, color)
        
        player_render = self.world.get_component(self.player_id, "Renderable")
        draw_text(screen, player_render.char, screen_center_x * char_w, screen_center_y * char_h, self.font, player_render.color)
        
        log_y = screen.get_height() - (self.message_log.max_lines * 20) - 10
        for msg, color in self.message_log.messages:
            draw_text(screen, msg, 10, log_y, self.ui_font, color)
            log_y += 20
        
        stats = self.world.get_component(self.player_id, "Stats")
        resources = self.world.get_component(self.player_id, "Resources")
        hp_text = f"HP: {stats.current_hp}/{stats.max_hp}"
        draw_text(screen, hp_text, 10, 10, self.ui_font, GREEN)
        draw_text(screen, f"Oil: {resources.oil} Food: {resources.food} Picks: {resources.picks}", 10, 35, self.ui_font, ORANGE)

class CombatScreen(BaseState):
    def __init__(self, game, world, player_id, monster_id, monster_key, area):
        super().__init__(game)
        self.world = world
        self.player_id = player_id
        self.monster_id = monster_id
        self.monster_key = monster_key 
        self.area = area 
        self.font = load_font(FONT_NAME, 28)
        self.log_font = load_font(FONT_NAME, 22)
        self.combat_log = ["Combat has begun!"]
        self.player_action = None
        self.menu_options = ['Attack', 'Flee']
        self.selected_index = 0
        self.is_combat_over = False

    def handle_events(self, event):
        if self.is_combat_over:
            if event.type == pygame.KEYDOWN: self.game.pop_state() 
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.selected_index = (self.selected_index - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN: self.selected_index = (self.selected_index + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN: self.player_action = self.menu_options[self.selected_index]
            elif event.key == pygame.K_f: self.game.toggle_fullscreen()

    def update(self):
        if self.player_action and not self.is_combat_over:
            self.resolve_combat_round()
            self.player_action = None 
            self.check_for_end_of_combat()

    def resolve_combat_round(self):
        self.combat_log.clear()
        player_stats = self.world.get_component(self.player_id, "Stats")
        monster_stats = self.world.get_component(self.monster_id, "Stats")
        monster_info = self.world.get_component(self.monster_id, "Info")

        if self.player_action == 'Attack':
            roll = d100()
            if roll <= 10: award_experience(self.world, self.player_id, 'str', 1)
            if roll <= player_stats.adj_str:
                damage = random.randint(1, 6) + player_stats.damage_mod - monster_stats.defense
                damage = max(0, damage)
                monster_stats.current_hp -= damage
                self.combat_log.append(f"Player hits {monster_info.name} for {damage} damage! (Rolled {roll})")
            else:
                self.combat_log.append(f"Player misses! (Rolled {roll})")
        elif self.player_action == 'Flee':
            self.combat_log.append("Fleeing not yet implemented. You attack instead.")
            self.player_action = 'Attack'
            self.resolve_combat_round()
            return

        if monster_stats.current_hp > 0:
            roll = d100()
            if roll <= monster_stats.av:
                damage = random.randint(1, 6) + monster_stats.damage_mod - player_stats.defense
                damage = max(0, damage)
                player_stats.current_hp -= damage
                self.combat_log.append(f"{monster_info.name} hits Player for {damage} damage! (Rolled {roll})")
            else:
                self.combat_log.append(f"{monster_info.name} misses! (Rolled {roll})")

    def generate_loot(self):
        monster_data = self.game.monsters_data[self.monster_key]
        loot_table_str = monster_data.get("loot_table", "")
        table_codes = loot_table_str.split('/')
        chosen_code = random.choice(table_codes)
        table_key = chosen_code[0]
        num_rolls = 1
        if len(chosen_code) > 1 and chosen_code[1:].isdigit(): num_rolls = int(chosen_code[1:])
        loot_map = {'A': 'armor', 'I': 'items', 'W': 'weapons', 'P': 'parts'}
        category = loot_map.get(table_key)
        if not category: return
        player_inventory = self.world.get_component(self.player_id, "Inventory")
        for _ in range(num_rolls):
            if category in self.game.items_data and self.game.items_data[category]:
                item_key = random.choice(list(self.game.items_data[category].keys()))
                item_data = self.game.items_data[category][item_key]
                item_id = self.world.create_entity()
                self.world.add_component(item_id, Item(name=item_data['name'], value=item_data['value'], slot=item_data['slot'], bonuses=item_data.get('bonuses', {})))
                player_inventory.items.append(item_id)
                self.combat_log.append(f"You found: {item_data['name']}!")

    def check_for_end_of_combat(self):
        player_stats = self.world.get_component(self.player_id, "Stats")
        player_info = self.world.get_component(self.player_id, "Info")
        monster_stats = self.world.get_component(self.monster_id, "Stats")

        if monster_stats.current_hp <= 0:
            self.is_combat_over = True
            monster_info = self.world.get_component(self.monster_id, "Info")
            self.combat_log.append(f"{monster_info.name} defeated!")
            self.generate_loot()
            
            if self.area:
                self.area.type = 'Yellow'
                self.area.color = YELLOW
                gameplay_screen = self.game.states[-2] 
                if isinstance(gameplay_screen, game_states.GameplayScreen):
                    gameplay_screen.message_log.add_message("The area is now clear.", GREEN)

            self.combat_log.append("Press any key to continue.")
            self.world.remove_entity(self.monster_id)
        elif player_stats.current_hp <= 0:
            player_info.life_points -= 1
            if player_info.life_points >= 0:
                player_stats.current_hp = player_stats.max_hp
                self.combat_log.append(f"You have fallen, but a Life Point saves you! ({player_info.life_points} left)")
            else:
                self.game.change_state(game_states.GameOverScreen(self.game))
                
    def draw(self, screen):
        screen.fill(BLACK)
        player_stats = self.world.get_component(self.player_id, "Stats")
        player_info = self.world.get_component(self.player_id, "Info")
        monster_exists = self.monster_id in self.world.entities
        if monster_exists:
            monster_stats = self.world.get_component(self.monster_id, "Stats")
            monster_info = self.world.get_component(self.monster_id, "Info")

        draw_text(screen, player_info.name, 150, 100, self.font, WHITE, center=True)
        hp_text_p = f"HP: {player_stats.current_hp} / {player_stats.max_hp}"
        hp_color_p = GREEN if player_stats.current_hp/player_stats.max_hp > 0.5 else YELLOW if player_stats.current_hp/player_stats.max_hp > 0.2 else RED
        draw_text(screen, hp_text_p, 150, 140, self.font, hp_color_p, center=True)
        draw_text(screen, f"Lives: {player_info.life_points}", 150, 180, self.font, WHITE, center=True)

        if monster_exists and monster_stats:
            draw_text(screen, monster_info.name, screen.get_width() - 150, 100, self.font, WHITE, center=True)
            hp_text_m = f"HP: {monster_stats.current_hp} / {monster_stats.max_hp}"
            hp_color_m = GREEN if monster_stats.current_hp/monster_stats.max_hp > 0.5 else YELLOW if monster_stats.current_hp/monster_stats.max_hp > 0.2 else RED
            draw_text(screen, hp_text_m, screen.get_width() - 150, 140, self.font, hp_color_m, center=True)

        log_y = screen.get_height() - (len(self.combat_log) * 30) - 150
        for i, msg in enumerate(self.combat_log):
            draw_text(screen, msg, screen.get_width()//2, log_y + i * 30, self.log_font, WHITE, center=True)

        if not self.is_combat_over:
            menu_y = screen.get_height() - 100
            for i, option in enumerate(self.menu_options):
                color = YELLOW if i == self.selected_index else WHITE
                draw_text(screen, option, screen.get_width()//2, menu_y + i * 40, self.font, color, center=True)

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
        message_log = self.world.get_component(self.game.states[-2].manager_id, "MessageLog")
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

class GameOverScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.font = load_font(FONT_NAME, 80)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.game.quit()

    def update(self): pass

    def draw(self, screen):
        screen.fill(BLACK)
        draw_text(screen, "GAME OVER", screen.get_width()//2, screen.get_height()//2, self.font, RED, center=True)
        draw_text(screen, "Press Enter to quit", screen.get_width()//2, screen.get_height()//2 + 80, load_font(FONT_NAME, 30), WHITE, center=True)
