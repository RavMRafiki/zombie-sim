"""Game grid and manager"""

import random
import pygame
import numpy as np
from zombie import Zombie
from human import Human
from infected import Infected
from medic import Medic
from soldier import Soldier
from constants import GRID_SIZE, CELL_SIZE, WINDOW_SIZE, COLOR_BACKGROUND, COLOR_GRID


class Grid:
    """Represents the game grid and manages characters"""
    
    def __init__(self, num_zombies=10, num_humans=15, num_infected=5, num_medics=2, num_soldiers=2):
        self.characters = []
        
        # Create zombies
        for _ in range(num_zombies):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Zombie(x, y, self))
        
        # Create humans
        for _ in range(num_humans):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Human(x, y, self))
        
        # Create infected
        for _ in range(num_infected):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Infected(x, y, self))
            
        # Create medics
        for _ in range(num_medics):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Medic(x, y, self))
        
        # Create soldiers
        for _ in range(num_soldiers):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Soldier(x, y, self))
    
    def update(self):
        """Update all characters"""
        current_time = pygame.time.get_ticks()
        for character in self.characters:
            character.update(current_time)
    
    def draw(self, screen, offset_y=0):
        """Draw grid and all characters"""
        # Draw grid lines
        for i in range(0, WINDOW_SIZE, CELL_SIZE): 
            pygame.draw.line(screen, COLOR_GRID, (i, offset_y), (i, WINDOW_SIZE + offset_y)) 
            pygame.draw.line(screen, COLOR_GRID, (0, i + offset_y), (WINDOW_SIZE, i + offset_y)) 
            
        # Draw characters (też przesunięte) 
        for character in self.characters: 
            character.draw(screen, offset_y=offset_y)
    
    def get_stats(self):
        """Get count of each character type"""
        zombie_count = sum(1 for c in self.characters if isinstance(c, Zombie))
        human_count = sum(1 for c in self.characters if isinstance(c, Human) and not isinstance(c, (Medic, Soldier)))
        infected_count = sum(1 for c in self.characters if isinstance(c, Infected))
        medic_count = sum(1 for c in self.characters if isinstance(c, Medic))
        soldier_count = sum(1 for c in self.characters if isinstance(c, Soldier))
        return zombie_count, human_count, infected_count, medic_count, soldier_count

    def get_global_map_matrix(self):
        """
        Tworzy macierz całej planszy (np. 128x128), gdzie:
        0 = Pusto, 1 = Ściana (jeśli są), -1 = Zombie/Infected, 0.5 = Human/Medic/Soldier
        Robimy to raz na klatkę, żeby było szybko.
        """
        matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        
        for char in self.characters:
            if isinstance(char, (Zombie, Infected)):
                matrix[char.y, char.x] = -1.0 # Wrogowie
            elif isinstance(char, (Human, Medic, Soldier)):
                matrix[char.y, char.x] = 0.5  # Sojusznicy
                
        return matrix
