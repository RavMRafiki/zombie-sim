"""Base Character class"""

import pygame
import math
from constants import GRID_SIZE, CELL_SIZE, MOVE_INTERVAL
import numpy as np
from collections import deque


class Character:
    """Base class for all characters on the grid"""
    
    char_type_name = "Character"
    color = (255, 255, 255)
    move_speed = MOVE_INTERVAL
    
    def __init__(self, x, y, grid=None):
        self.x = x
        self.y = y
        self.grid = grid
        self.is_alive = True
        self.last_move_time = pygame.time.get_ticks()
        self.signals = []
        self.SIGNAL_MEMORY_TIME = 10000 # Pamiętamy sygnały przez 10 sekund
        # Inicjalizacja pustego bufora (4 klatki, 11x11 zer)
        self.state_buffer = deque(maxlen=4)
        for _ in range(4):
            self.state_buffer.append(np.zeros((11, 11)))
    
    def update(self, current_time):
        """Update character movement based on elapsed time"""
        if current_time - self.last_move_time >= self.move_speed:
            self.move()
            self.act()
            self.process_signals()
            self.last_move_time = current_time
    
    def move(self, action_code=None):
        """Move character based on action code"""
        dx, dy = 0, 0
        if action_code == 0: dy = -1  # Góra
        elif action_code == 1: dy = 1 # Dół
        elif action_code == 2: dx = -1 # Lewo
        elif action_code == 3: dx = 1  # Prawo
        elif action_code == 4: pass   # Czekaj

        new_x = self.x + dx
        new_y = self.y + dy

        if new_x < 0 or new_x >= GRID_SIZE or new_y < 0 or new_y >= GRID_SIZE:
            return False # <--- Zwracamy Fałsz (uderzenie w krawędź)
        
        new_x = max(0, min(GRID_SIZE - 1, new_x))
        new_y = max(0, min(GRID_SIZE - 1, new_y))
        
        occupied = False
        if self.grid:
            for character in self.grid.characters:
                if character is not self and character.x == new_x and character.y == new_y:
                    occupied = True
                    break
        
        if not occupied:
            self.x = new_x
            self.y = new_y
            return True
        else:
            return False
    
    def act(self):
        """Perform character-specific action (override in subclasses)"""
        pass

    def process_signals(self):
        """Usuwa przestarzałe sygnały"""
        current_time = pygame.time.get_ticks()
        # Zostawiamy tylko te, które są młodsze niż 3 sekundy
        self.signals = [s for s in self.signals if current_time - s["time"] < self.SIGNAL_MEMORY_TIME]
    
    def send_signal(self, signal_type, broadcast_range=3, data=None):
        """Send a signal to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send signal if in range
            if distance <= broadcast_range:
                character.receive_signal(signal_type, {
                    "source": self,
                    "source_pos": (self.x, self.y),
                    "distance": distance,
                    "data": data
                })
    
    def receive_signal(self, signal_type, signal_data):
        """Receive a signal from another character"""
        self.signals.append({
            "type": signal_type,
            "data": signal_data,
            "time": pygame.time.get_ticks()
        })
    
    def draw(self, screen, offset_y=0):
        """Draw character on screen"""
        pixel_x = self.x * CELL_SIZE
        pixel_y = self.y * CELL_SIZE + offset_y
        pygame.draw.rect(screen, self.color, (pixel_x, pixel_y, CELL_SIZE, CELL_SIZE))
    
    def get_type_name(self):
        """Return character type name"""
        return self.char_type_name

    def get_surrounding_characters(self, radius=3):
        """Get characters within a certain radius"""
        if not self.grid:
            return []
        
        nearby_characters = []
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= radius:
                nearby_characters.append(character)
        
        return nearby_characters
    
    def get_observation(self, global_matrix):
        """
        Wyciąga wycinek 11x11 wokół postaci i aktualizuje stos 4 klatek.
        Args:
            global_matrix: Macierz całej planszy wygenerowana w Grid
        Returns:
            np.array o kształcie (4, 11, 11) gotowy dla sieci neuronowej
        """
        view_size = 11
        radius = view_size // 2 # 5 kratek w każdą stronę
        
        # Tworzymy pustą macierz 11x11 wypełnioną 1 (traktujemy granice mapy jak ściany)
        local_view = np.ones((view_size, view_size))
        
        # Obliczamy zakres wycinka (uważając na granice mapy)
        x_start = self.x - radius
        x_end = self.x + radius + 1
        y_start = self.y - radius
        y_end = self.y + radius + 1
        
        # Obliczamy indeksy w lokalnej macierzy (gdzie wkleić dane)
        local_x_start = 0
        local_x_end = view_size
        local_y_start = 0
        local_y_end = view_size
        
        # Przycinanie do granic mapy (jeśli jesteśmy przy krawędzi)
        if x_start < 0:
            local_x_start = -x_start # Przesuwamy początek wklejania
            x_start = 0
        if y_start < 0:
            local_y_start = -y_start
            y_start = 0
        if x_end > GRID_SIZE:
            local_x_end = view_size - (x_end - GRID_SIZE)
            x_end = GRID_SIZE
        if y_end > GRID_SIZE:
            local_y_end = view_size - (y_end - GRID_SIZE)
            y_end = GRID_SIZE

        # Wycinamy fragment z dużej mapy i wklejamy do lokalnej
        # Dzięki temu granice mapy (których nie nadpiszemy) zostaną jako 1 (ściana)
        if x_end > x_start and y_end > y_start:
            local_view[local_y_start:local_y_end, local_x_start:local_x_end] = \
                global_matrix[y_start:y_end, x_start:x_end]
                
        # Frame Stacking - dodajemy nową klatkę, stara wypada
        self.state_buffer.append(local_view)
        
        # Zamiana deque na numpy array (4, 11, 11)
        return np.array(self.state_buffer)
    
    def get_target_vector(self):
        # Placeholder method to get target vector (dx, dy)
        return np.array([0.0, 0.0], dtype=np.float32)
