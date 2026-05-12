# =========================================================
# charts.py
# =========================================================

import plotly.graph_objects as go


# =========================================================
# STRIKE-WISE CE vs PE OI BAR CHART
# =========================================================
def plot_oi_chart(df, atm):

    fig = go.Figure()

    # -----------------------------------------------------
    # CE OI
    # -----------------------------------------------------
    fig.add_trace(
        go.Bar(
            x=df["Strike"],
            y=df["CE_OI"],
            name="CE OI",
            marker_color="red",
        )
    )

    # -----------------------------------------------------
    # PE OI
    # -----------------------------------------------------
    fig.add_trace(
        go.Bar(
            x=df["Strike"],
            y=df["PE_OI"],
            name="PE OI",
            marker_color="#00ff66",
        )
    )

    # -----------------------------------------------------
    # ATM LINE
    # -----------------------------------------------------
    fig.add_vline(
        x=atm,
        line_width=2,
        line_dash="dash",
        line_color="white",
    )

    # -----------------------------------------------------
    # LAYOUT
    # -----------------------------------------------------
    fig.update_layout(

        title="Strike-wise CE vs PE Open Interest",

        barmode="group",

        xaxis_title="Strike",

        yaxis_title="Open Interest",

        height=420,

        template="plotly_dark",

        hovermode="x unified",

        paper_bgcolor="#020f06",

        plot_bgcolor="#020f06",

        font=dict(
            color="#a0ffb8"
        ),

        title_font=dict(
            color="#00ff66"
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="#020f06",
            bordercolor="#00ff66",
            borderwidth=1,
            font=dict(
             color="#a0ffb8"
            ),
        ),
        xaxis=dict(
            gridcolor="rgba(0,255,102,0.08)"
        ),

        yaxis=dict(
            gridcolor="rgba(0,255,102,0.08)"
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
                "font": {
                    "color": "#00ff66"
                }
            },

            number={
                "font": {
                    "color": "#a0ffb8"
                }
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
                        "width": 3
                    },
                    "thickness": 0.75,
                    "value": pcr,
                },
            },
        )
    )

    fig.update_layout(

        height=350,

        template="plotly_dark",

        paper_bgcolor="#020f06",

        font=dict(
            color="#a0ffb8"
        ),
    )

    return fig


# =========================================================
# TOTAL CE vs PE + LIVE PRICE TREND
# =========================================================
def plot_total_oi_trend(history_df, index_name="NIFTY"):

    # =====================================================
    # EMPTY CHECK
    # =====================================================
    if history_df.empty:
        return go.Figure()

    # =====================================================
    # FIX BYTES ISSUE
    # =====================================================
    for col in history_df.columns:

        if history_df[col].dtype == object:

            history_df[col] = history_df[col].apply(
                lambda x:
                x.decode("latin-1", errors="ignore")
                if isinstance(x, bytes)
                else x
            )

    fig = go.Figure()

    # -----------------------------------------------------
    # TOTAL CE OI
    # -----------------------------------------------------
    fig.add_trace(
        go.Scatter(

            x=history_df["timestamp"],

            y=history_df["total_ce_oi"],

            mode="lines",

            name="Total CE OI",

            line=dict(
                color="red",
                width=3
            ),
        )
    )

    # -----------------------------------------------------
    # TOTAL PE OI
    # -----------------------------------------------------
    fig.add_trace(
        go.Scatter(

            x=history_df["timestamp"],

            y=history_df["total_pe_oi"],

            mode="lines",

            name="Total PE OI",

            line=dict(
                color="#00ff66",
                width=3
            ),
        )
    )

    # -----------------------------------------------------
    # LIVE INDEX PRICE
    # -----------------------------------------------------
    fig.add_trace(
        go.Scatter(

            x=history_df["timestamp"],

            y=history_df["spot"],

            mode="lines",

            name=f"{index_name} Spot",

            line=dict(
                color="#00bfff",
                width=3
            ),

            yaxis="y2",
        )
    )

    # -----------------------------------------------------
    # LAYOUT
    # -----------------------------------------------------
    fig.update_layout(

        title=f"{index_name} OI + Live Price Trend",

        xaxis_title="Time",

        yaxis=dict(
            title="Open Interest",
            gridcolor="rgba(0,255,102,0.08)"
        ),

        yaxis2=dict(
            title="Spot Price",
            overlaying="y",
            side="right",
            showgrid=False,
        ),

        height=450,

        template="plotly_dark",

        hovermode="x unified",

        paper_bgcolor="#020f06",

        plot_bgcolor="#020f06",

        font=dict(
            color="#a0ffb8"
        ),

        title_font=dict(
            color="#00ff66"
        ),

        legend=dict(

            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="#020f06",
            bordercolor="#00ff66",
            borderwidth=1,

            font=dict(
                color="#a0ffb8"
            ),
        ),

        xaxis=dict(
            gridcolor="rgba(0,255,102,0.08)"
        ),
    )

    return fig