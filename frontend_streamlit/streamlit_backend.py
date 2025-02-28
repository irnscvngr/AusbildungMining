"""
Backend operations for the streamlit app
"""

import streamlit as st
import pandas as pd

@st.cache_data
def get_vacancies():
    vacancies = pd.read_parquet('frontend_streamlit/data/AusbildungMining/vacancies_2025-02-26.parquet')
    return vacancies