"""
Webapp to visualize data
"""
import pandas as pd
import plotly.express as px
import streamlit as st

import streamlit_backend as stb

st.set_page_config(page_title="AusbildungMining")

st.title("AusbildungMining")

"""
Interactive data visualization web app.
"""


tab1, tab2, tab3 = st.tabs(["Arbeit", "Ausbildung", "Sonstiges"])

with tab1:
    st.write('Under construction...')

with tab2:

    vacancies = stb.get_vacancies()

    professions = pd.Series(vacancies['Beruf'].unique()).sort_values()

    timestamps = pd.Series(vacancies['timestamp'].unique())

    # PROFESSION SELECT
    if 'prof_select' not in st.session_state:
        st.session_state['prof_select'] = professions.sample(1).values[0]

    shuffle = st.button(label='Zufälliger Beruf',
                        key='prof_shuffle')

    if shuffle:
        st.session_state['prof_select'] = professions.sample(1).values[0]

    prof_select = st.selectbox(label='Ausbildungsberuf auswählen',
                            options=professions,
                            key='prof_select')


    vacancies = vacancies[vacancies['Beruf']==prof_select]

    vacancies = stb.add_geoinfo_to_vacancies(vacancies)

    # PLOT VALUES OVER TIME
    df_temp = (vacancies
            .groupby(['Bundesland','timestamp'],as_index=False)
            .agg({'Plätze':'sum','Bundesland':'first'})
            .set_index('timestamp'))

    fig = px.line(df_temp,
                y='Plätze',
                color='Bundesland')

    fig.update_layout(margin={"r":0,"t":60,"l":0,"b":0},
                    xaxis_title='',
                    height=500)

    st.plotly_chart(fig)

    # TIMESTAMP SELECT
    if 'date_select' not in st.session_state:
        st.session_state['date_select'] = timestamps.values[-1]

    date_select = st.select_slider(label='Datum auswählen',
                                options=timestamps,
                                key='date_select')

    vacancies = vacancies[vacancies['timestamp']==date_select]

    vacancies = (vacancies
                .groupby('Bundesland',as_index=False)
                .agg({'Plätze':'sum',
                    'Bundesland':'first',
                    'id':'first'}))


    fig = stb.plot_map(vacancies)

    st.plotly_chart(fig)


    official_stats_df = stb.get_official_stats()

    official_stats_df['timestamp'] = pd.to_datetime(official_stats_df['timestamp'])

    fig = px.line(official_stats_df.set_index('timestamp'))
    st.plotly_chart(fig)


with tab3:
    st.write('Under construction...')
