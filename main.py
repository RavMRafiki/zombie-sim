"""Zombie Simulator - Main entry point"""

import pygame
import sys
import os
import argparse
from DQN.learn import DQNAgent
from grid import Grid
from infected import Infected
from soldier import Soldier
from zombie import Zombie
from human import Human
from medic import Medic
from constants import WINDOW_SIZE, COLOR_BACKGROUND, COLOR_ZOMBIE, COLOR_HUMAN, COLOR_INFECTED, COLOR_MEDIC, COLOR_SOLIDIER

# --- 2. Obsługa argumentów command line ---
parser = argparse.ArgumentParser(description='Zombie Outbreak Simulation')
parser.add_argument('--learn', action='store_true', help='Włącz tryb uczenia (trening sieci)')
args = parser.parse_args()

IS_TRAINING = args.learn # True jeśli podano --learn, False jeśli nie

print(f"--- SIMULATION MODE: {'TRAINING' if IS_TRAINING else 'INFERENCE (PLAYING)'} ---")
os.environ['SDL_VIDEO_WINDOW_POS'] = "100,100"
pygame.init()

zombie_agent = DQNAgent(input_shape=(4, 11, 11), vector_size=2, agent_name="zombie", training_mode=IS_TRAINING)
human_agent  = DQNAgent(input_shape=(4, 11, 11), vector_size=4, agent_name="human",  training_mode=IS_TRAINING)
soldier_agent= DQNAgent(input_shape=(4, 11, 11), vector_size=3, agent_name="soldier", training_mode=IS_TRAINING)

def main():
    """Main game loop"""
    print("Initializing simulation...")
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE+ 40))
    pygame.display.set_caption("Zombie Outbreak Simulation")
    clock = pygame.time.Clock()
    
    grid = Grid(num_zombies=38, num_humans=45, num_infected=0, num_medics=10, num_soldiers=25)
    font = pygame.font.Font(None, 24)
    
    running = True
    i = 0
    print("Starting simulation...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if IS_TRAINING:
                    zombie_agent.save_model()
                    human_agent.save_model()
                    soldier_agent.save_model()
                running = False

        if i % 10 == 0:
            print(f"Frame {i}")
        i += 1
        global_map = grid.get_global_map_matrix()
        
        update_game_logic(grid, global_map)
        
        # Draw
        screen.fill(COLOR_BACKGROUND)
        grid.draw(screen, offset_y=40)
        
        # Draw stats
        zombie_count, human_count, infected_count, medic_count, soldier_count = grid.get_stats()
        stats_data = [
            ("Zombie", zombie_count, COLOR_ZOMBIE),
            ("Human", human_count, COLOR_HUMAN),
            ("Infected", infected_count, COLOR_INFECTED),
            ("Medic", medic_count, COLOR_MEDIC),
            ("Soldier", soldier_count, COLOR_SOLIDIER)
        ]

        current_x = 10  
        y_pos = 10   
        icon_size = 15  
        spacing = 5      
        group_spacing = 15 

        for label, count, color in stats_data:

            pygame.draw.rect(screen, color, (current_x, y_pos, icon_size, icon_size))
            
            text_str = f"{label}: {count}"
            text_surface = font.render(text_str, True, (255, 255, 255))
            
            screen.blit(text_surface, (current_x + icon_size + spacing, y_pos + 2))
            current_x += icon_size + spacing + text_surface.get_width() + group_spacing
            
        pygame.display.flip()
        if IS_TRAINING:
            clock.tick(0) # Max speed
        else:
            clock.tick(60) # Oglądalna prędkość
    
    pygame.quit()

def update_game_logic(grid, global_map):
    """
    Dwuetapowa aktualizacja: najpierw wszyscy liczą akcję, potem wykonują ruchy
    i akcje, a na końcu renderujemy. Dzięki temu nowa klatka pojawia się po
    wyznaczeniu ruchu przez wszystkie jednostki.
    """

    # 1) FAZA DECYZYJNA — każdy liczy akcję na tej samej obserwacji
    decisions = []  # (char, current_state, action)
    for char in list(grid.characters):
        if isinstance(char, Infected):
            # Infected nie planują decyzji DQN
            decisions.append((char, None, None))
            continue

        char.process_signals()

        visual_state = char.get_observation(global_map)
        vector_state = char.get_target_vector()
        current_state = (visual_state, vector_state)

        if isinstance(char, Zombie):
            action = zombie_agent.get_action(current_state)
        elif isinstance(char, Human) and not isinstance(char, Soldier):
            action = human_agent.get_action(current_state)
        elif isinstance(char, Soldier):
            action = soldier_agent.get_action(current_state)
        elif isinstance(char, Medic):
            action = char.get_autonomous_action()
        else:
            action = 4

        decisions.append((char, current_state, action))

    # 2) FAZA RUCHU — wykonujemy ruchy zgodnie z policzonymi akcjami
    move_results = {}  # char -> bool
    for char, _, action in decisions:
        if action is None:
            continue
        move_results[char] = char.move(action)

    # 3) FAZA AKCJI I NAGRÓD — liczymy act() i rewardy już po ruchach
    pending = []  # (agent, char, current_state, action, reward, done)

    for char, current_state, action in decisions:
        if isinstance(char, Infected):
            char.act()
            continue

        reward = 0.0
        done = False
        move_success = move_results.get(char, True)

        if not move_success:
            if isinstance(char, Zombie):
                reward -= 0.1
            elif isinstance(char, Human) and not isinstance(char, Soldier):
                reward -= 0.5
            elif isinstance(char, Soldier):
                reward -= 0.1

        if isinstance(char, Medic):
            char.act()
        elif isinstance(char, Zombie):
            if action == 4:
                if hasattr(char, 'prev_dist') and char.prev_dist < char.SIEGE_RANGE:
                    pass
                else:
                    reward -= 0.5
            reward += char.act()
            reward -= 0.05
            if not char.is_alive:
                reward -= 10
                done = True
        elif isinstance(char, Soldier):
            reward += char.act()
            if not char.is_alive:
                reward = -10
                done = True
        elif isinstance(char, Human):
            reward += char.act()
            if not char.is_alive:
                reward = -10
                done = True

        agent = None
        if isinstance(char, Soldier):
            agent = soldier_agent
        elif isinstance(char, Zombie):
            agent = zombie_agent
        elif isinstance(char, Human) and not isinstance(char, Soldier):
            agent = human_agent

        if agent is not None and current_state is not None:
            pending.append((agent, char, current_state, action, reward, done))

    # 4) NEXT STATE — jedna, spójna mapa po wszystkich ruchach i akcjach
    global_map_next = grid.get_global_map_matrix()

    for agent, char, current_state, action, reward, done in pending:
        new_visual = char.get_observation(global_map_next)
        new_vector = char.get_target_vector()
        next_state = (new_visual, new_vector)
        agent.memory.push(current_state, action, reward, next_state, done)
        agent.learn()

if __name__ == "__main__":
    main()
