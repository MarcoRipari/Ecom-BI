# =============================================================================
# config.py
# Porting di CONFIG da AppScript → Python
# Aggiorna TASSI_CAMBIO ogni settimana direttamente qui
# =============================================================================

# -----------------------------------------------------------------------------
# COLONNE DEL DATASET (indici 0-based, stesso ordine del CSV)
# -----------------------------------------------------------------------------
COLS_DATASET = {
    "MKP":       0,
    "NAZ":       1,
    "CLZ":       2,
    "DATA":      4,
    "STATO":     8,
    "ORDINE_ID": 10,
    "VALUTA":    12,
    "PREZZO":    13,
    "IMPORTO":   14,
    "QTA":       15,
    "COUPON":    19,
    "SKU_FULL":  20,
}

# -----------------------------------------------------------------------------
# LOGISTICA ESTERNA — suffissi/pattern nell'ORDINE_ID
# -----------------------------------------------------------------------------
LOGISTICA_ESTERNA = ["_ZFS", "_FBA", "-AMZ"]

# -----------------------------------------------------------------------------
# IVA DEFAULT se la nazione non è mappata
# -----------------------------------------------------------------------------
DEFAULT_IVA = 0.21

# -----------------------------------------------------------------------------
# STAGIONI
# -----------------------------------------------------------------------------
SEASON = {
    "FW": {"inizio_mese": 9,  "inizio_giorno": 1,  "fine_mese": 3,  "fine_giorno": 31, "settimane": 26},
    "SS": {"inizio_mese": 3,  "inizio_giorno": 1,  "fine_mese": 9,  "fine_giorno": 30, "settimane": 26},
}

# -----------------------------------------------------------------------------
# MAPPA COLLEZIONI → BRAND
# -----------------------------------------------------------------------------
MAP_COLLECTION: dict[str, str] = {
    "NATURINO COCOON":              "NATURINO",
    "NATURINO CLASSIC":             "NATURINO",
    "NATURINO SNEAKERS":            "NATURINO",
    "NATURINO OUTDOOR":             "NATURINO",
    "NATURINO WILD LIFE":           "NATURINO",
    "NATURINO ACTIVE":              "NATURINO",
    "NATURINO BABY":                "NATURINO",
    "NATURINO EASY":                "NATURINO",
    "NATURINO BAREFOOT":            "NATURINO",
    "NATURINO RELAX":               "NATURINO",
    "NATURINO ROCK":                "NATURINO",
    "NATURINO MINI":                "NATURINO",
    "NATURINO YOUNG":               "NATURINO",
    "NATURINO ABBIGLIAMENTO":       "NATURINO",
    "NATURINO P_P_G_":              "NATURINO",
    "FALCOTTO SNEAKERS":            "FALCOTTO",
    "FALCOTTO CLASSIC":             "FALCOTTO",
    "FALCOTTO ACTIVE":              "FALCOTTO",
    "FALCOTTO OUTDOOR":             "FALCOTTO",
    "FALCOTTO ROCK":                "FALCOTTO",
    "FALCOTTO NORTH":               "FALCOTTO",
    "FALCOTTO":                     "FALCOTTO",
    "FALCOTTO BABY":                "FALCOTTO",
    "FALCOTTO CULLA ABBIGLIAM":     "FALCOTTO",
    "FALCOTTO ABBIGLIAMENTO":       "FALCOTTO",
    "FLOWER MOUNTAIN":              "FLOWER MOUNTAIN",
    "FLOWER M.BY NATURINO":         "FM BY NAT",
    "FM ACCESSORI":                 "FM ACCESSORI",
    "FLOWER M.ABBIGLIAMENTO BIMBO": "FM ACCESSORI",
    "W6YZ ADULTO":                  "W6YZ",
    "W6YZ Adulto":                  "W6YZ",
    "W6YZ BIMBO":                   "W6YZ BIMBO",
    "W6YZ Bimbo":                   "W6YZ BIMBO",
    "W6YZ Accessori-Abbigliamento": "W6YZ ACCESSORI",
    "VOILE BLANCHE":                "VOILE BLANCHE",
    "VOILE BLANCHE ACCESSORI":      "VB ACCESSORI",
    "CANDICE COOPER":               "CANDICE COOPER",
    "Candice Cooper":               "CANDICE COOPER",
}

# -----------------------------------------------------------------------------
# MAPPA NAZIONI → ISO 2
# -----------------------------------------------------------------------------
MAP_NATION: dict[str, str] = {
    "italia":         "IT",
    "italy":          "IT",
    "france":         "FR",
    "germany":        "DE",
    "spain":          "ES",
    "united kingdom": "GB",
    "united states":  "US",
    "stati uniti":    "US",
    "belgium":        "BE",
    "denmark":        "DK",
    "españa":         "ES",
    "poland":         "PL",
    "sweden":         "SE",
    "monaco":         "FR",
    "nederland":      "NL",
}

# -----------------------------------------------------------------------------
# TASSI DI CAMBIO → EUR
# Aggiornare settimanalmente
# -----------------------------------------------------------------------------
TASSI_CAMBIO: dict[str, float] = {
    "EUR": 1.0000,
    "CZK": 24.161,
    "DKK": 7.4686,
    "GBP": 0.8796,
    "PLN": 4.2380,
    "SEK": 10.9865,
    "USD": 1.1614,
    "CHF": 1.084569,
}

# -----------------------------------------------------------------------------
# ALIQUOTE IVA PER NAZIONE
# -----------------------------------------------------------------------------
IVA: dict[str, float] = {
    "IT": 0.22, "DE": 0.19, "FR": 0.20, "ES": 0.21, "BE": 0.21,
    "NL": 0.21, "AT": 0.20, "PL": 0.23, "SE": 0.25, "DK": 0.25,
    "CH": 0.081,"GB": 0.20, "US": 0.00, "PT": 0.23, "IE": 0.23,
    "GR": 0.24, "CZ": 0.21, "RO": 0.19, "HR": 0.25, "FI": 0.24,
    "HU": 0.27, "SK": 0.20, "BG": 0.20, "SI": 0.22, "LT": 0.21,
    "LV": 0.21, "EE": 0.22, "LU": 0.17, "CY": 0.19, "MT": 0.18,
    "NO": 0.25, "CA": 0.05, "RS": 0.20,
}

# -----------------------------------------------------------------------------
# GENERI VALIDI dall'anagrafica
# -----------------------------------------------------------------------------
GENERI_VALIDI = {
    "BAMBINO", "BAMBINA", "UOMO", "DONNA",
    "UNISEX", "ACCESSORI", "ABBIGLIAMENTO",
}

# -----------------------------------------------------------------------------
# PATTERN TAGLIE
# -----------------------------------------------------------------------------
import re

TAGLIA_NUMERICA    = re.compile(r"^\d+[/]?$")
TAGLIA_ALFANUMERICA = re.compile(r"^(XXS|XS|S|M|L|XL|XXL|XXXL)$", re.IGNORECASE)
