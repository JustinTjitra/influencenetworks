"""Static figures for the event study (PNG and SVG).

One hue for estimates; the distinction between main-test and robustness-only events
is carried by marker fill and a legend, not by colour. Zero is always drawn. Text is
neutral ink; grids and spines are recessive.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"       # categorical slot 1
NEUTRAL = "#b9b8b2"


def _style(ax, xlabel: str = "", title: str = "", subtitle: str = ""):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, length=0, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, color=INK_2, fontsize=9)
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold", pad=22 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9, va="bottom")


def _save(fig, out: Path) -> list[Path]:
    out.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "svg"):
        p = out.with_suffix(f".{ext}")
        fig.savefig(p, dpi=200, facecolor=SURFACE, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths


def _pct(v):
    return v * 100.0


def forest(per_event: pd.DataFrame, out: Path, title: str = "Connected firms' return gap, by event",
           subtitle: str = "") -> list[Path]:
    """Per-event d_e with 95% intervals, signed so that right of zero means the
    pre-registered direction. Needs: label, d_signed, ci_low_signed, ci_high_signed,
    main_test."""
    df = per_event[per_event.d_signed.notna()].iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.2, max(2.4, 0.42 * len(df) + 1.4)), facecolor=SURFACE)
    y = np.arange(len(df))
    ax.hlines(y, _pct(df.ci_low_signed), _pct(df.ci_high_signed), color=SERIES, linewidth=2)
    main = df.main_test.astype(bool).to_numpy()
    ax.scatter(_pct(df.d_signed[main]), y[main], s=64, color=SERIES, zorder=3,
               edgecolor=SURFACE, linewidth=2, label="main test")
    ax.scatter(_pct(df.d_signed[~main]), y[~main], s=64, facecolor=SURFACE, zorder=3,
               edgecolor=SERIES, linewidth=2, label="robustness only")
    ax.axvline(0, color=INK_2, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(df.label, color=INK, fontsize=9)
    ax.set_ylim(-0.7, len(df) - 0.3)
    _style(ax, "CAR gap, connected minus unconnected, percentage points "
               "(right of zero = pre-registered direction)", title, subtitle)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK_2)
    return _save(fig, out)


def stacked_by_type(stacked: pd.DataFrame, out: Path, title: str = "Stacked estimates by event type",
                    subtitle: str = "") -> list[Path]:
    """Stacked d with 95% intervals: one panel per event group, one row per model.
    Needs: group, model, d, ci_low, ci_high."""
    df = stacked[stacked.d.notna()]
    groups = list(dict.fromkeys(df.group))
    if not groups:
        groups = ["no identified estimate"]
    fig, axes = plt.subplots(1, len(groups), figsize=(3.4 * len(groups) + 1.2, 2.6),
                             facecolor=SURFACE, sharex=True, sharey=True, squeeze=False)
    models = list(dict.fromkeys(df.model)) if len(df) else []
    for ax, g in zip(axes[0], groups):
        s = df[df.group == g].set_index("model").reindex(models)
        y = np.arange(len(models))[::-1]
        ax.hlines(y, _pct(s.ci_low), _pct(s.ci_high), color=SERIES, linewidth=2)
        ax.scatter(_pct(s.d), y, s=64, color=SERIES, zorder=3, edgecolor=SURFACE, linewidth=2)
        ax.axvline(0, color=INK_2, linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels([m.replace("_", " ") for m in models], color=INK, fontsize=9)
        ax.set_ylim(-0.7, max(len(models) - 0.3, 0.7))
        _style(ax, "percentage points")
        ax.set_title(str(g).replace("_", " "), loc="left", color=INK, fontsize=10)
    fig.suptitle(title, x=0.02, ha="left", va="bottom", color=INK, fontsize=12, fontweight="bold", y=1.13)
    if subtitle:
        fig.text(0.02, 1.04, subtitle, color=INK_2, fontsize=9, va="bottom")
    return _save(fig, out)


def placebo_hist(draws: np.ndarray, d_true: float, out: Path, p_empirical: Optional[float] = None,
                 title: str = "Placebo distribution", subtitle: str = "") -> list[Path]:
    """Histogram of placebo estimates with the real estimate marked and labelled."""
    draws = np.asarray(draws, float)
    draws = draws[np.isfinite(draws)]
    fig, ax = plt.subplots(figsize=(7.2, 3.4), facecolor=SURFACE)
    if len(draws):
        ax.hist(_pct(draws), bins=min(30, max(8, len(draws) // 6)), color=NEUTRAL,
                edgecolor=SURFACE, linewidth=2)
    if np.isfinite(d_true):
        ax.axvline(_pct(d_true), color=SERIES, linewidth=2)
        label = f"real estimate {_pct(d_true):+.2f} pp"
        if p_empirical is not None and np.isfinite(p_empirical):
            label += f"\nplacebo p = {p_empirical:.3f}"
        right = len(draws) == 0 or _pct(d_true) < np.median(_pct(draws))
        ax.annotate(label, xy=(_pct(d_true), 0.97), xycoords=("data", "axes fraction"),
                    xytext=(6 if right else -6, 0), textcoords="offset points",
                    ha="left" if right else "right", va="top", color=INK, fontsize=9)
    ax.axvline(0, color=INK_2, linewidth=1)
    _style(ax, "stacked estimate on pseudo-event dates, percentage points", title, subtitle)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("draws", color=INK_2, fontsize=9)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    return _save(fig, out)
