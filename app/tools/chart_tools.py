import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

# Configure Chinese font
CHINESE_FONTS = ["Microsoft YaHei", "Noto Sans SC", "SimHei", "DengXian", "KaiTi"]
for font in CHINESE_FONTS:
    if any(font.lower() in f.name.lower() for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

# Modern styling
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#e0e0e0",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.8,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})

COLORS = sns.color_palette("husl", 8)
ACCENT = "#2ecc71"


def _save_chart(fig, output_dir: str, name: str) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return path


def plot_line(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df[x], df[y], marker="o", color=COLORS[0], linewidth=2.5, markersize=8, markerfacecolor="white", markeredgecolor=COLORS[0], markeredgewidth=2)
    ax.fill_between(range(len(df)), df[y], alpha=0.15, color=COLORS[0])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} over {x}")
    ax.grid(True, alpha=0.3)
    sns.despine(left=True, bottom=True)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)
    return _save_chart(fig, output_dir, f"line_{x}_{y}")


def plot_bar(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    n = len(df)
    colors = [COLORS[i % len(COLORS)] for i in range(n)]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(n), df[y], color=colors, edgecolor="white", linewidth=1.5, width=0.7)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_xticks(range(n))
    ax.set_xticklabels(df[x].astype(str), rotation=45, ha="right")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} by {x}")
    ax.set_ylim(0, df[y].max() * 1.15)
    ax.set_xlim(-0.6, n - 0.4)
    sns.despine(left=True, bottom=True)
    return _save_chart(fig, output_dir, f"bar_{x}_{y}")


def plot_scatter(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[x], df[y], alpha=0.7, color=COLORS[2], edgecolors="white", linewidth=1, s=80, zorder=5)
    z = None
    try:
        import numpy as np
        if len(df) > 2:
            z = np.polyfit(df[x], df[y], 1)
            p = np.poly1d(z)
            x_line = pd.Series(sorted(df[x].unique()))
            ax.plot(x_line, p(x_line), "--", color="#e74c3c", linewidth=2, alpha=0.7, label="Trend")
            ax.legend(loc="upper right")
    except Exception:
        pass
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} vs {x}")
    ax.grid(True, alpha=0.3)
    sns.despine(left=True, bottom=True)
    return _save_chart(fig, output_dir, f"scatter_{x}_{y}")


def plot_pie(df: pd.DataFrame, labels: str, values: str, title: str = "", output_dir: str = "data/charts") -> str:
    n = len(df)
    colors = COLORS[:n] if n <= len(COLORS) else sns.color_palette("husl", n_colors=n)
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        df[values], labels=df[labels], autopct="%1.1f%%",
        startangle=140, colors=colors, pctdistance=0.8,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
        textprops={"fontsize": 11}
    )
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight("bold")
        t.set_color("white")
    ax.set_title(title or f"{values} distribution", fontsize=14, fontweight="bold", pad=20)
    return _save_chart(fig, output_dir, f"pie_{labels}_{values}")


def get_chart_tools():
    from app.tools.registry import Tool
    return [
        Tool(name="plot_line", description="Create a line chart", parameters={"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["x", "y"]}, function=plot_line),
        Tool(name="plot_bar", description="Create a bar chart", parameters={"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["x", "y"]}, function=plot_bar),
        Tool(name="plot_scatter", description="Create a scatter plot", parameters={"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["x", "y"]}, function=plot_scatter),
        Tool(name="plot_pie", description="Create a pie chart", parameters={"type": "object", "properties": {"labels": {"type": "string"}, "values": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["labels", "values"]}, function=plot_pie),
    ]
