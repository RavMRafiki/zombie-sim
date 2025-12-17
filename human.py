"""Human character class"""

import math
import numpy as np
import pygame
from character import Character
from constants import MOVE_INTERVAL


class Human(Character):
    """Human character - moves defensively and communicates"""
    
    char_type_name = "Human"
    color = (0, 0, 255) # Niebieski
    move_speed = MOVE_INTERVAL
    
    # Zasięgi
    THREAT_DETECTION_RANGE = 4.0   # Zasięg wzroku (widzi zombie)
    THREAT_BROADCAST_RANGE = 25.0  # Zasięg krzyku (ostrzega innych)
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.prev_min_dist = float('inf')

    def get_target_vector(self):
        """
        Zwraca wektor 4-elementowy:
        [threat_dx, threat_dy, soldier_dx, soldier_dy]
        """
        # --- 1. WEKTOR ZAGROŻENIA (Zombie/Infected) ---
        # Łączymy to co widzimy (Grid) z tym co słyszymy (Sygnały)
        
        closest_threat_pos = None
        min_threat_dist = float('inf')
        
        # A. Wzrok (Skanowanie gridu - bliski zasięg)
        from zombie import Zombie
        from infected import Infected
        
        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)):
                dist_sq = (self.x - char.x)**2 + (self.y - char.y)**2
                # Jeśli widzimy wroga blisko
                if dist_sq < (self.THREAT_DETECTION_RANGE ** 2):
                    if dist_sq < min_threat_dist:
                        min_threat_dist = dist_sq
                        closest_threat_pos = (char.x, char.y)
        
        # B. Słuch (Sygnały threat_alert - dalszy zasięg)
        for signal in self.signals:
            if signal['type'] == 'threat_alert':
                # Idziemy od źródła sygnału (tam jest niebezpiecznie)
                s_pos = signal['data']['source_pos']
                dist_sq = (self.x - s_pos[0])**2 + (self.y - s_pos[1])**2
                if dist_sq < min_threat_dist:
                    min_threat_dist = dist_sq
                    closest_threat_pos = s_pos

        # Oblicz wektor zagrożenia (znormalizowany)
        threat_vec = [0.0, 0.0]
        if closest_threat_pos:
            dx = closest_threat_pos[0] - self.x
            dy = closest_threat_pos[1] - self.y
            length = math.sqrt(dx**2 + dy**2)
            if length > 0:
                threat_vec = [dx/length, dy/length]

        # --- 2. WEKTOR RATUNKU (Soldier) ---
        # Szukamy sygnałów 'zombies_killed' (tam jest bezpiecznie)
        
        closest_soldier_pos = None
        min_soldier_dist = float('inf')
        
        for signal in self.signals:
            if signal['type'] == 'zombies_killed':
                s_pos = signal['data']['soldier_pos']
                dist_sq = (self.x - s_pos[0])**2 + (self.y - s_pos[1])**2
                if dist_sq < min_soldier_dist:
                    min_soldier_dist = dist_sq
                    closest_soldier_pos = s_pos
                    
        # Oblicz wektor ratunku
        soldier_vec = [0.0, 0.0]
        if closest_soldier_pos:
            dx = closest_soldier_pos[0] - self.x
            dy = closest_soldier_pos[1] - self.y
            length = math.sqrt(dx**2 + dy**2)
            if length > 0:
                soldier_vec = [dx/length, dy/length]

        # ZWRACAMY POŁĄCZONY WEKTOR (Rozmiar 4)
        return np.array(threat_vec + soldier_vec, dtype=np.float32)

    def act(self):
        """Humans perform survival behavior - broadcast threat information"""
        if not self.grid:
            return 0
        
        from zombie import Zombie
        from infected import Infected

        # --- 1. Skanowanie wizualne (tylko do nagród i broadcastu) ---
        min_real_dist = float('inf')
        threats = []
        
        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)):
                dx = self.x - char.x
                dy = self.y - char.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Do nagród (fizyczna odległość)
                if distance < min_real_dist:
                    min_real_dist = distance
                
                # Do broadcastu (jeśli widzi)
                if distance <= self.THREAT_DETECTION_RANGE:
                    threats.append({
                        "type": "Zombie",
                        "position": (char.x, char.y),
                        "distance": distance
                    })

        # --- 2. Rozgłaszanie zagrożenia ---
        if threats:
            self.broadcast_threat_info(threats)

        # --- 3. Obliczanie Nagrody (Reward Shaping) ---
        SAFE_DISTANCE = 5.0 
        step_reward = 0.0
        
        if min_real_dist < float('inf'):
            # A. Kara za bliskość (Panika)
            if min_real_dist < SAFE_DISTANCE:
                panic_penalty = (SAFE_DISTANCE - min_real_dist) * 0.2
                step_reward -= panic_penalty
                
                # B. Nagroda za ucieczkę (zwiększanie dystansu)
                if min_real_dist > self.prev_min_dist:
                    step_reward += 0.5 
                # C. Kara za bieganie w stronę śmierci
                elif min_real_dist < self.prev_min_dist:
                    step_reward -= 0.5 
            
            self.prev_min_dist = min_real_dist
        else:
            self.prev_min_dist = float('inf')
        
        # D. Nagroda za przeżycie
        if self.is_alive:
            return step_reward + 0.1 
        
        return step_reward
    
    def broadcast_threat_info(self, threats):
        """Broadcast threat information to nearby characters"""
        if not self.grid: return

        for character in self.grid.characters:
            if character is self: continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= self.THREAT_BROADCAST_RANGE:
                # Upewniamy się, że obiekt ma metodę receive_signal
                if hasattr(character, 'receive_signal'):
                    character.receive_signal("threat_alert", {
                        "source": self,
                        "source_pos": (self.x, self.y),
                        "threats": threats
                    })

    def get_infected(self):
        """Metoda wywoływana przez Zombie, gdy infekcja się uda."""
        self.is_alive = False
        print(f"Człowiek {id(self)} został zarażony! Kara -10")
        # Wołamy o pomoc medyka!
        self.broadcast_help_request()

    def broadcast_help_request(self):
        """Broadcast help request to nearby characters (for Medics)"""
        if not self.grid: return
        
        for character in self.grid.characters:
            if character is self: continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Możemy krzyczeć dalej niż widzieć zagrożenie (np. 10 kratek)
            if distance <= 256:
                if hasattr(character, 'receive_signal'):
                    character.receive_signal("medic_requested", {
                        "source": self, # Przekazujemy obiekt (Medyk go użyje jako celu)
                        "source_pos": (self.x, self.y),
                        "distance": distance
                    })