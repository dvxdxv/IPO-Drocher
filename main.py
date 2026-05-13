import logging

import streamlit as st

from ui.pages.init import render_init_page
from ui.pages.trading import render_trading_page
from ui.pages.session_result import render_session_result_page


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force=True,
)

st.set_page_config(
    page_title="IPO Drocher",
    layout="wide",
)

# Critical: initialize page before reading it
if "page" not in st.session_state:
    st.session_state.page = "init"

if st.session_state.page == "init":
    render_init_page()

elif st.session_state.page == "trading":
    render_trading_page()

elif st.session_state.page == "session_result":
    render_session_result_page()

else:
    st.session_state.page = "init"
    st.rerun()