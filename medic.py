"""Medic character class"""

import math
import pygame
from character import Character
from constants import MOVE_INTERVAL
from pathfinding import a_star_search


class Medic(Character):
    """Medic character - supports humans"""
    
    char_type_name = "Medic"
    color = (255, 0, 0)
    move_speed = MOVE_INTERVAL
    HEAL_RANGE = 1.5
    HEAL_COOLDOWN = 5000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_heal_time = -self.HEAL_COOLDOWN
        self.target_infected = None # Obiekt Infected, do którego biegniemy
        self.path = [] # Lista kroków [(x,y), (x,y)...]
    
    def get_autonomous_action(self):
        """
        To jest 'mózg' Medyka (zamiast sieci neuronowej).
        Zwraca kod akcji (0-4) na podstawie algorytmu A*.
        """
        # Jeśli nie ma gridu, czekaj
        if not self.grid: return 4
        
        # 1. Walidacja celu (czy nadal istnieje i jest zainfekowany?)
        from infected import Infected
        if self.target_infected:
            if (self.target_infected not in self.grid.characters or 
                not isinstance(self.target_infected, Infected)):
                self.target_infected = None
                self.path = []

        # 2. Znalezienie nowego celu (jeśli brak) - Logika Koordynacji
        if not self.target_infected:
            self.find_best_target()

        # 3. Jeśli nadal brak celu (nikt nie choruje), czekaj lub chodź losowo
        if not self.target_infected:
            return 4 

        # 4. Sprawdź czy jesteśmy w zasięgu leczenia
        dist = math.sqrt((self.x - self.target_infected.x)**2 + (self.y - self.target_infected.y)**2)
        if dist <= self.HEAL_RANGE:
            return 4 # Stój w miejscu i lecz (act() to obsłuży)

        # 5. Oblicz/Aktualizuj ścieżkę A*
        # Przeliczamy ścieżkę co klatkę (lub co kilka), bo cel się rusza!
        # Dla optymalizacji można to robić rzadziej, ale A* na małej mapie jest szybki.
        obstacles = set() # Tu można dodać (c.x, c.y) dla Zombie, żeby ich omijać
        
        start = (self.x, self.y)
        goal = (self.target_infected.x, self.target_infected.y)
        
        # Wywołujemy zewnętrzną funkcję A*
        new_path = a_star_search(start, goal, obstacles)
        
        if new_path and len(new_path) > 0:
            next_step = new_path[0] # Pierwszy krok
            
            # Tłumaczenie koordynatów na akcję (0-3)
            dx = next_step[0] - self.x
            dy = next_step[1] - self.y

            
            if dy == -1: return 0 # UP
            if dy == 1:  return 1 # DOWN
            if dx == -1: return 2 # LEFT
            if dx == 1:  return 3 # RIGHT
            
        return 4 # Jeśli nie ma ścieżki, czekaj
    
    def act(self):
        """
        Faza interakcji: Tylko leczenie.
        Ruch został już wykonany przez move(action) w main loopie.
        """
        if not self.grid or not self.target_infected:
            return 0

        current_time = pygame.time.get_ticks()
        
        # Sprawdź cooldown
        if current_time - self.last_heal_time < self.HEAL_COOLDOWN:
            return 0

        # Sprawdź dystans
        dist = math.sqrt((self.x - self.target_infected.x)**2 + (self.y - self.target_infected.y)**2)
        
        if dist <= self.HEAL_RANGE:
            self.heal_target()
            return 1 # Zwraca 1 jako "nagrodę" (statystykę), że wyleczył
            
        return 0
    
    def find_best_target(self):
        """Znajduje najbliższego Infected, dla którego ten medyk jest najlepszym wyborem."""
        from infected import Infected
        from medic import Medic as MedicClass

        min_dist = float('inf')
        best_candidate = None
        
        my_pos = (self.x, self.y)
        all_infected = [c for c in self.grid.characters if isinstance(c, Infected)]
        all_medics = [c for c in self.grid.characters if isinstance(c, MedicClass)]
        
        for infected in all_infected:
            target_pos = (infected.x, infected.y)
            dist_to_me = math.sqrt((my_pos[0]-target_pos[0])**2 + (my_pos[1]-target_pos[1])**2)
            
            # Sprawdź konkurencję: Czy inny medyk ma bliżej do tego gościa?
            am_i_closest = True
            for medic in all_medics:
                if medic is self: continue
                dist_to_other = math.sqrt((medic.x-target_pos[0])**2 + (medic.y-target_pos[1])**2)
                if dist_to_other < dist_to_me:
                    am_i_closest = False
                    break
            
            # Wybieramy tylko jeśli jesteśmy najlepsi do tego zadania
            if am_i_closest and dist_to_me < min_dist:
                min_dist = dist_to_me
                best_candidate = infected
        
        self.target_infected = best_candidate

    def heal_target(self):
        """Convert infected back to their previous type and broadcast healing"""
        if self.grid:
            from human import Human
            from medic import Medic
            from soldier import Soldier
            
            idx = self.grid.characters.index(self.target_infected)
            
            # Restore to previous type based on stored type
            previous_type = self.target_infected.previous_type
            
            if previous_type == "Human":
                healed = Human(self.target_infected.x, self.target_infected.y, self.grid)
            elif previous_type == "Medic":
                healed = Medic(self.target_infected.x, self.target_infected.y, self.grid)
            elif previous_type == "Soldier":
                healed = Soldier(self.target_infected.x, self.target_infected.y, self.grid)
            else:
                healed = Human(self.target_infected.x, self.target_infected.y, self.grid)
            
            self.grid.characters[idx] = healed
            self.last_heal_time = pygame.time.get_ticks()
            
            # Broadcast healing action to nearby characters
            self.broadcast_heal(healed, previous_type)

            self.target_infected = None # Cel zniknął (wyzdrowiał)
            self.path = []
            self.last_heal_time = pygame.time.get_ticks()
    
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

    def get_infected(self):
        """Metoda wywoływana przez Zombie, gdy infekcja się uda."""
        self.is_alive = False
