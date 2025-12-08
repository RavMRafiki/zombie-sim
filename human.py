"""Human character class"""

import math
import pygame
from character import Character
from constants import MOVE_INTERVAL


class Human(Character):
    """Human character - moves defensively"""
    
    char_type_name = "Human"
    color = (0, 0, 255)
    move_speed = MOVE_INTERVAL
    THREAT_DETECTION_RANGE = 3.0
    THREAT_BROADCAST_RANGE = 7.0
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
    
    def act(self):
        """Humans perform survival behavior - broadcast threat information"""
        if not self.grid:
            return
        
        # Import here to avoid circular imports
        from zombie import Zombie
        from infected import Infected
        
        # Scan for zombies and infected nearby
        threats = []
        for character in self.grid.characters:
            if isinstance(character, (Zombie, Infected)):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Add to threats if in detection range
                if distance <= self.THREAT_DETECTION_RANGE:
                    threats.append({
                        "type": "Zombie" if isinstance(character, Zombie) else "Infected",
                        "position": (character.x, character.y),
                        "distance": distance
                    })
        
        # Broadcast threat information if threats detected
        if threats:
            self.broadcast_threat_info(threats)
    
    def broadcast_threat_info(self, threats):
        """Broadcast threat information to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send threat info if in broadcast range
            if distance <= self.THREAT_BROADCAST_RANGE:
                character.receive_signal("threat_alert", {
                    "source": self,
                    "source_pos": (self.x, self.y),
                    "threats": threats
                })
