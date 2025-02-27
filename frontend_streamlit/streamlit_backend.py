"""
Backend operations for the streamlit app
"""

import streamlit as st
import pandas as pd

@st.cache_data
def get_vacancies():
    vacancies = pd.read_csv('data/AusbildungMining/vacancies_2025-02-26.csv')
    return vacancies