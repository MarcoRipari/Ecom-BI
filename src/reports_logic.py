import pandas as pd
import numpy as np

def filter_carryover_data(df_curr: pd.DataFrame, df_old: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filtra i dataset mantenendo solo gli SKU (sku_13) presenti in ENTRAMBI i periodi."""
    if df_curr.empty or df_old.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    old_skus = set(df_old['sku_13'].unique())
    current_carryover = df_curr[df_curr['sku_13'].isin(old_skus)]
    
    current_skus = set(current_carryover['sku_13'].unique())
    old_carryover = df_old[df_old['sku_13'].isin(current_skus)]
    
    return current_carryover, old_carryover

def aggregate_y2y(df_curr: pd.DataFrame, df_old: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Aggrega e unisce due dataframe su una colonna per la comparativa Y2Y."""
    from src.metrics import aggregate_by_key
    
    agg_c = aggregate_by_key(df_curr, group_col)
    agg_o = aggregate_by_key(df_old, group_col)
    
    if agg_c.empty and agg_o.empty:
        return pd.DataFrame()
        
    if agg_c.empty:
        agg_c = pd.DataFrame(columns=agg_o.columns)
    if agg_o.empty:
        agg_o = pd.DataFrame(columns=agg_c.columns)
        
    # Rinomina colonne per fare il merge
    agg_c.columns = [group_col] + [f"{c}_curr" for c in agg_c.columns if c != group_col]
    agg_o.columns = [group_col] + [f"{c}_old" for c in agg_o.columns if c != group_col]
    
    df_merged = pd.merge(agg_c, agg_o, on=group_col, how='outer').fillna(0)
    
    # Calcolo Variazione %
    df_merged['var_fatturato'] = np.where(
        df_merged['fatturato_netto_old'] != 0, 
        (df_merged['fatturato_netto_curr'] / df_merged['fatturato_netto_old']) - 1, 
        np.where(df_merged['fatturato_netto_curr'] > 0, 1.0, 0.0)
    )
    
    df_merged['var_paia'] = np.where(
        df_merged['paia_nette_old'] != 0, 
        (df_merged['paia_nette_curr'] / df_merged['paia_nette_old']) - 1, 
        np.where(df_merged['paia_nette_curr'] > 0, 1.0, 0.0)
    )
    
    return df_merged.sort_values('fatturato_netto_curr', ascending=False)

def aggregate_taglie(df: pd.DataFrame) -> pd.DataFrame:
    """Aggrega per Taglia all'interno di Brand e Genere."""
    if df.empty:
        return pd.DataFrame()
        
    # Assicura il mapping corretto per il Genere
    valid_genders = ["UOMO", "DONNA", "UNISEX", "BAMBINO", "BAMBINA", "ACCESSORI", "ABBIGLIAMENTO"]
    df['sotto_gruppo'] = df['genere'].apply(lambda x: x if x in valid_genders else "NON CLASSIFICATO")
    df['brand'] = df['clz_mappata'].fillna("ALTRO")
    df['taglia'] = df['taglia_raw'].fillna("ND")
    
    agg = df.groupby(['brand', 'sotto_gruppo', 'taglia']).agg(
        paia_nette=('paia_nette', 'sum'),
        paia_spedite=('paia_spedite', 'sum'),
        paia_rese=('paia_rese', 'sum'),
        fatturato_netto=('netto_netto', 'sum')
    ).reset_index()
    
    # Calcola il totale per gruppo per la percentuale
    tot_gruppo = agg.groupby(['brand', 'sotto_gruppo'])['paia_nette'].transform('sum')
    agg['perc_su_gruppo'] = np.where(tot_gruppo > 0, agg['paia_nette'] / tot_gruppo, 0)
    agg['perc_reso'] = np.where(agg['paia_spedite'] > 0, agg['paia_rese'] / agg['paia_spedite'], 0)
    
    return agg.sort_values(['brand', 'sotto_gruppo', 'taglia'])
