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
    """Carica il CSV, gestisce errori di formattazione e normalizza i nomi delle colonne."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File non trovato: {file_path}")
    
    # Tentiamo la lettura rendendo il parser più flessibile e tollerante
    try:
        # Se sai che i tuoi CSV sono separati da punto e virgola, cambia sep=';'
        df = pd.read_csv(
            file_path, 
            sep=';', 
            dtype=str, 
            on_bad_lines='warn', # Se trova una riga rotta la salta, ma stampa un Warning nei log di GitHub
            engine='python'      # Usa il parser Python invece di quello C (risolve l'errore C Error)
        )
    except Exception as e:
        print(f"⚠️ Errore di parsing standard. Tentativo fallback con separatore ';' per {file_path}")
        df = pd.read_csv(
            file_path, 
            sep=';', 
            dtype=str, 
            on_bad_lines='warn', 
            engine='python'
        )
    
    # Normalizzazione headers (tutto minuscolo, spazi sostituiti da underscore)
    df.columns = df.columns.str.strip().str.lower()
    
    # Mappatura robusta per supportare i nomi colonne del file Excel/CSV originale
    rename_dict = {}
    for col in df.columns:
        if 'quantit' in col: rename_dict[col] = 'qta'
        elif col == 'collezione': rename_dict[col] = 'clz'
        elif col == 'nazione': rename_dict[col] = 'naz'
        elif col == 'acquirente': rename_dict[col] = 'nome_cliente'
        elif col == 'ordine': rename_dict[col] = 'ordine_id'
        elif 'sku' in col: rename_dict[col] = 'sku_full'
        elif 'market place' in col or col == 'mkp': rename_dict[col] = 'mkp'
        elif 'unnamed: 8' in col: rename_dict[col] = 'stato'
        
    df.rename(columns=rename_dict, inplace=True)
    df.columns = df.columns.str.replace(' ', '_')
    return df

def apply_business_logic(df: pd.DataFrame) -> pd.DataFrame:
    """Applica mapping, tassi di cambio, calcolo IVA e flag promozioni in modo vettoriale."""
    
    cols_to_float = ['prezzo', 'importo', 'qta']
    for col in cols_to_float:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].astype(float).fillna(0.0)
            else:
                df[col] = (df[col]
                           .astype(str)
                           .str.strip()
                           .str.replace('.', '', regex=False)  # Rimuove i separatori delle migliaia
                           .str.replace(',', '.', regex=False) # Converte la virgola in punto decimale
                           .astype(float)
                           .fillna(0.0))
            
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
    """Implementa la logica originale di identificazione dei resi tramite colonna 'stato' e incrocio con df_resi."""
    
    if 'stato' not in df_vendite.columns:
        df_vendite['stato'] = ''
        
    # Crea chiave in vendite per il match con df_resi
    if 'ordine_id' in df_vendite.columns and 'sku_full' in df_vendite.columns:
        chiave_vendite = df_vendite['ordine_id'].fillna("").astype(str) + "_" + \
                         df_vendite['sku_full'].fillna("").astype(str)
    else:
        chiave_vendite = pd.Series([""] * len(df_vendite))

    # Identifica le chiavi presenti nel master resi
    chiavi_rese = set()
    if not df_resi.empty and 'ordine_id' in df_resi.columns and 'sku_full' in df_resi.columns:
        chiave_reso = df_resi['ordine_id'].fillna("").astype(str) + "_" + \
                      df_resi['sku_full'].fillna("").astype(str)
        chiavi_rese = set(chiave_reso.unique())

    # Applichiamo il flag is_reso: è reso se lo stato dice 'reso' OPPURE se la chiave è trovata in df_resi
    is_reso_stato = df_vendite['stato'].str.lower().str.strip() == 'reso'
    is_reso_match = chiave_vendite.isin(chiavi_rese)
    
    df_vendite['is_reso'] = is_reso_stato | is_reso_match
    
    # Creiamo le colonne paia spedite/rese finali (ricalcando logica backend.gs)
    df_vendite['paia_spedite'] = df_vendite['qta_abs']
    df_vendite['paia_rese'] = np.where(df_vendite['is_reso'], df_vendite['qta_abs'], 0)
    df_vendite['paia_nette'] = df_vendite['paia_spedite'] - df_vendite['paia_rese']
    
    # Fatturato
    df_vendite['netto_spedito'] = df_vendite['netto_abs']
    df_vendite['netto_reso'] = np.where(df_vendite['is_reso'], df_vendite['netto_abs'], 0.0)
    df_vendite['netto_netto'] = df_vendite['netto_spedito'] - df_vendite['netto_reso']

    df_vendite['lordo_spedito'] = df_vendite['lordo_abs']
    df_vendite['lordo_reso'] = np.where(df_vendite['is_reso'], df_vendite['lordo_abs'], 0.0)
    df_vendite['lordo_netto'] = df_vendite['lordo_spedito'] - df_vendite['lordo_reso']

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

def apply_anagrafica(df: pd.DataFrame, df_anag: pd.DataFrame) -> pd.DataFrame:
    """
    Mappa le informazioni dell'anagrafica (genere, descrizione) usando prima lo SKU13,
    e in fallback lo SKU7, replicando la logica del vecchio motore dati.
    """
    # Assicuriamoci che gli SKU in anagrafica siano puliti
    # Adatta i nomi delle colonne 'sku', 'genere' e 'desc' in base agli header reali del tuo CSV anagrafica
    df_anag['sku'] = df_anag['sku'].astype(str).str.strip()
    
    # Creiamo dizionari per un lookup O(1) ultra-veloce
    dict_genere = df_anag.set_index('sku')['genere'].to_dict()
    dict_desc = df_anag.set_index('sku')['descrizione'].to_dict() 
    
    # Applichiamo il lookup in modo vettorializzato sfruttando Pandas (molto più veloce)
    df['genere_raw'] = df['sku_13'].map(dict_genere).fillna(df['sku_7'].map(dict_genere))
    df['descrizione'] = df['sku_13'].map(dict_desc).fillna(df['sku_7'].map(dict_desc))

    # --- Logica di normalizzazione Macro-Genere (Esatta replica del tuo backend.txt) ---
    valid_generi = ["BAMBINO", "BAMBINA", "UOMO", "DONNA", "UNISEX", "ACCESSORI", "ABBIGLIAMENTO"]
    
    # Pulizia
    df['genere_raw'] = df['genere_raw'].fillna("").astype(str).str.strip().str.upper()
    
    # Assegnazione condizionale
    cond_vuoto = df['genere_raw'] == ""
    cond_valido = df['genere_raw'].isin(valid_generi)
    
    df['genere'] = np.where(cond_vuoto, "NON CLASSIFICATO",
                   np.where(cond_valido, df['genere_raw'], "NON MAPPATO"))
    
    # Rimuoviamo la colonna di appoggio
    df.drop(columns=['genere_raw'], inplace=True)
    
    return df
