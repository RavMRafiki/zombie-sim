"""Game constants and configuration"""

GRID_SIZE = 128
CELL_SIZE = 6
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
MOVE_INTERVAL = 100  # milliseconds
FPS = 60

# Colors
COLOR_BACKGROUND = (50, 50, 50)
COLOR_GRID = (100, 100, 100)
COLOR_ZOMBIE = (0, 255, 0)
COLOR_HUMAN = (0, 0, 255)
COLOR_INFECTED = (255, 123, 0)
COLOR_MEDIC = (255, 0, 0)
COLOR_SOLIDIER = (255, 255, 0)

# Cooldowns / Timers (milliseconds)
ZOMBIE_INFECTION_COOLDOWN_MS = 5000
ZOMBIE_STARVATION_TIME_MS = 6000000
SOLDIER_KILL_COOLDOWN_MS = 5000
MEDIC_HEAL_COOLDOWN_MS = 5000

# Probabilities
# Chance that a Human reproduces when cooldown allows
HUMAN_REPRO_CHANCE = 0.01
# Chance that a newborn Human is assigned a role (Medic/Soldier)
HUMAN_ROLE_CHANCE = 0.2

# Ranges (in grid cells)
# How far around the parent can a newborn spawn
HUMAN_REPRO_RANGE = 2
