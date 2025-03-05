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

def get_state_names():
    """
    Returns list of german state names
    """
    with open("frontend_streamlit/data/maps/ars-to-state.json",encoding='utf-8') as f:
        state_names = json.load(f)
    return list(state_names.values())

@st.cache_data
def get_ba_values(param='branche'):
    if param=='branche':
        filename = "frontend_streamlit/data/AusbildungMining/ArbeitsagenturMining_Arbeit_Branche_2025-03-04 (22_33_49).csv"
    if param=='beruf':
        filename = "frontend_streamlit/data/AusbildungMining/ArbeitsagenturMining_Arbeit_Beruf_2025-03-04 (22_25_31).csv"
    if param=='arbeitgeber':
        filename = "frontend_streamlit/data/AusbildungMining/ArbeitsagenturMining_Arbeit_Arbeitgeber_2025-03-04 (22_35_28).csv"
    if param=='arbeitszeit':
        filename = "frontend_streamlit/data/AusbildungMining/ArbeitsagenturMining_Arbeit_Arbeitszeit_2025-03-04 (22_36_51).csv"
    if param=='befristung':
        filename = "frontend_streamlit/data/AusbildungMining/ArbeitsagenturMining_Arbeit_Befristung_2025-03-04 (22_38_45).csv"
        
    ba_df = pd.read_csv(filename,                                                                                                                                            
                        header=None,
                        names= ['id','timestamp','bundesland',param,'stellen']
                        )
    return ba_df

def ba_get_top10_values(ba_df,state_select):
    timestamps = list(ba_df['timestamp'].unique())

    ba_df = ba_df[ba_df['bundesland']==state_select]

    ba_df = ba_df[ba_df['timestamp']==timestamps[-1]]

    ba_df = ba_df.drop(columns=['id','timestamp','bundesland'])

    ba_df = ba_df.nlargest(10,'stellen').reset_index(drop=True)
    return ba_df
    

def ba_plot_state_top10(ba_df,xmax):
    
    col = ba_df.columns[0]

    fig = px.bar(ba_df.sort_values('stellen'),
                 x='stellen',
                 y=col,
                #  range_x=[0,xmax]
                 )

    fig.update_layout(xaxis_title='',
                      yaxis_title='',
                      margin={"r":0,"t":15,"l":0,"b":0},
                      height=300)
    
    return fig
