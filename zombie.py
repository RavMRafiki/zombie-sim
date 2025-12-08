"""Zombie character class"""

import math
import pygame
from character import Character
from constants import MOVE_INTERVAL


class Zombie(Character):
    """Zombie character - moves aggressively"""
    
    char_type_name = "Zombie"
    color = (0, 255, 0)
    move_speed = MOVE_INTERVAL
    INFECTION_RANGE = 1.99
    INFECTION_COOLDOWN = 5000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_infection_time = 5000
    
    def act(self):
        """Zombies perform aggressive behavior - infect nearby humans"""
        if not self.grid:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check if infection is off cooldown
        if current_time - self.last_infection_time < self.INFECTION_COOLDOWN:
            return
        
        # Import here to avoid circular imports
        from human import Human
        from medic import Medic
        from soldier import Soldier
        from infected import Infected
        
        # Check for infectable characters in range
        for character in self.grid.characters:
            if isinstance(character, (Human, Medic, Soldier)):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Infect if in range
                if distance <= self.INFECTION_RANGE:
                    self.infect_character(character)
                    self.last_infection_time = current_time
                    break
    
    def infect_character(self, character):
        """Convert a character to infected"""
        if self.grid:
            from infected import Infected
            
            idx = self.grid.characters.index(character)
            infected = Infected(character.x, character.y, self.grid, previous_type=character.get_type_name())
            self.grid.characters[idx] = infected
