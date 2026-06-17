# ==========================================
# 1. MAPPATURA COLLEZIONI E BRAND
# ==========================================
MAPS_COLLECTION = {
    'NATURINO COCOON': 'NATURINO', 'NATURINO CLASSIC': 'NATURINO', 
    'NATURINO SNEAKERS': 'NATURINO', 'NATURINO OUTDOOR': 'NATURINO', 
    'NATURINO WILD LIFE': 'NATURINO', 'NATURINO ACTIVE': 'NATURINO', 
    'NATURINO BABY': 'NATURINO', 'NATURINO EASY': 'NATURINO', 
    'NATURINO BAREFOOT': 'NATURINO', 'NATURINO RELAX': 'NATURINO',
    'NATURINO ROCK': 'NATURINO', 'NATURINO MINI': 'NATURINO',
    'NATURINO YOUNG': 'NATURINO', 
    'NATURINO ABBIGLIAMENTO': 'NATURINO', 'NATURINO P_P_G_': 'NATURINO',
    'FALCOTTO SNEAKERS': 'FALCOTTO', 'FALCOTTO CLASSIC': 'FALCOTTO', 
    'FALCOTTO ACTIVE': 'FALCOTTO', 'FALCOTTO OUTDOOR': 'FALCOTTO',
    'FALCOTTO': 'FALCOTTO', 'FALCOTTO BABY': 'FALCOTTO', 
    'FALCOTTO ROCK': 'FALCOTTO', 'FALCOTTO NORTH': 'FALCOTTO', 
    'FALCOTTO CULLA ABBIGLIAM': 'FALCOTTO', 'FALCOTTO ABBIGLIAMENTO': 'FALCOTTO',
    'FLOWER MOUNTAIN': 'FLOWER MOUNTAIN', 'FLOWER M.BY NATURINO': 'FM BY NAT', 
    'FM ACCESSORI': 'FM ACCESSORI', 'FLOWER M.ABBIGLIAMENTO BIMBO': 'FM ACCESSORI', 
    'W6YZ ADULTO': 'W6YZ', 'W6YZ Adulto': 'W6YZ', 
    'W6YZ BIMBO': 'W6YZ BIMBO', 'W6YZ Bimbo': 'W6YZ BIMBO', 
    'W6YZ Accessori-Abbigliamento': 'W6YZ ACCESSORI',
    'VOILE BLANCHE': 'VOILE BLANCHE', 'VOILE BLANCHE ACCESSORI': 'VB ACCESSORI',
    'CANDICE COOPER': 'CANDICE COOPER', 'Candice Cooper': 'CANDICE COOPER'
}

# ==========================================
# 2. MAPPATURA NAZIONI (Normalizzazione a Codice ISO)
# ==========================================
MAPS_NATION = {
    'italia': 'IT', 'italy': 'IT', 'france': 'FR', 'germany': 'DE', 
    'spain': 'ES', 'united kingdom': 'GB', 'united states': 'US',
    'stati uniti': 'US', 'belgium': 'BE', 'denmark': 'DK', 'españa': 'ES', 
    'poland': 'PL', 'sweden': 'SE', 'monaco': 'FR', 'nederland': 'NL'
}

# ==========================================
# 3. TASSI DI CAMBIO E IVA
# ==========================================
TASSI_CAMBIO = {
    'EUR': 1.00, 'CZK': 24.161, 'DKK': 7.4686, 'GBP': 0.8796,
    'PLN': 4.238, 'SEK': 10.9865, 'USD': 1.1614, 'CHF': 1.084569,
}

IVA_RATES = {
    'IT': 0.22, 'DE': 0.19, 'FR': 0.20, 'ES': 0.21, 'BE': 0.21,
    'NL': 0.21, 'AT': 0.20, 'PL': 0.23, 'SE': 0.25, 'DK': 0.25,
    'CH': 0.081,'GB': 0.20, 'US': 0.00, 'PT': 0.23, 'IE': 0.23,
    'GR': 0.24, 'CZ': 0.21, 'RO': 0.19, 'HR': 0.25, 'FI': 0.24,
    'HU': 0.27, 'SK': 0.20, 'BG': 0.20, 'SI': 0.22, 'LT': 0.21,
    'LV': 0.21, 'EE': 0.22, 'LU': 0.17, 'CY': 0.19, 'MT': 0.18,
    'NO': 0.25, 'CA': 0.05, 'RS': 0.20,
}

DEFAULT_IVA = 0.21

# ==========================================
# 4. LOGISTICA E STAGIONALITÀ
# ==========================================
LOGISTICA_ESTERNA = ["_ZFS", "_FBA", "-AMZ"]
