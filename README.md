# Zombie Outbreak Simulation

An agent-based outbreak simulator built with Pygame. The project models a population moving on a grid where each class has distinct behavior, ranges, and cooldowns. Over time, local interactions between units create larger emergent outcomes: collapse, containment, or unstable equilibrium.

## What This Project Is

- A real-time simulation of infection spread and response dynamics.
- A sandbox for tuning behavior constants and observing system-level effects.
- A lightweight codebase for experimenting with pathing and reinforcement learning ideas (`DQN/`).

## Simulation Roles

- `Zombie` (green): aggressively infects nearby targets.
- `Human` (blue): detects threats and broadcasts danger signals.
- `Infected` (orange): temporary state that eventually turns into a zombie.
- `Medic` (red): cures infected entities and restores their previous role.
- `Soldier` (yellow): removes nearby zombies with an attack cooldown.

## Core Mechanics

- Grid world (`256x256` by default) rendered in real time.
- Individual movement profiles per role.
- Infection, transformation, healing, and elimination loops.
- Signal system for local communication and coordination.
- Boundary handling and continuous population counters.

## Screenshots

Latest screenshots from the simulator:

![Early Stage Screeshot](docs/screenshots/Screenshot%20from%202026-03-13%2014-14-36.png)
![Late Stage Screenshot](docs/screenshots/Screenshot%20from%202026-03-13%2014-16-45.png)

## Quick Start

1. Clone the repository.
2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Run the simulation.

```bash
python main.py
```

## Configuration

You can tune simulation behavior directly in source constants.

### Global Runtime Settings

In `main.py`:

- `MOVE_INTERVAL`: milliseconds between move ticks (default: `500`).
- `CELL_SIZE`: pixel size of a grid cell (default: `4`).
- `FPS`: render frame rate (default: `60`).
- `GRID_SIZE`: world dimensions (default: `256x256`).

Initial population is set in `Grid(...)` construction, for example:

```python
grid = Grid(num_zombies=40, num_humans=60, num_infected=0, num_medics=16, num_soldiers=8)
```

### Role Parameters

| Role       | Main Tunables                                      |
| ---------- | -------------------------------------------------- |
| `Zombie`   | `INFECTION_RANGE`, `INFECTION_COOLDOWN`            |
| `Human`    | `THREAT_DETECTION_RANGE`, `THREAT_BROADCAST_RANGE` |
| `Infected` | `TRANSFORMATION_TIME`, `BROADCAST_RANGE`           |
| `Medic`    | `HEAL_RANGE`, `HEAL_TIME`                          |
| `Soldier`  | `KILL_RANGE`, `KILL_COOLDOWN`                      |

## Project Structure

- `main.py`: simulation entry point and loop.
- `grid.py`: world state and update/render orchestration.
- `character.py`: shared movement and signaling base class.
- `human.py`, `zombie.py`, `infected.py`, `medic.py`, `soldier.py`: role behavior implementations.
- `pathfinding.py`: pathing logic used by agents.
- `DQN/`: reinforcement-learning experiments.
- `tests/`: unit tests.

## Testing

Run tests with:

```bash
pytest
```
