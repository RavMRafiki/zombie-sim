"""Base Character class"""

import pygame
import math
from constants import GRID_SIZE, CELL_SIZE, MOVE_INTERVAL


class Character:
    """Base class for all characters on the grid"""
    
    char_type_name = "Character"
    color = (255, 255, 255)
    move_speed = MOVE_INTERVAL
    
    def __init__(self, x, y, grid=None):
        self.x = x
        self.y = y
        self.grid = grid
        self.last_move_time = pygame.time.get_ticks()
        self.signals = []
    
    def update(self, current_time):
        """Update character movement based on elapsed time"""
        if current_time - self.last_move_time >= self.move_speed:
            self.move()
            self.act()
            self.process_signals()
            self.last_move_time = current_time
    
    def move(self):
        """Move character randomly in one of 4 directions"""
        import random
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        new_x = self.x + direction[0]
        new_y = self.y + direction[1]
        
        self.x = max(0, min(GRID_SIZE - 1, new_x))
        self.y = max(0, min(GRID_SIZE - 1, new_y))
    
    def act(self):
        """Perform character-specific action (override in subclasses)"""
        pass
    
    def send_signal(self, signal_type, broadcast_range=3, data=None):
        """Send a signal to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send signal if in range
            if distance <= broadcast_range:
                character.receive_signal(signal_type, {
                    "source": self,
                    "source_pos": (self.x, self.y),
                    "distance": distance,
                    "data": data
                })
    
    def receive_signal(self, signal_type, signal_data):
        """Receive a signal from another character"""
        self.signals.append({
            "type": signal_type,
            "data": signal_data,
            "time": pygame.time.get_ticks()
        })
    
    def process_signals(self):
        """Process all received signals (override in subclasses for custom behavior)"""
        self.signals.clear()
    
    def draw(self, screen):
        """Draw character on screen"""
        pixel_x = self.x * CELL_SIZE
        pixel_y = self.y * CELL_SIZE
        pygame.draw.rect(screen, self.color, (pixel_x, pixel_y, CELL_SIZE, CELL_SIZE))
    
    def get_type_name(self):
        """Return character type name"""
        return self.char_type_name
