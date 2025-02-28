"""
Webapp to visualize data
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_backend import get_vacancies

st.set_page_config(page_title="AusbildungMining")

st.title("AusbildungMining")

"""
Interactive data visualization web app.
"""


vacancies = get_vacancies()

vacancies_professions = (vacancies
                         .groupby(['timestamp','Beruf'],as_index=False)
                         .agg({'Beruf':'first','Plätze':'sum'})
                         .set_index('timestamp'))

professions = pd.Series(vacancies_professions['Beruf'].unique())

professions_select = st.multiselect(label='Berufe auswählen',
                                    default=professions.sample(10),
                                    key='profselector',
                                    max_selections = 10,
                                    options=professions)

vacancies_select = vacancies_professions[vacancies_professions['Beruf'].isin(professions_select)]

fig = px.line(vacancies_select,
              color='Beruf')
st.plotly_chart(fig)


official_stats_df = pd.read_csv('frontend_streamlit/data/AusbildungMining/official_stats_2025-02-26.csv')

official_stats_df['timestamp'] = pd.to_datetime(official_stats_df['timestamp'])

fig = px.line(official_stats_df.set_index('timestamp'))
st.plotly_chart(fig)
