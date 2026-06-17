import pandas as pd
import numpy as np
import os
import shutil

from src.config import (
    MAPS_COLLECTION, 
    MAPS_NATION, 
    TASSI_CAMBIO, 
    IVA_RATES, 
    DEFAULT_IVA, 
    LOGISTICA_ESTERNA
)

def load_and_clean_data(file_path: str) -> pd.DataFrame:
    """Carica il CSV e normalizza i nomi delle colonne (tutto minuscolo, spazi in underscore)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File non trovato: {file_path}")
    
    # Adatta qui il separatore se i tuoi CSV usano ';' invece di ','
    df = pd.read_csv(file_path, sep=',', dtype=str)
    
    # Normalizzazione headers
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

def apply_business_logic(df: pd.DataFrame) -> pd.DataFrame:
    """Applica mapping, tassi di cambio, calcolo IVA e flag promozioni in modo vettoriale."""
    
    # 1. Cast dei tipi numerici (gestione delle virgole europee per i decimali se presenti)
    cols_to_float = ['prezzo', 'importo', 'qta']
    for col in cols_to_float:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float).fillna(0)
            
    # Assicuriamoci che qta sia assoluta
    df['qta_abs'] = df['qta'].abs()
    
    # 2. Mapping Collezioni e Nazioni
    # Fallback: se non trova la collezione, usa quella originale, se manca usa "NON MAPPATE"
    df['clz_mappata'] = df['clz'].map(MAPS_COLLECTION).fillna(df['clz']).fillna("NON MAPPATE")
    
    # Gestione Nazioni: Lowercase per il mapping, poi ISO
    df['nazione_iso'] = df['naz'].str.lower().map(MAPS_NATION).fillna(df['naz'].str.upper())

    # 3. Logistica Esterna (ZFS, FBA, AMZ)
    df['tipo_spedizione'] = 'DIRETTO'
    # Creiamo una regex OR con i valori della logistica esterna
    regex_esterna = '|'.join(LOGISTICA_ESTERNA)
    mask_esterna = df['ordine_id'].str.upper().str.contains(regex_esterna, na=False)
    df.loc[mask_esterna, 'tipo_spedizione'] = 'ESTERNA'

    # 4. Calcoli Finanziari (Lordo, Netto, IVA)
    # Mappiamo il tasso di cambio. Se la valuta non è in dict, usiamo 1.00
    df['rate'] = df['valuta'].str.upper().map(TASSI_CAMBIO).fillna(1.00)
    df['lordo_eur'] = df['importo'] / df['rate']
    
    # Mappiamo l'IVA per Nazione ISO
    df['iva_rate'] = df['nazione_iso'].map(IVA_RATES).fillna(DEFAULT_IVA)
    df['netto_eur'] = df['lordo_eur'] / (1 + df['iva_rate'])
    
    # Calcolo valori assoluti
    df['lordo_abs'] = df['lordo_eur'].abs()
    df['netto_abs'] = df['netto_eur'].abs()
    df['importo_abs'] = df['importo'].abs()

    # 5. Flag Promo: ((QTA * PREZZO) - IMPORTO > 0.01) e COUPON VUOTO
    # Usiamo np.where per operazioni vettoriali condizionali veloci
    condition_promo = (
        ((df['qta_abs'] * df['prezzo']) - df['importo_abs'] > 0.01) & 
        (df['coupon'].isna() | (df['coupon'].str.strip() == ""))
    )
    df['is_promo'] = condition_promo

    # 6. Estrazione e pulizia SKU
    df['sku_full'] = df['sku_full'].fillna("")
    df['sku_pulita'] = df['sku_full'].str.replace('-', '')
    df['sku_13'] = df['sku_pulita'].str[:13]
    df['sku_7'] = df['sku_pulita'].str[:7]
    
    # Taglia (estratta dall'ultima parte dello split sul trattino)
    df['taglia_raw'] = df['sku_full'].apply(lambda x: x.split('-')[-1].strip() if '-' in x else "")
    # (Potremo implementare la logica regex avanzata delle taglie nello step successivo)

    return df

def merge_returns_logic(df_vendite: pd.DataFrame, df_resi: pd.DataFrame) -> pd.DataFrame:
    """Implementa la nuova logica di identificazione dei resi tramite chiave composta."""
    
    # Assicurati che questi siano i nomi ESATTI normalizzati dopo load_and_clean_data
    # Se nel CSV si chiamano "Data Pagamento", diventeranno "data_pagamento"
    col_data = 'data_pagamento'
    col_cliente = 'nome_cliente'
    col_sku = 'sku_full'
    
    for df in [df_vendite, df_resi]:
        # Creiamo la chiave univoca: datapagamento_nomecliente_sku
        # fillna("") evita che un campo nullo corrompa l'intera stringa
        df['chiave_reso'] = (
            df[col_data].fillna("").astype(str) + "_" + 
            df[col_cliente].fillna("").astype(str) + "_" + 
            df[col_sku].fillna("").astype(str)
        )
    
    # Creiamo un set super veloce con le chiavi dei resi
    resi_keys_set = set(df_resi['chiave_reso'])
    
    # Applichiamo il flag is_reso
    df_vendite['is_reso'] = df_vendite['chiave_reso'].isin(resi_keys_set)
    
    # Creiamo le colonne paia spedite/rese finali (ricalcando logica backend.gs)
    df_vendite['paia_spedite'] = df_vendite['qta_abs']
    df_vendite['paia_rese'] = np.where(df_vendite['is_reso'], df_vendite['qta_abs'], 0)
    df_vendite['paia_nette'] = df_vendite['paia_spedite'] - df_vendite['paia_rese']
    
    # Fatturato
    df_vendite['netto_spedito'] = df_vendite['netto_abs']
    df_vendite['netto_reso'] = np.where(df_vendite['is_reso'], df_vendite['netto_abs'], 0.0)
    df_vendite['netto_netto'] = df_vendite['netto_spedito'] - df_vendite['netto_reso']

    return df_vendite

def run_etl_pipeline(vendite_path: str, resi_path: str, output_parquet_path: str):
    """Orchestra il caricamento, la pulizia e il salvataggio."""
    print("🚀 Avvio Pipeline ETL...")
    
    df_vendite = load_and_clean_data(vendite_path)
    df_resi = load_and_clean_data(resi_path)
    
    print("⚙️ Applicazione Business Logic sulle vendite...")
    df_vendite = apply_business_logic(df_vendite)
    
    print("🔄 Integrazione logica resi vettoriale...")
    df_final = merge_returns_logic(df_vendite, df_resi)
    
    # Creiamo la cartella di output se non esiste
    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
    
    # Salvataggio in formato Parquet compresso
    print(f"💾 Salvataggio in Parquet: {output_parquet_path}")
    df_final.to_parquet(output_parquet_path, index=False, engine='pyarrow')
    
    print("✅ ETL completato con successo!")
    return df_final

def update_master_parquet(df_daily: pd.DataFrame, master_path: str):
    """
    Fa l'upsert dei dati giornalieri nello storico master.
    Crea un backup del giorno precedente prima di sovrascrivere.
    """
    backup_path = master_path.replace('.parquet', '_backup.parquet')
    
    if os.path.exists(master_path):
        print("📦 Master storico trovato. Creazione backup...")
        shutil.copy2(master_path, backup_path)
        
        print("🔄 Lettura storico e unione con i nuovi dati...")
        df_storico = pd.read_parquet(master_path)
        
        # Uniamo storico e nuovo
        df_combined = pd.concat([df_storico, df_daily], ignore_index=True)
        
        # Rimuoviamo i duplicati basandoci su una chiave univoca dell'ordine/riga
        # (Assumiamo che ordine_id + sku_full identifichino univocamente una riga di vendita)
        df_combined = df_combined.drop_duplicates(subset=['ordine_id', 'sku_full'], keep='last')
    else:
        print("✨ Nessun master trovato. Inizializzazione nuovo storico...")
        df_combined = df_daily

    # Salvataggio
    df_combined.to_parquet(master_path, index=False, engine='pyarrow')
    print(f"✅ Master Parquet aggiornato: {len(df_combined)} righe totali.")
    return df_combined
