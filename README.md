# IPO Drocher

IPO Drocher is a web-based IPO trading simulator built with Streamlit.

The goal of the project is to help traders practice decision-making during IPO grade periods, about one week, using historical market replay data. The simulator replays one IPO asset at accelerated speed and allows the user to buy and sell shares using a simplified long-only trading model.

---

## Project Status

Current version: `v0.08`

Core features implemented:

- Streamlit web UI
- Init screen with username, deposit, and IPO asset selection
- Historical CSV market data loading
- Event-driven trading flow
- Auto-play market replay
- Auto-pause during trade confirmation
- BUY / SELL execution
- Portfolio impact preview
- Realized and unrealized P&L
- Transaction journal
- Final session result and grade
- Mobile-first UI direction

---

## Main Concept

The simulator uses historical 1-minute IPO data and replays it as a compressed trading session.

Current time compression model:

```text
1 market minute = 1 real second
1 market hour = 1 real minute