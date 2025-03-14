"""
Webapp to visualize data
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import streamlit_backend as stb

st.set_page_config(page_title="AusbildungMining")

st.title("AusbildungMining")

"""
Aufzeichnung und Auswertung von Arbeits- und Ausbildungsvakanzen in Deutschland.
"""


tab1, tab2, tab3, tab4 = st.tabs(["Arbeit", "Ausbildung", "Sonstiges","About"])

with tab1:
    tab1_sub1, tab1_sub2 = st.tabs(['Deutschlandweit','Bundesland'])

    with tab1_sub2:

        state_names = pd.Series(stb.get_state_names()).sort_values()

        if 'state_select' not in st.session_state:
            st.session_state['state_select'] = state_names.sample(1).values[0]

        shuffle = st.button(label='Zufälliges Bundesland',
                            key='state_shuffle')

        if shuffle:
            st.session_state['state_select'] = state_names.sample(1).values[0]

        state_select = st.selectbox(label='Bundesland auswählen',
                                options=state_names,
                                key='state_select')

        parameters = {'Branchen':'branche',
                    'Berufe':'beruf',
                    'Arbeitgeber':'arbeitgeber',
                    'Arbeitszeiten':'arbeitszeit',
                    'Befristungen':'befristung'}

        parameter_select = st.selectbox(label='Parameter auswählen',
                                        options=parameters.keys(),
                                        key='parameter_select')

        param = parameters[parameter_select]
        ba_df = stb.get_ba_values(param)
        
        xmax = 4500

        f"""
        ### Top 10 {parameter_select} in {state_select}
        *(nach aktuellen Vakanzen)*
        """
        if param=='branche':
            incl_tempwork= st.checkbox('Mit Zeitarbeit',
                                    key='incl_tempwork')    
            xmax = 45000

            if not incl_tempwork:
                sel = ba_df['branche']=="Arbeitnehmerueberlassung, Zeitarbeit"
                ba_df = ba_df[~sel]
                xmax = 15000

        # Shorten the names so they fit for plotting
        ba_df[param + '_short'] = stb.shorten_strings(ba_df[param].copy(),lmax=35)
                
        ba_df_plot = stb.ba_get_top10_values(ba_df,state_select)
        
        fig = stb.ba_plot_state_top10(ba_df_plot,xmax)
        
        # fig = px.pie(ba_df_plot.sort_values(param),
        #              values='stellen',
        #              names=param)

        st.plotly_chart(fig)

        f"""
        ---
        
        #### Zeitlicher Verlauf der {parameter_select}
        """

        ba_df = ba_df[ba_df[param].isin(ba_df_plot[param])]
        
        ba_df = (ba_df
                .groupby([param,'timestamp'],as_index=False)
                .agg({param:'first','stellen':'sum'})
                .set_index('timestamp'))
        
        fig = px.line(ba_df,
                    y='stellen',
                    color=param)
        
        fig.update_layout(xaxis_title='',
                          yaxis_title='Freie Stellen',
                          margin={"r":0,"t":15,"l":0,"b":0},
                          height=500,
                          legend=dict(x=0.5,
                                      y=-0.15,
                                      title='',
                                      orientation='h',
                                      xanchor='center',
                                      yanchor='top')
                        )
        
        st.plotly_chart(fig)
        
        """
        Quelle: [Bundesagentur für Arbeit](https://www.arbeitsagentur.de/jobsuche/)
        """
    
    with tab1_sub1:
        if 'parameter_select2' not in st.session_state:
            st.session_state['parameter_select2'] = st.session_state['parameter_select']
        
        parameter_select2 = st.selectbox(label='Parameter auswählen',
                                        options=parameters.keys(),
                                        key='parameter_select2')
        
        param2 = parameters[parameter_select2]

        ba_df = stb.get_ba_values(param2)

        available_params = pd.Series(ba_df[param2].unique()).sort_values()

        shuffle_text = {'branche':'Zufällige Branche',
                        'arbeitgeber':'Zufälliger Arbeitgeber',
                        'arbeitszeit':'Zufällige Arbeitszeit',
                        'beruf':'Zufälliger Beruf',
                        'befristung':'Zufällige Befristung'}

        shuffle = st.button(label=shuffle_text[param2],
                            key='param_shuffle')

        if shuffle:
            st.session_state['parameter_select2_sub'] = available_params.sample(1).values[0]

        parameter_select2_sub = st.selectbox(label=f"Aus {parameter_select2} auswählen",
                                             options=available_params,
                                             key='parameter_select2_sub')

        ba_df_daily = ba_df[ba_df[param2]==parameter_select2_sub].groupby(['timestamp','bundesland'],as_index=False).sum()

        ba_df_daily_total = ba_df_daily.set_index('timestamp').resample('D')['stellen'].sum().dropna()

        f"""
        ### Stellenentwicklung
        {parameter_select2_sub}
        """

        fig = px.line(ba_df_daily_total.iloc[1:])

        fig.update_layout(xaxis_title='',
                          yaxis_title='',
                          showlegend=False,
                          height=400)

        st.plotly_chart(fig)


        f"""
        ---
        ### Stellenverteilung in Deutschland
        {parameter_select2_sub}
        """

        # shuffle = st.button(label=shuffle_text[param2],
        #                     key='param_shuffle2')

        # if shuffle:
        #     st.session_state['parameter_select2_sub'] = available_params.sample(1).values[0]


        ba_df = (ba_df_daily[ba_df_daily['timestamp'] == ba_df_daily['timestamp'].unique()[-1]]
                 .loc[:,['bundesland','stellen']])

        
        fig = stb.plot_map_ba(ba_df)
        
        st.plotly_chart(fig)


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

    """
    ### Vakanzen auf Ausbildung.de
    """
    
    # PLOT VALUES OVER TIME
    df_temp = (vacancies
            .groupby(['Bundesland','timestamp'],as_index=False)
            .agg({'Plätze':'sum','Bundesland':'first'})
            .set_index('timestamp'))

    fig = px.line(df_temp,
                y='Plätze',
                color='Bundesland')

    fig.update_layout(margin={"r":0,"t":15,"l":0,"b":0},
                    xaxis_title='',
                    yaxis_title='',
                    height=450,
                    legend=dict(
                          title='',
                          orientation='h',
                          yanchor='top',
                          y=-0.15,
                          )
                    )

    st.plotly_chart(fig)

    """
    ---
    
    #### Regionale Verteilung
    """

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

    fig = stb.plot_map(vacancies,prof_select)    

    st.plotly_chart(fig)

    """
    ---
    
    #### Zeitlicher Verlauf von Vakanztypen
    """

    official_stats_df = stb.get_official_stats()

    official_stats_df['timestamp'] = pd.to_datetime(official_stats_df['timestamp'])

    fig = px.line(official_stats_df.set_index('timestamp'))

    fig.update_layout(xaxis_title='',
                      yaxis_title='',
                      margin={"r":0,"t":15,"l":0,"b":0},
                      legend=dict(
                          title='',
                          orientation='h',
                          yanchor='top',
                          y=-0.2,
                          ))

    st.plotly_chart(fig)


with tab3:
    st.write('Under construction...')

with tab4:
    st.write('Under construction...')

"""
---
"""

st.html("""
        <style>
        .colored-svg {
            filter: brightness(300%);
            }
        </style>
        <div style="text-align:center">
        Made by:<br>
        <a href="https://www.linkedin.com/in/patrickhausmann">Patrick Hausmann</a><br><br>
        <a href="https://www.github.com/irnscvngr"><img class="colored-svg",
        src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Octicons-mark-github.svg/600px-Octicons-mark-github.svg.png?20180806170715",
        width=50
        </img></a>
        </div>
        """)
