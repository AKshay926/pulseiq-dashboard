import plotly.graph_objects as go


# =========================================================
# STRIKE-WISE OI CHART
# =========================================================
def plot_oi_chart(df, atm):

    fig = go.Figure()

    # CE OI
    fig.add_trace(
        go.Bar(
            x=df["Strike"],
            y=df["CE_OI"],
            name="CE OI",
            marker_color="red",
        )
    )

    # PE OI
    fig.add_trace(
        go.Bar(
            x=df["Strike"],
            y=df["PE_OI"],
            name="PE OI",
            marker_color="#00ff66",
        )
    )

    # ATM line
    fig.add_vline(
        x=atm,
        line_width=2,
        line_dash="dash",
        line_color="white",
    )

    fig.update_layout(
        title="Strike-wise CE vs PE Open Interest",
        barmode="group",
        template="plotly_dark",
        height=500,
        hovermode="x unified",

        paper_bgcolor="#020f06",
        plot_bgcolor="#020f06",

        font=dict(color="#a0ffb8"),

        title_font=dict(
            color="#00ff66"
        ),

        xaxis=dict(
            title="Strike",
            gridcolor="rgba(0,255,102,0.06)",
        ),

        yaxis=dict(
            title="Open Interest",
            gridcolor="rgba(0,255,102,0.06)",
        ),

        legend=dict(
            bgcolor="#020f06",
            bordercolor="rgba(0,255,102,0.20)",
            borderwidth=1,
            font=dict(color="#a0ffb8"),
        ),
    )

    return fig


# =========================================================
# PCR GAUGE
# =========================================================
def plot_pcr_gauge(pcr):

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pcr,

            title={
                "text": "PCR",
                "font": {"color": "#00ff66"}
            },

            number={
                "font": {"color": "#a0ffb8"}
            },

            gauge={

                "axis": {
                    "range": [0, 2],
                    "tickcolor": "#00ff66"
                },

                "bar": {
                    "color": "#00ff66"
                },

                "bgcolor": "#020f06",

                "steps": [
                    {
                        "range": [0, 0.8],
                        "color": "#3d0000"
                    },
                    {
                        "range": [0.8, 1.2],
                        "color": "#3d3d00"
                    },
                    {
                        "range": [1.2, 2],
                        "color": "#003d1a"
                    },
                ],

                "threshold": {
                    "line": {
                        "color": "#39ff14",
                        "width": 4
                    },
                    "thickness": 0.75,
                    "value": pcr,
                },
            },
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020f06",
        height=350,
        font=dict(color="#a0ffb8"),
    )

    return fig


# =========================================================
# TOTAL OI TREND
# =========================================================
def plot_total_oi_trend(history_df):

    fig = go.Figure()

    # CE OI
    fig.add_trace(
        go.Scatter(
            x=history_df["timestamp"],
            y=history_df["total_ce_oi"],
            mode="lines",
            name="Total CE OI",
            line=dict(
                color="red",
                width=3,
            ),
        )
    )

    # PE OI
    fig.add_trace(
        go.Scatter(
            x=history_df["timestamp"],
            y=history_df["total_pe_oi"],
            mode="lines",
            name="Total PE OI",
            line=dict(
                color="#00ff66",
                width=3,
            ),
        )
    )

    fig.update_layout(

        title="Total CE vs PE Open Interest Trend",

        template="plotly_dark",

        hovermode="x unified",

        height=520,

        paper_bgcolor="#020f06",

        plot_bgcolor="#020f06",

        font=dict(color="#a0ffb8"),

        title_font=dict(
            color="#00ff66",
            size=22,
        ),

        xaxis=dict(
            title="Time",
            gridcolor="rgba(0,255,102,0.08)",
        ),

        yaxis=dict(
            title="Open Interest",
            gridcolor="rgba(0,255,102,0.08)",
        ),

        legend=dict(
            bgcolor="#020f06",
            bordercolor="rgba(0,255,102,0.20)",
            borderwidth=1,
            font=dict(color="#a0ffb8"),
        ),
    )

    return fig