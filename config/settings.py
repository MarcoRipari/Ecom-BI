# config/settings.py
import os

# --- PERCORSI FILE ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATH_VENDITE = os.path.join(BASE_DIR, "data", "VENDITE")
PATH_RESI = os.path.join(BASE_DIR, "data", "RESI")
PATH_BUYING = os.path.join(BASE_DIR, "data", "BUYING")
PATH_HISTORY = os.path.join(BASE_DIR, "data", "history")

FILE_STORICO_PARQUET = os.path.join(PATH_HISTORY, "sales_history.parquet")
FILE_BUYING_PARQUET = os.path.join(PATH_HISTORY, "buying_history.parquet")
FILE_KPI_AGGREGATI = os.path.join(PATH_HISTORY, "kpi_aggregati.parquet")

# --- REGOLE DI BUSINESS ---
ALIQUOTA_IVA_DEFAULT = 1.21  # Divisore per scorporo IVA (21%)
LOGISTICA_ESTERNA = ["_ZFS", "_FBA", "-AMZ"]

# --- DIZIONARI DI MAPPING E UNIFORMRE (Ex CONFIG.MAPS) ---
MAP_COLLECTIONS = {
    'NATURINO COCOON': 'NATURINO',
    'NATURINO CLASSIC': 'NATURINO',
    'NATURINO SNEAKERS': 'NATURINO',
    'NATURINO OUTDOOR': 'NATURINO',
    'NATURINO WILD LIFE': 'NATURINO',
    'NATURINO ACTIVE': 'NATURINO',
    'NATURINO BABY': 'NATURINO',
    'NATURINO EASY': 'NATURINO',
    'NATURINO BAREFOOT': 'NATURINO',
    'NATURINO RELAX': 'NATURINO',
    'NATURINO YOUNG': 'NATURINO',
    'NATURINO ABBIGLIAMENTO': 'NATURINO',
    'NATURINO P_P_G_': 'NATURINO',
    'NATURINO ROCK': 'NATURINO',
    'NATURINO MINI': 'NATURINO',
    'FALCOTTO SNEAKERS': 'FALCOTTO',
    'FALCOTTO CLASSIC': 'FALCOTTO',
    'FALCOTTO ACTIVE': 'FALCOTTO',
    'FALCOTTO OUTDOOR': 'FALCOTTO',
    'FALCOTTO ROCK': 'FALCOTTO',
    'FALCOTTO NORTH': 'FALCOTTO',
    'FALCOTTO ABBIGLIAMENTO': 'FALCOTTO',
    'FALCOTTO': 'FALCOTTO',
    'FALCOTTO BABY': 'FALCOTTO', 
    'FALCOTTO CULLA ABBIGLIAM': 'FALCOTTO',
    'FLOWER M.BY NATURINO': 'FM BY NAT',
    'FLOWER MOUNTAIN': 'FLOWER MOUNTAIN',
    'FM ACCESSORI': 'FM ACCESSORI',
    'FLOWER M.ABBIGLIAMENTO BIMBO': 'FM ACCESSORI',
    'W6YZ ADULTO': 'W6YZ',
    'W6YZ Adulto': 'W6YZ',
    'W6YZ BIMBO': 'W6YZ BIMBO',
    'W6YZ Bimbo': 'W6YZ BIMBO',
    'W6YZ Accessori-Abbigliamento': 'W6YZ ACCESSORI',
    'VOILE BLANCHE': 'VOILE BLANCHE',
    'VOILE BLANCHE ACCESSORI': 'VB ACCESSORI',
    'CANDICE COOPER': 'CANDICE COOPER',
    'Candice Cooper': 'CANDICE COOPER',
}

MAP_COUNTRIES = {
    'italia': 'IT',
    'italy': 'IT',
    'france': 'FR',
    'germany': 'DE',
    'spain': 'ES',
    'united kingdom': 'GB',
    'united states': 'US',
    'stati uniti': 'US',
    'belgium': 'BE',
    'denmark': 'DK',
    'españa': 'ES',
    'poland': 'PL',
    'sweden': 'SE',
    'monaco': 'FR',
    'nederland': 'NL'
}

TASSI_CAMBIO: {
    'EUR': 1.00,
    'CZK': 24.161,
    'DKK': 7.4686,
    'GBP': 0.8796,
    'PLN': 4.238,
    'SEK': 10.9865,
    'USD': 1.1614,
    'CHF': 1.084569,
}

IVA: {
    'IT': 0.22, 'DE': 0.19, 'FR': 0.20, 'ES': 0.21, 'BE': 0.21,
    'NL': 0.21, 'AT': 0.20, 'PL': 0.23, 'SE': 0.25, 'DK': 0.25,
    'CH': 0.081,'GB': 0.20, 'US': 0.00, 'PT': 0.23, 'IE': 0.23,
    'GR': 0.24, 'CZ': 0.21, 'RO': 0.19, 'HR': 0.25, 'FI': 0.24,
    'HU': 0.27, 'SK': 0.20, 'BG': 0.20, 'SI': 0.22, 'LT': 0.21,
    'LV': 0.21, 'EE': 0.22, 'LU': 0.17, 'CY': 0.19, 'MT': 0.18,
    'NO': 0.25, 'CA': 0.05, 'RS': 0.20,
}

# --- TIPI DATI DATASET (Per Coerenza e Ottimizzazione Memoria) ---
DTYPE_VENDITE = {
    'Market Place Sito': 'category',
    'Nazione': 'string',
    'Collezione': 'string',
    'Stato Riga': 'category',
    'Acquirente': 'string',
    'Ordine': 'string',
    'Riga': 'string',
    'Valuta': 'category',
    'Tipo Pagamento': 'category',
    'Coupon': 'string',
    'Id.Articolo.Sku': 'string'
}

DTYPE_BUYING = {
    'Id.Articolo.Sku': 'string',
    'Stagione': 'category',
    'Brand': 'category',
    'Modello': 'string',
    'Quantita_Ordinata': 'int32',
    'Prezzo_Acquisto': 'float64'
}
