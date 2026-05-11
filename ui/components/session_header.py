import streamlit as st

from core.utils import (
    format_duration_from_minutes,
    format_market_datetime,
)


def apply_session_header_css() -> None:
    st.markdown(
        """
        <style>
            .session-header {
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 10px;
                padding: 16px 18px;
                margin-bottom: 18px;
                background: rgba(255, 255, 255, 0.02);
            }

            .session-grid {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                row-gap: 10px;
                column-gap: 24px;
                align-items: start;
            }

            .h-cell {
                text-align: left;
            }

            .h-main {
                font-size: 1.15rem;
                font-weight: 800;
                line-height: 1.2;
                white-space: nowrap;
            }

            .h-sub {
                font-size: 0.95rem;
                opacity: 0.9;
                line-height: 1.25;
                white-space: nowrap;
            }

            .h-price {
                margin-left: 14px;
            }

            .h-strong {
                font-weight: 700;
            }

            .mobile-only {
                display: none;
            }

            .desktop-only {
                display: inline;
            }

            @media (max-width: 768px) {
                .session-header {
                    padding: 12px 10px;
                }

                .session-grid {
                    grid-template-columns: 1fr 1fr 1fr;
                    column-gap: 8px;
                    row-gap: 8px;
                }

                .h-main {
                    font-size: 0.82rem;
                }

                .h-sub {
                    font-size: 0.72rem;
                }

                .h-price {
                    margin-left: 6px;
                }

                .desktop-only {
                    display: none;
                }

                .mobile-only {
                    display: inline;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_session_header(account, clock, market) -> None:
    apply_session_header_css()

    asset_name = st.session_state.get("asset", "IPO")
    trader_name = st.session_state.get("username", "-")

    price = market.get_current_price()

    current_dt = format_market_datetime(market.get_current_timestamp())
    elapsed = format_duration_from_minutes(market.get_elapsed_steps())
    remaining = format_duration_from_minutes(market.get_remaining_steps())

    current_dt_short = current_dt.replace(":00 ", "")

    if clock.is_finished():
        status = "Finished"
    elif clock.is_paused:
        status = "Paused"
    else:
        status = "Running"

    html = (
        '<div class="session-header">'
        '<div class="session-grid">'

        f'<div class="h-cell h-main">'
        f'{asset_name}<span class="h-price">${price:,.2f}</span>'
        f'</div>'

        f'<div class="h-cell h-main">'
        f'<span class="desktop-only">Status: </span>{status}'
        f'</div>'

        f'<div class="h-cell h-main">'
        f'<span class="desktop-only">NYC: {current_dt}</span>'
        f'<span class="mobile-only">{current_dt_short}</span>'
        f'</div>'

        f'<div class="h-cell h-sub">'
        f'<span class="desktop-only">Trader: </span>'
        f'<span class="h-strong">{trader_name}</span>'
        f'</div>'

        f'<div class="h-cell h-sub">'
        f'<span class="desktop-only">Session Elapsed: </span>'
        f'<span class="mobile-only">Elapsed: </span>'
        f'<span class="h-strong">{elapsed}</span>'
        f'</div>'

        f'<div class="h-cell h-sub">'
        f'<span class="desktop-only">Time Left: </span>'
        f'<span class="mobile-only">Left: </span>'
        f'<span class="h-strong">{remaining}</span>'
        f'</div>'

        '</div>'
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)