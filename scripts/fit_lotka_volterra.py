#!/usr/bin/env python3
"""
Fit Lotka–Volterra parameters (predator–prey) to simulation data.
- Predator: zombies
- Prey: humans

Usage examples:
  python scripts/fit_lotka_volterra.py --steps 600 --no-plot
  python scripts/fit_lotka_volterra.py --csv notebooks/populations.csv --plot

Outputs:
- Prints fitted parameters: a, b, c, d
- Optionally writes plot to notebooks/lv_fit.png
- Optionally saves generated time series to notebooks/populations.csv
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np

# Lazy import SciPy/Matplotlib so basic help works without them
try:
    from scipy.integrate import solve_ivp
    from scipy.optimize import least_squares
except Exception as e:
    solve_ivp = None  # type: ignore
    least_squares = None  # type: ignore

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None  # type: ignore

# Import game modules for headless simulation
# We import `main` to reuse its update loop/agents without rendering.
import importlib
import sys


@dataclass
class LVParams:
    a: float  # prey growth rate (humans)
    b: float  # predation rate
    c: float  # predator death rate (zombies)
    d: float  # predator reproduction per prey eaten

    def to_dict(self):
        return {"a": self.a, "b": self.b, "c": self.c, "d": self.d}


def lotka_volterra_rhs(t: float, y: np.ndarray, a: float, b: float, c: float, d: float) -> Tuple[float, float]:
    H, Z = y
    dHdt = a * H - b * H * Z
    dZdt = -c * Z + d * H * Z
    return np.array([dHdt, dZdt])


def simulate_lv(t: np.ndarray, y0: Tuple[float, float], p: LVParams) -> np.ndarray:
    """Integrate LV ODE at sample times t, return array shape (len(t), 2)."""
    if solve_ivp is None:
        raise RuntimeError("scipy is required: pip install scipy")
    sol = solve_ivp(
        fun=lambda tt, yy: lotka_volterra_rhs(tt, yy, p.a, p.b, p.c, p.d),
        t_span=(t[0], t[-1]),
        y0=np.asarray(y0, dtype=float),
        t_eval=t,
        method="RK45",
        rtol=1e-6,
        atol=1e-8,
        vectorized=False,
    )
    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")
    return sol.y.T  # shape (T, 2)


def fit_lv(t: np.ndarray, H: np.ndarray, Z: np.ndarray, p0: LVParams) -> Tuple[LVParams, np.ndarray]:
    """Fit LV parameters by least squares on [H(t), Z(t)]. Returns (params, Yhat)."""
    if least_squares is None:
        raise RuntimeError("scipy is required: pip install scipy")

    y0 = (float(H[0]), float(Z[0]))

    def resid(theta: np.ndarray) -> np.ndarray:
        a, b, c, d = theta
        # Enforce non-negativity by parameterization inside least_squares bounds
        p = LVParams(a, b, c, d)
        try:
            Yhat = simulate_lv(t, y0, p)
        except RuntimeError:
            return np.full(2 * len(t), 1e6)
        # residuals stacked: [H_err, Z_err]
        rH = Yhat[:, 0] - H
        rZ = Yhat[:, 1] - Z
        return np.hstack([rH, rZ])

    theta0 = np.array([p0.a, p0.b, p0.c, p0.d], dtype=float)
    bounds = (0.0, np.inf)  # LV parameters should be non-negative
    res = least_squares(resid, theta0, bounds=bounds, xtol=1e-8, ftol=1e-8, gtol=1e-8, max_nfev=200)

    a, b, c, d = res.x
    p_hat = LVParams(float(a), float(b), float(c), float(d))
    Yhat = simulate_lv(t, y0, p_hat)
    return p_hat, Yhat


def run_headless_sim(steps: int, num_humans: int, num_zombies: int, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run a headless simulation (no rendering) and collect H,Z over time.
    Returns (t, H, Z).
    """
    if seed is not None:
        np.random.seed(seed)
    # Ensure project root is on sys.path for module imports
    try:
        from pathlib import Path
        proj_root = str(Path(__file__).resolve().parent.parent)
        if proj_root not in sys.path:
            sys.path.insert(0, proj_root)
    except Exception:
        pass
    # Import main lazily so CLI help doesn't require heavy deps
    # Import main with a clean argv so its argparse doesn't conflict
    _argv = list(sys.argv)
    try:
        sys.argv = [sys.argv[0]]
        main = importlib.import_module("main")
    finally:
        sys.argv = _argv
    grid_mod = importlib.import_module("grid")

    # Create a grid with only humans and zombies for LV simplicity
    grid = grid_mod.Grid(num_zombies=num_zombies, num_humans=num_humans, num_infected=0, num_medics=0, num_soldiers=0)

    t = []
    H = []
    Z = []
    for k in range(steps):
        global_map = grid.get_global_map_matrix()
        main.update_game_logic(grid, global_map)
        zc, hc, _, _, _ = grid.get_stats()
        # order H (prey), Z (predator)
        t.append(k)
        H.append(hc)
        Z.append(zc)
        # stop early if one species extinct
        if hc == 0 or zc == 0:
            break
    return np.asarray(t, dtype=float), np.asarray(H, dtype=float), np.asarray(Z, dtype=float)


def maybe_save_csv(path: str, t: np.ndarray, H: np.ndarray, Z: np.ndarray) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = np.column_stack([t, H, Z])
    header = "t,H,Z"
    np.savetxt(path, data, delimiter=",", header=header, comments="")


def maybe_plot(path: str, t: np.ndarray, H: np.ndarray, Z: np.ndarray, Yhat: np.ndarray, p: LVParams) -> None:
    if plt is None:
        print("matplotlib not available; skipping plot")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    ax.plot(t, H, "o", ms=3, label="Human (data)")
    ax.plot(t, Z, "o", ms=3, label="Zombie (data)")
    ax.plot(t, Yhat[:, 0], "-", lw=2, label="Human (LV fit)")
    ax.plot(t, Yhat[:, 1], "-", lw=2, label="Zombie (LV fit)")
    ax.set_xlabel("time (steps)")
    ax.set_ylabel("population")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title(f"LV fit: a={p.a:.4g}, b={p.b:.4g}, c={p.c:.4g}, d={p.d:.4g}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main_cli():
    ap = argparse.ArgumentParser(description="Fit Lotka–Volterra to human/zombie populations")
    ap.add_argument("--csv", type=str, default=None, help="Path to CSV with columns t,H,Z (if provided, skip sim)")
    ap.add_argument("--steps", type=int, default=600, help="Max steps for headless sim when CSV not provided")
    ap.add_argument("--humans", type=int, default=45, help="Initial humans for sim (CSV ignored)")
    ap.add_argument("--zombies", type=int, default=38, help="Initial zombies for sim (CSV ignored)")
    ap.add_argument("--seed", type=int, default=None, help="Random seed for sim (optional)")
    ap.add_argument("--save-csv", type=str, default="notebooks/populations.csv", help="Where to save generated series")
    ap.add_argument("--out-json", type=str, default="notebooks/lv_params.json", help="Where to save fitted params JSON")
    ap.add_argument("--plot", dest="plot", action="store_true", help="Save comparison plot")
    ap.add_argument("--no-plot", dest="plot", action="store_false", help="Do not save plot")
    ap.set_defaults(plot=True)

    args = ap.parse_args()

    # Load or generate data
    if args.csv:
        arr = np.loadtxt(args.csv, delimiter=",", skiprows=1)
        t, H, Z = arr[:, 0], arr[:, 1], arr[:, 2]
    else:
        t, H, Z = run_headless_sim(args.steps, num_humans=args.humans, num_zombies=args.zombies, seed=args.seed)
        maybe_save_csv(args.save_csv, t, H, Z)
        print(f"Saved series to {args.save_csv} ({len(t)} points)")

    # Initial guess from simple heuristics
    # Use scaled guesses to encourage convergence
    H0, Z0 = max(H[0], 1.0), max(Z[0], 1.0)
    p0 = LVParams(a=0.05, b=0.002 / max(H0, 1.0), c=0.05, d=0.002 / max(Z0, 1.0))

    p_hat, Yhat = fit_lv(t, H, Z, p0)

    print("Fitted Lotka–Volterra parameters:")
    print(json.dumps(p_hat.to_dict(), indent=2))

    # Save params JSON
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(p_hat.to_dict(), f, indent=2)
    print(f"Saved params to {args.out_json}")

    if args.plot:
        out_png = os.path.splitext(args.out_json)[0] + ".png"
        maybe_plot(out_png, t, H, Z, Yhat, p_hat)
        print(f"Saved plot to {out_png}")


if __name__ == "__main__":
    main_cli()
