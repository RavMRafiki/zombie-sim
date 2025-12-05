# Zombie Simulator

A Pygame-based simulation with three types of characters moving randomly on a 256x256 grid.

## Features

- **3 Character Types:**

  - **Zombies** (Green) - Moving randomly
  - **Humans** (Blue) - Moving randomly
  - **Infected** (Orange) - Moving randomly

- **Game Mechanics:**
  - 256x256 grid with 20x20 pixel cells
  - Characters move every 0.5 seconds in random directions (up, down, left, right)
  - Characters bounce at grid boundaries
  - Real-time character count display

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

- `MOVE_INTERVAL` - Time between moves (in milliseconds)
- Grid dimensions and number of each character type in the `Grid` initialization

## Architecture

- `Character` class: Represents individual characters with movement logic
- `Grid` class: Manages all characters and grid rendering
- Move events are tracked per-character to ensure smooth timing
