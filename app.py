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
            df['data_vendita'] = pd.to_datetime(df[date_col], format="%d/%m/%Y", errors='coerce')
        return df
    except FileNotFoundError:
        st.error("⚠️ File bi_metrics.parquet non trovato. Attendi l'esecuzione della pipeline notturna o lanciala manualmente.")
        st.stop()

df = load_data()

# --- SIDEBAR: FILTRI ---
st.sidebar.title("⚙️ Filtri Report")

# --- FILTRO DATE E Y2Y ---
df_filtered = df.copy()
df_old = pd.DataFrame()

if 'data_vendita' in df.columns and not df.empty and not pd.isna(df['data_vendita'].min()):
    min_date = df['data_vendita'].min()
    max_date = df['data_vendita'].max()
else:
    min_date = pd.to_datetime('2023-01-01')
    max_date = pd.to_datetime('today')

if pd.isna(min_date) or pd.isna(max_date) or min_date > max_date:
    min_date = pd.to_datetime('2023-01-01')
    max_date = pd.to_datetime('today')

date_range = st.sidebar.date_input(
    "Periodo di Analisi",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2 and 'data_vendita' in df.columns:
    start_date, end_date = date_range
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Crea df_filtered
    df_filtered = df[
        (df['data_vendita'] >= start_date) & 
        (df['data_vendita'] <= end_date)
    ]
    
    # Crea df_old (esattamente 1 anno prima)
    old_start_date = start_date - pd.DateOffset(years=1)
    old_end_date = end_date - pd.DateOffset(years=1)
    df_old = df[
        (df['data_vendita'] >= old_start_date) & 
        (df['data_vendita'] <= old_end_date)
    ]

# 1. Perimetro Logistico (Applicato ad entrambi)
perimetro = st.sidebar.radio(
    "Perimetro Logistico", 
    ["TOTALE (Diretti + Esterni)", "SOLO DIRETTI", "SOLO LOGISTICA ESTERNA"]
)

if perimetro == "SOLO DIRETTI":
    df_filtered = df_filtered[df_filtered['tipo_spedizione'] == 'DIRETTO']
    if not df_old.empty: df_old = df_old[df_old['tipo_spedizione'] == 'DIRETTO']
elif perimetro == "SOLO LOGISTICA ESTERNA":
    df_filtered = df_filtered[df_filtered['tipo_spedizione'] == 'ESTERNA']
    if not df_old.empty: df_old = df_old[df_old['tipo_spedizione'] == 'ESTERNA']

# --- SELEZIONE REPORT ---
report_selezionato = st.sidebar.selectbox(
    "Modulo di Analisi",
    ["Dashboard Anno Corrente", "Comparativa Y2Y", "Y2Y Collezioni", "Y2Y Codici", "Carryover", "Sell-Through", "Analisi Taglie", "🔧 Area Admin"]
)

st.sidebar.markdown("---")

# --- MAIN DASHBOARD ---
st.title(f"📈 {report_selezionato}")
st.markdown(f"**Analisi basata su:** `{perimetro}`")

# --- CALCOLO METRICHE GLOBALI ---
tot_fatturato = df_filtered['netto_netto'].sum()
tot_ordini = df_filtered['ordine_id'].nunique()
paia_nette = df_filtered['paia_nette'].sum()
paia_spedite = df_filtered['paia_spedite'].sum()
paia_rese = df_filtered['paia_rese'].sum()
perc_reso = (paia_rese / paia_spedite * 100) if paia_spedite > 0 else 0

st.write("### KPI Globali Periodo Selezionato")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Fatturato Netto", f"€ {tot_fatturato:,.2f}")
kpi2.metric("Totale Ordini", f"{tot_ordini:,}")
kpi3.metric("Paia Nette", f"{paia_nette:,.0f}")
kpi4.metric("Paia Spedite", f"{paia_spedite:,.0f}")
kpi5.metric("% Reso Globale", f"{perc_reso:.1f}%")

st.markdown("---")

if report_selezionato == "Dashboard Anno Corrente":
    tab1, tab2, tab3 = st.tabs(["🛒 Marketplace", "🏷️ Brand / Collezione", "📦 Dettaglio SKU"])

    with tab1:
        st.subheader("Performance per Marketplace")
        df_mkp = aggregate_by_key(df_filtered, 'mkp')
        if not df_mkp.empty:
            df_mkp.columns = ['Marketplace', 'Ordini', 'Paia Spedite', 'Paia Rese', 'Paia Nette', 'Fatturato Spedito', 'Fatturato Netto', '% Reso', 'Scontrino Medio']
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
        if not df_brand.empty:
            df_brand.columns = ['Collezione', 'Ordini', 'Paia Spedite', 'Paia Rese', 'Paia Nette', 'Fatturato Spedito', 'Fatturato Netto', '% Reso', 'Scontrino Medio']
            
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
                    "% Reso": st.column_config.ProgressColumn(format="%.2f%%", min_value=0, max_value=100)
                }
            )

    with tab3:
        st.subheader("Top Articoli (Analisi SKU)")
        df_sku = aggregate_by_key(df_filtered, 'sku_13')
        if not df_sku.empty:
            df_sku.columns = ['SKU', 'Ordini', 'Paia Spedite', 'Paia Rese', 'Paia Nette', 'Fatturato Spedito', 'Fatturato Netto', '% Reso', 'Scontrino Medio']
            st.dataframe(
                df_sku[['SKU', 'Paia Nette', 'Fatturato Netto', '% Reso']].head(50), 
                use_container_width=True,
                column_config={
                    "Fatturato Netto": st.column_config.NumberColumn(format="€ %.2f"),
                    "% Reso": st.column_config.NumberColumn(format="%.2f%%")
                }
            )
elif report_selezionato == "Comparativa Y2Y":
    st.subheader("📊 Comparativa Generali Flat (Mkp/Naz/Clz)")
    from src.reports_logic import aggregate_y2y
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 🌍 Dettaglio per Nazione")
        df_y2y_naz = aggregate_y2y(df_filtered, df_old, 'nazione_iso')
        if not df_y2y_naz.empty:
            from src.charts import plot_y2y_comparison
            st.plotly_chart(plot_y2y_comparison(df_y2y_naz, 'nazione_iso', 'fatturato_netto_curr', 'fatturato_netto_old', "Fatturato Y2Y Nazioni"), use_container_width=True)
            st.dataframe(df_y2y_naz[['nazione_iso', 'fatturato_netto_curr', 'fatturato_netto_old', 'var_fatturato']], use_container_width=True,
                column_config={"var_fatturato": st.column_config.NumberColumn(format="%.2f%%")})

    with col2:
        st.write("#### 🛒 Dettaglio per Marketplace")
        df_y2y_mkp = aggregate_y2y(df_filtered, df_old, 'mkp')
        if not df_y2y_mkp.empty:
            st.plotly_chart(plot_y2y_comparison(df_y2y_mkp, 'mkp', 'fatturato_netto_curr', 'fatturato_netto_old', "Fatturato Y2Y Marketplace"), use_container_width=True)
            st.dataframe(df_y2y_mkp[['mkp', 'fatturato_netto_curr', 'fatturato_netto_old', 'var_fatturato']], use_container_width=True,
                column_config={"var_fatturato": st.column_config.NumberColumn(format="%.2f%%")})

elif report_selezionato == "Y2Y Collezioni":
    st.subheader("📈 Comparativa Brand / Collezioni")
    from src.reports_logic import aggregate_y2y
    df_y2y_clz = aggregate_y2y(df_filtered, df_old, 'clz_mappata')
    if not df_y2y_clz.empty:
        from src.charts import plot_y2y_comparison
        st.plotly_chart(plot_y2y_comparison(df_y2y_clz, 'clz_mappata', 'paia_nette_curr', 'paia_nette_old', "Paia Nette Y2Y Collezioni"), use_container_width=True)
        st.dataframe(df_y2y_clz[['clz_mappata', 'paia_nette_curr', 'paia_nette_old', 'var_paia', 'fatturato_netto_curr', 'fatturato_netto_old', 'var_fatturato']], use_container_width=True,
            column_config={
                "var_paia": st.column_config.NumberColumn(format="%.2f%%"),
                "var_fatturato": st.column_config.NumberColumn(format="%.2f%%")
            })

elif report_selezionato == "Y2Y Codici":
    st.subheader("🏷️ Comparativa Solo Codici Articolo (SKU)")
    from src.reports_logic import aggregate_y2y
    df_y2y_sku = aggregate_y2y(df_filtered, df_old, 'sku_13')
    if not df_y2y_sku.empty:
        st.dataframe(df_y2y_sku[['sku_13', 'paia_nette_curr', 'paia_nette_old', 'var_paia', 'fatturato_netto_curr', 'fatturato_netto_old', 'var_fatturato']].head(100), use_container_width=True,
            column_config={
                "var_paia": st.column_config.NumberColumn(format="%.2f%%"),
                "var_fatturato": st.column_config.NumberColumn(format="%.2f%%")
            })

elif report_selezionato == "Carryover":
    st.subheader("📦 Analisi Carryover (Solo SKU presenti in entrambi i periodi)")
    from src.reports_logic import filter_carryover_data, aggregate_y2y
    df_curr_carry, df_old_carry = filter_carryover_data(df_filtered, df_old)
    
    if not df_curr_carry.empty and not df_old_carry.empty:
        df_y2y_carry = aggregate_y2y(df_curr_carry, df_old_carry, 'clz_mappata')
        st.dataframe(df_y2y_carry[['clz_mappata', 'paia_nette_curr', 'paia_nette_old', 'var_paia', 'fatturato_netto_curr', 'fatturato_netto_old', 'var_fatturato']], use_container_width=True,
            column_config={
                "var_paia": st.column_config.NumberColumn(format="%.2f%%"),
                "var_fatturato": st.column_config.NumberColumn(format="%.2f%%")
            })
    else:
        st.warning("Nessun articolo in comune tra i due periodi o dati mancanti per il periodo precedente.")

elif report_selezionato == "Sell-Through":
    st.subheader("🔥 Analisi Sell-Through Stagionale")
    import os
    if not os.path.exists('data/gold/buying.parquet'):
        st.error("⚠️ Il file **buying.parquet** non è stato trovato in `data/gold/`. Esegui la pipeline notturna dopo aver caricato il file BUYING.csv.")
    else:
        df_buying = pd.read_parquet('data/gold/buying.parquet')
        from src.reports_logic import aggregate_sellthrough
        df_sellthrough = aggregate_sellthrough(df_filtered, df_buying)
        
        if not df_sellthrough.empty:
            # Aggiungiamo dettagli anagrafici dal dataframe vendite
            anagrafica_subset = df_filtered[['sku_13', 'clz_mappata', 'descrizione']].drop_duplicates('sku_13')
            df_sellthrough = pd.merge(df_sellthrough, anagrafica_subset, on='sku_13', how='left')
            
            df_sellthrough = df_sellthrough[['sku_13', 'clz_mappata', 'descrizione', 'paia_acquistate', 'paia_nette', 'sell_through', 'fatturato_netto']]
            
            st.dataframe(df_sellthrough, use_container_width=True,
                column_config={
                    "sell_through": st.column_config.ProgressColumn(format="%.2f%%", min_value=0, max_value=100),
                    "fatturato_netto": st.column_config.NumberColumn(format="€ %.2f")
                })
        else:
            st.warning("Nessun dato corrispondente trovato.")

elif report_selezionato == "Analisi Taglie":
    st.subheader("📏 Analisi Taglie per Brand e Genere")
    from src.reports_logic import aggregate_taglie
    df_taglie = aggregate_taglie(df_filtered)
    
    if not df_taglie.empty:
        from src.charts import plot_taglie_heatmap
        st.plotly_chart(plot_taglie_heatmap(df_taglie, "Heatmap Vendite per Taglia e Genere"), use_container_width=True)
        st.dataframe(df_taglie, use_container_width=True,
            column_config={
                "perc_su_gruppo": st.column_config.NumberColumn(format="%.2f%%"),
                "perc_reso": st.column_config.NumberColumn(format="%.2f%%")
            })

elif report_selezionato == "🔧 Area Admin":
    st.subheader("🛠️ Area Amministrazione e Upload Dati")
    st.markdown("In questa sezione puoi caricare nuovi dataset e forzare l'esecuzione della Pipeline ETL su GitHub Actions.")
    
    from src.github_integration import trigger_github_workflow, get_workflow_runs
    
    # Check active runs
    runs = []
    is_running = False
    if "GITHUB_TOKEN" in st.secrets:
        runs = get_workflow_runs(st.secrets["GITHUB_TOKEN"], "MarcoRipari/Ecom-BI")
        is_running = any(r['status'] in ["in_progress", "queued"] for r in runs) if runs else False
        
    if is_running:
        st.warning("⚠️ C'è una pipeline in elaborazione o in coda. I caricamenti sono disabilitati finché non termina per evitare conflitti su GitHub.")

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 📤 Upload Dataset")
        upload_type = st.selectbox("Seleziona il tipo di file:", ["VENDITE", "RESI", "BUYING", "ANAGRAFICA"])
        uploaded_file = st.file_uploader(f"Carica il file {upload_type} (CSV)", type=["csv"])
        
        if uploaded_file is not None:
            if is_running:
                st.button(f"⏳ Attendi fine pipeline per caricare", disabled=True)
            else:
                if st.button(f"🚀 Carica {upload_type} su GitHub"):
                    from src.github_integration import upload_file_to_github
                    if "GITHUB_TOKEN" in st.secrets:
                        token = st.secrets["GITHUB_TOKEN"]
                        repo = "MarcoRipari/Ecom-BI"
                        
                        # Definisci il path di destinazione in base al tipo
                        if upload_type == "VENDITE":
                            path = "data/raw/vendite_oggi.csv"
                        elif upload_type == "RESI":
                            path = "data/raw/resi_oggi.csv"
                        elif upload_type == "BUYING":
                            path = "data/raw/buying_oggi.csv"
                        elif upload_type == "ANAGRAFICA":
                            path = "data/raw/anagrafica_oggi.csv"
                            
                        with st.spinner(f"Caricamento di {upload_type} in corso..."):
                            success = upload_file_to_github(
                                token=token,
                                repo=repo,
                                file_path=path,
                                new_content_bytes=uploaded_file.getvalue(),
                                commit_message=f"Upload manuale file {upload_type} da Area Admin"
                            )
                            if success:
                                st.success(f"✅ {upload_type} caricato con successo in `{path}`. Verrà processato dalla prossima pipeline ETL.")
                            else:
                                st.error("❌ Errore durante l'upload. Controlla il Token o i permessi del repository.")
                    else:
                        st.error("❌ GITHUB_TOKEN non configurato nei secrets di Streamlit.")
                    
    with col2:
        st.write("#### ⚙️ Pipeline ETL")
        
        if is_running:
            st.button("⏳ Attendi fine pipeline per avviare ETL", disabled=True)
        else:
            if st.button("🔄 Forza Avvio ETL (GitHub Actions)"):
                if "GITHUB_TOKEN" in st.secrets:
                    with st.spinner("Invio comando a GitHub..."):
                        if trigger_github_workflow(st.secrets["GITHUB_TOKEN"], "MarcoRipari/Ecom-BI"):
                            st.success("✅ Pipeline ETL avviata! Il processo richiederà alcuni minuti.")
                            st.rerun()
                        else:
                            st.error("❌ Impossibile avviare la pipeline. Verifica il token o il nome del workflow.")
                else:
                    st.error("❌ GITHUB_TOKEN non configurato nei secrets di Streamlit.")
                
        st.write("##### 📊 Coda e Stato Azioni (Ultime Esecuzioni):")
        if "GITHUB_TOKEN" in st.secrets:
            if runs:
                for run in runs:
                    status_icon = "✅" if run['conclusion'] == "success" else ("⏳" if run['status'] in ["in_progress", "queued"] else "❌")
                    nome_run = run.get('name', 'Pipeline')
                    conclusion_str = f" (Esito: {run.get('conclusion')})" if run.get('conclusion') else ""
                    st.write(f"{status_icon} **{nome_run}** - Stato: `{run['status']}`{conclusion_str} - [Vedi Log]({run['html_url']})")
            else:
                st.info("Nessuna esecuzione recente trovata.")

    st.markdown("---")
    st.write("#### 🔎 Visualizzatore Dati Parquet")
    st.markdown("Ispeziona i dati grezzi storici o elaborati.")
    
    col_file, col_date = st.columns(2)
    with col_file:
        parquet_file = st.selectbox("Seleziona File Parquet da esplorare:", [
            "data/gold/bi_metrics.parquet (Vendite elaborate UI)",
            "data/gold/buying.parquet (Acquisti elaborati UI)",
            "data/storici/master_vendite.parquet (Storico Grezzo)",
            "data/storici/master_resi.parquet (Storico Grezzo)",
            "data/storici/anagrafica.parquet (Anagrafica Grezza)",
            "data/storici/buying.parquet (Acquisti Grezzi)"
        ])
    
    with col_date:
        if st.checkbox("Filtra per data (se applicabile)"):
            date_filter = st.date_input("Range date:", value=(min_date, max_date))
        else:
            date_filter = None
            
    try:
        file_path = parquet_file.split(" ")[0]
        df_parquet = pd.read_parquet(file_path)
        
        # Identifica colonna data
        date_cols = [c for c in df_parquet.columns if 'data' in c.lower()]
        date_c = None
        for dc in ['data_vendita', 'data_pagamento', 'data_reso/sped.']:
            if dc in df_parquet.columns:
                date_c = dc
                break
        if not date_c and date_cols:
            date_c = date_cols[0]
            
        if date_filter and len(date_filter) == 2 and date_c:
            try:
                # Prova a convertire per il filtro
                df_parquet['_temp_date'] = pd.to_datetime(df_parquet[date_c], format="%d/%m/%Y", errors='coerce')
                # Fallback
                mask_na = df_parquet['_temp_date'].isna()
                if mask_na.any():
                    df_parquet.loc[mask_na, '_temp_date'] = pd.to_datetime(df_parquet.loc[mask_na, date_c], errors='coerce')
                    
                df_parquet = df_parquet[
                    (df_parquet['_temp_date'].dt.date >= date_filter[0]) & 
                    (df_parquet['_temp_date'].dt.date <= date_filter[1])
                ]
                df_parquet = df_parquet.drop(columns=['_temp_date'])
            except Exception as e:
                st.warning(f"Impossibile filtrare per data su questa colonna: {e}")
                
        st.write(f"Righe trovate: **{len(df_parquet):,}**")
        st.dataframe(df_parquet.head(1000), use_container_width=True) # Mostra max 1000 righe per UI
        
    except FileNotFoundError:
        st.error("Il file selezionato non è ancora stato generato.")

