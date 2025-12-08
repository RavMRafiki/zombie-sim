"""Medic character class"""

import math
import pygame
from human import Human
from constants import MOVE_INTERVAL


class Medic(Human):
    """Medic character - supports humans"""
    
    char_type_name = "Medic"
    color = (255, 0, 0)
    move_speed = MOVE_INTERVAL
    HEAL_RANGE = 2.0
    HEAL_TIME = 20000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_heal_time = pygame.time.get_ticks()
    
    def act(self):
        """Medics perform healing/support behavior"""
        if not self.grid:
            return
        
        # Call parent class to broadcast threats
        super().act()
        
        from infected import Infected
        
        current_time = pygame.time.get_ticks()
        time_since_heal = current_time - self.last_heal_time
        
        if time_since_heal < self.HEAL_TIME:
            return
        
        for character in self.grid.characters:
            if isinstance(character, Infected):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Heal if in range
                if distance <= self.HEAL_RANGE:
                    self.heal_infected(character)
                    break
    
    def heal_infected(self, infected):
        """Convert infected back to their previous type and broadcast healing"""
        if self.grid:
            from human import Human
            from medic import Medic
            from soldier import Soldier
            from infected import Infected
            
            idx = self.grid.characters.index(infected)
            
            # Restore to previous type based on stored type
            previous_type = infected.previous_type
            
            if previous_type == "Human":
                healed = Human(infected.x, infected.y, self.grid)
            elif previous_type == "Medic":
                healed = Medic(infected.x, infected.y, self.grid)
            elif previous_type == "Soldier":
                healed = Soldier(infected.x, infected.y, self.grid)
            else:
                healed = Human(infected.x, infected.y, self.grid)
            
            self.grid.characters[idx] = healed
            self.last_heal_time = pygame.time.get_ticks()
            
            # Broadcast healing action to nearby characters
            self.broadcast_heal(healed, previous_type)
    
    def broadcast_heal(self, healed_character, healed_type):
        """Broadcast healing action to nearby characters"""
        if not self.grid:
            return
        
        broadcast_range = 7.0
        
        for character in self.grid.characters:
            if character is self or character is healed_character:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send healing info if in broadcast range
            if distance <= broadcast_range:
                character.receive_signal("healing_performed", {
                    "medic": self,
                    "medic_pos": (self.x, self.y),
                    "healed_pos": (healed_character.x, healed_character.y),
                    "healed_type": healed_type,
                    "distance": distance
                })
