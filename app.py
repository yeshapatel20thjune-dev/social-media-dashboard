# ============================================================
# app.py — Social Media Marketing Dashboard
# MADSC202 | Spring 2026 | KPIs 1–7
# Deploy on Render.com
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ── LOAD & CLEAN ──────────────────────────────────────────────
df = pd.read_csv("marketing_campaign_small.csv")
df["Duration"]         = df["Duration"].str.replace(" days", "").astype(int)
df["Acquisition_Cost"] = (df["Acquisition_Cost"]
                          .str.replace("$", "", regex=False)
                          .str.replace(",", "", regex=False)
                          .astype(float))
df["Date"]        = pd.to_datetime(df["Date"])
df["Month"]       = df["Date"].dt.to_period("M").astype(str)
df["CTR"]         = (df["Clicks"] / df["Impressions"] * 100).round(4)
df["CPC"]         = (df["Acquisition_Cost"] / df["Clicks"]).round(2)
df["CostPerConv"] = (df["Acquisition_Cost"] / (df["Conversion_Rate"] * df["Clicks"])).round(2)

# ── APP ───────────────────────────────────────────────────────
app = Dash(__name__)
server = app.server  # Required for gunicorn on Render

channel_options  = [{"label": "All Channels", "value": "All"}] + [
    {"label": c, "value": c} for c in sorted(df["Channel_Used"].unique())]
campaign_options = [{"label": "All Types",    "value": "All"}] + [
    {"label": c, "value": c} for c in sorted(df["Campaign_Type"].unique())]

CARD_STYLE = {"backgroundColor": "#fff", "padding": "20px", "borderRadius": "10px",
              "boxShadow": "0 2px 6px rgba(0,0,0,0.08)", "marginBottom": "24px"}
PAGE_STYLE = {"fontFamily": "Segoe UI, sans-serif",
              "backgroundColor": "#f4f6f9", "padding": "20px"}

def section(kpi_title, description, children):
    return html.Div([
        html.H3(kpi_title, style={"color": "#1a1a2e", "marginBottom": "4px"}),
        html.P(description,  style={"color": "#888", "marginTop": "0", "fontSize": "13px"}),
        *children,
    ], style=CARD_STYLE)

# ── LAYOUT ────────────────────────────────────────────────────
app.layout = html.Div(style=PAGE_STYLE, children=[

    html.Div([
        html.H1("📊 Social Media Marketing Dashboard",
                style={"color": "#1a1a2e", "marginBottom": "4px"}),
        html.P("MADSC202 | Spring 2026 | KPIs 1–7",
               style={"color": "#666", "marginTop": "0"}),
    ], style={"marginBottom": "24px"}),

    # Filters
    html.Div([
        html.Div([
            html.Label("🌐 Channel", style={"fontWeight": "bold"}),
            dcc.Dropdown(id="channel-filter", options=channel_options,
                         value="All", clearable=False, style={"width": "220px"}),
        ], style={"marginRight": "30px"}),
        html.Div([
            html.Label("📣 Campaign Type", style={"fontWeight": "bold"}),
            dcc.Dropdown(id="campaign-filter", options=campaign_options,
                         value="All", clearable=False, style={"width": "220px"}),
        ]),
    ], style={"display": "flex", **CARD_STYLE}),

    # Scorecards
    html.Div(id="kpi-cards", style={"marginBottom": "24px"}),

    # KPI 1
    section("KPI #1 — Click-Through Rate (CTR)",
            "How often people click after seeing the ad (Clicks ÷ Impressions)",
            [html.Div([
                html.Div([dcc.Graph(id="ctr-bar")],  style={"flex": "1"}),
                html.Div([dcc.Graph(id="ctr-line")], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "16px"})]),

    # KPI 2
    section("KPI #2 — Conversion Rate",
            "Average % of clicks that result in a conversion, by Campaign Type",
            [dcc.Graph(id="conv-donut")]),

    # KPI 3
    section("KPI #3 — Cost Per Click (CPC)",
            "Average acquisition cost per click by channel (Acquisition Cost ÷ Clicks)",
            [dcc.Graph(id="cpc-bar")]),

    # KPI 4
    section("KPI #4 — Return on Ad Spend (ROAS / ROI)",
            "Average ROI per Campaign Type grouped by Channel",
            [dcc.Graph(id="roas-bar")]),

    # KPI 5
    section("KPI #5 — Engagement Score by Platform & Month",
            "Heatmap showing average engagement score across channels over time",
            [dcc.Graph(id="eng-heatmap")]),

    # KPI 6
    section("KPI #6 — Impressions by Platform",
            "Total reach (impressions) across all channels — treemap view",
            [dcc.Graph(id="imp-treemap")]),

    # KPI 7
    section("KPI #7 — Cost Per Conversion",
            "Scatter plot of acquisition cost vs conversions — spot efficiency outliers",
            [dcc.Graph(id="cpc-scatter")]),
])

# ── CALLBACKS ─────────────────────────────────────────────────
@app.callback(
    Output("kpi-cards",   "children"),
    Output("ctr-bar",     "figure"),
    Output("ctr-line",    "figure"),
    Output("conv-donut",  "figure"),
    Output("cpc-bar",     "figure"),
    Output("roas-bar",    "figure"),
    Output("eng-heatmap", "figure"),
    Output("imp-treemap", "figure"),
    Output("cpc-scatter", "figure"),
    Input("channel-filter",  "value"),
    Input("campaign-filter", "value"),
)
def update(channel, campaign):
    f = df.copy()
    if channel  != "All": f = f[f["Channel_Used"]  == channel]
    if campaign != "All": f = f[f["Campaign_Type"] == campaign]

    # ── Scorecards ────────────────────────────────────────────
    cards = html.Div([
        _card("Avg CTR",          f"{f['CTR'].mean():.2f}%",            "#4361ee"),
        _card("Avg Conv. Rate",   f"{f['Conversion_Rate'].mean():.2%}", "#3a0ca3"),
        _card("Avg CPC",          f"${f['CPC'].mean():.2f}",            "#7209b7"),
        _card("Avg ROI",          f"{f['ROI'].mean():.2f}x",            "#f72585"),
        _card("Avg Engagement",   f"{f['Engagement_Score'].mean():.2f}","#4cc9f0"),
        _card("Total Impressions",f"{f['Impressions'].sum():,}",        "#06d6a0"),
        _card("Total Campaigns",  f"{len(f):,}",                        "#ffd166"),
    ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap"})

    # ── KPI 1a: Bar — CTR by Channel ──────────────────────────
    ctr_ch = (f.groupby("Channel_Used")["CTR"]
               .mean().reset_index().sort_values("CTR", ascending=False))
    ctr_bar = px.bar(ctr_ch, x="Channel_Used", y="CTR",
                     color="CTR", color_continuous_scale="Blues", text="CTR",
                     title="Avg CTR by Channel",
                     labels={"Channel_Used": "Channel", "CTR": "CTR (%)"})
    ctr_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    ctr_bar.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff",
                          coloraxis_showscale=False, title_font_size=14)

    # ── KPI 1b: Line — CTR by Duration ────────────────────────
    f2 = f.copy()
    f2["Duration_Bin"] = pd.cut(f2["Duration"], bins=4,
                                labels=["15 days","30 days","45 days","60 days"])
    ctr_dur = f2.groupby("Duration_Bin", observed=True)["CTR"].mean().reset_index()
    ctr_line = px.line(ctr_dur, x="Duration_Bin", y="CTR", markers=True,
                       title="CTR Trend by Campaign Duration",
                       labels={"Duration_Bin": "Duration", "CTR": "CTR (%)"},
                       color_discrete_sequence=["#4361ee"])
    ctr_line.update_traces(line_width=3, marker_size=10)
    ctr_line.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff",
                           title_font_size=14)

    # ── KPI 2: Donut — Conversion Rate by Campaign Type ───────
    conv = f.groupby("Campaign_Type")["Conversion_Rate"].mean().reset_index()
    conv["Conv_Pct"] = (conv["Conversion_Rate"] * 100).round(2)
    donut = px.pie(conv, names="Campaign_Type", values="Conv_Pct", hole=0.55,
                   title="Avg Conversion Rate by Campaign Type (%)",
                   color_discrete_sequence=px.colors.sequential.Purples_r)
    donut.update_traces(textinfo="label+percent", pull=[0.03]*len(conv))
    donut.update_layout(paper_bgcolor="#fff", title_font_size=14,
                        legend=dict(orientation="h", y=-0.1))

    # ── KPI 3: Horizontal Bar — CPC by Channel ────────────────
    cpc_ch = (f.groupby("Channel_Used")["CPC"]
               .mean().reset_index().sort_values("CPC", ascending=True))
    cpc_bar = px.bar(cpc_ch, x="CPC", y="Channel_Used", orientation="h",
                     color="CPC", color_continuous_scale="Reds", text="CPC",
                     title="Avg Cost Per Click (CPC) by Channel",
                     labels={"Channel_Used": "Channel", "CPC": "CPC ($)"})
    cpc_bar.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    cpc_bar.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff",
                          coloraxis_showscale=False, title_font_size=14)

    # ── KPI 4: Grouped Bar — ROI by Campaign Type & Channel ───
    roas = f.groupby(["Campaign_Type","Channel_Used"])["ROI"].mean().reset_index().round(2)
    roas_bar = px.bar(roas, x="Campaign_Type", y="ROI", color="Channel_Used",
                      barmode="group", title="Avg ROI by Campaign Type & Channel",
                      labels={"Campaign_Type":"Campaign Type",
                              "ROI":"ROI (x)","Channel_Used":"Channel"},
                      color_discrete_sequence=px.colors.qualitative.Bold)
    roas_bar.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff",
                           title_font_size=14, legend=dict(orientation="h", y=-0.2))

    # ── KPI 5: Heatmap — Engagement Score by Channel & Month ──
    top_months = f.groupby("Month")["Engagement_Score"].mean().nlargest(12).index
    eng = (f[f["Month"].isin(top_months)]
            .groupby(["Channel_Used","Month"])["Engagement_Score"]
            .mean().reset_index())
    eng_pivot = eng.pivot(index="Channel_Used", columns="Month",
                          values="Engagement_Score").fillna(0)
    heatmap = go.Figure(go.Heatmap(
        z=eng_pivot.values,
        x=eng_pivot.columns.tolist(),
        y=eng_pivot.index.tolist(),
        colorscale="Teal",
        text=eng_pivot.values.round(2),
        texttemplate="%{text}",
        showscale=True,
    ))
    heatmap.update_layout(
        title="Avg Engagement Score by Channel & Month",
        paper_bgcolor="#fff", plot_bgcolor="#fff", title_font_size=14,
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="Channel"),
    )

    # ── KPI 6: Treemap — Impressions by Platform ──────────────
    imp = f.groupby(["Channel_Used","Campaign_Type"])["Impressions"].sum().reset_index()
    treemap = px.treemap(imp,
                         path=["Channel_Used","Campaign_Type"],
                         values="Impressions",
                         title="Total Impressions by Channel & Campaign Type",
                         color="Impressions",
                         color_continuous_scale="Blues")
    treemap.update_traces(textinfo="label+value+percent root")
    treemap.update_layout(paper_bgcolor="#fff", title_font_size=14)

    # ── KPI 7: Scatter — Acquisition Cost vs Conversions ──────
    f3 = f.copy()
    f3["Conversions"] = (f3["Conversion_Rate"] * f3["Clicks"]).round(0)
    sample = f3.sample(min(2000, len(f3)), random_state=42)
    scatter = px.scatter(sample,
                         x="Acquisition_Cost", y="Conversions",
                         color="Channel_Used", size="Clicks",
                         hover_data=["Campaign_Type","ROI"],
                         trendline="ols",
                         title="Cost Per Conversion: Acquisition Cost vs Conversions",
                         labels={"Acquisition_Cost":"Acquisition Cost ($)",
                                 "Conversions":"Conversions",
                                 "Channel_Used":"Channel"},
                         color_discrete_sequence=px.colors.qualitative.Bold)
    scatter.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff",
                          title_font_size=14, legend=dict(orientation="h", y=-0.2))

    return cards, ctr_bar, ctr_line, donut, cpc_bar, roas_bar, heatmap, treemap, scatter


# ── Helper: metric card ───────────────────────────────────────
def _card(label, value, color):
    return html.Div([
        html.P(label, style={"margin": "0", "fontSize": "12px", "color": "#888"}),
        html.H2(value, style={"margin": "4px 0 0", "color": color, "fontSize": "20px"}),
    ], style={"backgroundColor": "#fff", "padding": "14px 18px", "borderRadius": "10px",
              "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
              "borderLeft": f"5px solid {color}", "minWidth": "130px", "flex": "1"})


# ── LAUNCH ────────────────────────────────────────────────────
import os
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=port)
