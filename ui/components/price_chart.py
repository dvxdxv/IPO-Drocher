import plotly.graph_objects as go
import streamlit as st

def get_recent_prices(market, window: int = 60):
    if hasattr(market, "get_recent_prices"):
        return market.get_recent_prices(window)

    return [market.get_current_price()]


def render_price_chart(
    market,
    window: int = 60,
    height: int = 200,
    interactive: bool = False,
) -> None:
    """
    Render compact price chart.

    Mobile-first defaults:
    - lower height
    - Plotly toolbar disabled
    - chart interactions disabled
    """

    recent_prices = get_recent_prices(market, window)

    with st.container(border=True):
        st.markdown("#### Price Chart")

        if len(recent_prices) <= 1:
            st.info("Waiting for market ticks...")
            return

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=recent_prices,
                mode="lines",
                line=dict(color="#22c55e", width=3),
                hoverinfo="skip" if not interactive else "y",
            )
        )

        fig.update_layout(
            height=height,
            margin=dict(l=4, r=4, t=4, b=4),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                visible=False,
                fixedrange=True,
            ),
            yaxis=dict(
                visible=False,
                fixedrange=True,
            ),
            showlegend=False,
        )

        config = {
            "displayModeBar": interactive,
            "scrollZoom": False,
            "doubleClick": False,
            "staticPlot": not interactive,
            "responsive": True,
        }

        st.plotly_chart(
            fig,
            width="stretch",
            config=config,
        )