import streamlit as st

from adapters.file_storage_adapter import FileStorageAdapter
from ui.state import init_engine

DATA_FOLDER = "data/"  

def apply_custom_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
                color: #f5f5f5;
            }

            .glass-card {
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 2.5rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
            }

            .app-title {
                font-size: 3.2rem;
                font-weight: 800;
                text-align: center;
                background: linear-gradient(90deg, #00ff9d, #00d4ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.25rem;
            }

            .app-subtitle {
                text-align: center;
                color: rgba(255, 255, 255, 0.65);
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
            placeholder="Alex",
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
            format_func=lambda file_name: file_name.replace(".csv", ""),
        )

        if st.button("Start Trading", type="primary", width="stretch"):
            if not username.strip():
                st.error("Enter username")
                st.stop()

            file_path = storage.get_file_path(asset)

            init_engine(deposit, file_path)

            st.session_state.username = username.strip()
            st.session_state.asset = asset.replace(".csv", "")
            st.session_state.page = "trading"

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)