import pandas as pd
import numpy as np

def calculate_global_metrics(df: pd.DataFrame) -> dict:
    """
    Sostituisce calculateGlobalMetricsDetailed.
    Ritorna le metriche globali divise per perimetro (Totale, Diretti, Esterni).
    """
    metrics = {}
    
    for perimetro, mask in [
        ('tot', pd.Series(True, index=df.index)),  # Tutte le righe
        ('dir', df['tipo_spedizione'] == 'DIRETTO'),
        ('est', df['tipo_spedizione'] == 'ESTERNA')
    ]:
        df_subset = df[mask]
        metrics[perimetro] = {
            'lordo': df_subset['lordo_abs'].sum(),
            'netto': df_subset['netto_netto'].sum(),
            'paia_spedite': df_subset['paia_spedite'].sum(),
            'paia_rese': df_subset['paia_rese'].sum(),
            'paia_nette': df_subset['paia_nette'].sum(),
            'ordini': df_subset['ordine_id'].nunique() # Equivalente a ordiniSet.size
        }
        
    return metrics

def aggregate_by_key(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """
    Sostituisce aggregateByKey. 
    Raggruppa per colonna (es. 'mkp', 'nazione', 'clz_mappata') e calcola le somme.
    Ritorna un DataFrame già ordinato per fatturato netto.
    """
    if key_column not in df.columns:
        return pd.DataFrame()

    agg_df = df.groupby(key_column).agg(
        ordini=('ordine_id', 'nunique'),
        paia_spedite=('paia_spedite', 'sum'),
        paia_rese=('paia_rese', 'sum'),
        paia_nette=('paia_nette', 'sum'),
        fatturato_spedito=('netto_spedito', 'sum'),
        fatturato_netto=('netto_netto', 'sum')
    ).reset_index()

    # Calcolo incidenze e % di reso
    agg_df['perc_reso'] = (agg_df['paia_rese'] / agg_df['paia_spedite'].replace(0, np.nan)).fillna(0) * 100
    agg_df['scontrino_medio'] = (agg_df['fatturato_spedito'] / agg_df['ordini']).fillna(0)
    
    # Ordiniamo per fatturato decrescente
    return agg_df.sort_values(by='fatturato_netto', ascending=False)

def aggregate_by_taglia_brand(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sostituisce aggregateByTagliaPerBrand.
    Struttura flat perfetta per Streamlit: Brand -> Genere -> Taglia
    """
    # Se il genere non è mappato, usiamo un default
    if 'genere' not in df.columns:
        df['genere'] = 'NON CLASSIFICATO'
        
    agg_df = df.groupby(['clz_mappata', 'genere', 'taglia_raw']).agg(
        paia_spedite=('paia_spedite', 'sum'),
        paia_rese=('paia_rese', 'sum'),
        paia_nette=('paia_nette', 'sum'),
        fatturato_netto=('netto_netto', 'sum')
    ).reset_index()
    
    return agg_df
