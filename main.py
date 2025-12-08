"""Zombie Simulator - Main entry point"""

import pygame
from grid import Grid
from constants import WINDOW_SIZE, COLOR_BACKGROUND, FPS

pygame.init()


def main():
    """Main game loop"""
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Zombie Outbreak Simulation")
    clock = pygame.time.Clock()
    
    grid = Grid(num_zombies=40, num_humans=60, num_infected=0, num_medics=16, num_soldiers=8)
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
