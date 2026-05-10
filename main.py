"""Zombie Simulator - Main entry point"""

from numpy import dtype, float64, ndarray
from typing import Any

from typing import Any

from typing import Any

import pygame
import logging

from pygame.event import Event
from DQN.learn import DQNAgent
from grid import Grid
from infected import Infected
from soldier import Soldier
from zombie import Zombie
from human import Human
from medic import Medic
from constants import (
    WINDOW_SIZE,
    COLOR_BACKGROUND,
    COLOR_ZOMBIE,
    COLOR_HUMAN,
    COLOR_INFECTED,
    COLOR_MEDIC,
    COLOR_SOLIDIER,
)

pygame.init()
logging.basicConfig(level=logging.INFO)

zombie_agent = DQNAgent(input_shape=(4, 11, 11))
human_agent = DQNAgent(input_shape=(4, 11, 11), vector_size=4)
soldier_agent = DQNAgent(input_shape=(4, 11, 11), vector_size=3)


def main() -> None:
    """Main game loop"""
    logging.info("Initializing simulation...")
    screen: pygame.Surface = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 40))
    pygame.display.set_caption("Zombie Outbreak Simulation")
    clock = pygame.time.Clock()

    grid = Grid(
        num_zombies=30, num_humans=40, num_infected=0, num_medics=10, num_soldiers=20
    )
    font = pygame.font.Font(None, 24)

    running = True
    i = 0
    logging.info("Starting simulation...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if i % 10 == 0:
            logging.info(f"Frame {i}")
        i += 1
        global_map: ndarray[tuple[int, int], dtype[float64]] = grid.get_global_map_matrix()

        update_game_logic(grid, global_map)

        # Draw
        screen.fill(COLOR_BACKGROUND)
        grid.draw(screen, offset_y=40)

        # Draw stats
        zombie_count, human_count, infected_count, medic_count, soldier_count = (
            grid.get_stats()
        )
        stats_data = [
            ("Zombie", zombie_count, COLOR_ZOMBIE),
            ("Human", human_count, COLOR_HUMAN),
            ("Infected", infected_count, COLOR_INFECTED),
            ("Medic", medic_count, COLOR_MEDIC),
            ("Soldier", soldier_count, COLOR_SOLIDIER),
        ]

        current_x = 10
        y_pos = 10
        icon_size = 15
        spacing = 5
        group_spacing = 15

        for label, count, color in stats_data:
            pygame.draw.rect(screen, color, (current_x, y_pos, icon_size, icon_size))

            text_str: str = f"{label}: {count}"
            text_surface: pygame.Surface = font.render(text_str, True, (255, 255, 255))

            screen.blit(text_surface, (current_x + icon_size + spacing, y_pos + 2))
            current_x += icon_size + spacing + text_surface.get_width() + group_spacing

        pygame.display.flip()
        clock.tick()

    pygame.quit()


def update_game_logic(grid, global_map) -> None:
    """
    To zastępuje twoje proste `grid.update()`.
    Tutaj łączymy stan gry z sieciami neuronowymi.
    """

    # Przechodzimy przez każdą postać
    for char in grid.characters:
        if isinstance(char, Infected):
            char.act()
            continue  # Infected nie używają sieci neuronowej

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
            action: int | Any = zombie_agent.get_action(current_state)
        elif isinstance(char, Human):
            action: int | Any = human_agent.get_action(current_state)
        elif isinstance(char, Soldier):
            action: int | Any = soldier_agent.get_action(current_state)
        elif isinstance(char, Medic):
            # Medyk nie używa sieci neuronowej, tylko swojego algorytmu
            action: int = char.get_autonomous_action()
        else:
            action = 4  # Czekaj (dla innych klas)

        # 3. RUCH I INTERAKCJA (Step)
        # Zmieniamy metodę move, żeby przyjmowała akcję (0=Góra, 1=Dół, itd.)
        move_success = char.move(action)

        # Pobieramy nagrodę z interakcji (infekcja, przeżycie)
        reward = 0
        if not move_success:
            if isinstance(char, Zombie):
                reward -= 0.1  # Kara za uderzenie w krawędź
            elif isinstance(char, Human):
                reward -= 0.5
            elif isinstance(char, Soldier):
                reward -= 0.1
        done = False  # Czy postać "skończyła grę" (zginęła)

        if isinstance(char, Medic):
            char.act()
        if isinstance(char, Zombie):
            if action == 4:
                # Sprawdzamy czy ma kogoś blisko
                if hasattr(char, "prev_dist") and char.prev_dist < char.SIEGE_RANGE:
                    pass  # Nie karzemy za stanie, jeśli stoi przy ofierze (atakuje/czeka w kolejce)
                else:
                    reward -= 0.5  # Kara za stanie bezczynnie daleko od ofiar
            reward += char.act()  # Tu wróci +10 jeśli zaraził
            reward -= 0.05  # Kara za czas (pogania zombie)
        elif isinstance(char, Soldier):
            reward += char.act()  # Tu wróci +0.5 za przeżycie i +10 za zabicie
            if not char.is_alive:
                reward = -10
                done = True
        elif isinstance(char, Human):
            reward += char.act()  # Tu wróci +0.1 za przeżycie
            if not char.is_alive:  # Ustalone w get_infected()
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
