import streamlit as st

from adapters.file_storage_adapter import FileStorageAdapter
from ui.state import init_engine

DATA_FOLDER = "data/"  

def extract_ticker(file_name: str) -> str:
    return file_name.split("_", 1)[0]

def apply_custom_css() -> None:
    st.markdown(
        """
        <style>
            .app-title {
                font-size: 2.8rem;
                font-weight: 800;
                text-align: center;
                margin-bottom: 0.25rem;
            }

            .app-subtitle {
                text-align: center;
                opacity: 0.75;
                margin-bottom: 2rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
def render_init_page() -> None:
    apply_custom_css()

    st.markdown('<div class="app-title">IPO Drocher</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">IPO trading simulator for high-pressure market replay</div>',
        unsafe_allow_html=True,
    )

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        username = st.text_input(
            "Username",
            placeholder="Enter your trader name..",
        )

        deposit = st.number_input(
            "Deposit ($)",
            min_value=100,
            max_value=100000,
            value=10000,
            step=1,
        )

        storage = FileStorageAdapter(DATA_FOLDER)
        files = storage.list_csv_files()

        if not files:
            st.error(f"No CSV files found in {DATA_FOLDER}")
            st.stop()

        asset = st.selectbox(
            "Choose IPO Asset",
            files,
            format_func=extract_ticker,
        )

        if st.button("Start Trading", type="primary", width="stretch"):
            if not username.strip():
                st.error("Enter username")
                st.stop()

            file_path = storage.get_file_path(asset)

            init_engine(deposit, file_path)

            st.session_state.username = username.strip()
            st.session_state.asset = extract_ticker(asset)
            st.session_state.page = "trading"

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)