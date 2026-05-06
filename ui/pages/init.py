import streamlit as st

from adapters.data.file_storage_adapter import FileStorageAdapter
from ui.state import init_engine


def render_init_page():
    st.title("IPO Drocher")

    username = st.text_input("Username")

    deposit = st.number_input(
        "Deposit ($)",
        min_value=100,
        max_value=100000,
        value=10000,
        step=1
    )

    storage = FileStorageAdapter("adapters/data/")
    files = storage.list_csv_files()

    if not files:
        st.error("No CSV files found in data/ folder")
        st.stop()

    asset = st.selectbox("Choose IPO Asset", files)

    if st.button("Start Trading"):
        if not username.strip():
            st.error("Enter username")
            st.stop()

        file_path = storage.get_file_path(asset)

        init_engine(deposit, file_path)

        st.session_state.username = username.strip()
        st.session_state.asset = asset
        st.session_state.page = "trading"

        st.rerun()