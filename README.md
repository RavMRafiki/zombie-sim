# Zombie Outbreak Simulation

A Pygame-based simulation with five types of characters interacting on a 256x256 grid with dynamic gameplay mechanics.

## Features

- **5 Character Types:**
  - **Zombies** (Green) - Aggressive hunters that infect humans and infected characters
  - **Humans** (Blue) - Defensive survivors that detect and broadcast threat information
  - **Infected** (Orange) - Transitional state that eventually transforms into zombies
  - **Medics** (Red) - Support units that heal infected characters back to their previous type
  - **Soldiers** (Yellow) - Combat specialists that eliminate nearby zombies

- **Game Mechanics:**
  - 256x256 grid with variable cell size (4px default)
  - Character-specific movement speeds and behaviors
  - Dynamic infection system: Zombies infect nearby humans/infected
  - Healing system: Medics can cure infected characters
  - Combat system: Soldiers eliminate threats with cooldown mechanics
  - Signal/communication system between characters for threat awareness
  - Characters bounce at grid boundaries
  - Real-time character count display for all types

## Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

```bash
python main.py
```

## Controls

- Close the window to exit the simulation

## Configuration

Edit the constants in `main.py` to customize:

- `MOVE_INTERVAL` - Time between moves (default: 500ms)
- `CELL_SIZE` - Pixel size of each grid cell (default: 4px)
- `FPS` - Frame rate (default: 60)
- `GRID_SIZE` - Grid dimensions (default: 256x256)

In the `Grid` initialization in `main()`, adjust character counts:

```python
grid = Grid(num_zombies=40, num_humans=60, num_infected=0, num_medics=16, num_soldiers=8)
```

### Character-Specific Configuration

Each character type has customizable parameters:

- **Zombie:**
  - `INFECTION_RANGE` - Distance to infect characters (default: 1.99 cells)
  - `INFECTION_COOLDOWN` - Time between infections (default: 5000ms)

- **Human:**
  - `THREAT_DETECTION_RANGE` - Radius to detect zombies/infected (default: 3.0 cells)
  - `THREAT_BROADCAST_RANGE` - Radius to broadcast threat info (default: 7.0 cells)

- **Infected:**
  - `TRANSFORMATION_TIME` - Time to transform into zombie (default: 10000ms)
  - `BROADCAST_RANGE` - Radius to broadcast infected status (default: 5.0 cells)

- **Medic:**
  - `HEAL_RANGE` - Distance to heal infected (default: 2.0 cells)
  - `HEAL_TIME` - Cooldown between heals (default: 20000ms)

- **Soldier:**
  - `KILL_RANGE` - Distance to eliminate zombies (default: 3.0 cells)
  - `KILL_COOLDOWN` - Cooldown between kills (default: 5000ms)

## Architecture

- `Zombie` - Hunts and infects other characters
- `Human` - Detects threats and broadcasts warnings
- `Infected` - Transitional state between Human and Zombie
- `Medic(Human)` - Heals infected characters
- `Soldier(Human)` - Eliminates zombie threats

### Key Systems

## SZR Model Fitting

Fit parameters (alpha, beta, gamma, delta) of the SZR ODE system to observed time-series data with columns `time,S,Z,R`:

```bash
python scripts/fit_szr.py --csv path/to/populations.csv --plot --out-json notebooks/szr_params.json
```

Options:

- `--guess a,b,g,d` initial parameter guess (default 0.05,0.2,0.05,0.05)
- `--bounds aL:aH,bL:bH,gL:gH,dL:dH` parameter bounds (default non-negative)
