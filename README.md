# Zombie Outbreak Simulation

Simulation of a multi-agent zombie outbreak written with Pygame and a small
DQN experiment. The system models agents moving on a discrete grid where each
agent type (`Zombie`, `Human`, `Infected`, `Medic`, `Soldier`) has its own
behavior, observation space and reward shaping.

## Highlights

- Real-time visualization with population counters.
- Multi-agent interactions: infection, healing, transformation and local
  signaling.
- DQN experiments for learned control (see `DQN/`). Agents are initialized
  with random weights and learn online unless you provide saved checkpoints.

## Screenshots

Full-size simulator screenshots (rendered at runtime):

![Early Stage Screenshot](docs/screenshots/Screenshot%20from%202026-03-13%2014-14-36.png)
![Late Stage Screenshot](docs/screenshots/Screenshot%20from%202026-03-13%2014-16-45.png)

## Quick Start

1. Clone the repository.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the simulation:

```bash
python main.py
```

Notes:

- Each run initializes DQN agent weights randomly — training starts from
  scratch unless you modify the code to load checkpoints.
- Close the Pygame window to stop the simulation.

## User-facing Description

The simulator runs on a 128×128 grid. Each agent maintains an internal state
buffer (4 frames of an 11×11 local view) used by the DQN input. Typical
default initialization used in the documentation was: 40 zombies, 60 humans,
0 infected, 20 medics and 20 soldiers.

### Legend (colors)

- Green — `Zombie`
- Blue — `Human`
- Orange — `Infected`
- White — `Medic`
- Yellow — `Soldier`

## Architecture & Agent Inputs

- Observation: stack of 4 local frames (4×11×11) plus a small vector
  (agent-specific):
  - Zombie vector size: 2
  - Soldier vector size: 3
  - Human vector size: 4 (threat and rescue vectors)
- Action space (discrete, 5 actions): Up, Down, Left, Right, Wait.

## DQN (high-level)

- Dual-stream network: CNN for visual input (two conv layers) and MLP for the
  vector input. Features are concatenated and fed to dense layers producing
  Q-values for 5 actions.

### Typical hyperparameters (from documentation)

|           Parameter |         Value          |
| ------------------: | :--------------------: |
|         Input shape |      (4, 11, 11)       |
|          Batch size |           64           |
|       Learning rate |         0.001          |
|    Gamma (discount) |          0.99          |
|       Replay buffer |         10,000         |
|       Target update |       1000 steps       |
| Epsilon start/decay | 1.0 / 0.995 (min 0.05) |

## Configuration

Most tunables live in `constants.py` and the `Grid(...)` constructor in
`main.py` (initial population counts). Typical values referenced in the
documentation:

- Grid size: `128`
- Cell display size: `6` px per cell
- Agent move interval: 100 ms (tick rate shown in docs)

## Hardware Notes

- The DQN experiments can benefit from CUDA-enabled GPUs. PyTorch device
  selection is automatic (CUDA if available, otherwise CPU). Running many
  learning agents on CPU can reduce frame rates.

## Project layout

- `main.py` — entry point and loop
- `grid.py` — world state and rendering
- `character.py` — base class for agents
- role files — `human.py`, `zombie.py`, `infected.py`, `medic.py`, `soldier.py`
- `DQN/` — `learn.py`, `q_network.py` (experiments)
- `tests/` — unit tests

## Testing

Run the test-suite with:

```bash
pytest
```

## References

See `dokumentacja.tex` for the full project documentation (mathematical
formulation, reward shaping, and algorithm pseudocode).
