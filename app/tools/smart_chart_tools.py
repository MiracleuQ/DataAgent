import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Plotly 主题配置
THEME = {
    "template": "plotly_white",
    "font_family": "Microsoft YaHei, SimHei, sans-serif",
    "title_font_size": 18,
    "axis_title_font_size": 14,
    "tick_font_size": 12,
    "colorway": px.colors.qualitative.Vivid,
    "plot_bgcolor": "white",
    "paper_bgcolor": "white",
}


def _apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """应用统一主题到图表"""
    fig.update_layout(
        template=THEME["template"],
        font=dict(family=THEME["font_family"], size=THEME["tick_font_size"]),
        title=dict(text=title, font=dict(size=THEME["title_font_size"], color="#2c3e50"), x=0.5),
        xaxis=dict(gridcolor="#ecf0f1", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#ecf0f1", showgrid=True, zeroline=False),
        plot_bgcolor=THEME["plot_bgcolor"],
        paper_bgcolor=THEME["paper_bgcolor"],
        legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#ecf0f1", borderwidth=1),
        margin=dict(l=60, r=30, t=80, b=60),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Microsoft YaHei"),
    )
    return fig


def _save_chart(fig: go.Figure, output_dir: str, name: str, format: str = "png") -> str:
    """保存图表到文件"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.{format}")
    fig.write_image(path, width=1200, height=700, scale=2)
    return path


def analyze_data_for_chart(df: pd.DataFrame, df_name: str) -> Dict[str, Any]:
    """分析数据特征，为 AI 推荐图表类型"""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    analysis = {
        "df_name": df_name,
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": numeric_cols[:10],
        "categorical_columns": categorical_cols[:10],
        "datetime_columns": datetime_cols[:5],
        "column_stats": {}
    }

    for col in numeric_cols[:5]:
        analysis["column_stats"][col] = {
            "type": "numeric",
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "unique_ratio": len(df[col].unique()) / len(df)
        }

    for col in categorical_cols[:5]:
        analysis["column_stats"][col] = {
            "type": "categorical",
            "unique_count": len(df[col].unique()),
            "top_values": df[col].value_counts().head(5).to_dict(),
            "unique_ratio": len(df[col].unique()) / len(df)
        }

    return analysis


def create_smart_chart(df: pd.DataFrame, chart_type: str, config: Dict[str, Any], df_name: str = "", output_dir: str = "data/charts") -> str:
    """根据 AI 配置创建美观的图表"""
    title = config.get("title", f"{df_name} Analysis")
    chart_type = chart_type.lower()

    if chart_type == "bar":
        fig = _create_bar_chart(df, config, title)
    elif chart_type == "line":
        fig = _create_line_chart(df, config, title)
    elif chart_type == "scatter":
        fig = _create_scatter_chart(df, config, title)
    elif chart_type == "pie":
        fig = _create_pie_chart(df, config, title)
    elif chart_type == "heatmap":
        fig = _create_heatmap(df, config, title)
    elif chart_type == "box":
        fig = _create_box_chart(df, config, title)
    elif chart_type == "histogram":
        fig = _create_histogram(df, config, title)
    elif chart_type == "treemap":
        fig = _create_treemap(df, config, title)
    else:
        fig = _create_bar_chart(df, config, title)

    fig = _apply_theme(fig, title)
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in f"{df_name}_{chart_type}_{config.get('x', '')}_{config.get('y', '')}")
    return _save_chart(fig, output_dir, safe_name[:50])


def _create_bar_chart(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    x = config.get("x")
    y = config.get("y")
    color = config.get("color")
    orientation = config.get("orientation", "v")

    if orientation == "h":
        fig = go.Figure(go.Bar(
            x=df[y], y=df[x], orientation="h",
            marker=dict(color=df[y], colorscale="Viridis", showscale=True, colorbar=dict(title=y)),
            text=df[y].apply(lambda v: f"{v:,.0f}"), textposition="outside",
            hovertemplate=f"<b>{x}: %{{y}}</b><br>{y}: %{{x:,.0f}}<extra></extra>"
        ))
        fig.update_layout(xaxis_title=y, yaxis_title=x)
    else:
        fig = go.Figure(go.Bar(
            x=df[x], y=df[y], marker=dict(color=df[y], colorscale="Viridis", showscale=True, colorbar=dict(title=y)),
            text=df[y].apply(lambda v: f"{v:,.0f}"), textposition="outside",
            hovertemplate=f"<b>{x}: %{{x}}</b><br>{y}: %{{y:,.0f}}<extra></extra>"
        ))
        fig.update_layout(xaxis_title=x, yaxis_title=y)

    return fig


def _create_line_chart(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    x = config.get("x")
    y = config.get("y")
    color = config.get("color")
    markers = config.get("markers", True)
    area = config.get("area", False)

    if area:
        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y], mode="lines+markers" if markers else "lines",
            fill="tozeroy", fillcolor="rgba(46, 204, 113, 0.2)",
            line=dict(color="#2ecc71", width=3),
            marker=dict(size=10, color="white", line=dict(color="#2ecc71", width=2)),
            hovertemplate=f"<b>{x}: %{{x}}</b><br>{y}: %{{y:,.0f}}<extra></extra>"
        ))
    else:
        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y], mode="lines+markers" if markers else "lines",
            line=dict(color="#3498db", width=3, shape="spline"),
            marker=dict(size=10, color="white", line=dict(color="#3498db", width=2)),
            hovertemplate=f"<b>{x}: %{{x}}</b><br>{y}: %{{y:,.0f}}<extra></extra>"
        ))

    fig.update_layout(xaxis_title=x, yaxis_title=y)
    return fig


def _create_scatter_chart(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    x = config.get("x")
    y = config.get("y")
    color = config.get("color")
    size = config.get("size")

    fig = go.Figure(go.Scatter(
        x=df[x], y=df[y], mode="markers",
        marker=dict(
            size=df[size] if size and size in df.columns else 15,
            color=df[color] if color and color in df.columns else "#e74c3c",
            colorscale="Viridis" if color and color in df.columns else None,
            showscale=bool(color and color in df.columns),
            opacity=0.8,
            line=dict(width=2, color="white")
        ),
        hovertemplate=f"<b>{x}: %{{x}}</b><br>{y}: %{{y}}<extra></extra>"
    ))

    fig.update_layout(xaxis_title=x, yaxis_title=y)
    return fig


def _create_pie_chart(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    labels = config.get("labels")
    values = config.get("values")
    hole = config.get("hole", 0.4)

    fig = go.Figure(go.Pie(
        labels=df[labels], values=df[values],
        hole=hole,
        marker=dict(colors=px.colors.qualitative.Vivid[:len(df)], line=dict(color="white", width=2)),
        textfont_size=13,
        hovertemplate=f"<b>%{{label}}</b><br>Value: %{{value:,.0f}}<br>Percent: %{{percent}}<extra></extra>"
    ))

    return fig


def _create_heatmap(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    cols = config.get("columns", df.select_dtypes(include=["number"]).columns[:8].tolist())
    corr = df[cols].corr()

    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdBu_r", zmid=0,
        text=corr.values.round(2), texttemplate="%{text}",
        hovertemplate="<b>%{x} vs %{y}</b><br>Correlation: %{z:.3f}<extra></extra>"
    ))

    return fig


def _create_box_chart(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    x = config.get("x")
    y = config.get("y")

    if x:
        fig = go.Figure(go.Box(x=df[x], y=df[y], boxpoints="outliers", marker=dict(color="#3498db")))
        fig.update_layout(xaxis_title=x, yaxis_title=y)
    else:
        fig = go.Figure(go.Box(y=df[y], boxpoints="outliers", marker=dict(color="#3498db")))
        fig.update_layout(yaxis_title=y)

    return fig


def _create_histogram(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    x = config.get("x")
    bins = config.get("bins", 30)

    fig = go.Figure(go.Histogram(
        x=df[x], nbinsx=bins,
        marker=dict(color="#9b59b6", line=dict(width=1, color="white")),
        hovertemplate=f"<b>{x}: %{{x}}</b><br>Count: %{{y}}<extra></extra>"
    ))

    fig.update_layout(xaxis_title=x, yaxis_title="Count")
    return fig


def _create_treemap(df: pd.DataFrame, config: Dict, title: str) -> go.Figure:
    labels = config.get("labels")
    values = config.get("values")
    parents = config.get("parents")

    if parents and parents in df.columns:
        fig = go.Figure(go.Treemap(labels=df[labels], parents=df[parents], values=df[values],
                                    marker=dict(colorscale="Viridis")))
    else:
        fig = go.Figure(go.Treemap(labels=df[labels], values=df[values],
                                    marker=dict(colorscale="Viridis")))

    return fig


def get_ai_chart_tools():
    """获取 AI 图表工具"""
    from app.tools.registry import Tool
    return [
        Tool(
            name="analyze_data",
            description="Analyze data features and recommend chart types",
            parameters={"type": "object", "properties": {"df_name": {"type": "string"}}, "required": ["df_name"]},
            function=lambda df_name: json.dumps(analyze_data_for_chart(pd.DataFrame(), df_name), ensure_ascii=False)
        ),
        Tool(
            name="create_smart_chart",
            description="Create beautiful chart based on AI config",
            parameters={"type": "object", "properties": {
                "df_name": {"type": "string"},
                "chart_type": {"type": "string", "enum": ["bar", "line", "scatter", "pie", "heatmap", "box", "histogram", "treemap"]},
                "config": {"type": "object"}
            }, "required": ["df_name", "chart_type", "config"]},
            function=lambda df_name, chart_type, config, **kwargs: create_smart_chart(
                pd.DataFrame(), chart_type, config, df_name
            )
        ),
    ]
