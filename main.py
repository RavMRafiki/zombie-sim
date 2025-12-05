import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
GRID_SIZE = 128
CELL_SIZE = 8  # Each cell is 20x20 pixels
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
MOVE_INTERVAL = 500  # milliseconds (0.5 seconds)
FPS = 60

# Colors
COLOR_BACKGROUND = (50, 50, 50)
COLOR_GRID = (100, 100, 100)
COLOR_ZOMBIE = (0, 255, 0)
COLOR_HUMAN = (0, 0, 255)
COLOR_INFECTED = (255, 165, 0)
COLOR_MEDIC = (255, 0, 0)
COLOR_SOLIDIER = (255, 255, 0)

class Character:
    """Base class for all characters on the grid"""
    
    char_type_name = "Character"
    color = (255, 255, 255)
    move_speed = MOVE_INTERVAL
    
    def __init__(self, x, y):
        self.x = x  # Grid coordinates
        self.y = y
        self.last_move_time = pygame.time.get_ticks()
    
    def update(self, current_time):
        """Update character movement based on elapsed time"""
        if current_time - self.last_move_time >= self.move_speed:
            self.move()
            self.act()
            self.last_move_time = current_time
    
    def move(self):
        """Move character randomly in one of 4 directions"""
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        new_x = self.x + direction[0]
        new_y = self.y + direction[1]
        
        # Keep within grid bounds
        self.x = max(0, min(GRID_SIZE - 1, new_x))
        self.y = max(0, min(GRID_SIZE - 1, new_y))
    
    def act(self):
        """Perform character-specific action (override in subclasses)"""
        pass
    
    def draw(self, screen):
        """Draw character on screen"""
        pixel_x = self.x * CELL_SIZE
        pixel_y = self.y * CELL_SIZE
        pygame.draw.rect(screen, self.color, (pixel_x, pixel_y, CELL_SIZE, CELL_SIZE))
    
    def get_type_name(self):
        """Return character type name"""
        return self.char_type_name


class Zombie(Character):
    """Zombie character - moves aggressively"""
    
    char_type_name = "Zombie"
    color = COLOR_ZOMBIE
    move_speed = MOVE_INTERVAL
    
    def act(self):
        """Zombies perform aggressive behavior"""
        # Can be extended with hunting logic, infection spreading, etc.
        pass


class Human(Character):
    """Human character - moves defensively"""
    
    char_type_name = "Human"
    color = COLOR_HUMAN
    move_speed = MOVE_INTERVAL
    
    def act(self):
        """Humans perform survival behavior"""
        # Can be extended with fleeing logic, etc.
        pass


class Infected(Character):
    """Infected character - in transition state"""
    
    char_type_name = "Infected"
    color = COLOR_INFECTED
    move_speed = int(MOVE_INTERVAL * 0.75)  # Infected move faster
    
    def act(self):
        """Infected perform transitional behavior"""
        # Can be extended with transformation logic, etc.
        pass


class Medic(Character):
    """Medic character - supports humans"""
    
    char_type_name = "Medic"
    color = COLOR_MEDIC
    move_speed = MOVE_INTERVAL
    
    def act(self):
        """Medics perform healing/support behavior"""
        # Can be extended with healing logic, etc.
        pass


class Soldier(Character):
    """Soldier character - combat specialist"""
    
    char_type_name = "Soldier"
    color = COLOR_SOLIDIER
    move_speed = int(MOVE_INTERVAL * 0.8)  # Soldiers move slightly faster
    
    def act(self):
        """Soldiers perform combat behavior"""
        # Can be extended with combat logic, etc.
        pass


class Grid:
    """Represents the game grid and manages characters"""
    
    def __init__(self, num_zombies=10, num_humans=15, num_infected=5, num_medics=2, num_soldiers=2):
        self.characters = []
        
        # Create zombies
        for _ in range(num_zombies):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Zombie(x, y))
        
        # Create humans
        for _ in range(num_humans):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Human(x, y))
        
        # Create infected
        for _ in range(num_infected):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Infected(x, y))
            
        # Create medics
        for _ in range(num_medics):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Medic(x, y))
        
        # Create soldiers
        for _ in range(num_soldiers):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.characters.append(Soldier(x, y))
    
    def update(self):
        """Update all characters"""
        current_time = pygame.time.get_ticks()
        for character in self.characters:
            character.update(current_time)
    
    def draw(self, screen):
        """Draw grid and all characters"""
        # Draw grid lines
        for i in range(0, WINDOW_SIZE, CELL_SIZE):
            pygame.draw.line(screen, COLOR_GRID, (i, 0), (i, WINDOW_SIZE))
            pygame.draw.line(screen, COLOR_GRID, (0, i), (WINDOW_SIZE, i))
        
        # Draw characters
        for character in self.characters:
            character.draw(screen)
    
    def get_stats(self):
        """Get count of each character type"""
        zombie_count = sum(1 for c in self.characters if isinstance(c, Zombie))
        human_count = sum(1 for c in self.characters if isinstance(c, Human))
        infected_count = sum(1 for c in self.characters if isinstance(c, Infected))
        medic_count = sum(1 for c in self.characters if isinstance(c, Medic))
        soldier_count = sum(1 for c in self.characters if isinstance(c, Soldier))
        return zombie_count, human_count, infected_count, medic_count, soldier_count


def main():
    """Main game loop"""
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Zombie Outbreak Simulation")
    clock = pygame.time.Clock()
    
    grid = Grid(num_zombies=10, num_humans=15, num_infected=5, num_medics=2, num_soldiers=2)
    font = pygame.font.Font(None, 24)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update
        grid.update()
        
        # Draw
        screen.fill(COLOR_BACKGROUND)
        grid.draw(screen)
        
        # Draw stats
        zombie_count, human_count, infected_count, medic_count, soldier_count = grid.get_stats()
        stats_text = f"Zombies: {zombie_count} | Humans: {human_count} | Infected: {infected_count} | Medics: {medic_count} | Soldiers: {soldier_count}"
        stats_surface = font.render(stats_text, True, (255, 255, 255))
        screen.blit(stats_surface, (10, 10))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()


if __name__ == "__main__":
    main()
