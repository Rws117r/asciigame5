# main.py
# The main entry point for the game.

import pygame
import sys
import json

# Import the necessary classes from our new modules
from config import *
# --- MODIFICATION START ---
# Import the entire game_states module to ensure all its classes are loaded.
import game_states
# --- MODIFICATION END ---

class Game:
    """The main class that runs the game and manages states."""
    def __init__(self):
        pygame.init()

        self.win_width = 1280
        self.win_height = 720
        self.screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
        pygame.display.set_caption("D100 ASCII Dungeon")
        self.clock = pygame.time.Clock()
        self.running = True
        self.is_fullscreen = False
        
        # Load all game data on initialization
        self.monsters_data = self.load_json_data("monsters.json")
        self.items_data = self.load_json_data("items.json")
        self.player_data = None # Will be created in CharCreationScreen

        # --- MODIFICATION START ---
        # The state stack starts with the title screen, referenced through the module.
        self.states = [game_states.TitleScreen(self)]
        # --- MODIFICATION END ---

    def load_json_data(self, filepath):
        """Loads data from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {filepath}: {e}")
            self.quit()
            return {}

    def run(self):
        """The main game loop."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                # Pass events to the current state, which is always the last one in the list
                self.states[-1].handle_events(event)

            # Update the current state
            self.states[-1].update()
            
            # Draw the current state
            self.states[-1].draw(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)

    def change_state(self, new_state):
        """Replaces the entire state stack with a new state."""
        self.states = [new_state]

    def push_state(self, new_state):
        """Adds a new state on top of the stack (e.g., opening a menu)."""
        self.states.append(new_state)

    def pop_state(self):
        """Removes the top state from the stack (e.g., closing a menu)."""
        if len(self.states) > 1:
            self.states.pop()

    def toggle_fullscreen(self):
        """Switches between fullscreen and windowed mode."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)

    def quit(self):
        """Shuts down the game."""
        self.running = False
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = Game()
    game.run()
