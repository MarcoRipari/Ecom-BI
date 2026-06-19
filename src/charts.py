import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Colori Corporate
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#18bc9c',
    'accent': '#e74c3c',
    'background': '#ffffff',
    'grid': '#f0f2f6',
    'text': '#2c3e50'
}

def apply_corporate_layout(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title={'text': title, 'font': {'size': 20, 'color': COLORS['text']}},
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text'], family="Arial, sans-serif"),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=True, gridcolor=COLORS['grid'], gridwidth=1, linecolor=COLORS['grid']),
        yaxis=dict(showgrid=True, gridcolor=COLORS['grid'], gridwidth=1, linecolor=COLORS['grid']),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_sales_trend(df: pd.DataFrame, date_col: str, value_col: str, title: str = "Trend Vendite") -> go.Figure:
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return go.Figure()
        
    df_grouped = df.groupby(pd.Grouper(key=date_col, freq='W'))[value_col].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_grouped[date_col], 
        y=df_grouped[value_col],
        mode='lines+markers',
        line=dict(color=COLORS['secondary'], width=3),
        fill='tozeroy',
        fillcolor='rgba(24, 188, 156, 0.1)',
        name=value_col,
        hovertemplate='<b>Data</b>: %{x|%d %b %Y}<br><b>Fatturato</b>: €%{y:,.2f}<extra></extra>'
    ))
    return apply_corporate_layout(fig, title)

def plot_y2y_comparison(df_merged: pd.DataFrame, category_col: str, curr_col: str, old_col: str, title: str = "Comparativa Y2Y") -> go.Figure:
    if df_merged.empty:
        return go.Figure()
        
    df_plot = df_merged.head(10).sort_values(curr_col, ascending=True) # Prendi i top 10 e ordina per chart orizzontale
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_plot[category_col],
        x=df_plot[old_col],
        name='Anno Precedente',
        orientation='h',
        marker_color='#bdc3c7',
        hovertemplate='%{y}: €%{x:,.2f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        y=df_plot[category_col],
        x=df_plot[curr_col],
        name='Anno Corrente',
        orientation='h',
        marker_color=COLORS['primary'],
        hovertemplate='%{y}: €%{x:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(barmode='group')
    return apply_corporate_layout(fig, title)

def plot_returns_waterfall(paia_spedite: float, paia_rese: float, title: str = "Analisi Resi") -> go.Figure:
    fig = go.Figure(go.Waterfall(
        name="Resi", 
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Paia Spedite", "Paia Rese", "Paia Nette"],
        textposition="outside",
        text=[f"{paia_spedite:,.0f}", f"-{paia_rese:,.0f}", f"{paia_spedite - paia_rese:,.0f}"],
        y=[paia_spedite, -paia_rese, paia_spedite - paia_rese],
        connector={"line":{"color": COLORS['grid']}},
        decreasing={"marker":{"color": COLORS['accent']}},
        increasing={"marker":{"color": COLORS['secondary']}},
        totals={"marker":{"color": COLORS['primary']}}
    ))
    return apply_corporate_layout(fig, title)

def plot_taglie_heatmap(df_taglie: pd.DataFrame, title: str = "Distribuzione Taglie") -> go.Figure:
    if df_taglie.empty:
        return go.Figure()
        
    pivot = df_taglie.pivot_table(index='sotto_gruppo', columns='taglia', values='paia_nette', aggfunc='sum').fillna(0)
    
    fig = px.imshow(
        pivot, 
        color_continuous_scale='Teal',
        aspect="auto",
        labels=dict(color="Paia Nette")
    )
    
    fig.update_traces(hovertemplate='Gruppo: %{y}<br>Taglia: %{x}<br>Paia: %{z:,.0f}<extra></extra>')
    return apply_corporate_layout(fig, title)
