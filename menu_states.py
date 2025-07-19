# menu_states.py
# This file contains the menu-related game states (title screen, character creation, etc.)

import pygame
import json
import random
from config import *
from systems import load_font, draw_text

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
        from gameplay_states import GameplayScreen
        from menu_states import CharCreationScreen
        
        option = self.menu_options[self.selected_index]
        if option == 'New Game': self.game.change_state(CharCreationScreen(self.game))
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

    def generate_starting_equipment(self):
        """Generate starting equipment: 1 weapon and 3 armor pieces, plus consumables."""
        starting_items = []
        
        # Roll once on weapons table (Table W)
        if 'weapons' in self.game.items_data and self.game.items_data['weapons']:
            weapon_key = random.choice(list(self.game.items_data['weapons'].keys()))
            weapon_data = self.game.items_data['weapons'][weapon_key]
            starting_items.append({
                'type': 'weapon',
                'key': weapon_key,
                'data': weapon_data
            })
        
        # Roll three times on armor table (Table A)
        equipped_slots = set()
        for _ in range(3):
            attempts = 0
            while attempts < 10:  # Prevent infinite loop
                if 'armor' in self.game.items_data and self.game.items_data['armor']:
                    armor_key = random.choice(list(self.game.items_data['armor'].keys()))
                    armor_data = self.game.items_data['armor'][armor_key]
                    
                    # Check if we already have armor for this slot
                    if armor_data['slot'] not in equipped_slots:
                        starting_items.append({
                            'type': 'armor',
                            'key': armor_key,
                            'data': armor_data
                        })
                        equipped_slots.add(armor_data['slot'])
                        break
                attempts += 1
        
        # Add consumables: 20 oil, 10 food, 15 picks, 3 Lesser Healing Potions
        consumables = [
            {'name': 'Lantern Oil (Flask)', 'effect': 'add_oil', 'value': 30, 'amount': 20},
            {'name': 'Food (Leather Bag)', 'effect': 'add_food', 'value': 20, 'amount': 10}, 
            {'name': 'Lock Picks (Pouch)', 'effect': 'add_picks', 'value': 40, 'amount': 15},
            {'name': 'Potion of Lesser Healing', 'effect': 'heal', 'value': 80, 'amount': 3}
        ]
        
        for consumable in consumables:
            for _ in range(consumable['amount']):
                starting_items.append({
                    'type': 'consumable',
                    'key': f"starting_{consumable['name'].lower().replace(' ', '_')}",
                    'data': {
                        'name': consumable['name'],
                        'slot': 'consumable',
                        'value': consumable['value'],
                        'effect': consumable['effect']
                    }
                })
        
        return starting_items

    def finish_creation(self):
        race = self.races[self.selections[1]]
        path = self.paths[self.selections[2]]
        
        if path == 'Warrior': self.stats['Str'] += 10; self.stats['Dex'] -= 5; self.stats['Int'] -= 5
        elif path == 'Rogue': self.stats['Dex'] += 10; self.stats['Int'] -= 5; self.stats['Str'] -= 5
        elif path == 'Sorcerer': self.stats['Int'] += 10; self.stats['Dex'] -= 5; self.stats['Str'] -= 5
        
        if race == 'Dwarf': self.stats['Str'] += 5; self.stats['Int'] -= 5
        elif race == 'Elf': self.stats['Dex'] += 5; self.stats['Str'] -= 5
        elif race == 'Human': self.stats['Int'] += 5; self.stats['Dex'] -= 5
        
        # Generate starting equipment
        starting_equipment = self.generate_starting_equipment()
            
        self.game.player_data = {
            "name": "Adventurer", "race": race, "hero_path": path,
            "stats": {"str": self.stats['Str'], "dex": self.stats['Dex'], "int": self.stats['Int'], "hp": 20},
            "info": {"life": 3, "rep": 1, "fate": 3}, "equipment": {}, "inventory": [],
            "skills_choice": self.chosen_skills,
            "starting_equipment": starting_equipment  # Store for use in GameplayScreen
        }
        try:
            with open("player.json", "w") as f:
                json.dump(self.game.player_data, f, indent=4)
            print("Player data saved to player.json")
        except Exception as e:
            print(f"Could not save player data: {e}")
        
        from gameplay_states import GameplayScreen
        self.game.change_state(GameplayScreen(self.game))

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