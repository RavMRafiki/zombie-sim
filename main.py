import pygame
import random
import math

pygame.init()

GRID_SIZE = 12
CELL_SIZE = 80  # Each cell is 20x20 pixels
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
MOVE_INTERVAL = 500  # milliseconds (0.5 seconds)
FPS = 60

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
    signals = []
    
    def __init__(self, x, y, grid=None):
        self.x = x
        self.y = y
        self.grid = grid
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
        
        self.x = max(0, min(GRID_SIZE - 1, new_x))
        self.y = max(0, min(GRID_SIZE - 1, new_y))
    
    def act(self):
        """Perform character-specific action (override in subclasses)"""
        pass
    
    def send_signal(self, signal_type, broadcast_range=3, data=None):
        """Send a signal to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            # Calculate distance
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
    
    def process_signals(self):
        """Process all received signals (override in subclasses for custom behavior)"""
        self.signals.clear()
    
    def draw(self, screen):
        """Draw character on screen"""
        pixel_x = self.x * CELL_SIZE
        pixel_y = self.y * CELL_SIZE
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


class Zombie(Character):
    """Zombie character - moves aggressively"""
    
    char_type_name = "Zombie"
    color = COLOR_ZOMBIE
    move_speed = MOVE_INTERVAL
    INFECTION_RANGE = 1.99
    INFECTION_COOLDOWN = 5000
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_infection_time = 5000
    
    def act(self):
        """Zombies perform aggressive behavior - infect nearby humans"""
        if not self.grid:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check if infection is off cooldown
        if current_time - self.last_infection_time < self.INFECTION_COOLDOWN:
            return
        
        # Check for infectable characters in range
        for character in self.grid.characters:
            if isinstance(character, (Human, Medic, Soldier)):
                # Calculate distance
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Infect if in range
                if distance <= self.INFECTION_RANGE:
                    self.infect_character(character)
                    self.last_infection_time = current_time
                    break
    
    def infect_character(self, character):
        """Convert a character to infected"""
        if self.grid:
            idx = self.grid.characters.index(character)
            infected = Infected(character.x, character.y, self.grid, previous_type=character.get_type_name())
            self.grid.characters[idx] = infected


class Human(Character):
    """Human character - moves defensively"""
    
    char_type_name = "Human"
    color = COLOR_HUMAN
    move_speed = MOVE_INTERVAL
    THREAT_DETECTION_RANGE = 3.0
    THREAT_BROADCAST_RANGE = 7.0
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
    
    def act(self):
        """Humans perform survival behavior - broadcast threat information"""
        if not self.grid:
            return
        
        # Scan for zombies and infected nearby
        threats = []
        for character in self.grid.characters:
            if isinstance(character, (Zombie, Infected)):
                # Calculate distance
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Add to threats if in detection range
                if distance <= self.THREAT_DETECTION_RANGE:
                    threats.append({
                        "type": "Zombie" if isinstance(character, Zombie) else "Infected",
                        "position": (character.x, character.y),
                        "distance": distance
                    })
        
        # Broadcast threat information if threats detected
        if threats:
            self.broadcast_threat_info(threats)
    
    def broadcast_threat_info(self, threats):
        """Broadcast threat information to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send threat info if in broadcast range
            if distance <= self.THREAT_BROADCAST_RANGE:
                character.receive_signal("threat_alert", {
                    "source": self,
                    "source_pos": (self.x, self.y),
                    "threats": threats
                })


class Infected(Character):
    """Infected character - in transition state"""
    
    char_type_name = "Infected"
    previous_type = "Human"
    color = COLOR_INFECTED
    move_speed = int(MOVE_INTERVAL * 0.75)
    TRANSFORMATION_TIME = 10000
    BROADCAST_RANGE = 5.0
    
    def __init__(self, x, y, grid=None, previous_type=None):
        super().__init__(x, y, grid)
        self.infection_start_time = pygame.time.get_ticks()
        if previous_type:
            self.previous_type = previous_type
    
    def act(self):
        """Infected perform transitional behavior - transform to zombie and broadcast"""
        if not self.grid:
            return
        
        current_time = pygame.time.get_ticks()
        time_infected = current_time - self.infection_start_time
        
        self.broadcast_infected_status()
        
        if time_infected >= self.TRANSFORMATION_TIME:
            self.transform_to_zombie()
    
    def broadcast_infected_status(self):
        """Broadcast infected status to nearby characters"""
        if not self.grid:
            return
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            dx = self.x - character.x
            dy = self.y - character.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Send infected status if in broadcast range
            if distance <= self.BROADCAST_RANGE:
                character.receive_signal("got infected", {
                    "source": self,
                    "source_pos": (self.x, self.y),
                    "distance": distance,
                    "time_until_zombie": self.TRANSFORMATION_TIME - (pygame.time.get_ticks() - self.infection_start_time)
                })
    
    def transform_to_zombie(self):
        """Convert this infected to zombie"""
        if self.grid:
            idx = self.grid.characters.index(self)
            zombie = Zombie(self.x, self.y, self.grid)
            self.grid.characters[idx] = zombie


class Medic(Human):
    """Medic character - supports humans"""
    
    char_type_name = "Medic"
    color = COLOR_MEDIC
    move_speed = MOVE_INTERVAL
    HEAL_RANGE = 2.0  # Grid cells
    HEAL_TIME = 20000  # milliseconds before can heal again
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_heal_time = pygame.time.get_ticks()
        # self.heal_ticks = 0
    
    def act(self):
        """Medics perform healing/support behavior"""
        if not self.grid:
            return
        
        current_time = pygame.time.get_ticks()
        time_infected = current_time - self.last_heal_time
        
        if time_infected >= self.HEAL_TIME:
            return
        
        for character in self.grid.characters:
            if isinstance(character, Infected):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Heal if in range
                if distance <= self.HEAL_RANGE:
                    self.heal_infected(character)
                    break  # Only heal one infected per cooldown
    
    def heal_infected(self, infected):
        """Convert infected back to their previous type and broadcast healing"""
        if self.grid:
            idx = self.grid.characters.index(infected)
            
            # Restore to previous type based on stored type
            previous_type = infected.previous_type
            
            if previous_type == "Human":
                healed = Human(infected.x, infected.y, self.grid)
            elif previous_type == "Medic":
                healed = Medic(infected.x, infected.y, self.grid)
            elif previous_type == "Soldier":
                healed = Soldier(infected.x, infected.y, self.grid)
            else:
                healed = Human(infected.x, infected.y, self.grid)  # Default to Human
            
            self.grid.characters[idx] = healed
            
            # Broadcast healing action to nearby characters
            self.broadcast_heal(healed, previous_type)
    
    def broadcast_heal(self, healed_character, healed_type):
        """Broadcast healing action to nearby characters"""
        if not self.grid:
            return
        
        broadcast_range = 7.0  # Grid cells
        
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


class Soldier(Human):
    """Soldier character - combat specialist"""
    
    char_type_name = "Soldier"
    color = COLOR_SOLIDIER
    move_speed = int(MOVE_INTERVAL * 0.8)  # Soldiers move slightly faster
    KILL_RANGE = 3.0  # Grid cells
    KILL_COOLDOWN = 5000  # milliseconds
    
    def __init__(self, x, y, grid=None):
        super().__init__(x, y, grid)
        self.last_kill_time = 0
    
    def act(self):
        """Soldiers perform combat behavior - kill one zombie in range per cooldown"""
        if not self.grid:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check if killing is off cooldown
        if current_time - self.last_kill_time < self.KILL_COOLDOWN:
            return
        
        # Find first zombie in range
        for character in self.grid.characters:
            if isinstance(character, Zombie):
                dx = self.x - character.x
                dy = self.y - character.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Kill if in range
                if distance <= self.KILL_RANGE:
                    kill_pos = (character.x, character.y)
                    self.grid.characters.remove(character)
                    self.last_kill_time = current_time
                    self.broadcast_kill(kill_pos)
                    break
    
    def broadcast_kill(self, kill_pos):
        """Broadcast kill action to nearby characters"""
        if not self.grid:
            return
        
        broadcast_range = 7.0
        
        for character in self.grid.characters:
            if character is self:
                continue
            
            # Calculate distance
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
    
    grid = Grid(num_zombies=5, num_humans=2, num_infected=0, num_medics=2, num_soldiers=1)
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
