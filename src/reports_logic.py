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
    
    # Calcolo Variazione % con safe division e moltiplicazione x 100
    df_merged['var_fatturato'] = np.where(
        df_merged['fatturato_netto_old'] != 0, 
        (df_merged['fatturato_netto_curr'] / df_merged['fatturato_netto_old'].replace(0, np.nan)) - 1, 
        np.where(df_merged['fatturato_netto_curr'] > 0, 1.0, 0.0)
    ) * 100
    
    df_merged['var_paia'] = np.where(
        df_merged['paia_nette_old'] != 0, 
        (df_merged['paia_nette_curr'] / df_merged['paia_nette_old'].replace(0, np.nan)) - 1, 
        np.where(df_merged['paia_nette_curr'] > 0, 1.0, 0.0)
    ) * 100
    
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
    agg['perc_su_gruppo'] = np.where(tot_gruppo > 0, agg['paia_nette'] / tot_gruppo.replace(0, np.nan), 0) * 100
    agg['perc_reso'] = np.where(agg['paia_spedite'] > 0, agg['paia_rese'] / agg['paia_spedite'].replace(0, np.nan), 0) * 100
    
    return agg.sort_values(['brand', 'sotto_gruppo', 'taglia'])

def aggregate_sellthrough(df_vendite: pd.DataFrame, df_buying: pd.DataFrame) -> pd.DataFrame:
    """Calcola il Sell-Through unendo le vendite e il buying (acquisti)."""
    if df_vendite.empty or df_buying.empty:
        return pd.DataFrame()
        
    # Pulisci il dataframe buying
    df_buying.columns = df_buying.columns.str.strip().str.lower().str.replace(' ', '_')
    if 'articolo' not in df_buying.columns or 'quantita' not in df_buying.columns:
        return pd.DataFrame()
        
    # Il campo ARTICOLO nel buying corrisponde a sku_13 (con i trattini da rimuovere)
    df_buying['sku_13'] = df_buying['articolo'].astype(str).str.replace('-', '').str[:13]
    df_buying['quantita'] = pd.to_numeric(df_buying['quantita'], errors='coerce').fillna(0)
    
    # Aggrega le paie acquistate per SKU
    buying_agg = df_buying.groupby('sku_13')['quantita'].sum().reset_index()
    buying_agg.rename(columns={'quantita': 'paia_acquistate'}, inplace=True)
    
    # Aggrega le vendite per SKU
    vendite_agg = df_vendite.groupby('sku_13').agg(
        paia_nette=('paia_nette', 'sum'),
        fatturato_netto=('netto_netto', 'sum')
    ).reset_index()
    
    # Merge
    merged = pd.merge(buying_agg, vendite_agg, on='sku_13', how='left').fillna(0)
    
    # Calcolo Sell-Through
    merged['sell_through'] = np.where(merged['paia_acquistate'] > 0, 
                                      merged['paia_nette'] / merged['paia_acquistate'], 0) * 100
    
    # Cap a 100% per casi in cui le paia nette superano il buying (riassortimenti non tracciati)
    merged['sell_through'] = merged['sell_through'].clip(upper=100)
    
    # Ordina per Sell-Through e Paia Nette
    return merged.sort_values(['sell_through', 'paia_nette'], ascending=[False, False])

