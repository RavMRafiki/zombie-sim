"""Soldier character class"""

import math
import numpy as np
import pygame
from human import Human
from character import Character

from constants import MOVE_INTERVAL


class Soldier(Character):
    """Soldier character - combat specialist"""
    
    char_type_name = "Soldier"
    color = (255, 255, 0) # Żółty
    move_speed = MOVE_INTERVAL 
    
    # Parametry bojowe
    KILL_RANGE = 3.0
    KILL_COOLDOWN = 5000
    SIGHT_RANGE = 5.0      # Zasięg wzroku (widzi zombie)
    BROADCAST_RANGE = 50.0  
    SIGNAL_MEMORY_TIME = 4000 # Pamięta wezwania przez 4 sekundy
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_kill_time = 0
        self.prev_dist = float('inf')


    def get_target_vector(self):
        """
        Zwraca wektor [dx, dy, weapon_status].
        Priorytet 1: Widoczny Zombie (Atak).
        Priorytet 2: Sygnał 'threat_alert' (Bieg na pomoc).
        """
        current_time = pygame.time.get_ticks()
        
        # 1. Status broni (0.0 - 1.0)
        time_since_shot = current_time - self.last_kill_time
        weapon_status = 1.0
        if time_since_shot < self.KILL_COOLDOWN:
            weapon_status = time_since_shot / self.KILL_COOLDOWN
            
        # 2. Szukanie celu
        target_pos = None
        min_dist = float('inf')

        # Importy lokalne
        from zombie import Zombie 
        from infected import Infected

        # PRIORYTET A: Wzrok (Walka bezpośrednia)
        # Skanujemy tylko bliskie otoczenie (zasięg wzroku)
        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)):
                dist_sq = (self.x - char.x)**2 + (self.y - char.y)**2
                
                # Jeśli widzi wroga
                if dist_sq <= (self.SIGHT_RANGE ** 2):
                    if dist_sq < min_dist:
                        min_dist = dist_sq
                        target_pos = (char.x, char.y)
        
        # PRIORYTET B: Radio (Reagowanie na wezwania)
        # Jeśli nie widzę wroga, sprawdzam czy ktoś woła pomocy
        if not target_pos:
            for signal in self.signals:
                if signal['type'] == 'threat_alert':
                    # Idziemy do źródła sygnału (tam gdzie jest człowiek w opałach)
                    s_pos = signal['data']['source_pos']
                    dist_sq = (self.x - s_pos[0])**2 + (self.y - s_pos[1])**2
                    
                    if dist_sq < min_dist:
                        min_dist = dist_sq
                        target_pos = s_pos
        
        # Jeśli nadal brak celu -> wektor zerowy
        if not target_pos:
            return np.array([0.0, 0.0, weapon_status], dtype=np.float32)

        # 3. Oblicz wektor znormalizowany
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0: 
            return np.array([0.0, 0.0, weapon_status], dtype=np.float32)
        
        return np.array([dx / length, dy / length, weapon_status], dtype=np.float32)

    def act(self):
        """Logika walki i nagród Żołnierza"""
        if not self.grid:
            return 0
            
        current_time = pygame.time.get_ticks()
        step_reward = 0
        
        # 1. Nagroda za przeżycie
        if self.is_alive:
            step_reward += 0.5 # Mniejsza niż za fraga, ale stała
        else:
            return 0 
        
        from zombie import Zombie 
        from infected import Infected
        
        # 2. Próba strzału (jeśli cooldown minął)
        if current_time - self.last_kill_time >= self.KILL_COOLDOWN:
            
            # Szukamy celu w zasięgu strzału (KILL_RANGE)
            # Tu musimy przeskanować grid, bo strzał jest natychmiastowy
            for character in self.grid.characters:
                if isinstance(character, (Zombie, Infected)):
                    dx = self.x - character.x
                    dy = self.y - character.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance <= self.KILL_RANGE:
                        # STRZAŁ!
                        character.is_alive = False
                        # Bezpieczne usuwanie w pętli main, tu tylko oznaczamy
                        if character in self.grid.characters:
                             self.grid.characters.remove(character)
                        
                        self.last_kill_time = current_time
                        self.broadcast_kill((character.x, character.y))
                        
                        step_reward += 10.0 # FRAG
                        # print(f"Soldier {id(self)} killed a Zombie!")
                        break
        
        # 3. Reward Shaping (Zachęta do podążania za celem)
        # Obliczamy dystans do tego, co wskazuje wektor celu (Zombie lub Sygnał)
        
        # Musimy odtworzyć logikę wyboru celu, żeby wiedzieć czy się zbliżamy
        target_pos = None
        min_dist = float('inf')

        # (Kopia logiki z get_target_vector dla spójności nagród)
        # A. Wzrok
        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)):
                d = math.sqrt((self.x - char.x)**2 + (self.y - char.y)**2)
                if d <= self.SIGHT_RANGE and d < min_dist:
                    min_dist = d
                    target_pos = (char.x, char.y)
        
        # B. Radio
        if not target_pos:
            for signal in self.signals:
                if signal['type'] == 'threat_alert':
                    s_pos = signal['data']['source_pos']
                    d = math.sqrt((self.x - s_pos[0])**2 + (self.y - s_pos[1])**2)
                    if d < min_dist:
                        min_dist = d
                        target_pos = s_pos

        # Nagradzanie ruchu
        if target_pos:
            # Sprawdzamy status broni
            is_weapon_ready = (current_time - self.last_kill_time) > (self.KILL_COOLDOWN * 0.8)
            
            if is_weapon_ready:
                # Jeśli broń gotowa -> idź do celu
                if min_dist < self.prev_dist:
                    step_reward += 0.2
                elif min_dist > self.prev_dist:
                    step_reward -= 0.2
            else:
                # Jeśli cooldown -> trzymaj dystans (opcjonalne)
                pass
                
            self.prev_dist = min_dist
        else:
            self.prev_dist = float('inf')
            
        return step_reward
    
    def broadcast_kill(self, kill_pos):
        """Broadcast kill action to nearby characters"""
        self.send_signal(
            signal_type="zombies_killed",
            broadcast_range=self.BROADCAST_RANGE,
            data={
                "soldier_pos": kill_pos,
                # 'soldier' i 'distance' doda automatycznie send_signal jako 'source' i 'distance'
            }
        )

    def get_infected(self):
        """Metoda wywoływana przez Zombie, gdy infekcja się uda."""
        self.is_alive = False
        # Żołnierz też może wołać medyka
        if hasattr(self, 'broadcast_help_request'):
             self.broadcast_help_request()
