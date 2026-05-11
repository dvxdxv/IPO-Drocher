import plotly.graph_objects as go
import streamlit as st


def get_recent_prices(market, window: int = 60):
    if hasattr(market, "get_recent_prices"):
        return market.get_recent_prices(window)

    return [market.get_current_price()]


def render_price_chart(market, window: int = 60) -> None:
    recent_prices = get_recent_prices(market, window)

    with st.container(border=True):
        st.markdown("#### Price Chart")

        if len(recent_prices) > 1:
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    y=recent_prices,
                    mode="lines",
                    line=dict(color="#22c55e", width=3),
                )
            )

            fig.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_visible=False,
                yaxis_visible=False,
            )

            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Waiting for market ticks...")