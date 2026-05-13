import streamlit as st


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _format_signed_money(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def _cell(label: str, value: str) -> str:
    return (
        '<div class="dashboard-cell">'
        f'<div class="dashboard-cell-label">{label}</div>'
        f'<div class="dashboard-cell-value">{value}</div>'
        '</div>'
    )


def render_account_metrics(account, price: float) -> dict:
    """
    Render compact IPO Trader Dashboard.

    Desktop:
    - 4 columns

    Mobile:
    - 2 columns via CSS grid
    """

    equity = account.get_equity(price)
    unrealized_pnl = account.get_unrealized_pnl(price)
    total_pnl = account.realized_pnl + unrealized_pnl
    position_value = account.shares * price

    avg_price_text = _format_money(account.avg_price) if account.shares > 0 else "—"

    dashboard_html = (
        '<div class="trader-dashboard">'
        '<div class="dashboard-title">IPO Trader Dashboard</div>'
        '<div class="dashboard-grid">'
        + _cell("Price", _format_money(price))
        + _cell("Avg Price", avg_price_text)
        + _cell("Shares", f"{account.shares}")
        + _cell("Total P&L", _format_signed_money(total_pnl))
        + _cell("Cash", _format_money(account.cash))
        + _cell("Position Value", _format_money(position_value))
        + _cell("Unrealized P&L", _format_signed_money(unrealized_pnl))
        + _cell("Realized P&L", _format_signed_money(account.realized_pnl))
        + '</div>'
        '</div>'
    )

    st.html(dashboard_html)

    return {
        "equity": equity,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": total_pnl,
        "position_value": position_value,
    }