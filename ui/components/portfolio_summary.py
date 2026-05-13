import streamlit as st


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _format_signed_money(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def render_portfolio_summary(
    account,
    price: float,
    equity: float,
    unrealized_pnl: float,
) -> None:
    """
    Render compact portfolio summary.

    This is position-focused, not account-focused.
    """

    st.subheader("Portfolio")

    position_value = account.shares * price
    position_pct = (position_value / equity) * 100 if equity > 0 else 0

    with st.container(border=True):
        if account.shares <= 0:
            st.markdown("**No open position**")
            st.caption("Buy shares to start building a position.")
            st.write(f"Cash: **{_format_money(account.cash)}**")
            return

        st.markdown(
            f"**{account.shares} shares @ avg {_format_money(account.avg_price)}**"
        )

        st.write(f"Current Price: **{_format_money(price)}**")
        st.write(f"Position Value: **{_format_money(position_value)}**")
        st.write(f"Position Size: **{position_pct:.1f}%**")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.caption("Unrealized P&L")
            st.markdown(f"**{_format_signed_money(unrealized_pnl)}**")

        with col2:
            st.caption("Realized P&L")
            st.markdown(f"**{_format_signed_money(account.realized_pnl)}**")