import streamlit as st
import pandas as pd


st.set_page_config(page_title="DataFrame Display", layout="wide")

sx_head, dx_head = st.columns([8, 1])


dx_head.image('logoEM.png?raw=True', width=300)
sx_head.title('ODA con vendita materiale')

st.divider()

LAYOUT = [
    'Materiale',
    'Descrizione doc.',
    'UM',
    'Quantità',
    'Data consegna',
    'Intestatario',
    'Numero OdV',
    'Pos. OdV',
    'C_ALTE-Altezza effettiva',
    'C_LARGHE-Larghezza effettiva',
    'C_NOTATESTO1-Nota testo 1',
    'C_NOTATESTO2-Nota testo 2',
    'C_NOTATESTO3-Nota testo 3'
]

PATH = st.file_uploader("Caricare ZSD67", width=500)
st.info('Il file deve essere in formato Excel esattamente come esce da SAP', width=500)
if PATH is not None:
    df = pd.read_excel(PATH)
    #st.dataframe(df)
else:
    st.warning("Caricare un file Excel per visualizzare il DataFrame.")
    st.stop()

# Verifica quali colonne del LAYOUT sono presenti nel dataframe
colonne_opzionali = [
    'C_ALTE-Altezza effettiva',
    'C_LARGHE-Larghezza effettiva',
    'C_NOTATESTO1-Nota testo 1',
    'C_NOTATESTO2-Nota testo 2',
    'C_NOTATESTO3-Nota testo 3'
]

colonne_mancanti = [col for col in colonne_opzionali if col not in df.columns]
if colonne_mancanti:
    st.info(f"Colonne opzionali non presenti nel file: {', '.join(colonne_mancanti)}")

# Usa solo le colonne effettivamente presenti
LAYOUT_EFFETTIVO = [col for col in LAYOUT if col in df.columns]

# df = filtra se materiale Inizia con 311 o con 77 
filtered_df = df[df['Materiale'].astype(str).str.startswith(('311', '77'))]
#st.dataframe(filtered_df[LAYOUT], width='content')

#formatta data consegna in formato gg/mm/aaaa
filtered_df['Data consegna'] = pd.to_datetime(filtered_df['Data consegna'], errors='coerce').dt.strftime('%d/%m/%Y')





#stampa un df per ogni fornitore (intestatario) con i dati filtrati ordina i singoli df per Numero OdV e Pos. OdV e colora le righe in base all OdV (colore diverso per ogni OdV)


# evita il rosso per il colore di sfondo, usa invece una palette di colori pastello


for fornitore, group in filtered_df.groupby('Intestatario'):
    st.subheader(f"Fornitore: {fornitore}")
    group_sorted = group.sort_values(by=['Numero OdV', 'Pos. OdV'])
    # Colora le righe in base al Numero OdV con colori pastello (evitando il rosso)
    unique_odv = group_sorted['Numero OdV'].unique()
    # Usa tonalità da 60° a 300° (giallo -> verde -> ciano -> blu -> magenta) evitando il rosso (0-60, 300-360)
    color_map = {odv: f"hsl({60 + (i * 240 / len(unique_odv))}, 50%, 88%)" for i, odv in enumerate(unique_odv)}
    
    def color_row(row):
        return [f'background-color: {color_map[row["Numero OdV"]]}'] * len(row)
    
    styled_df = group_sorted[LAYOUT_EFFETTIVO].style.apply(color_row, axis=1)
    st.dataframe(styled_df, width='stretch')







