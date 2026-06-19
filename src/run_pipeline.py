# src/run_pipeline.py
import pandas as pd
import os
from src.etl import apply_business_logic, merge_returns_logic, apply_anagrafica

# Definizione dei percorsi
MASTER_VENDITE_PATH = "data/storici/master_vendite.parquet"
MASTER_RESI_PATH = "data/storici/master_resi.parquet"
MASTER_BUYING_PATH = "data/storici/buying.parquet"
ANAGRAFICA_PATH = "data/storici/anagrafica.parquet"

GOLD_BI_PATH = "data/gold/bi_metrics.parquet"
GOLD_BUYING_PATH = "data/gold/buying.parquet"

def main():
    print("🚀 Inizio Pipeline Notturna ETL...")

    # --- 1. CARICAMENTO VENDITE E BUSINESS LOGIC ---
    if os.path.exists(MASTER_VENDITE_PATH):
        print("\n📥 Lettura master vendite...")
        df_vendite = pd.read_parquet(MASTER_VENDITE_PATH)
        df_vendite = apply_business_logic(df_vendite)
        
        if os.path.exists(ANAGRAFICA_PATH):
            print("📖 Lettura e mappatura Anagrafica...")
            df_anagrafica = pd.read_parquet(ANAGRAFICA_PATH) 
            df_vendite = apply_anagrafica(df_vendite, df_anagrafica)
        else:
            print("⚠️ File anagrafica non trovato. I generi saranno 'NON CLASSIFICATO'.")
            df_vendite['genere'] = 'NON CLASSIFICATO'
            df_vendite['descrizione'] = '-'
    else:
        print("❌ Nessun master vendite trovato! Interruzione.")
        return

    # --- 2. CARICAMENTO RESI ---
    if os.path.exists(MASTER_RESI_PATH):
        print("\n📥 Lettura master resi...")
        df_resi = pd.read_parquet(MASTER_RESI_PATH)
    else:
        print("\n⚠️ Nessun master resi trovato. Assumo 0 resi.")
        df_resi = pd.DataFrame()

    # --- 3. RICOSTRUZIONE GOLD LAYER VENDITE/RESI ---
    print("\n🔨 Ricostruzione del dataset BI (Gold Layer)...")
    # Facciamo passare TUTTO lo storico vendite sotto la lente d'ingrandimento di TUTTO lo storico resi
    df_gold = merge_returns_logic(df_vendite, df_resi)
    
    # Salva il file finale ottimizzato per Streamlit
    os.makedirs(os.path.dirname(GOLD_BI_PATH), exist_ok=True)
    df_gold.to_parquet(GOLD_BI_PATH, index=False, engine='pyarrow')
    print(f"🌟 Gold Layer generato con successo! ({len(df_gold)} righe)")

    # --- 4. BUYING GOLD LAYER ---
    if os.path.exists(MASTER_BUYING_PATH):
        print("\n📥 Elaborazione file Buying per il Gold Layer...")
        df_buying = pd.read_parquet(MASTER_BUYING_PATH)
        os.makedirs(os.path.dirname(GOLD_BUYING_PATH), exist_ok=True)
        df_buying.to_parquet(GOLD_BUYING_PATH, index=False, engine='pyarrow')
        print(f"🌟 Gold Layer Buying generato con successo! ({len(df_buying)} righe)")

    print("✅ ETL notturno completato con successo.")

if __name__ == "__main__":
    main()
