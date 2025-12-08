"""Infected character class"""

import math
import pygame
from character import Character
from constants import MOVE_INTERVAL


class Infected(Character):
    """Infected character - in transition state"""
    
    char_type_name = "Infected"
    previous_type = "Human"
    color = (255, 165, 0)
    move_speed = int(MOVE_INTERVAL * 0.75)
    TRANSFORMATION_TIME = 10000
    BROADCAST_RANGE = 5.0
    
    def __init__(self, x, y, grid=None, previous_type=None):
        super().__init__(x, y, grid)
        self.infection_start_time = pygame.time.get_ticks()
        if previous_type:
            self.previous_type = previous_type
    
    def act(self):
        """Infected perform transitional behavior - transform to zombie and broadcast"""
        if not self.grid:
            return
        
        current_time = pygame.time.get_ticks()
        time_infected = current_time - self.infection_start_time
        
        self.broadcast_infected_status()
        
        if time_infected >= self.TRANSFORMATION_TIME:
            self.transform_to_zombie()
    
    def broadcast_infected_status(self):
        """Broadcast infected status to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send infected status if in broadcast range
            if distance <= self.BROADCAST_RANGE:
                character.receive_signal("got infected", {
                    "source": self,
                    "source_pos": (self.x, self.y),
                    "distance": distance,
                    "time_until_zombie": self.TRANSFORMATION_TIME - (pygame.time.get_ticks() - self.infection_start_time)
                })
    
    def transform_to_zombie(self):
        """Convert this infected to zombie"""
        if self.grid:
            from zombie import Zombie
            
            idx = self.grid.characters.index(self)
            zombie = Zombie(self.x, self.y, self.grid)
            self.grid.characters[idx] = zombie
