import streamlit as st

from ui.pages.init import render_init_page
from ui.pages.trading import render_trading_page

st.set_page_config(
    page_title="IPO Drocher",
    layout="wide"
)

if "page" not in st.session_state:
    st.session_state.page = "init"

if st.session_state.page == "init":
    render_init_page()
elif st.session_state.page == "trading":
    render_trading_page()