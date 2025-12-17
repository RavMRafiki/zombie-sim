"""Medic character class"""

import math
import pygame
from character import Character
from constants import MOVE_INTERVAL
from pathfinding import a_star_search


class Medic(Character):
    """Medic character - coordinates via radio signals"""
    
    char_type_name = "Medic"
    color = (255, 255, 255)
    move_speed = MOVE_INTERVAL
    
    HEAL_RANGE = 1.5
    HEAL_COOLDOWN = 5000
    VISION_RANGE = 12.0        # Zasięg wzroku
    BROADCAST_RANGE = 40.0    # Zasięg radia medycznego (szerszy niż krzyku)
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_heal_time = -self.HEAL_COOLDOWN
        self.target_infected = None 
        self.path = [] 
        self.last_broadcast_time = 0

    def get_autonomous_action(self):
        if not self.grid: return 4
        
        from infected import Infected

        # 1. Walidacja celu (czy istnieje?)
        if self.target_infected:
            if (self.target_infected not in self.grid.characters or 
                not isinstance(self.target_infected, Infected)):
                self.target_infected = None
                self.path = []

        # 2. Sprawdzenie konkurencji (CZY KTOŚ MA BLIŻEJ?)
        # To jest nowa logika zamiast "God Mode"
        if self.target_infected:
            should_yield = self.check_competition()
            if should_yield:
                # print(f"Medic {id(self)} yielding target to a closer medic.")
                self.target_infected = None
                self.path = []

        # 3. Jeśli brak celu -> Szukaj nowego
        if not self.target_infected:
            self.find_best_target()

        # 4. Jeśli mamy cel -> Rozgłoś to innym!
        if self.target_infected:
            self.broadcast_intent()

        # 5. (Standardowa logika ruchu i A* - bez zmian)
        if not self.target_infected:
            return 4 

        dist = math.sqrt((self.x - self.target_infected.x)**2 + (self.y - self.target_infected.y)**2)
        if dist <= self.HEAL_RANGE:
            return 4 

        obstacles = set()

        for c in self.grid.characters:
            # 1. Nie jestem przeszkodą dla siebie
            if c is self: continue
            
            # 2. Cel nie jest przeszkodą (muszę do niego dojść)
            if c is self.target_infected: continue
            
            # 3. Sprawdzam czy widzę tę postać
            d_to_char = math.sqrt((self.x - c.x)**2 + (self.y - c.y)**2)
            
            # Dodajemy do przeszkód TYLKO jeśli jest w zasięgu wzroku
            if d_to_char <= self.VISION_RANGE:
                obstacles.add((c.x, c.y))
        
        start = (self.x, self.y)
        goal = (self.target_infected.x, self.target_infected.y)
        
        new_path = a_star_search(start, goal, obstacles)
        
        if new_path and len(new_path) > 0:
            first_step = new_path[0]
            if first_step == (self.x, self.y):
                if len(new_path) > 1:
                    next_step = new_path[1]
                else:
                    return 4 
            else:
                next_step = new_path[0]

            dx = next_step[0] - self.x
            dy = next_step[1] - self.y
            
            if dy == -1: return 0
            if dy == 1:  return 1
            if dx == -1: return 2
            if dx == 1:  return 3
        else:
            # Fallback
            dx = self.target_infected.x - self.x
            dy = self.target_infected.y - self.y
            if abs(dx) > abs(dy):
                return 3 if dx > 0 else 2
            else:
                return 1 if dy > 0 else 0
            
        return 4

    def find_best_target(self):
        """
        Znajduje cel LOKALNIE (na podstawie odebranych sygnałów i wzroku).
        Nie sprawdza konkurencji tutaj (to robi check_competition).
        """
        from infected import Infected

        best_candidate = None
        min_dist = float('inf')
        
        potential_targets = set()

        # A. Słuch (medic_requested od ludzi)
        for signal in self.signals:
            if signal['type'] == 'medic_requested':
                sig_pos = signal['data']['source_pos']
                # Szukamy Infected w miejscu sygnału
                for char in self.grid.characters:
                    if isinstance(char, Infected):
                        d = math.sqrt((char.x - sig_pos[0])**2 + (char.y - sig_pos[1])**2)
                        if d <= 2.0: # Margines błędu
                            potential_targets.add(char)
        
        # B. Wzrok (Bezpośredni kontakt)
        for char in self.grid.characters:
            if isinstance(char, Infected):
                d = math.sqrt((self.x - char.x)**2 + (self.y - char.y)**2)
                if d <= self.VISION_RANGE:
                    potential_targets.add(char)

        # Wybór najbliższego (Naiwny - konkurencję sprawdzimy później)
        for infected in potential_targets:
            dist = math.sqrt((self.x - infected.x)**2 + (self.y - infected.y)**2)
            if dist < min_dist:
                min_dist = dist
                best_candidate = infected
        
        self.target_infected = best_candidate

    def broadcast_intent(self):
        """Wysyła sygnał do innych medyków: 'Zajmuję ten cel'"""
        if not self.target_infected: return
        
        # Ograniczamy spam
        current_time = pygame.time.get_ticks()
        if current_time - self.last_broadcast_time < 500:
            return
            
        self.last_broadcast_time = current_time
        
        # Obliczamy dystans do celu (potrzebny innym medykom do decyzji)
        dist_to_target = math.sqrt((self.x - self.target_infected.x)**2 + (self.y - self.target_infected.y)**2)
        
        self.send_signal(
            signal_type="medic_en_route",
            broadcast_range=self.BROADCAST_RANGE,
            data={
                "medic_id": id(self),
                "target_id": id(self.target_infected),
                "target_pos": (self.target_infected.x, self.target_infected.y),
                "dist_to_target": dist_to_target
            }
        )

    def check_competition(self):
        """
        Sprawdza sygnały 'medic_en_route'.
        Jeśli inny medyk zgłosił ten sam cel I ma bliżej -> zwraca True (Ustąp).
        """
        if not self.target_infected: return False
        
        my_dist = math.sqrt((self.x - self.target_infected.x)**2 + (self.y - self.target_infected.y)**2)
        my_target_id = id(self.target_infected)
        
        for signal in self.signals:
            if signal['type'] == 'medic_en_route':
                other_target_id = signal['data']['target_id']
                
                # Czy mówimy o tym samym pacjencie?
                # (Porównujemy ID obiektu Infected lub przybliżoną pozycję)
                if other_target_id == my_target_id:
                    other_dist = signal['data']['dist_to_target']
                    other_medic_id = signal['data']['medic_id']
                    
                    # Logika ustępowania:
                    # 1. Jeśli on ma bliżej -> Ustąp.
                    # 2. Jeśli mamy tyle samo (rzadkie), użyj ID medyka jako tie-breaker (żeby obaj nie ustąpili)
                    if other_dist < my_dist:
                        return True
                    elif other_dist == my_dist and other_medic_id < id(self):
                        return True
                        
        return False

    def act(self):
        """Faza leczenia (bez zmian)"""
        # ... (Twoja metoda act z poprzedniej odpowiedzi) ...
        # (Skopiuj act() i heal_target() i broadcast_heal() z poprzedniej wersji)
        if not self.grid or not self.target_infected:
            return 0

        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_heal_time < self.HEAL_COOLDOWN:
            return 0

        dist = math.sqrt((self.x - self.target_infected.x)**2 + (self.y - self.target_infected.y)**2)
        
        if dist <= self.HEAL_RANGE:
            self.heal_target()
            return 1 
            
        return 0
        
    def heal_target(self):
        if self.grid:
            from human import Human
            from soldier import Soldier
            from medic import Medic as MedicClass
            
            if self.target_infected not in self.grid.characters:
                self.target_infected = None
                return

            idx = self.grid.characters.index(self.target_infected)
            previous_type = getattr(self.target_infected, 'previous_type', 'Human')
            
            # Przywracanie postaci
            if previous_type == "Medic":
                healed = MedicClass(self.target_infected.x, self.target_infected.y, self.grid)
            elif previous_type == "Soldier":
                healed = Soldier(self.target_infected.x, self.target_infected.y, self.grid)
            else:
                healed = Human(self.target_infected.x, self.target_infected.y, self.grid)
            
            self.grid.characters[idx] = healed
            self.last_heal_time = pygame.time.get_ticks()
            
            # Broadcast sukcesu
            self.broadcast_heal(healed, previous_type)

            self.target_infected = None
            self.path = []

    def broadcast_heal(self, healed_character, healed_type):
        """Informuje o uleczeniu"""
        self.send_signal(
            signal_type="healing_performed",
            broadcast_range=10.0,
            data={
                "healed_pos": (healed_character.x, healed_character.y),
                "healed_type": healed_type
                # 'medic' to 'source' z send_signal
            }
        )

    def get_infected(self):
        self.is_alive = False
