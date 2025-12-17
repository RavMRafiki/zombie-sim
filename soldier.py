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
    color = (255, 255, 0)
    move_speed = int(MOVE_INTERVAL * 0.8)
    KILL_RANGE = 3.0
    KILL_COOLDOWN = 5000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_kill_time = 0
    
    def act(self):
        """Logika walki i nagród Żołnierza"""
        if not self.grid:
            return 0
            
        current_time = pygame.time.get_ticks()
        step_reward = 0
        
        # 1. Nagroda za przeżycie (Standard)
        if self.is_alive:
            step_reward += 1
        else:
            return 0 # Martwy żołnierz nic nie robi
        
        from zombie import Zombie 
        from infected import Infected
        
        # Sprawdzamy Cooldown
        if current_time - self.last_kill_time >= self.KILL_COOLDOWN:
            
            # Szukamy celu w zasięgu
            for character in self.grid.characters:
                if isinstance(character, (Zombie, Infected)):
                    dx = self.x - character.x
                    dy = self.y - character.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance <= self.KILL_RANGE:
                        # STRZAŁ!
                        # Usuwamy zombie z gry (i z listy gridu)
                        # Uwaga: Musimy to zrobić bezpiecznie, żeby nie posypała się pętla w main
                        character.is_alive = False # Oznaczamy jako martwego
                        # W main.py trzeba dodać usuwanie martwych postaci z listy!
                        self.grid.characters.remove(character) 
                        
                        self.last_kill_time = current_time
                        self.broadcast_kill((character.x, character.y))
                        
                        step_reward += 10 # <--- DUŻA NAGRODA ZA FRAGA
                        print(f"Soldier {id(self)} killed a Zombie! Reward +50")
                        break
        
        # 3. Reward Shaping (Węch)
        # Obliczamy dystans do najbliższego wroga
        min_dist = float('inf')
        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)): # Importy już są wyżej
                dist = math.sqrt((self.x - char.x)**2 + (self.y - char.y)**2)
                if dist < min_dist:
                    min_dist = dist
                    
        # Inicjalizacja pamięci dystansu (dla pierwszego kroku)
        if not hasattr(self, 'prev_dist'): self.prev_dist = min_dist

        if min_dist < float('inf'):
            # Sprawdzamy czy broń jest gotowa (lub prawie gotowa)
            is_weapon_ready = (current_time - self.last_kill_time) > (self.KILL_COOLDOWN * 0.8)
            
            if is_weapon_ready:
                # Jeśli broń gotowa -> nagroda za ZBLIŻANIE SIĘ (Atak)
                if min_dist < self.prev_dist:
                    step_reward += 0.5 
                elif min_dist > self.prev_dist:
                    step_reward -= 0.5
            else:
                # Jeśli przeładowuje -> nagroda za UTRZYMANIE DYSTANSU (Kiting)
                # (Opcjonalnie: można to pominąć i pozwolić mu samemu odkryć, że blisko zombie = śmierć)
                pass

            self.prev_dist = min_dist
            
        return step_reward
    
    def broadcast_kill(self, kill_pos):
        """Broadcast kill action to nearby characters"""
        if not self.grid:
            return
        
        broadcast_range = 7.0
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send kill info if in broadcast range
            if distance <= broadcast_range:
                character.receive_signal("zombies_killed", {
                    "soldier": self,
                    "soldier_pos": (self.x, self.y),
                    "kill_position": kill_pos,
                    "distance": distance
                })

    def get_target_vector(self):
        """
        Zwraca wektor [dx, dy, weapon_status].
        Wskazuje na najbliższego ZOMBIE (nie człowieka).
        """
        # 1. Oblicz status broni (0.0 - 1.0)
        current_time = pygame.time.get_ticks()
        time_since_shot = current_time - self.last_kill_time
        
        weapon_status = 1.0 # Domyślnie gotowa
        if time_since_shot < self.KILL_COOLDOWN:
            weapon_status = time_since_shot / self.KILL_COOLDOWN
            
        # 2. Znajdź najbliższego ZOMBIE
        closest_zombie = None
        min_dist = float('inf')

        from zombie import Zombie 
        from infected import Infected

        for char in self.grid.characters:
            if isinstance(char, (Zombie, Infected)): # Żołnierz celuje we wrogów
                dist = (self.x - char.x)**2 + (self.y - char.y)**2
                if dist < min_dist:
                    min_dist = dist
                    closest_zombie = char
                    
        # Jeśli brak wrogów, zwracamy same zera (i status broni)
        if closest_zombie is None:
            return np.array([0.0, 0.0, weapon_status], dtype=np.float32)
            
        # 3. Oblicz wektor znormalizowany
        dx = closest_zombie.x - self.x
        dy = closest_zombie.y - self.y
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0: 
            return np.array([0.0, 0.0, weapon_status], dtype=np.float32)
        
        # Zwracamy wektor 3-elementowy
        return np.array([dx / length, dy / length, weapon_status], dtype=np.float32)
    
    def get_infected(self):
        """Metoda wywoływana przez Zombie, gdy infekcja się uda."""
        self.is_alive = False
        print(f"Żołnierz {id(self)} został zarażony! Kara -10")
