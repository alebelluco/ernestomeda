# raggruppamento utility
# 26-06-2024

import pandas as pd 
import streamlit as st 
from io import BytesIO
import xlsxwriter
import zipfile

#@st.cache_data

@st.cache_data
def db_prepare(df, layout):
    df['importo_unitario'] = df['Importo DI']/df['Quantità']
    df = df[df['importo_unitario'] > 0.011]
    df = df[layout]
    df['anno'] = [data.year for data in df['Data doc.']]
    df['mese'] = [data.month for data in df['Data doc.']]
    df['key'] = None
    for i in range(len(df)):
        df['key'].iloc[i] = str(df['Articolo'].iloc[i])  + '--' + str(df['anno'].iloc[i])+ '--' + str(df['mese'].iloc[i])
    return df

def calcolo_delta_early(df, articolo, lay, filtro):
    df = df[df.Articolo == articolo] # tutte le entrate merce per l'articolo
    df['anno'] = [data.year for data in df['Data doc.']]
    df['mese'] = [data.month for data in df['Data doc.']] 
    df['anno'] = [data.year for data in df['Data doc.']] 
    out = df[lay].groupby(by=filtro, as_index=False).min() # prendo il prezzo minore di ogni mese
    #out_rif = out[[data.year == anno-1 for data in out['Data doc.']]] # filtro l'anno precedente per calcolare il prezzo di riferimento
    out_rif = out

    '''

    try:
        riferimento = out_rif['importo_unitario'].iloc[-1] # il prezzo di riferimento è l'ultima riga 
        deep = out_rif # ok
        testo = 'Rif 31/12/2023'  
    except:
        out = df[lay].groupby(by=filtro, as_index=False).min()
        out_rif2 = out[[data.year == anno for data in out['Data doc.']]]
        riferimento = out_rif2['importo_unitario'].iloc[0]
        deep = out_rif2
        testo = 'Rif 1/1/2024'
    '''

    anno_min = out_rif.anno.min()

    mese_min = out_rif['mese'][out_rif.anno == anno_min].min()
    riferimento = out_rif['importo_unitario'][(out_rif['anno']==anno_min) & (out_rif['mese']==mese_min)].iloc[0]

    #riferimento = out_rif['importo_unitario'].iloc[-1] # il prezzo di riferimento è l'entrata merce più vecchia

    testo='testo'
    deep='deep'

    out['delta_listino'] = out["importo_unitario"] - riferimento #out["importo_unitario"].shift(1)
    out['key'] = None
    out['key'].iloc[0] = str(out['Articolo'].iloc[0]) + '--' + str(out['anno'].iloc[0])+ '--' + str(out['mese'].iloc[0])
    for i in range(1,len(out)):
        out['key'].iloc[i] = str(out['Articolo'].iloc[i])  + '--' + str(out['anno'].iloc[i]) + '--' + str(out['mese'].iloc[i])
    
    out = out.sort_values(by=['Articolo','anno','mese'])
    out = out.reset_index(drop=True)

    return out[['key','delta_listino']], deep, (riferimento, testo)

@st.cache_data
def iter_delta(df, lay, filtro, articoli, deltas):
    for articolo in articoli:
        out = calcolo_delta_early(df,articolo,lay,filtro)[0]
        deltas = pd.concat([deltas,out])
    df = df.merge(deltas, how='left', left_on='key',right_on='key')
    return df, deltas

@st.cache_data
def filtra_fornitore(df, fornitori, scelta):
    df = df.merge(fornitori, how='left', left_on='Fornitore', right_on='fornitore')
    df = df[[any(fornitore in check for fornitore in scelta) for check in df['Ragione sociale'].astype(str)]]
    return df

def unisci_colonne(df, colonne, new):
    new_col = [] 
    for col in colonne:
        try:
            df[col]=df[col].fillna('')
            new_col.append(col)
        except:
            pass
  
    df[new] = None
    for i in range(len(df)):
        key = []
        for col in new_col:
            key.append(str(df[col].iloc[i]))
        df[new].iloc[i] = ''.join(list(set(key))) #list-set-list serve per eliminare eventuali valori doppi popolati su due colonne

    return df

def crea_chiave(df, dic_key):
    df['key']=None
    for i in range(len(df)):
        fornitore = df['Intestatario'].iloc[i]
        colonne = dic_key[fornitore]
        key = []
        for col in colonne:
            key.append(str(df[col].iloc[i]))
        df['key'].iloc[i] = ''.join((key))
    return df

def scarica_excel(df, filename):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1',index=False)
    writer.close()

    st.download_button(
        label="Download Excel workbook",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.ms-excel"
    )

def create_excel_file(df, file_name):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def create_zip_file(files):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in files.items():
            zip_file.writestr(file_name, data)
    return zip_buffer.getvalue()


