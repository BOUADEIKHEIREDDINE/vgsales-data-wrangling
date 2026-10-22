"""Constantes partagées par le notebook et l'interface : chemins, régions, plateformes, couleurs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "BDD_states"
RAW_FILE = DATA_DIR / "vgsales.csv"
CLEAN_FILE = DATA_DIR / "vgsales_clean.csv"
MPI_FILE = DATA_DIR / "market_power_index.csv"
DIVERGENCE_FILE = DATA_DIR / "divergence_regionale.csv"
FIGURES_DIR = ROOT / "figures"

# Le fichier provient d'un scraping VGChartz réalisé fin 2016 : l'année 2016 est incomplète.
ANNEE_MAX = 2016
ANNEE_PARTIELLE = 2016

# Seuil "hit" : un titre qui dépasse le million d'exemplaires (convention du secteur).
SEUIL_HIT = 1.0

REGIONS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
REGION_LABELS = {
    "NA_Sales": "Amérique du Nord",
    "EU_Sales": "Europe",
    "JP_Sales": "Japon",
    "Other_Sales": "Reste du monde",
}
REGION_SHORT = {"NA_Sales": "NA", "EU_Sales": "EU", "JP_Sales": "JP", "Other_Sales": "Autres"}

# Code plateforme -> (nom complet, constructeur, type, génération, année de lancement)
PLATEFORMES = {
    "2600": ("Atari 2600", "Atari", "Salon", 2, 1977),
    "NES": ("NES", "Nintendo", "Salon", 3, 1983),
    "SNES": ("Super Nintendo", "Nintendo", "Salon", 4, 1990),
    "N64": ("Nintendo 64", "Nintendo", "Salon", 5, 1996),
    "GC": ("GameCube", "Nintendo", "Salon", 6, 2001),
    "Wii": ("Wii", "Nintendo", "Salon", 7, 2006),
    "WiiU": ("Wii U", "Nintendo", "Salon", 8, 2012),
    "GB": ("Game Boy", "Nintendo", "Portable", 4, 1989),
    "GBA": ("Game Boy Advance", "Nintendo", "Portable", 6, 2001),
    "DS": ("Nintendo DS", "Nintendo", "Portable", 7, 2004),
    "3DS": ("Nintendo 3DS", "Nintendo", "Portable", 8, 2011),
    "PS": ("PlayStation", "Sony", "Salon", 5, 1994),
    "PS2": ("PlayStation 2", "Sony", "Salon", 6, 2000),
    "PS3": ("PlayStation 3", "Sony", "Salon", 7, 2006),
    "PS4": ("PlayStation 4", "Sony", "Salon", 8, 2013),
    "PSP": ("PSP", "Sony", "Portable", 7, 2004),
    "PSV": ("PS Vita", "Sony", "Portable", 8, 2011),
    "XB": ("Xbox", "Microsoft", "Salon", 6, 2001),
    "X360": ("Xbox 360", "Microsoft", "Salon", 7, 2005),
    "XOne": ("Xbox One", "Microsoft", "Salon", 8, 2013),
    "GEN": ("Mega Drive", "Sega", "Salon", 4, 1988),
    "SCD": ("Mega-CD", "Sega", "Salon", 4, 1991),
    "SAT": ("Saturn", "Sega", "Salon", 5, 1994),
    "DC": ("Dreamcast", "Sega", "Salon", 6, 1998),
    "GG": ("Game Gear", "Sega", "Portable", 4, 1990),
    "PC": ("PC", "PC", "PC", 0, 1980),
    "NG": ("Neo Geo", "Autres", "Salon", 4, 1990),
    "TG16": ("TurboGrafx-16", "Autres", "Salon", 4, 1987),
    "3DO": ("3DO", "Autres", "Salon", 5, 1993),
    "PCFX": ("PC-FX", "Autres", "Salon", 5, 1994),
    "WS": ("WonderSwan", "Autres", "Portable", 5, 1999),
}

GENRES_FR = {
    "Action": "Action",
    "Adventure": "Aventure",
    "Fighting": "Combat",
    "Misc": "Divers",
    "Platform": "Plates-formes",
    "Puzzle": "Puzzle",
    "Racing": "Course",
    "Role-Playing": "RPG",
    "Shooter": "Tir",
    "Simulation": "Simulation",
    "Sports": "Sport",
    "Strategy": "Stratégie",
}

# Palette catégorielle validée (ordre fixe, jamais recyclé) + encre et surfaces.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GRIS = "#b8b7b0"
ENCRE = "#0b0b0b"
ENCRE_2 = "#52514e"
ENCRE_MUTED = "#898781"
GRILLE = "#e1e0d9"
SURFACE = "#fcfcfb"
SEQ_BLEU = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIV_BLEU, DIV_NEUTRE, DIV_ROUGE = "#256abf", "#f0efec", "#d03b3b"

# Couleur fixe par entité : une couleur suit toujours le même constructeur / la même région.
COULEURS_CONSTRUCTEUR = {
    "Nintendo": PALETTE[7],
    "Sony": PALETTE[0],
    "Microsoft": PALETTE[5],
    "Sega": PALETTE[6],
    "PC": PALETTE[3],
    "Autres": GRIS,
    "Atari": PALETTE[1],
}
COULEURS_REGION = {
    "NA_Sales": PALETTE[0],
    "EU_Sales": PALETTE[1],
    "JP_Sales": PALETTE[2],
    "Other_Sales": GRIS,
}
# Ordre d'empilement validé (couleurs adjacentes distinguables, y compris daltonisme).
ORDRE_CONSTRUCTEURS = ["Atari", "Sega", "Nintendo", "Sony", "Microsoft", "PC", "Autres"]

# --------------------------------------------------------------------------------------
# Deuxième base : notes Metacritic (Kaggle rush4ratio, scraping du 22/12/2016)
# --------------------------------------------------------------------------------------
RATINGS_RAW_FILE = DATA_DIR / "video_games_ratings.csv"
RATINGS_CLEAN_FILE = DATA_DIR / "video_games_ratings_clean.csv"
JOINTURE_FILE = DATA_DIR / "vgsales_ratings_joint.csv"

# Classification d'âge ESRB : code -> libellé (K-A est l'ancien nom de E, avant 1998).
ESRB_LABELS = {
    "EC": "Petite enfance (3+)",
    "E": "Tout public",
    "E10+": "10 ans et plus",
    "T": "Adolescents (13+)",
    "M": "Adultes (17+)",
    "AO": "Adultes uniquement (18+)",
    "RP": "En attente de classification",
}
