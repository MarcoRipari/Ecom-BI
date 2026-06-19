import os
import pandas as pd
import sys
import datetime

import json

def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

def fix_anonymized_nations(df, last_col):
    if 'naz' not in df.columns or last_col not in df.columns:
        return df
        
    config_path = "config/nation_mapping.json"
    if not os.path.exists(config_path):
        os.makedirs("config", exist_ok=True)
        default_config = {
            "Miinto": {"action": "order_first_two"},
            "Sarenza": {"action": "set", "value": "FR"}
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
            
    with open(config_path, "r") as f:
        mapping = json.load(f)
        
    mask = df['naz'].astype(str).str.lower().str.strip() == 'anonymized'
    if not mask.any():
        return df
        
    def resolve_single(mkp_val, ordine_val):
        mkp_val = str(mkp_val).strip()
        ordine_val = str(ordine_val).strip()
        
        for key, rule in mapping.items():
            if key.lower() in mkp_val.lower():
                if rule['action'] == 'order_first_two':
                    return ordine_val[:2].upper()
                elif rule['action'] == 'set':
                    return rule['value']
                    
        if '_' in mkp_val:
            return mkp_val.split('_')[0].upper()
            
        if len(mkp_val) >= 2:
            return mkp_val[-2:].upper()
            
        return 'ND'

    df.loc[mask, 'naz'] = df[mask].apply(lambda x: resolve_single(x[last_col], x.get('ordine_id', '')), axis=1)
    return df

def ingest_vendite():
    raw_path = "data/raw/vendite_oggi.csv"
    master_path = "data/storici/master_vendite.parquet"
    if not os.path.exists(raw_path):
        print("Nessun file vendite da processare.")
        return
    
    try:
        df_new = pd.read_csv(raw_path, sep=',', encoding='utf-8', dtype=str)
    except:
        df_new = pd.read_csv(raw_path, sep=';', encoding='utf-8', dtype=str)
    
    df_new = clean_columns(df_new)
    
    last_col = df_new.columns[-1]
    
    # Rinominiamo colonne come in etl.py per coerenza
    rename_dict = {}
    for col in df_new.columns:
        if col == last_col: rename_dict[col] = 'mkp_source_ext'
        elif 'quantit' in col: rename_dict[col] = 'qta'
        elif col == 'collezione': rename_dict[col] = 'clz'
        elif col == 'nazione': rename_dict[col] = 'naz'
        elif col == 'acquirente': rename_dict[col] = 'nome_cliente'
        elif col == 'ordine' or col == 'numero_ordine': rename_dict[col] = 'ordine_id'
        elif 'sku' in col: rename_dict[col] = 'sku_full'
        elif 'market_place' in col or col == 'mkp': rename_dict[col] = 'mkp'
        elif 'unnamed:_8' in col or col == 'stato': rename_dict[col] = 'stato'
    df_new.rename(columns=rename_dict, inplace=True)
    
    last_col_mapped = rename_dict.get(last_col, last_col)
    df_new = fix_anonymized_nations(df_new, last_col_mapped)
    
    if os.path.exists(master_path):
        df_master = pd.read_parquet(master_path).astype(str)
        df_combined = pd.concat([df_master, df_new], ignore_index=True)
        # Deduplicazione su data, ordine, riga, sku
        dedup_cols = [c for c in ['data_pagamento', 'ordine_id', 'riga', 'sku_full'] if c in df_combined.columns]
        if dedup_cols:
            df_combined.drop_duplicates(subset=dedup_cols, keep='last', inplace=True)
    else:
        df_combined = df_new
        
    df_combined.to_parquet(master_path, index=False)
    os.remove(raw_path)
    print("Ingestione vendite completata con successo.")

def ingest_resi():
    raw_path = "data/raw/resi_oggi.csv"
    master_path = "data/storici/master_resi.parquet"
    if not os.path.exists(raw_path):
        print("Nessun file resi da processare.")
        return
        
    try:
        df_new = pd.read_csv(raw_path, sep=',', encoding='utf-8', dtype=str)
    except:
        df_new = pd.read_csv(raw_path, sep=';', encoding='utf-8', dtype=str)
        
    df_new = clean_columns(df_new)
    
    last_col = df_new.columns[-1]
    
    rename_dict = {}
    for col in df_new.columns:
        if col == last_col: rename_dict[col] = 'mkp_source_ext'
        elif 'quantit' in col: rename_dict[col] = 'qta'
        elif col == 'collezione': rename_dict[col] = 'clz'
        elif col == 'nazione': rename_dict[col] = 'naz'
        elif col == 'acquirente': rename_dict[col] = 'nome_cliente'
        elif col == 'ordine' or col == 'numero_ordine': rename_dict[col] = 'ordine_id'
        elif 'sku' in col: rename_dict[col] = 'sku_full'
        elif 'market_place' in col or col == 'mkp': rename_dict[col] = 'mkp'
    df_new.rename(columns=rename_dict, inplace=True)
    
    last_col_mapped = rename_dict.get(last_col, last_col)
    df_new = fix_anonymized_nations(df_new, last_col_mapped)
    
    if os.path.exists(master_path):
        df_master = pd.read_parquet(master_path).astype(str)
        df_combined = pd.concat([df_master, df_new], ignore_index=True)
        # Deduplicazione su data, ordine, riga, sku
        # In resi la data potrebbe chiamarsi diversamente (es. data_reso/sped.)
        date_col = 'data_reso/sped.' if 'data_reso/sped.' in df_combined.columns else 'data_pagamento'
        dedup_cols = [c for c in [date_col, 'ordine_id', 'riga', 'sku_full'] if c in df_combined.columns]
        if dedup_cols:
            df_combined.drop_duplicates(subset=dedup_cols, keep='last', inplace=True)
    else:
        df_combined = df_new
        
    df_combined.to_parquet(master_path, index=False)
    os.remove(raw_path)
    print("Ingestione resi completata con successo.")

def ingest_buying():
    raw_path = "data/raw/buying.csv"
    master_path = "data/storici/buying.parquet"
    if not os.path.exists(raw_path):
        print("Nessun file buying da processare.")
        return
        
    try:
        df_new = pd.read_csv(raw_path, sep=',', encoding='utf-8', dtype=str)
    except:
        df_new = pd.read_csv(raw_path, sep=';', encoding='utf-8', dtype=str)
        
    df_new.to_parquet(master_path, index=False)
    os.remove(raw_path)
    print("Ingestione buying completata con successo.")

def ingest_anagrafica():
    raw_path = "data/raw/anagrafica_new.csv"
    master_path = "data/storici/anagrafica.parquet"
    if not os.path.exists(raw_path):
        print("Nessun file anagrafica da processare.")
        return
        
    try:
        df_new = pd.read_csv(raw_path, sep=',', encoding='utf-8', dtype=str)
    except:
        df_new = pd.read_csv(raw_path, sep=';', encoding='utf-8', dtype=str)
        
    df_new = clean_columns(df_new)
    
    if os.path.exists(master_path):
        df_master = pd.read_parquet(master_path)
        # Upsert: se lo SKU esiste, sovrascrivi, altrimenti aggiungi
        chiave = 'sku' if 'sku' in df_new.columns else df_new.columns[0]
        df_master = df_master[~df_master[chiave].isin(df_new[chiave])]
        df_combined = pd.concat([df_master, df_new], ignore_index=True)
    else:
        df_combined = df_new
        
    df_combined.to_parquet(master_path, index=False)
    os.remove(raw_path)
    print("Ingestione anagrafica completata con successo.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Specifica il tipo di dato da ingestire: vendite, resi, buying, anagrafica")
        sys.exit(1)
        
    tipo = sys.argv[1].lower()
    if tipo == 'vendite':
        ingest_vendite()
    elif tipo == 'resi':
        ingest_resi()
    elif tipo == 'buying':
        ingest_buying()
    elif tipo == 'anagrafica':
        ingest_anagrafica()
    else:
        print(f"Tipo sconosciuto: {tipo}")
