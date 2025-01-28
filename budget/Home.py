import streamlit as  st 
import pandas as pd 
from utils import dataprep as dp
import plotly_express as px
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout='wide')
st.title('Analisi andamento prezzo MTS')
st.divider()
@st.cache_data
def up_forn():
    fornitori = pd.read_excel("https://github.com/alebelluco/ernestomeda/blob/main/budget/fornitori.xlsx?raw=True")
    codici = list(fornitori['Codice'])
    ragsoc = list(fornitori['Ragione sociale'])
    dic_forn = dict(zip(codici, ragsoc))
    return fornitori, dic_forn

fornitori, dic_forn = up_forn()
dic_mesi = {
    1:'Gennaio',
    2:'Febbraio',
    3:'Marzo',
    4:'Aprile',
    5:'Maggio',
    6:'Giugno',
    7:'Luglio',
    8:'Agosto',
    9:'Settembre',
    10:'Ottobre',
    11:'Novembre',
    12:'Dicembre'
}

path1 = st.file_uploader('Caricare entrata merce')
if not path1:
    st.stop()

@st.cache_data
def upload(path1):
    df = pd.read_excel(path1)
    return df

df = upload(path1)

# Il tracciato è diverso da quello Scavolini=======================================

df = df.rename(columns={'Imp. div. int.':'Importo DI'})

df['ragione_sociale'] = [dic_forn[codice] for codice in df.Fornitore]

#nomi_fornitori = pd.read_excel('/Users/Alessandro/Documents/AB/Clienti/ADI!/Scavolini/Budget/nomi_fornitori.xlsx')

#anno = st.radio('selezionare anno', options=[2023,2024])

#df = df[[data.year == anno for data in df['Data doc.']]]

layout = [
    "Articolo",
    "Descrizione materiale",
    "Quantità",
    "Importo DI",
    "Data doc.",
    "importo_unitario",
    "Fornitore",
    'ragione_sociale'
    ]

layout2 = [
    "Articolo",
    "Descrizione materiale",
    "Quantità",
    "Importo DI",
    "Data doc.",
    "importo_unitario",
    'mese',
    'anno'
    ]

filtro_group = [
     "Articolo",
    "Descrizione materiale",
    "mese",
    "anno"
    ]

df = dp.db_prepare(df, layout)

#--------

articoli = list(df.Articolo.unique())
deltas = pd.DataFrame(columns=['key','delta_listino'])

df = dp.iter_delta(df, layout2, filtro_group, articoli, deltas)[0] # cache_data
deltas_out = dp.iter_delta(df, layout2, filtro_group, articoli, deltas)[1]

df['saving'] = -1*df['delta_listino']*df['Quantità']


# QUI INSERIAMO IL FILTRO SUL FORNITORE

forn_select = st.multiselect('Selezionare fornitore', options = df.ragione_sociale.unique())

if len(forn_select) == 0:
    forn_select = df.ragione_sociale.unique()
    
df = df[[any(forn in check for forn in forn_select) for check in df.ragione_sociale]]


#------------------------

colonne=[
  "Materiale",
  "Fornitore",
  "Ragione sociale"
]

#------------------------

df['art-desc'] = df['Articolo'].astype(str) + ' | ' + df['Descrizione materiale'].astype(str)
selected = st.multiselect('Selezionare codice',options = df['art-desc'].unique())

if selected == []:
    andamento_prezzo = False
    selected = df['art-desc'].unique()
else:
    if len(selected)==1:
        andamento_prezzo = True # sblocca la stampa a video del grafico del prezzo
    else:
        andamento_prezzo = False
    
df = df[[any(codice in check for codice in selected) for check in df['art-desc'].astype(str)]]

st.subheader('Storico entrate merce per i codici selezionati', divider='grey')
st.dataframe(df, use_container_width=True)


# ANDAMENTO PREZZO DEL SINGOLO ARTICOLO ==================================================================
if andamento_prezzo:
    db_price = df[['anno','mese','importo_unitario']].groupby(by=['anno','mese'], as_index=False).min()
    db_price['x'] = db_price['anno'].astype(str) + '-' + db_price['mese'].astype(str)
    db_price['deltapct'] = ((db_price['importo_unitario']/db_price['importo_unitario'].iloc[0])-1)

    fig_prezzo = go.Figure()
    fig_prezzo.add_trace(go.Scatter(
        x=db_price.x, y=db_price.deltapct, mode='lines', line=dict(color='red', width=3)
        ))
    fig_prezzo.update_yaxes(tickformat=".0%")

    st.subheader('Andamento percentuale del prezzo', divider ='grey')
    sx_and, dx_and = st.columns([3,1])

    with sx_and:
        st.plotly_chart(fig_prezzo, use_container_width=True)
    
    with dx_and:
        anno_early = db_price['anno'].iloc[0]
        mese_early = db_price['mese'].iloc[0]
        delta_pct = db_price.deltapct.iloc[-1]*100

        if delta_pct > 0:
            st.subheader(':red[Aumento del {:0,.2f} % ]'.format(delta_pct))
        else:
            st.subheader(':green[Riduzione del {:0,.2f} % ]'.format(delta_pct))
        st.subheader('rispetto a  {} {}'.format(dic_mesi[mese_early], anno_early))

# RISULTATI CUMULATIVI




if st.toggle('visualizza impatto totale'):

    st.subheader('Saving totale: {:0,.0f} €'.format(df['saving'].sum()).replace(',', '.'))
    st.subheader('Spending totale: {:0,.0f} €'.format(df['Importo DI'].sum()).replace(',', '.'))

    base = df['Importo DI'].sum() + df['saving'].sum()
    delta = -1*df['saving'].sum()/base*100
    st.subheader('Impatto: {:0,.2f} %'.format(delta))

    cum = df[['anno','mese','saving']].groupby(by=['anno','mese'],as_index=False).sum()
    cum['cum'] = cum['saving'].cumsum()
    cum['x'] = cum['anno'].astype(str) + '-' + cum['mese'].astype(str)
    cum['color'] = np.where(cum['cum'] >=0 , 'verde', 'rosso')
    cum['+'] = np.where(cum['cum']>=0,cum['cum'],0)
    cum['-'] = np.where(cum['cum']<0,cum['cum'],0)

    #fig = px.line(cum, x='x', y="cum")
    #fig = px.area(cum, x='x', y="cum", color='color', color_discrete_map={'verde':'green', 'rosso':'red'})
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cum.x, y=cum['+'], fill='tozeroy', mode='none',fillcolor='green', opacity = 0.5
    ))

    fig.add_trace(go.Scatter(
        x=cum.x, y=cum['-'], fill='tozeroy', mode='none',fillcolor='red', opacity = 0.5
    ))

    fig.update_layout(showlegend=False)

    #, 'tozeroy', 'tozerox', 'tonexty', 'tonextx', 'toself', 'tonext'
    sx, dx = st.columns([5,2])
    with sx:
        st.plotly_chart(fig, use_container_width=True)
    with dx:
        st.dataframe(cum[['anno','mese','saving','cum']], width=500)
else:

    anno_bgt = st.radio('Selezionare anno', options = [2021,2022,2023,2024,2025])
    df_bgt = df[df.anno <= anno_bgt].copy() # così non prende anni dopo l'anno di analisi
    df_bgt['price_ref'] = None

    for codice in df_bgt.Articolo.unique():
        try:
            price_ref = df_bgt['importo_unitario'][(df_bgt.Articolo == codice) & (df_bgt.anno != anno_bgt)].iloc[-1]
        except:
            price_ref = df_bgt['importo_unitario'][(df_bgt.Articolo == codice) & (df_bgt.anno == anno_bgt)].iloc[0]
        df_bgt['price_ref'][(df_bgt.Articolo == codice) & (df_bgt.anno == anno_bgt)] = price_ref

    df_bgt = df_bgt[df_bgt.anno == anno_bgt]
    if len(df_bgt)==0:
        st.warning('Nessuna entrata merce per i filtri selezionati')
        st.stop()


    df_bgt['delta_bgt'] = df_bgt['importo_unitario'] - df_bgt['price_ref']
    df_bgt['saving_bgt'] = -1 * df_bgt['delta_bgt'] * df_bgt['Quantità']

    st.write(df_bgt)

    cum_bgt = df_bgt[['anno','mese','saving_bgt']].groupby(by=['anno','mese'],as_index=False).sum()
    cum_bgt['cum'] = cum_bgt['saving_bgt'].cumsum()
    cum_bgt['x'] = cum_bgt['anno'].astype(str) + '-' + cum_bgt['mese'].astype(str)
    cum_bgt['color'] = np.where(cum_bgt['cum'] >=0 , 'verde', 'rosso')
    cum_bgt['+'] = np.where(cum_bgt['cum']>=0,cum_bgt['cum'],0)
    cum_bgt['-'] = np.where(cum_bgt['cum']<0,cum_bgt['cum'],0)

    fig_bgt = go.Figure()
    fig_bgt.add_trace(go.Scatter(
        x=cum_bgt.x, y=cum_bgt['+'], fill='tozeroy', mode='none',fillcolor='green', opacity = 0.5
    ))

    fig_bgt.add_trace(go.Scatter(
        x=cum_bgt.x, y=cum_bgt['-'], fill='tozeroy', mode='none',fillcolor='red', opacity = 0.5
    ))

    fig_bgt.update_layout(showlegend=False)

    #, 'tozeroy', 'tozerox', 'tonexty', 'tonextx', 'toself', 'tonext'
    sx_bgt, dx_bgt = st.columns([5,1])
    with sx_bgt:
        st.plotly_chart(fig_bgt, use_container_width=True)
    with dx_bgt:
        #st.dataframe(cum_bgt[['anno','mese','saving_bgt','cum']], width=500)
        st.subheader('Saving totale: {:0,.0f} €'.format(cum_bgt.cum.iloc[-1]).replace(',', '.'))
        st.subheader('Acquistato: {:0,.0f} €'.format(df_bgt['Importo DI'].sum()).replace(',', '.'))

    #st.write(df_bgt)
#dp.scarica_excel(df,'output MTS.xlsx')

# Bisogna debuggare con un file entrata merce ridotto


