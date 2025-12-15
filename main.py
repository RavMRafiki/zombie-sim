"""Zombie Simulator - Main entry point"""

import pygame
from DQN.learn import DQNAgent
from grid import Grid
from zombie import Zombie
from human import Human
from constants import WINDOW_SIZE, COLOR_BACKGROUND, FPS

pygame.init()

zombie_agent = DQNAgent(input_shape=(4, 11, 11))
human_agent = DQNAgent(input_shape=(4, 11, 11))


def main():
    """Main game loop"""
    print("Initializing simulation...")
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Zombie Outbreak Simulation")
    clock = pygame.time.Clock()
    
    grid = Grid(num_zombies=40, num_humans=60, num_infected=0, num_medics=0, num_soldiers=0)
    font = pygame.font.Font(None, 24)
    
    running = True
    i = 0
    print("Starting simulation...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if i % 10 == 0:
            print(f"Frame {i}")
        i += 1
        global_map = grid.get_global_map_matrix()
        
        # Update
        # grid.update()
        update_game_logic(grid, global_map)
        
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

def update_game_logic(grid, global_map):
    """
    To zastępuje twoje proste `grid.update()`.
    Tutaj łączymy stan gry z sieciami neuronowymi.
    """
    
    # Przechodzimy przez każdą postać
    for char in grid.characters:
        
        # 1. OBSERWACJA (State)
        # Musisz napisać metodę get_observation(), która zwraca 4x11x11
        # 1. Pobierz obserwację wizualną
        visual_state = char.get_observation(global_map)

        # 2. Pobierz wektor celu (NOWOŚĆ)
        vector_state = char.get_target_vector() 

        # 3. Złóż w jeden stan
        current_state = (visual_state, vector_state)
        
        # 2. DECYZJA (Action)
        if isinstance(char, Zombie):
            action = zombie_agent.get_action(current_state)
        elif isinstance(char, Human):
            action = human_agent.get_action(current_state)
        else:
            action = 4 # Czekaj (dla innych klas)
            
        # 3. RUCH I INTERAKCJA (Step)
        # Zmieniamy metodę move, żeby przyjmowała akcję (0=Góra, 1=Dół, itd.)
        move_success = char.move(action) 
        
        # Pobieramy nagrodę z interakcji (infekcja, przeżycie)
        reward = 0
        if not move_success:
            if isinstance(char, Zombie):
                reward -= 0.1 # Kara za uderzenie w krawędź
            elif isinstance(char, Human):
                reward -= 0.5 
        done = False # Czy postać "skończyła grę" (zginęła)
        
        if isinstance(char, Zombie):
            if action == 4:
                reward -= 0.5 # Kara za czekanie (pogania zombie)
            reward += char.act() # Tu wróci +10 jeśli zaraził
            reward -= 0.1 # Kara za czas (pogania zombie)
        elif isinstance(char, Human):
            reward += char.act() # Tu wróci +1 za przeżycie
            if not char.is_alive: # Ustalone w get_infected()
                reward = -10
                done = True
        
        # 4. NOWY STAN (Next State)
        new_visual = char.get_observation(global_map)
        new_vector = char.get_target_vector()
        next_state = (new_visual, new_vector)
        
        # 5. NAUKA (Store & Learn)
        if isinstance(char, Zombie):
            zombie_agent.memory.push(current_state, action, reward, next_state, done)
            zombie_agent.learn() # Odpalamy backpropagation
            
        elif isinstance(char, Human):
            human_agent.memory.push(current_state, action, reward, next_state, done)
            human_agent.learn()

if __name__ == "__main__":
    main()
