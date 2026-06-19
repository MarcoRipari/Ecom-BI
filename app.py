import streamlit as st
import pandas as pd
from src.metrics import aggregate_by_key, calculate_global_metrics

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="BI Dashboard | Footwear",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CARICAMENTO DATI (Latenza Zero grazie al caching) ---
@st.cache_data(ttl=3600) # Ricarica i dati dalla cache se non è passata un'ora
def load_data():
    try:
        df = pd.read_parquet("data/gold/bi_metrics.parquet")
        # Trova la colonna data corretta (gestisce diverse intestazioni)
        date_col = 'data_vendita' if 'data_vendita' in df.columns else 'data_pagamento'
        if date_col in df.columns:
            df['data_vendita'] = pd.to_datetime(df[date_col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("⚠️ File bi_metrics.parquet non trovato. Attendi l'esecuzione della pipeline notturna o lanciala manualmente.")
        st.stop()

df = load_data()

# --- SIDEBAR: FILTRI ---
st.sidebar.title("⚙️ Filtri Report")

# 1. Perimetro Logistico (Sostituisce il vecchio UI Prompt)
perimetro = st.sidebar.radio(
    "Perimetro Logistico", 
    ["TOTALE (Diretti + Esterni)", "SOLO DIRETTI", "SOLO LOGISTICA ESTERNA"]
)

# Applica il filtro al DataFrame
if perimetro == "SOLO DIRETTI":
    df_filtered = df[df['tipo_spedizione'] == 'DIRETTO']
elif perimetro == "SOLO LOGISTICA ESTERNA":
    df_filtered = df[df['tipo_spedizione'] == 'ESTERNA']
else:
    df_filtered = df.copy()

# 2. Filtro Date (Sostituisce le logiche Y2Y statiche)
st.sidebar.markdown("---")
if 'data_vendita' in df_filtered.columns and not df_filtered.empty and not pd.isna(df_filtered['data_vendita'].min()):
    min_date = df_filtered['data_vendita'].min()
    max_date = df_filtered['data_vendita'].max()
else:
    min_date = pd.to_datetime('2023-01-01')
    max_date = pd.to_datetime('today')

# Assicuriamoci che min_date non sia NaT o superiore a max_date per evitare crash
if pd.isna(min_date) or pd.isna(max_date) or min_date > max_date:
    min_date = pd.to_datetime('2023-01-01')
    max_date = pd.to_datetime('today')

date_range = st.sidebar.date_input(
    "Periodo di Analisi",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2 and 'data_vendita' in df_filtered.columns:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered['data_vendita'] >= pd.to_datetime(start_date)) & 
        (df_filtered['data_vendita'] <= pd.to_datetime(end_date))
    ]

# --- MAIN DASHBOARD ---
st.title("📈 Dashboard Vendite & Resi")
st.markdown(f"**Analisi basata su:** `{perimetro}`")

# --- CALCOLO METRICHE GLOBALI ---
tot_fatturato = df_filtered['netto_netto'].sum()
tot_ordini = df_filtered['ordine_id'].nunique()
tot_paia_spedite = df_filtered['paia_spedite'].sum()
tot_paia_rese = df_filtered['paia_rese'].sum()
perc_reso = (tot_paia_rese / tot_paia_spedite) if tot_paia_spedite > 0 else 0

# --- RIGA 1: KPI PRINCIPALI ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Fatturato Netto", f"€ {tot_fatturato:,.2f}")
col2.metric("Totale Ordini", f"{tot_ordini:,}")
col3.metric("Paia Nette", f"{(tot_paia_spedite - tot_paia_rese):,}")
col4.metric("% Reso Globale", f"{perc_reso * 100:.2f}%")

st.markdown("---")

# --- NAVIGAZIONE A SCHEDE (Sostituisce i fogli Google) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard Base", "👕 Analisi Resi", "🏆 Top Articoli", "🌍 Dettaglio Nazioni"])

with tab1:
    st.subheader("Dettaglio per Marketplace")
    df_mkp = aggregate_by_key(df_filtered, 'mkp')
    # Rinomina colonne per UI (9 elementi)
    df_mkp.columns = ['Marketplace', 'Ordini', 'Paia Spedite', 'Paia Rese', 'Paia Nette', 'Fatturato Spedito', 'Fatturato Netto', '% Reso', 'Scontrino Medio']
    # Seleziona e riordina le colonne da mostrare
    df_mkp = df_mkp[['Marketplace', 'Ordini', 'Paia Spedite', 'Paia Rese', 'Paia Nette', 'Scontrino Medio', 'Fatturato Netto', '% Reso']]
    st.dataframe(
        df_mkp, 
        use_container_width=True,
        column_config={
            "Fatturato Netto": st.column_config.NumberColumn(format="€ %.2f"),
            "Scontrino Medio": st.column_config.NumberColumn(format="€ %.2f"),
            "% Reso": st.column_config.NumberColumn(format="%.2f%%")
        }
    )

with tab2:
    st.subheader("Status Resi per Brand / Collezione")
    df_brand = aggregate_by_key(df_filtered, 'clz_mappata')
    # Rinomina colonne (9 elementi)
    df_brand.columns = ['Collezione', 'Ordini', 'Paia Spedite', 'Paia Rese', 'Paia Nette', 'Fatturato Spedito', 'Fatturato Netto', '% Reso', 'Scontrino Medio']
    
    # Ricostruzione della logica semaforo (ex generateResiModulo)
    def get_status(perc):
        if perc >= 1: return "🔴 CRITICO (100%)"
        if perc > 0.7: return "🔴 CRITICO"
        if perc > 0.4: return "🟠 PESSIMO"
        if perc > 0.3: return "🟡 MONITORARE"
        if perc > 0.24: return "🔵 STABILE"
        return "🟢 OTTIMO"
        
    df_brand['Status'] = df_brand['% Reso'].apply(get_status)
    df_brand = df_brand.sort_values(by='% Reso', ascending=False)
    
    st.dataframe(
        df_brand[['Collezione', 'Paia Spedite', 'Paia Rese', '% Reso', 'Fatturato Netto', 'Status']], 
        use_container_width=True,
        column_config={
            "Fatturato Netto": st.column_config.NumberColumn(format="€ %.2f"),
            "% Reso": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)
        }
    )

with tab3:
    st.subheader("Top Articoli Venduti")
    df_sku = aggregate_by_key(df_filtered, 'sku_13')
    
    # Generazione dell'URL immagine per Falc
    df_sku['Immagine'] = df_sku['sku_13'].apply(lambda x: f"https://repository.falc.biz/fal001{str(x).lower()}-1.jpg")
    
    df_sku_ui = df_sku[['Immagine', 'sku_13', 'paia_nette', 'fatturato_netto', 'perc_reso']].head(50)
    # Rinomina per UI
    df_sku_ui.columns = ['Foto', 'SKU', 'Paia Nette', 'Fatturato Netto', '% Reso']
    
    st.dataframe(
        df_sku_ui,
        use_container_width=True,
        column_config={
            "Foto": st.column_config.ImageColumn("Foto", help="Anteprima prodotto"),
            "Fatturato Netto": st.column_config.NumberColumn(format="€ %.2f"),
            "% Reso": st.column_config.NumberColumn(format="%.2f")
        }
    )

with tab4:
    st.subheader("Performance per Nazione")
    df_naz = aggregate_by_key(df_filtered, 'nazione_iso')
    # Generiamo un semplice grafico a barre nativo di Streamlit
    st.bar_chart(data=df_naz, x='nazione_iso', y='fatturato_netto', use_container_width=True)
