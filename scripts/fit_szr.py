#!/usr/bin/env python3
"""
Fit parameters for the SZR (Susceptible–Zombie–Removed) ODE system to time-series data.

Equations (S(t), Z(t), R(t)) with N = S + Z + R:
    dS/dt = -beta * S * Z / N + alpha * S + delta * Z
    dZ/dt =  beta * S * Z / N - gamma * Z - delta * Z
    dR/dt =  gamma * Z

Parameters to fit: alpha, beta, gamma, delta (all >= 0).

CSV input expected with header containing at least: time,S,Z,R
- time units arbitrary but consistent with dynamics
- values should be non-negative

Example:
    python scripts/fit_szr.py --csv notebooks/populations.csv --plot --out-json notebooks/szr_params.json
"""
from __future__ import annotations
import argparse
import json
from dataclasses import dataclass
from typing import Tuple, Sequence

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - soft dependency in case pandas missing
    pd = None

try:
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover
    plt = None


@dataclass
class FitResult:
    alpha: float
    beta: float
    gamma: float
    delta: float
    sse: float
    success: bool
    message: str


def szr_rhs(_t: float, y: Sequence[float], alpha: float, beta: float, gamma: float, delta: float):
    S, Z, R = y
    N = S + Z + R
    # prevent division by zero; when N is ~0, interaction term vanishes
    if N <= 1e-12:
        N = 1.0
    dS = -beta * S * Z / N + alpha * S + delta * Z
    dZ = beta * S * Z / N - gamma * Z - delta * Z
    dR = gamma * Z
    return (dS, dZ, dR)


def simulate(params: Sequence[float], t: np.ndarray, y0: Sequence[float]) -> np.ndarray:
    alpha, beta, gamma, delta = params
    sol = solve_ivp(
        fun=lambda tt, yy: szr_rhs(tt, yy, alpha, beta, gamma, delta),
        t_span=(float(t[0]), float(t[-1])),
        y0=np.asarray(y0, dtype=float),
        t_eval=t,
        method="RK45",
        rtol=1e-7,
        atol=1e-9,
        vectorized=False,
    )
    if not sol.success:
        # return NaNs to penalize this parameter set
        return np.full((3, t.size), np.nan)
    return sol.y  # shape (3, T)


def residuals(params: Sequence[float], t: np.ndarray, data: np.ndarray, y0: Sequence[float], weights: Sequence[float] | None = None) -> np.ndarray:
    # Enforce non-negativity softly by squashing negatives
    params = np.maximum(params, 0.0)
    sim = simulate(params, t, y0)  # (3, T)
    if np.any(~np.isfinite(sim)):
        return np.full(3 * t.size, 1e6)
    res = sim - data.T  # (3, T)
    if weights is not None:
        w = np.asarray(weights).reshape(-1, 1)
        res = w * res
    return res.ravel(order="F")


def load_csv(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Return (t, data) where data has columns [S, Z, R]."""
    if pd is not None:
        df = pd.read_csv(path)
        # flexible column naming
        cols = {c.lower(): c for c in df.columns}
        tcol = cols.get("time") or list(df.columns)[0]
        scol = cols.get("s") or "S"
        zcol = cols.get("z") or "Z"
        rcol = cols.get("r") or "R"
        t = df[tcol].to_numpy(dtype=float)
        S = df[scol].to_numpy(dtype=float)
        Z = df[zcol].to_numpy(dtype=float)
        R = df[rcol].to_numpy(dtype=float)
        data = np.vstack([S, Z, R]).T
        return t, data
    # Fallback without pandas (expects header)
    raw = np.genfromtxt(path, delimiter=",", names=True, dtype=float)
    # Attempt common field names (case-insensitive)
    lower_map = {name.lower(): name for name in raw.dtype.names or []}
    tname = lower_map.get("time") or (raw.dtype.names or [])[0]
    sname = lower_map.get("s") or "S"
    zname = lower_map.get("z") or "Z"
    rname = lower_map.get("r") or "R"
    t = np.asarray(raw[tname], dtype=float)
    S = np.asarray(raw[sname], dtype=float)
    Z = np.asarray(raw[zname], dtype=float)
    R = np.asarray(raw[rname], dtype=float)
    data = np.vstack([S, Z, R]).T
    return t, data


def fit_szr(t: np.ndarray, data: np.ndarray, guess=(0.05, 0.2, 0.05, 0.05), bounds=((0, 0, 0, 0), (np.inf, np.inf, np.inf, np.inf)), weights: Sequence[float] | None = None) -> FitResult:
    y0 = data[0]
    # Scale weights to balance magnitudes; default uses 1/N0 for S,Z,R to be scale-invariant
    if weights is None:
        N0 = max(np.sum(y0), 1.0)
        weights = (1.0 / N0, 1.0 / N0, 1.0 / N0)

    def fun(p):
        return residuals(p, t, data, y0, weights)

    res = least_squares(fun, x0=np.asarray(guess, dtype=float), bounds=bounds, method="trf", xtol=1e-10, ftol=1e-10, gtol=1e-10, max_nfev=2000)

    sim = simulate(np.maximum(res.x, 0.0), t, y0)
    sse = float(np.nansum((sim.T - data) ** 2))
    fr = FitResult(alpha=float(res.x[0]), beta=float(res.x[1]), gamma=float(res.x[2]), delta=float(res.x[3]), sse=sse, success=bool(res.success), message=str(res.message))
    return fr


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fit SZR model parameters to time-series data.")
    p.add_argument("--csv", required=True, help="Path to CSV with columns time,S,Z,R")
    p.add_argument("--plot", action="store_true", help="Plot data vs fitted trajectory")
    p.add_argument("--out-json", help="Where to write fitted params as JSON")
    p.add_argument("--guess", type=str, default=None, help="Initial guess alpha,beta,gamma,delta (comma-separated)")
    p.add_argument("--bounds", type=str, default=None, help="Bounds as a_low:a_high,b_low:b_high,g_low:g_high,d_low:d_high")
    return p


def parse_guess(s: str | None) -> Tuple[float, float, float, float] | None:
    if not s:
        return None
    vals = [float(x) for x in s.split(",")]
    if len(vals) != 4:
        raise ValueError("--guess requires 4 comma-separated values")
    return tuple(vals)  # type: ignore


def parse_bounds(s: str | None):
    if not s:
        return None
    lows, highs = [], []
    parts = s.split(",")
    if len(parts) != 4:
        raise ValueError("--bounds must provide 4 ranges")
    for part in parts:
        lo, hi = part.split(":")
        lows.append(float(lo))
        highs.append(float(hi))
    return (tuple(lows), tuple(highs))


def main():
    args = build_parser().parse_args()
    t, data = load_csv(args.csv)
    guess = parse_guess(args.guess) or (0.05, 0.2, 0.05, 0.05)
    bounds = parse_bounds(args.bounds) or ((0, 0, 0, 0), (np.inf, np.inf, np.inf, np.inf))

    result = fit_szr(t, data, guess=guess, bounds=bounds)

    print("Fit result:")
    print(json.dumps({
        "alpha": result.alpha,
        "beta": result.beta,
        "gamma": result.gamma,
        "delta": result.delta,
        "sse": result.sse,
        "success": result.success,
        "message": result.message,
    }, indent=2))

    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({
                "alpha": result.alpha,
                "beta": result.beta,
                "gamma": result.gamma,
                "delta": result.delta,
                "sse": result.sse,
            }, f, indent=2)
        print(f"Saved parameters to {args.out_json}")

    if args.plot:
        if plt is None:
            print("matplotlib not available; install it to enable plotting")
        else:
            y0 = data[0]
            sim = simulate((result.alpha, result.beta, result.gamma, result.delta), t, y0)
            S_sim, Z_sim, R_sim = sim
            fig, ax = plt.subplots(1, 1, figsize=(8, 5))
            ax.plot(t, data[:, 0], "o", label="S data", alpha=0.6)
            ax.plot(t, data[:, 1], "o", label="Z data", alpha=0.6)
            ax.plot(t, data[:, 2], "o", label="R data", alpha=0.6)
            ax.plot(t, S_sim, "-", label="S fit")
            ax.plot(t, Z_sim, "-", label="Z fit")
            ax.plot(t, R_sim, "-", label="R fit")
            ax.set_xlabel("time")
            ax.set_ylabel("population")
            ax.legend()
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            plt.show()


if __name__ == "__main__":
    main()
