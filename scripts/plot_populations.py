#!/usr/bin/env python3
"""
Generate styled plots from notebooks/populations.csv:
- Line plot of S, Z, R over time
- Stacked area (counts)
- Normalized stacked area (percent)
- Rolling mean (smoothing)

Outputs PNGs into fig/.
"""
import os
import json
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PALETTE = {
    'S': '#1f77b4',  # Blue
    'Z': '#2ca02c',  # Green
    'R': '#7f7f7f',  # Gray
}

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    time_col = cols.get('time', df.columns[0])
    S_col = cols.get('s', 'S')
    Z_col = cols.get('z', 'Z')
    R_col = cols.get('r', 'R')
    return pd.DataFrame({
        'time': df[time_col].values,
        'S': df[S_col].values,
        'Z': df[Z_col].values,
        'R': df[R_col].values,
    })

def plot_line(df: pd.DataFrame, outpath: str):
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in ['S','Z','R']:
        ax.plot(df['time'], df[col], label=col, color=PALETTE[col], linewidth=2)
    ax.set_xlabel('Czas'); ax.set_ylabel('Liczebność'); ax.set_title('Populacje — linie'); ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(outpath, dpi=160); plt.close(fig)

def plot_stacked(df: pd.DataFrame, outpath: str):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.stackplot(df['time'], df['S'], df['Z'], df['R'], labels=['S','Z','R'], colors=[PALETTE['S'],PALETTE['Z'],PALETTE['R']], alpha=0.9)
    ax.set_xlabel('Czas'); ax.set_ylabel('Liczebność'); ax.set_title('Populacje — stacked area'); ax.legend(loc='upper left'); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(outpath, dpi=160); plt.close(fig)

def plot_percent(df: pd.DataFrame, outpath: str):
    normalized = df[['S','Z','R']].div(df[['S','Z','R']].sum(axis=1), axis=0).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.stackplot(df['time'], normalized['S'], normalized['Z'], normalized['R'], labels=['S','Z','R'], colors=[PALETTE['S'],PALETTE['Z'],PALETTE['R']], alpha=0.9)
    ax.set_xlabel('Czas'); ax.set_ylabel('Udział [%]'); ax.set_title('Populacje — udział procentowy'); ax.legend(loc='upper left'); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(outpath, dpi=160); plt.close(fig)

def plot_rolling(df: pd.DataFrame, outpath: str, win: int = 5):
    smoothed = df[['S','Z','R']].rolling(window=win, min_periods=1, center=True).mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in ['S','Z','R']:
        ax.plot(df['time'], smoothed[col], label=f"{col} (rolling {win})", color=PALETTE[col], linewidth=2)
    ax.set_xlabel('Czas'); ax.set_ylabel('Liczebność (wygładzone)'); ax.set_title('Populacje — rolling mean'); ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(outpath, dpi=160); plt.close(fig)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default=os.path.join('notebooks','populations.csv'))
    p.add_argument('--outdir', default='fig')
    p.add_argument('--win', type=int, default=5)
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = load_csv(args.csv)

    outputs = {
        'line': os.path.join(args.outdir, 'populations_line.png'),
        'stacked': os.path.join(args.outdir, 'populations_stacked.png'),
        'percent': os.path.join(args.outdir, 'populations_percent.png'),
        'rolling': os.path.join(args.outdir, 'populations_rolling.png'),
    }

    plot_line(df, outputs['line'])
    plot_stacked(df, outputs['stacked'])
    plot_percent(df, outputs['percent'])
    plot_rolling(df, outputs['rolling'], win=args.win)

    print(json.dumps(outputs, indent=2))

if __name__ == '__main__':
    main()
