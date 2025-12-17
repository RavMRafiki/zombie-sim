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
        self.prev_min_dist = float('inf')
    
    def act(self):
        """Humans perform survival behavior - broadcast threat information"""
        if not self.grid:
            return 0
        
        # Import here to avoid circular imports
        from zombie import Zombie
        from infected import Infected

        min_dist = float('inf')
        # Skanujemy otoczenie (można to ograniczyć np. do promienia wzroku dla optymalizacji)
        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)):
                # Obliczamy dystans euklidesowy
                dist = math.sqrt((self.x - char.x)**2 + (self.y - char.y)**2)
                if dist < min_dist:
                    min_dist = dist

        # 3. Logika Strachu i Ucieczki
        SAFE_DISTANCE = 5.0 # Dystans, powyżej którego człowiek czuje się bezpiecznie
        step_reward = 0.0
        
        if min_dist < float('inf'):
            # A. Kara za posiadanie zombie w otoczeniu (PANIKA)
            if min_dist < SAFE_DISTANCE:
                # Im bliżej zombie, tym większa kara (np. od -0.1 do -1.0)
                # Wzór: (SAFE - dist) * waga
                panic_penalty = (SAFE_DISTANCE - min_dist) * 0.2
                step_reward -= panic_penalty
                
                # B. Nagroda za ucieczkę (Porównanie z poprzednią klatką)
                # Jeśli dystans się zwiększył -> uciekasz -> BRAWO
                if min_dist > self.prev_min_dist:
                    step_reward += 0.5 # Nagroda za dobry kierunek ucieczki
                
                # C. Kara za przybliżanie się do zombie (Samobójstwo)
                elif min_dist < self.prev_min_dist:
                    step_reward -= 0.5 # Kara za bieganie w stronę zagrożenia
            
            # Aktualizujemy pamięć na następną klatkę
            self.prev_min_dist = min_dist
        else:
            # Jeśli nie ma zombie na mapie (rzadkie), resetujemy pamięć
            self.prev_min_dist = float('inf')
        
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

        if self.is_alive:
            return step_reward + 0.1 # Nagroda za przeżycie
        
        return step_reward
    
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

    def get_infected(self):
        """Metoda wywoływana przez Zombie, gdy infekcja się uda."""
        self.is_alive = False
        print(f"Człowiek {id(self)} został zarażony! Kara -10")
