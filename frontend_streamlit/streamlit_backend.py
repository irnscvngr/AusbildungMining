"""
Backend operations for the streamlit app
"""
import json
from urllib.request import urlopen
import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def get_vacancies():
    """
    Load the "vacancies" data, containing detailed information about
    vacancies found on Ausbildung.de
    """
    vacancies = pd.read_parquet('frontend_streamlit/data/AusbildungMining/vacancies_2025-02-26.parquet')
    return vacancies

@st.cache_data
def get_official_stats():
    """
    Load the "official stats" data, containing general numbers
    on Ausbildung.de
    """
    official_stats_df = pd.read_csv('frontend_streamlit/data/AusbildungMining/official_stats_2025-02-26.csv')
    return official_stats_df

# Landkreis-geoJSON:
with open("frontend_streamlit/data/maps/landkreise_simplify200.geojson",'r',encoding='utf-8') as response:
    counties = json.load(response)

# Bundesland-geoJSON
with urlopen('https://github.com/isellsoap/deutschlandGeoJSON/raw/refs/heads/main/2_bundeslaender/3_mittel.geo.json') as response:
    states = json.load(response)

with open("frontend_streamlit/data/maps/bundesland_id-to-state.json",'r',encoding='utf-8') as response:
    id_to_state = json.load(response)

state_to_id = {}
for key,value in id_to_state.items():
    state_to_id[value] = key

with open("frontend_streamlit/data/maps/ars-to-state.json",'r',encoding='utf-8') as response:
    ars_to_state = json.load(response)

@st.cache_data
def add_geoinfo_to_vacancies(vacancies:pd.DataFrame):
    """
    Takes a vacancies-dataframe and adds state (Bundesland) and geoJSON-id
    to each vacancy.
    """
    # Get Bundesland name fromm ARS
    vacancies['Bundesland'] = (vacancies['Amtlicher Regionalschlüssel']
                               .str[:2]
                               .apply(lambda x: ars_to_state[x]))
    # Get geo id from Bundesland name
    vacancies['id'] = vacancies['Bundesland'].apply(lambda x: state_to_id[x])

    return vacancies

def plot_map(vacancies,prof_select):
    """
    Plots a map of vacancies in German states
    """
    fig = px.choropleth_map(data_frame=vacancies,
                        geojson=states,
                        locations='id',
                        color='Plätze',
                        color_continuous_scale="Viridis",
                        range_color=(0, vacancies['Plätze'].max()),
                        map_style="carto-positron",
                        # map_style='white-bg',
                        zoom=4.8,
                        center = {"lat": 51.2, "lon": 9.9167},
                        opacity=0.5,
                        hover_name='Bundesland',
                        hover_data={'id':False,
                                    'Plätze':True},
                        )

    fig.update_layout(title=f"Vakanzen für {prof_select} auf Ausbildung.de",
                  margin={"r":0,"t":60,"l":0,"b":0},
                  width=800,
                  height=600,
                  )

    return fig
