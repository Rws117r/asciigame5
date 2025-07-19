# room_painter.py
# A standalone Pygame application for visually creating ASCII room templates.

import pygame
import json
import os
import pyperclip # A library to handle clipboard functionality. You may need to install it: pip install pyperclip
import copy

# --- CONFIGURATION ---
FONT_NAME = "JetBrainsMonoNerdFontMono-Regular.ttf"

PALETTES = {
    "Dungeon": ['#', '.', ',', '~', 'S', 'D', chr(9617), chr(9618), chr(9619), chr(9608)],
    "Nature": ['T', 't', '^', chr(0x2663), chr(0x2666), '~', ',', '.'],
    "Buildings": ['=', '|', '+', 'H', 'O', '-', '[', ']'],
    "Misc": [chr(11700), 'w', 'o', '^']
}

# --- CHARACTER COLOR MAPPING ---
CHAR_COLORS = {
    '#': (139, 69, 19), # Brown for walls
    'T': (0, 100, 0),     # Dark Green for Trees
    't': (50, 205, 50),   # Light Green for smaller trees/grass
    '~': (0, 0, 205),     # Blue for water
    'D': (210, 105, 30)   # A color for Doors
}

# --- NEW COLOR PALETTE ---
C_PANEL_BG = (172, 170, 178) # acaab2
C_BUTTON = (143, 127, 176) # 8f7fb0
C_BUTTON_ACTIVE = (116, 83, 128) # 745380
C_TEXT_INPUT = (59, 51, 102) # 3b3366
C_BORDER = (26, 24, 26) # 1a181a
C_TEXT_ON_LIGHT = (26, 24, 26) # 1a181a
C_TEXT_ON_DARK = (255, 243, 242) # fff3f2
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_YELLOW = (255, 255, 0)
C_ASCII_FLOOR = (80, 80, 80)

# --- UI LAYOUT ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TOP_BAR_HEIGHT = 30
TOOLBAR_WIDTH = 60 
BOTTOM_BAR_HEIGHT = 60
CANVAS_BG = C_BLACK 

def load_font(size):
    """Loads the custom font file, with a fallback to a system font."""
    try:
        return pygame.font.Font(FONT_NAME, size)
    except pygame.error:
        print(f"Warning: Font '{FONT_NAME}' not found. Falling back to system font 'Courier'.")
        return pygame.font.SysFont("Courier", size)

# --- NEW CLASS FOR UNDO/REDO ---
class HistoryManager:
    """Manages the undo and redo stacks for the grid state."""
    def __init__(self, initial_grid_data):
        self.undo_stack = [copy.deepcopy(initial_grid_data)]
        self.redo_stack = []
        self.max_history = 50

    def record_action(self, grid_data):
        """Adds a new state to the undo stack and clears the redo stack."""
        self.undo_stack.append(copy.deepcopy(grid_data))
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        """Moves the current state to the redo stack and returns the previous state."""
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            return copy.deepcopy(self.undo_stack[-1])
        return None

    def redo(self):
        """Moves a state from the redo stack to the undo stack and returns it."""
        if self.redo_stack:
            state_to_restore = self.redo_stack.pop()
            self.undo_stack.append(state_to_restore)
            return copy.deepcopy(state_to_restore)
        return None

class Grid:
    """Manages the grid data and drawing."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [['.' for _ in range(width)] for _ in range(height)]
        self.tile_size = 16
        self.surface = pygame.Surface((width * self.tile_size, height * self.tile_size))
        self.needs_redraw = True

    def draw(self, char_cache):
        """Draws the grid using a pre-rendered character cache for performance."""
        if not self.needs_redraw:
            return self.surface
            
        self.surface.fill(CANVAS_BG)
        for y, row in enumerate(self.data):
            for x, char in enumerate(row):
                char_surf = char_cache.get(char, char_cache.get('.', None))
                if char_surf:
                    self.surface.blit(char_surf, (x * self.tile_size, y * self.tile_size))
        
        self.needs_redraw = False
        return self.surface
    
    def set_char(self, x, y, char):
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.data[y][x] != char:
                self.data[y][x] = char
                self.needs_redraw = True
            
    def get_char(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.data[y][x]
        return None

    def resize(self, new_width, new_height):
        new_data = [['.' for _ in range(new_width)] for _ in range(new_height)]
        for y in range(min(self.height, new_height)):
            for x in range(min(self.width, new_width)):
                new_data[y][x] = self.data[y][x]
        self.width = new_width
        self.height = new_height
        self.data = new_data
        self.surface = pygame.Surface((self.width * self.tile_size, self.height * self.tile_size))
        self.needs_redraw = True
        
    def clear(self):
        self.data = [['.' for _ in range(self.width)] for _ in range(self.height)]
        self.needs_redraw = True

class Button:
    """A simple clickable button."""
    def __init__(self, rect, text, font, callback=None, data=None, text_color=C_TEXT_ON_DARK):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.data = data
        self.is_active = False
        self.text_surf = self.font.render(self.text, True, text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen):
        color = C_BUTTON_ACTIVE if self.is_active else C_BUTTON
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, C_BORDER, self.rect, 1)
        screen.blit(self.text_surf, self.text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback(self.data)
                return True
        return False

class TextInput:
    """A simple text input box."""
    def __init__(self, rect, font, initial_text=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = initial_text
        self.is_active = False
        self.text_surface = self.font.render(self.text, True, C_TEXT_ON_DARK)

    def draw(self, screen):
        color = C_TEXT_INPUT
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, C_BORDER, self.rect, 1)
        screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.is_active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.text_surface = self.font.render(self.text, True, C_TEXT_ON_DARK)

class Modal:
    """A pop-up window for prompts and inputs."""
    def __init__(self, title, painter_instance):
        self.painter = painter_instance
        self.title = title
        self.rect = pygame.Rect(0, 0, 400, 200)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.elements = {}
        self.is_active = True

    def handle_event(self, event):
        for el in self.elements.values():
            el.handle_event(event)

    def draw(self, screen):
        if not self.is_active: return
        dim_surf = pygame.Surface(screen.get_size())
        dim_surf.set_alpha(180)
        dim_surf.fill(C_BLACK)
        screen.blit(dim_surf, (0, 0))

        pygame.draw.rect(screen, C_PANEL_BG, self.rect)
        pygame.draw.rect(screen, C_BORDER, self.rect, 2)
        self.painter.draw_text(self.title, (self.rect.x + 20, self.rect.y + 20), color=C_TEXT_ON_LIGHT, font_size=24)
        
        for el in self.elements.values():
            el.draw(screen)

class RoomPainter:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ASCII Room Painter")
        self.clock = pygame.time.Clock()
        
        self.fonts = {
            12: load_font(12), 14: load_font(14),
            16: load_font(16), 24: load_font(24)
        }
        
        self.grid = Grid(40, 20)
        self.running = True
        
        self.current_palette = "Dungeon"
        self.current_char = PALETTES[self.current_palette][0]
        self.current_tool = 'brush'
        self.is_drawing = False
        self.draw_start_pos = (0, 0)
        
        self.selection_rect = None
        self.clipboard = None

        self.camera_offset = [0, 0]
        self.is_panning = False
        self.pan_start_pos = (0, 0)

        self.active_modal = None
        self.active_dropdown = None

        self.history = HistoryManager(self.grid.data)
        self.char_cache = self.create_char_cache()
        self.setup_ui()

    def create_char_cache(self):
        cache = {}
        font = load_font(self.grid.tile_size - 2)
        all_chars = set(c for p in PALETTES.values() for c in p)
        for char in all_chars:
            char_surface = pygame.Surface((self.grid.tile_size, self.grid.tile_size), pygame.SRCALPHA)
            color = CHAR_COLORS.get(char, C_WHITE if char != '.' else C_ASCII_FLOOR)
            text_surf = font.render(char, True, color)
            text_rect = text_surf.get_rect(center=(self.grid.tile_size / 2, self.grid.tile_size / 2))
            char_surface.blit(text_surf, text_rect)
            cache[char] = char_surface
        return cache

    def setup_ui(self):
        self.buttons = {}
        self.inputs = {}
        self.palette_buttons = {}
        
        font_ui = self.fonts[14]
        font_icon = self.fonts[24]

        self.buttons['file_menu'] = Button((0, 0, 80, TOP_BAR_HEIGHT), "File", font_ui, self.toggle_dropdown, 'file', C_TEXT_ON_LIGHT)
        self.buttons['palette_menu'] = Button((80, 0, 100, TOP_BAR_HEIGHT), "Palettes", font_ui, self.toggle_dropdown, 'palette', C_TEXT_ON_LIGHT)

        tool_x = SCREEN_WIDTH - TOOLBAR_WIDTH + 5
        tools = [
            {'id': 'brush', 'icon': chr(0xf00e3)}, {'id': 'line', 'icon': chr(0xf0624)},
            {'id': 'rectangle', 'icon': chr(0xf065f)}, {'id': 'ellipse', 'icon': chr(0xf0ea1)},
            {'id': 'fill', 'icon': chr(0xf0266)}, {'id': 'eraser', 'icon': chr(0xf01fe)},
            {'id': 'select', 'icon': chr(0xf05c6)}, {'id': 'paste', 'icon': chr(0xf429)}
        ]
        for i, tool in enumerate(tools):
            self.buttons[f'tool_{tool["id"]}'] = Button((tool_x, 10 + i * 55, 50, 50), tool['icon'], font_icon, self.set_tool, tool['id'])
        
        self.update_palette_buttons()
        export_x = SCREEN_WIDTH - TOOLBAR_WIDTH - 310
        bottom_y = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT + 10
        self.inputs['room_name'] = TextInput((export_x, bottom_y, 200, 30), font_ui, "my_room")
        self.buttons['copy'] = Button((export_x + 205, bottom_y, 95, 30), "Copy JSON", font_ui, self.copy_to_clipboard)
        self.json_output = ""

    def update_palette_buttons(self):
        self.palette_buttons.clear()
        font_ui = self.fonts[14]
        pal_x, pal_y = 10, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT + 10
        for i, char in enumerate(PALETTES[self.current_palette]):
            self.palette_buttons[f'char_{char}'] = Button((pal_x + (i * 35), pal_y, 30, 30), char, font_ui, self.set_char, char)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def screen_to_grid_coords(self, screen_pos):
        mx, my = screen_pos
        grid_x = int((mx - self.camera_offset[0]) // self.grid.tile_size)
        grid_y = int((my - self.camera_offset[1]) // self.grid.tile_size)
        return grid_x, grid_y

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            
            if self.active_modal:
                self.active_modal.handle_event(event)
                continue

            ui_handled = False
            if self.active_dropdown:
                if self.active_dropdown.handle_event(event):
                    ui_handled = True
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.active_dropdown.rect.collidepoint(event.pos):
                    if not (self.buttons['file_menu'].rect.collidepoint(event.pos) or self.buttons['palette_menu'].rect.collidepoint(event.pos)):
                        self.active_dropdown = None
            
            if ui_handled:
                continue

            for btn in self.buttons.values(): 
                if btn.handle_event(event): break
            for btn in self.palette_buttons.values(): 
                if btn.handle_event(event): break
            for inp in self.inputs.values(): 
                inp.handle_event(event)

            if event.type == pygame.KEYDOWN:
                ctrl_pressed = pygame.key.get_mods() & pygame.KMOD_CTRL
                if ctrl_pressed:
                    if event.key == pygame.K_z: self.undo()
                    elif event.key == pygame.K_y: self.redo()
                    elif event.key == pygame.K_c:
                        if self.selection_rect: self.copy_selection()
                    elif event.key == pygame.K_v: self.set_tool('paste')
                    elif event.key == pygame.K_a:
                        self.selection_rect = pygame.Rect(0, 0, self.grid.width, self.grid.height)
                elif event.key == pygame.K_DELETE:
                    if self.selection_rect: self.delete_selection()

            keys = pygame.key.get_pressed()
            is_panning_mode = keys[pygame.K_SPACE]

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if is_panning_mode:
                        self.is_panning = True
                        self.pan_start_pos = event.pos
                    elif event.pos[0] < SCREEN_WIDTH - TOOLBAR_WIDTH and event.pos[1] > TOP_BAR_HEIGHT and event.pos[1] < SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT:
                        self.is_drawing = True
                        self.draw_start_pos = self.screen_to_grid_coords(event.pos)
                        self.handle_draw(*self.draw_start_pos, record_history=False)
                elif event.button == 4: self.zoom(1)
                elif event.button == 5: self.zoom(-1)
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_panning: self.is_panning = False
                elif self.is_drawing:
                    self.is_drawing = False
                    grid_end_pos = self.screen_to_grid_coords(event.pos)
                    if self.current_tool in ['rectangle', 'ellipse', 'line']:
                        self.apply_shape(self.draw_start_pos, grid_end_pos)
                    elif self.current_tool == 'select':
                        min_x = min(self.draw_start_pos[0], grid_end_pos[0])
                        min_y = min(self.draw_start_pos[1], grid_end_pos[1])
                        max_x = max(self.draw_start_pos[0], grid_end_pos[0])
                        max_y = max(self.draw_start_pos[1], grid_end_pos[1])
                        self.selection_rect = pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
                    else:
                        self.history.record_action(self.grid.data)

            if event.type == pygame.MOUSEMOTION:
                if self.is_panning:
                    dx = event.pos[0] - self.pan_start_pos[0]
                    dy = event.pos[1] - self.pan_start_pos[1]
                    self.camera_offset[0] += dx
                    self.camera_offset[1] += dy
                    self.pan_start_pos = event.pos
                elif self.is_drawing and self.current_tool in ['brush', 'eraser']:
                    self.handle_draw(*self.screen_to_grid_coords(event.pos), record_history=False)

    def zoom(self, direction):
        old_tile_size = self.grid.tile_size
        if direction > 0: self.grid.tile_size += 2
        elif direction < 0: self.grid.tile_size -= 2
        self.grid.tile_size = max(8, min(self.grid.tile_size, 64))
        
        if old_tile_size != self.grid.tile_size:
            self.char_cache = self.create_char_cache()
            self.grid.surface = pygame.Surface((self.grid.width * self.grid.tile_size, self.grid.height * self.grid.tile_size))
            self.grid.needs_redraw = True

    def update(self):
        for name, btn in self.buttons.items():
            if name.startswith('tool_'): btn.is_active = (btn.data == self.current_tool)
        for name, btn in self.palette_buttons.items():
            if name.startswith('char_'): btn.is_active = (btn.data == self.current_char)

    def draw(self):
        self.screen.fill(C_BLACK)
        
        canvas_surf = self.grid.draw(self.char_cache)
        self.screen.blit(canvas_surf, self.camera_offset)
        
        if self.is_drawing and self.current_tool in ['rectangle', 'ellipse', 'select', 'line']:
            self.draw_shape_preview(self.draw_start_pos, self.screen_to_grid_coords(pygame.mouse.get_pos()))
            
        if self.selection_rect:
            rect_px = self.selection_rect.copy()
            rect_px.x = rect_px.x * self.grid.tile_size + self.camera_offset[0]
            rect_px.y = rect_px.y * self.grid.tile_size + self.camera_offset[1]
            rect_px.width *= self.grid.tile_size
            rect_px.height *= self.grid.tile_size
            pygame.draw.rect(self.screen, C_YELLOW, rect_px, 1)

        pygame.draw.rect(self.screen, C_PANEL_BG, (0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.rect(self.screen, C_PANEL_BG, (SCREEN_WIDTH - TOOLBAR_WIDTH, 0, TOOLBAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, C_PANEL_BG, (0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT, SCREEN_WIDTH - TOOLBAR_WIDTH, BOTTOM_BAR_HEIGHT))

        for btn in self.buttons.values(): btn.draw(self.screen)
        for btn in self.palette_buttons.values(): btn.draw(self.screen)
        for inp in self.inputs.values(): inp.draw(self.screen)
            
        self.draw_text("Palette", (10, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT - 20), color=C_TEXT_ON_LIGHT)
        self.draw_text("Export", (SCREEN_WIDTH - TOOLBAR_WIDTH - 310, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT - 20), color=C_TEXT_ON_LIGHT)
        
        if self.active_dropdown: self.active_dropdown.draw(self.screen)
        if self.active_modal: self.active_modal.draw(self.screen)

        pygame.display.flip()

    def draw_text(self, text, pos, color=C_WHITE, font_size=16):
        font = self.fonts.get(font_size, self.fonts[16])
        text_surf = font.render(text, True, color)
        self.screen.blit(text_surf, pos)

    def handle_draw(self, x, y, record_history=True):
        char_to_draw = '.' if self.current_tool == 'eraser' else self.current_char
        action_taken = False
        if self.current_tool in ['brush', 'eraser']:
            self.grid.set_char(x, y, char_to_draw)
            action_taken = True
        elif self.current_tool == 'fill':
            target_char = self.grid.get_char(x,y)
            if target_char is not None:
                self.flood_fill(x, y, target_char)
                action_taken = True
        elif self.current_tool == 'paste':
            self.paste_selection(x, y)
            action_taken = True
        
        if action_taken and record_history:
            self.history.record_action(self.grid.data)

    def apply_shape(self, start, end):
        x1, y1 = start; x2, y2 = end
        if self.current_tool == 'line': self.draw_line_on_grid(x1, y1, x2, y2)
        else:
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            if self.current_tool == 'rectangle':
                for x in range(min_x, max_x + 1):
                    self.grid.set_char(x, min_y, self.current_char); self.grid.set_char(x, max_y, self.current_char)
                for y in range(min_y, max_y + 1):
                    self.grid.set_char(min_x, y, self.current_char); self.grid.set_char(max_x, y, self.current_char)
            elif self.current_tool == 'ellipse':
                 for x in range(min_x, max_x + 1):
                    self.grid.set_char(x, min_y, self.current_char); self.grid.set_char(x, max_y, self.current_char)
        self.history.record_action(self.grid.data)

    def draw_line_on_grid(self, x1, y1, x2, y2):
        # --- MODIFICATION START ---
        # Bresenham's line algorithm now handles diagonals
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self.grid.set_char(x1, y1, self.current_char)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
        # --- MODIFICATION END ---

    def draw_shape_preview(self, start, end):
        x1_px = start[0] * self.grid.tile_size + self.camera_offset[0]
        y1_px = start[1] * self.grid.tile_size + self.camera_offset[1]
        x2_px = end[0] * self.grid.tile_size + self.camera_offset[0]
        y2_px = end[1] * self.grid.tile_size + self.camera_offset[1]
        
        # --- MODIFICATION START ---
        if self.current_tool == 'line':
            # Draw a direct line to the cursor for the preview
            pygame.draw.line(self.screen, C_YELLOW, 
                             (x1_px + self.grid.tile_size//2, y1_px + self.grid.tile_size//2), 
                             (x2_px + self.grid.tile_size//2, y2_px + self.grid.tile_size//2), 1)
        # --- MODIFICATION END ---
        else:
            rect = pygame.Rect(x1_px, y1_px, x2_px - x1_px, y2_px - y1_px)
            rect.normalize()
            pygame.draw.rect(self.screen, C_YELLOW, rect, 1)

    def flood_fill(self, x, y, target_char):
        char_to_draw = '.' if self.current_tool == 'eraser' else self.current_char
        if self.grid.get_char(x, y) != target_char or char_to_draw == target_char: return
        q = [(x, y)]; self.grid.set_char(x, y, char_to_draw)
        head = 0
        while head < len(q):
            px, py = q[head]; head += 1
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = px + dx, py + dy
                if 0 <= nx < self.grid.width and 0 <= ny < self.grid.height and self.grid.get_char(nx, ny) == target_char:
                    self.grid.set_char(nx, ny, char_to_draw)
                    q.append((nx, ny))
        self.grid.needs_redraw = True

    def copy_selection(self):
        if not self.selection_rect: return
        self.clipboard = []
        for y in range(self.selection_rect.top, self.selection_rect.bottom):
            row = [self.grid.get_char(x, y) for x in range(self.selection_rect.left, self.selection_rect.right)]
            self.clipboard.append(row)
        print("Selection copied!")

    def paste_selection(self, x, y):
        if not self.clipboard: return
        for row_idx, row in enumerate(self.clipboard):
            for col_idx, char in enumerate(row):
                self.grid.set_char(x + col_idx, y + row_idx, char)
        self.history.record_action(self.grid.data)

    def delete_selection(self):
        if not self.selection_rect: return
        for y in range(self.selection_rect.top, self.selection_rect.bottom):
            for x in range(self.selection_rect.left, self.selection_rect.right):
                self.grid.set_char(x, y, '.')
        self.selection_rect = None
        self.history.record_action(self.grid.data)
        print("Selection deleted.")

    def set_tool(self, tool):
        self.current_tool = tool
        if tool != 'select': self.selection_rect = None
        print(f"Tool set to: {tool}")

    def set_char(self, char):
        self.current_char = char
        print(f"Character set to: {char}")

    def resize_grid(self, _=None):
        w = int(self.active_modal.elements['width_input'].text)
        h = int(self.active_modal.elements['height_input'].text)
        self.grid.resize(w, h)
        self.history.record_action(self.grid.data)
        self.active_modal = None

    def export_json(self, _=None):
        room_name = self.active_modal.elements['filename_input'].text
        if not room_name: room_name = "unnamed_room"
        
        exits = {}
        for y, row in enumerate(self.grid.data):
            for x, char in enumerate(row):
                if char == 'D':
                    if y == 0: exits['north'] = (x, y)
                    if y == self.grid.height - 1: exits['south'] = (x, y)
                    if x == 0: exits['west'] = (x, y)
                    if x == self.grid.width - 1: exits['east'] = (x, y)

        map_data = ["".join(row) for row in self.grid.data]
        output_obj = { room_name: { "map": map_data, "exits": exits } }
        
        try:
            with open(f"{room_name}.json", 'w') as f:
                json.dump(output_obj, f, indent=4)
            print(f"Saved to {room_name}.json")
        except Exception as e:
            print(f"Error saving file: {e}")
        self.active_modal = None

    def copy_to_clipboard(self, _=None):
        room_name = self.inputs['room_name'].text or "unnamed_room"
        exits = {}
        for y, row in enumerate(self.grid.data):
            for x, char in enumerate(row):
                if char == 'D':
                    if y == 0: exits['north'] = (x, y)
                    if y == self.grid.height - 1: exits['south'] = (x, y)
                    if x == 0: exits['west'] = (x, y)
                    if x == self.grid.width - 1: exits['east'] = (x, y)
        map_data = ["".join(row) for row in self.grid.data]
        output_obj = { room_name: { "map": map_data, "exits": exits } }
        json_output = json.dumps(output_obj, indent=4)
        pyperclip.copy(json_output)
        print("JSON copied to clipboard!")

    def toggle_dropdown(self, menu_type):
        if self.active_dropdown and self.active_dropdown.type == menu_type:
            self.active_dropdown = None
        else:
            if menu_type == 'file':
                options = ["New", "Save", "Canvas Size"]
                rect = pygame.Rect(0, TOP_BAR_HEIGHT, 120, len(options) * 35)
                self.active_dropdown = Dropdown(rect, options, self.fonts[14], self.file_menu_action, menu_type)
            elif menu_type == 'palette':
                options = list(PALETTES.keys())
                rect = pygame.Rect(80, TOP_BAR_HEIGHT, 120, len(options) * 35)
                self.active_dropdown = Dropdown(rect, options, self.fonts[14], self.palette_menu_action, menu_type)

    def file_menu_action(self, option):
        self.active_dropdown = None
        if option == "New":
            modal = Modal("Clear Canvas?", self)
            modal.elements['confirm'] = Button((modal.rect.x + 50, modal.rect.y + 120, 100, 40), "Yes", self.fonts[16], lambda _: (self.grid.clear(), self.history.record_action(self.grid.data), setattr(self, 'active_modal', None)))
            modal.elements['cancel'] = Button((modal.rect.x + 250, modal.rect.y + 120, 100, 40), "No", self.fonts[16], lambda _: setattr(self, 'active_modal', None))
            self.active_modal = modal
        elif option == "Save":
            modal = Modal("Save Room", self)
            modal.elements['filename_input'] = TextInput((modal.rect.x + 50, modal.rect.y + 70, 300, 30), self.fonts[14], "my_room")
            modal.elements['save'] = Button((modal.rect.x + 50, modal.rect.y + 120, 100, 40), "Save", self.fonts[16], self.export_json)
            modal.elements['cancel'] = Button((modal.rect.x + 250, modal.rect.y + 120, 100, 40), "Cancel", self.fonts[16], lambda _: setattr(self, 'active_modal', None))
            self.active_modal = modal
        elif option == "Canvas Size":
            modal = Modal("Resize Canvas", self)
            modal.elements['width_input'] = TextInput((modal.rect.x + 50, modal.rect.y + 70, 100, 30), self.fonts[14], str(self.grid.width))
            modal.elements['height_input'] = TextInput((modal.rect.x + 250, modal.rect.y + 70, 100, 30), self.fonts[14], str(self.grid.height))
            modal.elements['resize'] = Button((modal.rect.x + 150, modal.rect.y + 120, 100, 40), "Apply", self.fonts[16], self.resize_grid)
            self.active_modal = modal

    def palette_menu_action(self, option):
        self.current_palette = option
        self.current_char = PALETTES[self.current_palette][0]
        self.update_palette_buttons()
        self.active_dropdown = None
    
    def undo(self):
        previous_data = self.history.undo()
        if previous_data:
            self.grid.data = previous_data
            self.grid.height = len(previous_data)
            self.grid.width = len(previous_data[0]) if self.grid.height > 0 else 0
            self.grid.needs_redraw = True
            print("Undo successful.")

    def redo(self):
        next_data = self.history.redo()
        if next_data:
            self.grid.data = next_data
            self.grid.height = len(next_data)
            self.grid.width = len(next_data[0]) if self.grid.height > 0 else 0
            self.grid.needs_redraw = True
            print("Redo successful.")

class Dropdown:
    def __init__(self, rect, options, font, callback, menu_type):
        self.rect = pygame.Rect(rect)
        self.type = menu_type
        self.buttons = []
        for i, option in enumerate(options):
            btn_rect = (rect.x, rect.y + i * 35, rect.width, 35)
            self.buttons.append(Button(btn_rect, option, font, callback, option, C_TEXT_ON_LIGHT))

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False
    
    def draw(self, screen):
        for btn in self.buttons:
            btn.draw(screen)

if __name__ == '__main__':
    painter = RoomPainter()
    painter.run()
