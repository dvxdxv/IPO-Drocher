import streamlit as st
from app import create_engine

def init_engine(deposit, file_path):
    st.session_state.engine = create_engine(deposit, file_path)

def get_engine():
    return st.session_state.get("engine")