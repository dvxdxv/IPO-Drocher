import streamlit as st


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _format_signed_money(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def _metric_cell(label: str, value: str) -> None:
    st.caption(label)
    st.markdown(f"### {value}")


def render_account_metrics(account, price: float) -> dict:
    """
    Render IPO Trader Dashboard.

    This dashboard contains only decision-useful trading data.
    Session-level metrics like ROI, grade, win rate should live on Session Result page.
    """

    equity = account.get_equity(price)
    unrealized_pnl = account.get_unrealized_pnl(price)
    total_pnl = account.realized_pnl + unrealized_pnl
    position_value = account.shares * price

    avg_price_text = _format_money(account.avg_price) if account.shares > 0 else "—"

    with st.container(border=True):
        st.markdown("### IPO Trader Dashboard")

        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)

        with row1_col1:
            _metric_cell("Price", _format_money(price))

        with row1_col2:
            _metric_cell("Avg Price", avg_price_text)

        with row1_col3:
            _metric_cell("Shares", f"{account.shares}")

        with row1_col4:
            _metric_cell("Total P&L", _format_signed_money(total_pnl))

        st.divider()

        row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

        with row2_col1:
            _metric_cell("Cash", _format_money(account.cash))

        with row2_col2:
            _metric_cell("Position Value", _format_money(position_value))

        with row2_col3:
            _metric_cell("Unrealized P&L", _format_signed_money(unrealized_pnl))

        with row2_col4:
            _metric_cell("Realized P&L", _format_signed_money(account.realized_pnl))

    return {
        "equity": equity,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": total_pnl,
        "position_value": position_value,
    }