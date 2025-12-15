"""Zombie character class"""

import math
import pygame
from character import Character
from constants import MOVE_INTERVAL


class Zombie(Character):
    """Zombie character - moves aggressively"""
    
    char_type_name = "Zombie"
    color = (0, 255, 0)
    move_speed = MOVE_INTERVAL
    INFECTION_RANGE = 1.99
    INFECTION_COOLDOWN = 5000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_infection_time = 5000
        self.prev_dist = 0
    
    def act(self):
        """Zombies perform aggressive behavior - infect nearby humans"""
        if not self.grid: 
            return 0
        
        current_time = pygame.time.get_ticks()
        step_reward = 0 # Domyślna nagroda (może być -0.1 za upływ czasu)

        min_dist = float('inf')
        from human import Human # Importy
        
        # Znajdź najbliższego człowieka
        for char in self.grid.characters:
            if isinstance(char, Human): # (Dla uproszczenia pomijam Medic/Soldier w tym przykładzie)
                dist = math.sqrt((self.x - char.x)**2 + (self.y - char.y)**2)
                if dist < min_dist:
                    min_dist = dist
        
        # Logika "Węchu" (Reward Shaping)
        VIEW_RANGE = 5.0

        if min_dist < float('inf'):
            # Nagroda za zbliżanie się do najbliższego człowieka
            if min_dist < VIEW_RANGE:
                step_reward += (VIEW_RANGE - min_dist) * 0.2 # Im bliżej, tym większa nagroda

                if min_dist < self.prev_dist:
                    step_reward += 0.5 # Dodatkowa nagroda za dobry kierunek

                elif min_dist > self.prev_dist:
                    step_reward -= 0.5 # Kara za zły kierunek

            self.prev_dist = min_dist
        else:
            self.prev_dist = float('inf')
        
        # Check if infection is off cooldown
        if current_time - self.last_infection_time < self.INFECTION_COOLDOWN:
            return step_reward
        
        # Import here to avoid circular imports
        
        from medic import Medic
        from soldier import Soldier
        from infected import Infected
        
        # Check for infectable characters in range
        for character in self.grid.characters:
            if isinstance(character, (Human, Medic, Soldier)):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Infect if in range
                if distance <= self.INFECTION_RANGE:
                    success = self.infect_character(character)
                    if success:
                        step_reward += 10 # <--- TUTAJ JEST TWOJA NAGRODA
                        print(f"Zombie {id(self)} zaraził człowieka! Nagroda +10")
                        self.last_infection_time = current_time
                        break # Zazwyczaj jeden atak na turę

        return step_reward
    
    def infect_character(self, character):
        """Convert a character to infected"""
        if self.grid:
            from infected import Infected
            
            idx = self.grid.characters.index(character)
            infected = Infected(character.x, character.y, self.grid, previous_type=character.get_type_name())
            self.grid.characters[idx] = infected

        character.get_infected()

        return True

    def get_target_vector(self):
        """
        Zwraca znormalizowany wektor [dx, dy] wskazujący na najbliższego człowieka.
        Jeśli brak ludzi, zwraca [0, 0].
        """
        closest_human = None
        min_dist = float('inf')
        from human import Human
        import numpy as np
        
        # Znajdź najbliższego człowieka (używając globalnej listy z gridu)
        for char in self.grid.characters:
            if isinstance(char, Human): # i ewentualnie Medic/Soldier
                dist = (self.x - char.x)**2 + (self.y - char.y)**2 # Bez pierwiastka szybciej
                if dist < min_dist:
                    min_dist = dist
                    closest_human = char
                    
        if closest_human is None:
            return np.array([0.0, 0.0], dtype=np.float32)
            
        # Oblicz różnicę
        dx = closest_human.x - self.x
        dy = closest_human.y - self.y
        
        # Normalizacja wektora (żeby miał długość 1)
        length = math.sqrt(dx**2 + dy**2)
        if length == 0: return np.array([0.0, 0.0], dtype=np.float32)
        
        return np.array([dx / length, dy / length], dtype=np.float32)
