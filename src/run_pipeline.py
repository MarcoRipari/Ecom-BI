# src/run_pipeline.py
import pandas as pd
import os
from src.etl import load_and_clean_data, apply_business_logic, merge_returns_logic, apply_anagrafica

# Definizione dei percorsi
RAW_VENDITE_PATH = "data/raw/vendite_oggi.csv"
RAW_RESI_PATH = "data/raw/resi_oggi.csv"
RAW_ANAGRAFICA_PATH = "data/raw/anagrafica.csv" 
RAW_ANAGRAFICA_OGGI_PATH = "data/raw/anagrafica_oggi.csv"
RAW_BUYING_PATH = "data/raw/buying_oggi.csv"

MASTER_VENDITE_PATH = "data/storici/master_vendite.parquet"
MASTER_RESI_PATH = "data/storici/master_resi.parquet"
MASTER_BUYING_PATH = "data/storici/master_buying.parquet"

GOLD_BI_PATH = "data/gold/bi_metrics.parquet"
GOLD_BUYING_PATH = "data/gold/buying.parquet"

def update_master_dataset(df_daily: pd.DataFrame, master_path: str, subset_keys: list) -> pd.DataFrame:
    """
    Gestisce la logica di Append + Deduplicazione (Upsert).
    Funziona sia per le vendite che per i resi.
    """
    if os.path.exists(master_path):
        print(f"📦 Lettura storico da {master_path}...")
        df_storico = pd.read_parquet(master_path)
        
        # Concatena storico e file odierno
        df_combined = pd.concat([df_storico, df_daily], ignore_index=True)
        
        # Deduplica mantenendo l'ultima versione caricata
        df_combined = df_combined.drop_duplicates(subset=subset_keys, keep='last')
    else:
        print(f"✨ Nessun master trovato. Inizializzazione {master_path}...")
        df_combined = df_daily

    # Salva il nuovo master aggiornato
    os.makedirs(os.path.dirname(master_path), exist_ok=True)
    df_combined.to_parquet(master_path, index=False, engine='pyarrow')
    print(f"✅ Master aggiornato: {len(df_combined)} righe totali.")
    
    return df_combined

def main():
    print("🚀 Inizio Pipeline Notturna...")

    # --- 0. UPSERT ANAGRAFICA ---
    if os.path.exists(RAW_ANAGRAFICA_OGGI_PATH):
        print("\n📥 Elaborazione nuovo file Anagrafica...")
        df_ana_oggi = pd.read_csv(RAW_ANAGRAFICA_OGGI_PATH, sep=None, engine='python', dtype=str)
        df_ana_oggi.columns = df_ana_oggi.columns.str.strip().str.lower()
        if os.path.exists(RAW_ANAGRAFICA_PATH):
            df_ana_storico = pd.read_csv(RAW_ANAGRAFICA_PATH, sep=None, engine='python', dtype=str)
            df_ana_storico.columns = df_ana_storico.columns.str.strip().str.lower()
            
            # Assumiamo che ci sia una colonna 'sku' o 'codice' come chiave
            chiave = 'sku_13' if 'sku_13' in df_ana_oggi.columns else (df_ana_oggi.columns[0])
            
            df_ana_storico.set_index(chiave, inplace=True)
            df_ana_oggi.set_index(chiave, inplace=True)
            
            df_ana_storico.update(df_ana_oggi) # Sovrascrive i vecchi dati
            new_rows = df_ana_oggi[~df_ana_oggi.index.isin(df_ana_storico.index)]
            df_ana_final = pd.concat([df_ana_storico, new_rows]).reset_index()
        else:
            df_ana_final = df_ana_oggi
            
        df_ana_final.to_csv(RAW_ANAGRAFICA_PATH, index=False)
        os.remove(RAW_ANAGRAFICA_OGGI_PATH)
        print("✅ Anagrafica aggiornata e master salvato.")

    # --- 1. INGESTIONE E APPEND VENDITE ---
    if os.path.exists(RAW_VENDITE_PATH):
        print("\n📥 Elaborazione nuovo file Vendite...")
        df_vendite_daily = load_and_clean_data(RAW_VENDITE_PATH)
        df_vendite_daily = apply_business_logic(df_vendite_daily)
        
        if os.path.exists(RAW_ANAGRAFICA_PATH):
            print("📖 Lettura e mappatura Anagrafica...")
            df_anagrafica = pd.read_csv(RAW_ANAGRAFICA_PATH, sep=None, engine='python', dtype=str) 
            df_anagrafica.columns = df_anagrafica.columns.str.strip().str.lower()
            df_vendite_daily = apply_anagrafica(df_vendite_daily, df_anagrafica)
        else:
            print("⚠️ File anagrafica non trovato. I generi saranno 'NON CLASSIFICATO'.")
            df_vendite_daily['genere'] = 'NON CLASSIFICATO'
            df_vendite_daily['descrizione'] = '-'
            
        df_master_vendite = update_master_dataset(df_vendite_daily, MASTER_VENDITE_PATH, ['ordine_id', 'sku_full', 'stato'])
    elif os.path.exists(MASTER_VENDITE_PATH):
        print("\n⚠️ Nessun nuovo file vendite trovato. Utilizzo dello storico...")
        df_master_vendite = pd.read_parquet(MASTER_VENDITE_PATH)
    else:
        raise Exception("Nessun file vendite trovato, né in raw né in storico.")

    # --- 2. INGESTIONE E APPEND RESI ---
    if os.path.exists(RAW_RESI_PATH):
        print("\n📥 Elaborazione nuovo file Resi...")
        df_resi_daily = load_and_clean_data(RAW_RESI_PATH)
        # La chiave per deduplicare un reso è la combinazione della data, cliente e sku (la stessa usata in etl.py)
        # Generiamola sul momento per la deduplicazione
        df_resi_daily['chiave_reso'] = df_resi_daily['data_pagamento'].fillna("").astype(str) + "_" + \
                                       df_resi_daily['nome_cliente'].fillna("").astype(str) + "_" + \
                                       df_resi_daily['sku_full'].fillna("").astype(str)
        df_master_resi = update_master_dataset(df_resi_daily, MASTER_RESI_PATH, ['chiave_reso'])
    elif os.path.exists(MASTER_RESI_PATH):
        print("\n⚠️ Nessun nuovo file resi trovato. Utilizzo dello storico...")
        df_master_resi = pd.read_parquet(MASTER_RESI_PATH)
    else:
        print("\n⚠️ Nessun master resi trovato. Assumo 0 resi.")
        df_master_resi = pd.DataFrame(columns=['chiave_reso'])

    # --- 3. RICOSTRUZIONE GOLD LAYER (La logica del ritardo di 7+ giorni si risolve qui) ---
    print("\n🔨 Ricostruzione del dataset BI (Gold Layer)...")
    # Facciamo passare TUTTO lo storico vendite sotto la lente d'ingrandimento di TUTTO lo storico resi
    df_gold = merge_returns_logic(df_master_vendite, df_master_resi)
    
    # Salva il file finale ottimizzato per Streamlit
    os.makedirs(os.path.dirname(GOLD_BI_PATH), exist_ok=True)
    df_gold.to_parquet(GOLD_BI_PATH, index=False, engine='pyarrow')
    print(f"🌟 Gold Layer generato con successo! ({len(df_gold)} righe)")

    # --- 4. INGESTIONE E APPEND BUYING ---
    if os.path.exists(RAW_BUYING_PATH):
        print("\n📥 Elaborazione nuovo file Buying...")
        df_buying_daily = pd.read_csv(RAW_BUYING_PATH, sep=None, engine='python', dtype=str)
        # Semplice append allo storico
        if os.path.exists(MASTER_BUYING_PATH):
            df_buying_storico = pd.read_parquet(MASTER_BUYING_PATH)
            df_buying = pd.concat([df_buying_storico, df_buying_daily], ignore_index=True).drop_duplicates()
        else:
            df_buying = df_buying_daily
            
        df_buying.to_parquet(MASTER_BUYING_PATH, index=False, engine='pyarrow')
        os.makedirs(os.path.dirname(GOLD_BUYING_PATH), exist_ok=True)
        df_buying.to_parquet(GOLD_BUYING_PATH, index=False, engine='pyarrow')
        print(f"🌟 Gold Layer Buying generato con successo! ({len(df_buying)} righe)")
    elif os.path.exists(MASTER_BUYING_PATH):
        df_buying_storico = pd.read_parquet(MASTER_BUYING_PATH)
        os.makedirs(os.path.dirname(GOLD_BUYING_PATH), exist_ok=True)
        df_buying_storico.to_parquet(GOLD_BUYING_PATH, index=False, engine='pyarrow')

    # Pulizia dei file CSV raw caricati per preparare la cartella per il giorno dopo
    if os.path.exists(RAW_VENDITE_PATH): os.remove(RAW_VENDITE_PATH)
    if os.path.exists(RAW_RESI_PATH): os.remove(RAW_RESI_PATH)
    if os.path.exists(RAW_BUYING_PATH): os.remove(RAW_BUYING_PATH)
    print("🧹 File temporanei rimossi.")

if __name__ == "__main__":
    main()
