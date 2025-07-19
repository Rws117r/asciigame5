# combat_states.py
# This file contains the combat-related game states

import pygame
import random
from config import *
from systems import *
from components import Item
from menu_states import BaseState

def d100():
    """Helper function for dice rolls."""
    return random.randint(1, 100)

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
        self.small_font = load_font(FONT_NAME, 16)
        self.combat_log = ["Combat has begun!"]
        self.player_action = None
        self.menu_options = ['Attack', 'Change Equipment', 'Cast Spell', 'Use Belt Item', 'Flee']
        self.selected_index = 0
        self.is_combat_over = False
        self.in_submenu = False
        self.current_submenu = None
        self.submenu_items = []
        self.submenu_selected = 0

    def handle_events(self, event):
        if self.is_combat_over:
            if event.type == pygame.KEYDOWN: self.game.pop_state() 
            return
            
        if event.type == pygame.KEYDOWN:
            if self.in_submenu:
                self.handle_submenu_input(event)
            else:
                self.handle_main_menu_input(event)

    def handle_main_menu_input(self, event):
        if event.key == pygame.K_UP: 
            self.selected_index = (self.selected_index - 1) % len(self.menu_options)
        elif event.key == pygame.K_DOWN: 
            self.selected_index = (self.selected_index + 1) % len(self.menu_options)
        elif event.key == pygame.K_RETURN: 
            self.select_main_action()
        elif event.key == pygame.K_f: 
            self.game.toggle_fullscreen()

    def handle_submenu_input(self, event):
        if event.key == pygame.K_UP:
            self.submenu_selected = (self.submenu_selected - 1) % len(self.submenu_items)
        elif event.key == pygame.K_DOWN:
            self.submenu_selected = (self.submenu_selected + 1) % len(self.submenu_items)
        elif event.key == pygame.K_RETURN:
            self.select_submenu_action()
        elif event.key == pygame.K_ESCAPE:
            self.in_submenu = False
            self.current_submenu = None

    def select_main_action(self):
        action = self.menu_options[self.selected_index]
        
        if action == 'Attack':
            self.player_action = 'Attack'
        elif action == 'Flee':
            self.player_action = 'Flee'
        elif action == 'Change Equipment':
            self.open_equipment_submenu()
        elif action == 'Cast Spell':
            self.open_spell_submenu()
        elif action == 'Use Belt Item':
            self.open_belt_item_submenu()

    def open_equipment_submenu(self):
        """Open submenu for changing equipment during combat."""
        self.in_submenu = True
        self.current_submenu = 'equipment'
        self.submenu_items = []
        self.submenu_selected = 0
        
        inventory = self.world.get_component(self.player_id, "Inventory")
        equipment = self.world.get_component(self.player_id, "Equipment")
        
        # Add inventory items that can be equipped
        for item_id in inventory.items:
            item = self.world.get_component(item_id, "Item")
            if item and item.slot in equipment.slots:
                self.submenu_items.append({
                    'type': 'equip',
                    'item_id': item_id,
                    'name': f"Equip {item.name}",
                    'slot': item.slot
                })
        
        # Add equipped items that can be unequipped
        for slot, item_id in equipment.slots.items():
            if item_id:
                item = self.world.get_component(item_id, "Item")
                if item:
                    self.submenu_items.append({
                        'type': 'unequip',
                        'item_id': item_id,
                        'name': f"Unequip {item.name}",
                        'slot': slot
                    })
        
        if not self.submenu_items:
            self.submenu_items.append({'type': 'none', 'name': "No equipment changes available"})

    def open_spell_submenu(self):
        """Open submenu for casting spells during combat using D100 rules."""
        from spell_system import enhanced_open_spell_submenu
        enhanced_open_spell_submenu(self)

    def open_belt_item_submenu(self):
        """Open submenu for using belt items (consumables) during combat."""
        self.in_submenu = True
        self.current_submenu = 'belt'
        self.submenu_items = []
        self.submenu_selected = 0
        
        inventory = self.world.get_component(self.player_id, "Inventory")
        
        # Find consumable items in inventory
        for item_id in inventory.items:
            item = self.world.get_component(item_id, "Item")
            if item and item.slot == 'consumable':
                effect_text = ""
                if hasattr(item, 'effect'):
                    if item.effect == 'heal':
                        effect_text = f" (Heal {getattr(item, 'effect_value', 4)} HP)"
                    elif item.effect == 'add_oil':
                        effect_text = f" (+{getattr(item, 'effect_value', 1)} Oil)"
                    elif item.effect == 'add_food':
                        effect_text = f" (+{getattr(item, 'effect_value', 1)} Food)"
                
                self.submenu_items.append({
                    'type': 'consumable',
                    'item_id': item_id,
                    'name': f"{item.name}{effect_text}"
                })
        
        if not self.submenu_items:
            self.submenu_items.append({'type': 'none', 'name': "No belt items available"})

    def select_submenu_action(self):
        if not self.submenu_items or self.submenu_selected >= len(self.submenu_items):
            return
            
        selected_item = self.submenu_items[self.submenu_selected]
        
        if selected_item['type'] == 'none':
            self.in_submenu = False
            return
        
        if self.current_submenu == 'equipment':
            self.handle_equipment_action(selected_item)
        elif self.current_submenu == 'spell':
            self.handle_spell_action(selected_item)
        elif self.current_submenu == 'belt':
            self.handle_belt_action(selected_item)
        
        self.in_submenu = False
        self.current_submenu = None

    def handle_equipment_action(self, item_data):
        """Handle equipping/unequipping items during combat."""
        equipment = self.world.get_component(self.player_id, "Equipment")
        inventory = self.world.get_component(self.player_id, "Inventory")
        
        if item_data['type'] == 'equip':
            # Equip item
            item_id = item_data['item_id']
            slot = item_data['slot']
            
            # If slot is occupied, move current item to inventory
            if equipment.slots[slot] is not None:
                old_item = equipment.slots[slot]
                inventory.items.append(old_item)
            
            # Equip new item
            equipment.slots[slot] = item_id
            inventory.items.remove(item_id)
            
            item = self.world.get_component(item_id, "Item")
            self.player_action = f"Equipped {item.name}"
            
        elif item_data['type'] == 'unequip':
            # Unequip item
            item_id = item_data['item_id']
            slot = item_data['slot']
            
            equipment.slots[slot] = None
            inventory.items.append(item_id)
            
            item = self.world.get_component(item_id, "Item")
            self.player_action = f"Unequipped {item.name}"
        
        # Update player stats after equipment change
        update_player_stats(self.world, self.player_id)

    def handle_spell_action(self, spell_item):
        """Handle casting spells during combat using D100 rules."""
        from spell_system import enhanced_handle_spell_action
        enhanced_handle_spell_action(self, spell_item)

    def handle_belt_action(self, item_data):
        """Handle using consumable items during combat."""
        item_id = item_data['item_id']
        item = self.world.get_component(item_id, "Item")
        inventory = self.world.get_component(self.player_id, "Inventory")
        stats = self.world.get_component(self.player_id, "Stats")
        resources = self.world.get_component(self.player_id, "Resources")
        
        # Use the item
        if hasattr(item, 'effect'):
            if item.effect == 'heal':
                heal_amount = getattr(item, 'effect_value', 4)
                stats.current_hp = min(stats.max_hp, stats.current_hp + heal_amount)
                self.player_action = f"Used {item.name}, healed {heal_amount} HP!"
            elif item.effect == 'add_oil':
                oil_amount = getattr(item, 'effect_value', 1)
                resources.oil += oil_amount
                self.player_action = f"Used {item.name}, gained {oil_amount} oil!"
            elif item.effect == 'add_food':
                food_amount = getattr(item, 'effect_value', 1)
                resources.food += food_amount
                self.player_action = f"Used {item.name}, gained {food_amount} food!"
            else:
                self.player_action = f"Used {item.name}!"
        else:
            self.player_action = f"Used {item.name}!"
        
        # Remove item from inventory
        inventory.items.remove(item_id)
        self.world.remove_entity(item_id)

    def update(self):
        if self.player_action and not self.is_combat_over and not self.in_submenu:
            if self.player_action in ['Attack', 'Flee']:
                self.resolve_combat_round()
            else:
                # Non-attack actions still consume the turn but don't trigger normal combat
                self.combat_log.clear()
                self.combat_log.append(self.player_action)
                self.monster_turn()
            
            self.player_action = None 
            self.check_for_end_of_combat()

    def monster_turn(self):
        """Handle the monster's turn."""
        player_stats = self.world.get_component(self.player_id, "Stats")
        monster_stats = self.world.get_component(self.monster_id, "Stats")
        monster_info = self.world.get_component(self.monster_id, "Info")
        
        if monster_stats.current_hp > 0:
            roll = d100()
            if roll <= monster_stats.av:
                damage = random.randint(1, 6) + monster_stats.damage_mod - player_stats.defense
                damage = max(0, damage)
                player_stats.current_hp -= damage
                self.combat_log.append(f"{monster_info.name} hits Player for {damage} damage! (Rolled {roll})")
            else:
                self.combat_log.append(f"{monster_info.name} misses! (Rolled {roll})")

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

        self.monster_turn()

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
                # Find the gameplay screen in the state stack
                from gameplay_states import GameplayScreen
                for state in reversed(self.game.states):
                    if isinstance(state, GameplayScreen):
                        state.message_log.add_message("The area is now clear.", GREEN)
                        break

            self.combat_log.append("Press any key to continue.")
            self.world.remove_entity(self.monster_id)
        elif player_stats.current_hp <= 0:
            player_info.life_points -= 1
            if player_info.life_points >= 0:
                player_stats.current_hp = player_stats.max_hp
                self.combat_log.append(f"You have fallen, but a Life Point saves you! ({player_info.life_points} left)")
            else:
                from menu_states import GameOverScreen
                self.game.change_state(GameOverScreen(self.game))
                
    def draw(self, screen):
        screen.fill(BLACK)
        player_stats = self.world.get_component(self.player_id, "Stats")
        player_info = self.world.get_component(self.player_id, "Info")
        monster_exists = self.monster_id in self.world.entities
        if monster_exists:
            monster_stats = self.world.get_component(self.monster_id, "Stats")
            monster_info = self.world.get_component(self.monster_id, "Info")

        # Draw player info
        draw_text(screen, player_info.name, 150, 100, self.font, WHITE, center=True)
        hp_text_p = f"HP: {player_stats.current_hp} / {player_stats.max_hp}"
        hp_color_p = GREEN if player_stats.current_hp/player_stats.max_hp > 0.5 else YELLOW if player_stats.current_hp/player_stats.max_hp > 0.2 else RED
        draw_text(screen, hp_text_p, 150, 140, self.font, hp_color_p, center=True)
        draw_text(screen, f"Lives: {player_info.life_points}", 150, 180, self.font, WHITE, center=True)

        # Draw monster info
        if monster_exists and monster_stats:
            draw_text(screen, monster_info.name, screen.get_width() - 150, 100, self.font, WHITE, center=True)
            hp_text_m = f"HP: {monster_stats.current_hp} / {monster_stats.max_hp}"
            hp_color_m = GREEN if monster_stats.current_hp/monster_stats.max_hp > 0.5 else YELLOW if monster_stats.current_hp/monster_stats.max_hp > 0.2 else RED
            draw_text(screen, hp_text_m, screen.get_width() - 150, 140, self.font, hp_color_m, center=True)

        # Draw combat log
        log_y = screen.get_height() - (len(self.combat_log) * 30) - 200
        for i, msg in enumerate(self.combat_log):
            draw_text(screen, msg, screen.get_width()//2, log_y + i * 30, self.log_font, WHITE, center=True)

        # Draw menus
        if not self.is_combat_over:
            if self.in_submenu:
                self.draw_submenu(screen)
            else:
                self.draw_main_menu(screen)

    def draw_main_menu(self, screen):
        """Draw the main combat action menu."""
        menu_y = screen.get_height() - 120
        for i, option in enumerate(self.menu_options):
            color = YELLOW if i == self.selected_index else WHITE
            draw_text(screen, option, screen.get_width()//2, menu_y + i * 25, self.font, color, center=True)

    def draw_submenu(self, screen):
        """Draw the current submenu."""
        # Draw background
        menu_bg = pygame.Rect(screen.get_width()//2 - 200, screen.get_height()//2 - 150, 400, 300)
        pygame.draw.rect(screen, DARK_GREY, menu_bg)
        pygame.draw.rect(screen, WHITE, menu_bg, 2)
        
        # Draw title
        title = f"{self.current_submenu.title()} Actions"
        draw_text(screen, title, screen.get_width()//2, menu_bg.y + 20, self.font, YELLOW, center=True)
        
        # Draw items
        start_y = menu_bg.y + 60
        for i, item in enumerate(self.submenu_items):
            color = YELLOW if i == self.submenu_selected else WHITE
            draw_text(screen, item['name'], screen.get_width()//2, start_y + i * 25, self.small_font, color, center=True)
        
        # Draw instructions
        draw_text(screen, "Enter: Select | Escape: Back", screen.get_width()//2, menu_bg.bottom - 30, self.small_font, GREY, center=True)