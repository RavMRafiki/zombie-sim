"""Zombie Simulator - Main entry point"""

import pygame
from DQN.learn import DQNAgent
from grid import Grid
from infected import Infected
from soldier import Soldier
from zombie import Zombie
from human import Human
from medic import Medic
from constants import WINDOW_SIZE, COLOR_BACKGROUND, COLOR_ZOMBIE, COLOR_HUMAN, COLOR_INFECTED, COLOR_MEDIC, COLOR_SOLIDIER

pygame.init()

zombie_agent = DQNAgent(input_shape=(4, 11, 11))
human_agent = DQNAgent(input_shape=(4, 11, 11), vector_size=4)
soldier_agent = DQNAgent(input_shape=(4, 11, 11), vector_size=3)

def main():
    """Main game loop"""
    print("Initializing simulation...")
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE+ 40))
    pygame.display.set_caption("Zombie Outbreak Simulation")
    clock = pygame.time.Clock()
    
    grid = Grid(num_zombies=30, num_humans=40, num_infected=0, num_medics=10, num_soldiers=20)
    font = pygame.font.Font(None, 24)
    
    # Game state management
    game_state = "menu"  # menu | running | gameover_dead | gameover_win
    final_kills = 0
    final_humans = 0
    
    # Pick one Soldier for player control
    player_soldier = next((c for c in grid.characters if isinstance(c, Soldier)), None)
    control_enabled = True if player_soldier else False
    if player_soldier:
        player_soldier.is_player_controlled = True
        # Highlight player-controlled soldier with a different color (cyan)
        player_soldier.color = (0, 255, 255)
    
    running = True
    i = 0
    print("Starting simulation...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_state == "menu":
                    # Any key starts the game (Space/Enter recommended)
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        game_state = "running"
                elif game_state.startswith("gameover"):
                    # Restart with R
                    if event.key == pygame.K_r:
                        grid = Grid(num_zombies=30, num_humans=40, num_infected=0, num_medics=10, num_soldiers=20)
                        player_soldier = next((c for c in grid.characters if isinstance(c, Soldier)), None)
                        control_enabled = True if player_soldier else False
                        if player_soldier:
                            player_soldier.is_player_controlled = True
                            player_soldier.color = (0, 255, 255)
                        final_kills = 0
                        final_humans = 0
                        game_state = "running"
                    # Quit with Q or Esc
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False
                else:
                    # Toggle player control on/off during gameplay
                    if event.key == pygame.K_c and player_soldier:
                        control_enabled = not control_enabled
                        player_soldier.is_player_controlled = control_enabled
                        # Switch color based on control state
                        player_soldier.color = (0, 255, 255) if control_enabled else COLOR_SOLIDIER

        if i % 10 == 0:
            print(f"Frame {i}")
        i += 1
        # Draw
        screen.fill(COLOR_BACKGROUND)
        
        if game_state == "menu":
            # Start screen
            title = pygame.font.Font(None, 36).render("Zombie Outbreak Simulation", True, (255, 255, 255))
            subtitle = font.render("Press Space or Enter to start", True, (200, 200, 200))
            info1 = font.render("Control one Soldier (cyan). WASD/Arrows move.", True, (200, 200, 255))
            info2 = font.render("Press C to toggle AI control.", True, (200, 200, 255))
            screen.blit(title, ((WINDOW_SIZE - title.get_width()) // 2, (WINDOW_SIZE - title.get_height()) // 2 - 40))
            screen.blit(subtitle, ((WINDOW_SIZE - subtitle.get_width()) // 2, (WINDOW_SIZE - subtitle.get_height()) // 2))
            screen.blit(info1, ((WINDOW_SIZE - info1.get_width()) // 2, (WINDOW_SIZE - info1.get_height()) // 2 + 30))
            screen.blit(info2, ((WINDOW_SIZE - info2.get_width()) // 2, (WINDOW_SIZE - info2.get_height()) // 2 + 55))
        elif game_state == "running":
            global_map = grid.get_global_map_matrix()
            
            # Read player input and map to action codes
            player_action = None
            if control_enabled and player_soldier and player_soldier.is_alive:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    player_action = 0
                elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    player_action = 1
                elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    player_action = 2
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    player_action = 3
                else:
                    player_action = 4  # wait/no move
            
            update_game_logic(grid, global_map, player_soldier=player_soldier, player_action=player_action)
            
            # Draw grid and characters
            grid.draw(screen, offset_y=40)
            
            # After drawing and stats, check end conditions
            zombie_count, human_count, infected_count, medic_count, soldier_count = grid.get_stats()
            # Player died
            if player_soldier and not player_soldier.is_alive:
                final_kills = getattr(player_soldier, "kills_count", 0)
                final_humans = human_count
                game_state = "gameover_dead"
            # All zombies eliminated
            elif zombie_count == 0:
                final_kills = getattr(player_soldier, "kills_count", 0)
                final_humans = human_count
                game_state = "gameover_win"
        else:
            # Game over screens
            grid.draw(screen, offset_y=40)
            panel_w, panel_h = 420, 140
            panel_x = (WINDOW_SIZE - panel_w) // 2
            panel_y = (WINDOW_SIZE - panel_h) // 2
            pygame.draw.rect(screen, (30, 30, 30), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(screen, (180, 180, 180), (panel_x, panel_y, panel_w, panel_h), width=2)
            
            if game_state == "gameover_dead":
                title = pygame.font.Font(None, 36).render("You died", True, (255, 80, 80))
                msg1 = font.render(f"Zombies killed: {final_kills}", True, (230, 230, 230))
                msg2 = font.render(f"Humans alive: {final_humans}", True, (230, 230, 230))
            else:
                title = pygame.font.Font(None, 36).render("All zombies eliminated!", True, (80, 255, 120))
                msg1 = font.render(f"Your kills: {final_kills}", True, (230, 230, 230))
                msg2 = font.render(f"Humans alive: {final_humans}", True, (230, 230, 230))
            hint = font.render("Press R to restart, Q/Esc to quit", True, (200, 200, 200))
            screen.blit(title, (panel_x + (panel_w - title.get_width()) // 2, panel_y + 12))
            screen.blit(msg1, (panel_x + 20, panel_y + 56))
            screen.blit(msg2, (panel_x + 20, panel_y + 82))
            screen.blit(hint, (panel_x + (panel_w - hint.get_width()) // 2, panel_y + 110))
        
        # Draw stats (top bar) when running; show counts even on menu/over for context
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
        
        # Player control hint
        if player_soldier and game_state == "running":
            hint = "Control: WASD/Arrows move, C toggles AI" if control_enabled else "AI active: press C to take control"
            hint_surface = font.render(hint, True, (200, 200, 255))
            screen.blit(hint_surface, (10, 25))

        # Bottom-right cooldown HUD for player soldier (during gameplay)
        if game_state == "running" and player_soldier and player_soldier.is_alive:
            current_time = pygame.time.get_ticks()
            time_since_shot = current_time - player_soldier.last_kill_time
            fill_ratio = max(0.0, min(1.0, time_since_shot / player_soldier.KILL_COOLDOWN))
            remaining_ms = max(0, player_soldier.KILL_COOLDOWN - time_since_shot)

            panel_w, panel_h = 160, 20
            margin = 8
            panel_x = WINDOW_SIZE - panel_w - margin
            panel_y = WINDOW_SIZE + 40 - panel_h - margin

            # Panel background and border
            pygame.draw.rect(screen, (40, 40, 40), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(screen, (120, 120, 120), (panel_x, panel_y, panel_w, panel_h), width=1)

            # Fill bar
            fill_w = int(panel_w * fill_ratio)
            bar_color = (0, 200, 200) if fill_ratio < 1.0 else (0, 220, 0)
            if fill_w > 0:
                pygame.draw.rect(screen, bar_color, (panel_x + 1, panel_y + 1, fill_w - 2 if fill_w >= 2 else fill_w, panel_h - 2))

            # Label text
            if fill_ratio >= 1.0:
                label = "Weapon: Ready"
            else:
                label = f"Cooldown: {remaining_ms/1000:.1f}s"
            label_surface = font.render(label, True, (230, 230, 230))
            # Center text in panel
            text_x = panel_x + (panel_w - label_surface.get_width()) // 2
            text_y = panel_y + (panel_h - label_surface.get_height()) // 2
            screen.blit(label_surface, (text_x, text_y))
            
        pygame.display.flip()
        clock.tick()
    
    pygame.quit()

def update_game_logic(grid, global_map, player_soldier=None, player_action=None):
    """
    To zastępuje twoje proste `grid.update()`.
    Tutaj łączymy stan gry z sieciami neuronowymi.
    """
    
    # Przechodzimy przez każdą postać
    for char in grid.characters:
        
        if isinstance(char, Infected):
            char.act()
            continue # Infected nie używają sieci neuronowej

        char.process_signals()  # Przetwarzamy sygnały (usuwamy stare)
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
        elif isinstance(char, Soldier):
            # Override with player input if controlled soldier
            if getattr(char, "is_player_controlled", False) and player_soldier is char and player_action is not None:
                action = player_action
            else:
                action = soldier_agent.get_action(current_state)
        elif isinstance(char, Medic):
            # Medyk nie używa sieci neuronowej, tylko swojego algorytmu
            action = char.get_autonomous_action()
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
            elif isinstance(char, Soldier):
                reward -= 0.1
        done = False # Czy postać "skończyła grę" (zginęła)
        
        if isinstance(char, Medic):
             char.act()
        if isinstance(char, Zombie):
            if action == 4:
                # Sprawdzamy czy ma kogoś blisko
                if hasattr(char, 'prev_dist') and char.prev_dist < char.SIEGE_RANGE:
                    pass # Nie karzemy za stanie, jeśli stoi przy ofierze (atakuje/czeka w kolejce)
                else:
                    reward -= 0.5 # Kara za stanie bezczynnie daleko od ofiar
            reward += char.act() # Tu wróci +10 jeśli zaraził
            reward -= 0.05 # Kara za czas (pogania zombie)
        elif isinstance(char, Soldier):
            reward += char.act() # Tu wróci +0.5 za przeżycie i +10 za zabicie
            if not char.is_alive:
                reward = -10
                done = True
        elif isinstance(char, Human):
            reward += char.act() # Tu wróci +0.1 za przeżycie
            if not char.is_alive: # Ustalone w get_infected()
                reward = -10
                done = True
        
        # 4. NOWY STAN (Next State)
        new_visual = char.get_observation(global_map)
        new_vector = char.get_target_vector()
        next_state = (new_visual, new_vector)
        
        # 5. NAUKA (Store & Learn)
        if isinstance(char, Soldier):
            soldier_agent.memory.push(current_state, action, reward, next_state, done)
            soldier_agent.learn()
            
        elif isinstance(char, Zombie):
            zombie_agent.memory.push(current_state, action, reward, next_state, done)
            zombie_agent.learn()
            
        elif isinstance(char, Human):
            # Ważne: Ten warunek musi być PO Soldierze, jeśli Soldier dziedziczy po Human!
            human_agent.memory.push(current_state, action, reward, next_state, done)
            human_agent.learn()

if __name__ == "__main__":
    main()
