"""Zombie character class"""

import math
import numpy as np
import pygame
from character import Character
from constants import MOVE_INTERVAL, ZOMBIE_INFECTION_COOLDOWN_MS, ZOMBIE_STARVATION_TIME_MS



class Zombie(Character):
    """Zombie character - Aggressive Swarm Intelligence"""
    
    char_type_name = "Zombie"
    color = (0, 255, 0) # Zielony
    move_speed = MOVE_INTERVAL
    
    # Parametry
    INFECTION_RANGE = 1.99
    INFECTION_COOLDOWN = ZOMBIE_INFECTION_COOLDOWN_MS
    SIGHT_RANGE = 7.2       # Zasięg wzroku (krótki)
    SIEGE_RANGE = 2.5 # Zasięg "Oblężenia" (tłok przy ofierze)
    BROADCAST_RANGE = 65.0  # Zasięg "jęku" (sygnalizowanie innym zombie)
    SIGNAL_MEMORY_TIME = 3000 # Pamięta sygnały przez 3 sekundy
    STARVATION_TIME = ZOMBIE_STARVATION_TIME_MS   # Umiera, jeśli długo nikogo nie zarazi (ms)
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_infection_time = 0
        self.prev_dist = float('inf')
        # Liczymy "ostatnie jedzenie" od startu, by dać im czas na polowanie
        self.last_feed_time = pygame.time.get_ticks()
        

    def get_target_vector(self):
        """
        Zwraca wektor [dx, dy].
        1. Jeśli widzę człowieka -> Idź do niego + KRZYCZ (Broadcast).
        2. Jeśli słyszę innego Zombie -> Idź do źródła sygnału.
        3. W przeciwnym razie -> [0,0].
        """
        target_pos = None
        min_dist = float('inf')

        # Importy lokalne
        from human import Human
        from medic import Medic
        from soldier import Soldier

        # --- 1. WZROK (Priorytet najwyższy) ---
        found_victim = False
        
        for char in self.grid.characters:
            if isinstance(char, (Human, Medic, Soldier)):
                dist_sq = (self.x - char.x)**2 + (self.y - char.y)**2
                
                # Jeśli jest w zasięgu wzroku
                if dist_sq <= (self.SIGHT_RANGE ** 2):
                    if dist_sq < min_dist:
                        min_dist = dist_sq
                        target_pos = (char.x, char.y)
                        found_victim = True

        # Jeśli znaleźliśmy ofiarę wzrokiem -> WOŁAMY INNYCH!
        if found_victim and target_pos:
            self.broadcast_prey_spotted(target_pos)

        # --- 2. SŁUCH (Priorytet niższy) ---
        # Jeśli nie widzę nikogo, sprawdzam czy koledzy coś widzieli
        if not target_pos:
            for signal in self.signals:
                if signal['type'] == 'prey_spotted':
                    # Idziemy tam, gdzie inny zombie widział ofiarę
                    prey_pos = signal['data']['prey_pos']
                    dist_sq = (self.x - prey_pos[0])**2 + (self.y - prey_pos[1])**2
                    
                    if dist_sq < min_dist:
                        min_dist = dist_sq
                        target_pos = prey_pos

        # --- 3. KONSTRUKCJA WEKTORA ---
        if target_pos is None:
            return np.array([0.0, 0.0], dtype=np.float32)
            
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0: return np.array([0.0, 0.0], dtype=np.float32)
        
        return np.array([dx / length, dy / length], dtype=np.float32)

    def act(self):
        """Zombies perform aggressive behavior - infect nearby humans"""
        if not self.grid: 
            return 0
        
        current_time = pygame.time.get_ticks()
        step_reward = 0 

        # GŁÓD: jeśli za długo bez infekcji -> zombie umiera
        if current_time - getattr(self, 'last_feed_time', 0) > self.STARVATION_TIME:
            self.is_alive = False
            # Bezpieczne usunięcie z planszy
            if self in self.grid.characters:
                self.grid.characters.remove(self)
            # Lekka kara, by uczyć sieć unikać głodu
            return step_reward - 5.0

        # Musimy odtworzyć logikę znajdowania celu, aby obliczyć nagrodę
        # (Ale bez broadcastu, żeby nie dublować)
        
        from human import Human
        from medic import Medic
        from soldier import Soldier
        
        target_pos = None
        min_dist = float('inf')
        
        # 1. Sprawdzamy co widzi/słyszy agent (tak samo jak w get_target_vector)
        # Wzrok
        for char in self.grid.characters:
            if isinstance(char, (Human, Medic, Soldier)):
                d = math.sqrt((self.x - char.x)**2 + (self.y - char.y)**2)
                if d <= self.SIGHT_RANGE and d < min_dist:
                    min_dist = d
                    target_pos = (char.x, char.y)
        
        # Słuch (jeśli wzrok zawiódł)
        if not target_pos:
             for signal in self.signals:
                if signal['type'] == 'prey_spotted':
                    p_pos = signal['data']['prey_pos']
                    d = math.sqrt((self.x - p_pos[0])**2 + (self.y - p_pos[1])**2)
                    if d < min_dist:
                        min_dist = d
                        # Uwaga: To jest dystans do ofiary widzianej przez kogoś innego
        
        # --- LOGIKA NAGRÓD (Reward Shaping) ---
        if min_dist < float('inf'):
            # Nagroda za zbliżanie się do celu (widzianego lub słyszanego)
            if min_dist < self.SIGHT_RANGE:
                step_reward += (self.SIGHT_RANGE - min_dist) * 0.2 

            # STREFA A: OBLĘŻENIE (Bardzo blisko)
            if min_dist <= self.SIEGE_RANGE:
                # Jesteś w "młynie". Nie karzemy za to, że nie możesz podejść bliżej.
                # Nagradzamy za samo wywieranie presji.
                step_reward += 0.5 
                
                # TUTAJ NIE MA KARY ZA ZŁY KIERUNEK!
                # Zombie może krążyć wokół ofiary szukając luki i nie dostanie minusów.

            # STREFA B: POŚCIG (Daleko)
            else:
                # Tutaj musisz biec prosto do celu. Jak się cofasz -> Kara.
                if min_dist < self.prev_dist:
                    step_reward += 0.5 # Brawo, biegniesz do ofiary
                elif min_dist > self.prev_dist:
                    step_reward -= 0.5 # Źle! Uciekasz/Błądzisz -> Kara

            self.prev_dist = min_dist
        else:
            self.prev_dist = float('inf')
        
        # --- LOGIKA INFEKCJI (Bez zmian) ---
        if current_time - self.last_infection_time < self.INFECTION_COOLDOWN:
            return step_reward
        
        for character in self.grid.characters:
            if isinstance(character, (Human, Medic, Soldier)):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= self.INFECTION_RANGE:
                    success = self.infect_character(character)
                    if success:
                        step_reward += 10 
                        # print(f"Zombie {id(self)} zaraził człowieka! Nagroda +10")
                        self.last_infection_time = current_time
                        # Zaktualizuj też czas ostatniego "posiłku"
                        self.last_feed_time = current_time
                        break 

        return step_reward
    
    def broadcast_prey_spotted(self, prey_pos):
        """
        Wysyła sygnał do innych Zombie: 'Znalazłem jedzenie tutaj!'
        """
        self.send_signal(
            signal_type="prey_spotted",
            broadcast_range=self.BROADCAST_RANGE,
            data={
                "prey_pos": prey_pos
            }
        )

    def infect_character(self, character):
        """Convert a character to infected"""
        if self.grid:
            from infected import Infected
            
            idx = self.grid.characters.index(character)
            # Przekazujemy previous_type, żeby Medyk wiedział kogo wskrzesić
            infected = Infected(character.x, character.y, self.grid, previous_type=character.char_type_name)
            self.grid.characters[idx] = infected

        character.get_infected() # To wywoła krzyki o pomoc u ofiary

        return True