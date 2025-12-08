"""Soldier character class"""

import math
import pygame
from human import Human
from constants import MOVE_INTERVAL


class Soldier(Human):
    """Soldier character - combat specialist"""
    
    char_type_name = "Soldier"
    color = (255, 255, 0)
    move_speed = int(MOVE_INTERVAL * 0.8)
    KILL_RANGE = 3.0
    KILL_COOLDOWN = 5000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_kill_time = 0
    
    def act(self):
        """Soldiers perform combat behavior - kill one zombie in range per cooldown"""
        if not self.grid:
            return
        
        # Call parent class to broadcast threats
        super().act()
        
        from zombie import Zombie
        
        current_time = pygame.time.get_ticks()
        
        # Check if killing is off cooldown
        if current_time - self.last_kill_time < self.KILL_COOLDOWN:
            return
        
        # Find first zombie in range
        for character in self.grid.characters:
            if isinstance(character, Zombie):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Kill if in range
                if distance <= self.KILL_RANGE:
                    kill_pos = (character.x, character.y)
                    self.grid.characters.remove(character)
                    self.last_kill_time = current_time
                    self.broadcast_kill(kill_pos)
                    break
    
    def broadcast_kill(self, kill_pos):
        """Broadcast kill action to nearby characters"""
        if not self.grid:
            return
        
        broadcast_range = 7.0
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send kill info if in broadcast range
            if distance <= broadcast_range:
                character.receive_signal("zombies_killed", {
                    "soldier": self,
                    "soldier_pos": (self.x, self.y),
                    "kill_position": kill_pos,
                    "distance": distance
                })
