import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

CHINESE_FONTS = ["SimHei", "Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei"]
for font in CHINESE_FONTS:
    if any(font.lower() in f.name.lower() for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [font]
        break
plt.rcParams["axes.unicode_minus"] = False

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)

COLOR_PALETTE = sns.color_palette("muted")
BAR_COLORS = sns.color_palette("viridis", n_colors=12)
PIE_COLORS = sns.color_palette("pastel")


def _save_chart(fig, output_dir: str, name: str) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_line(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df[x], df[y], marker="o", color=COLOR_PALETTE[0], linewidth=2, markersize=5)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} over {x}", fontweight="bold")
    ax.grid(True, alpha=0.3)
    sns.despine()
    return _save_chart(fig, output_dir, f"line_{x}_{y}")


def plot_bar(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    n = len(df)
    colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(n)]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(n), df[y], color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(n))
    ax.set_xticklabels(df[x].astype(str), rotation=45, ha="right")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} by {x}", fontweight="bold")
    ax.set_xlim(-0.6, n - 0.4)
    sns.despine()
    return _save_chart(fig, output_dir, f"bar_{x}_{y}")


def plot_scatter(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[x], df[y], alpha=0.6, color=COLOR_PALETTE[2], edgecolors="white", linewidth=0.3, s=60)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} vs {x}", fontweight="bold")
    ax.grid(True, alpha=0.3)
    sns.despine()
    return _save_chart(fig, output_dir, f"scatter_{x}_{y}")


def plot_pie(df: pd.DataFrame, labels: str, values: str, title: str = "", output_dir: str = "data/charts") -> str:
    n = len(df)
    colors = PIE_COLORS[:n] if n <= len(PIE_COLORS) else sns.color_palette("husl", n_colors=n)
    fig, ax = plt.subplots(figsize=(10, 6))
    wedges, texts, autotexts = ax.pie(
        df[values], labels=df[labels], autopct="%1.1f%%",
        startangle=90, colors=colors, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1},
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    ax.set_title(title or f"{values} distribution", fontweight="bold")
    return _save_chart(fig, output_dir, f"pie_{labels}_{values}")


def get_chart_tools():
    from app.tools.registry import Tool
    return [
        Tool(name="plot_line", description="Create a line chart", parameters={"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["x", "y"]}, function=plot_line),
        Tool(name="plot_bar", description="Create a bar chart", parameters={"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["x", "y"]}, function=plot_bar),
        Tool(name="plot_scatter", description="Create a scatter plot", parameters={"type": "object", "properties": {"x": {"type": "string"}, "y": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["x", "y"]}, function=plot_scatter),
        Tool(name="plot_pie", description="Create a pie chart", parameters={"type": "object", "properties": {"labels": {"type": "string"}, "values": {"type": "string"}, "title": {"type": "string", "default": ""}}, "required": ["labels", "values"]}, function=plot_pie),
    ]
