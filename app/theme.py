"""Thème arcade de l'interface, aligné sur les diapos (style Pac-Man, minimaliste).

À importer avant app.charts et app.views : remplace les couleurs de modules.config pour ce processus seulement
(le notebook garde sa palette claire).
"""

from __future__ import annotations

import base64
from pathlib import Path

from modules import config as C

# Couleurs des diapos
NOIR, MUR, MUR_CLAIR = "#000000", "#2121DE", "#3D3DFF"
JAUNE, ROUGE, ROSE, CYAN, ORANGE, PECHE, VERT = "#FFE600", "#FF2D2D", "#FFB8FF", "#00FFFF", "#FFB852", "#FFB8AE", "#00DE00"
TEXTE, TEXTE_2, TEXTE_MUTED, GRILLE, NUIT = "#FFFFFF", "#C4C4E4", "#7C7CAA", "#1A1A4A", "#0A0A2A"

C.PALETTE = [MUR_CLAIR, JAUNE, CYAN, ORANGE, ROSE, VERT, "#B48CFF", ROUGE]
C.GRIS = "#55557A"
C.ENCRE, C.ENCRE_2, C.ENCRE_MUTED = TEXTE, TEXTE_2, TEXTE_MUTED
C.GRILLE, C.SURFACE = GRILLE, NOIR
C.SEQ_BLEU = ["#10104A", "#18187A", MUR, MUR_CLAIR, "#00A8FF", CYAN, JAUNE]
C.DIV_BLEU, C.DIV_NEUTRE, C.DIV_ROUGE = MUR_CLAIR, GRILLE, ROUGE
C.COULEURS_CONSTRUCTEUR = {
    "Nintendo": ROUGE, "Sony": MUR_CLAIR, "Microsoft": VERT, "Sega": "#B48CFF",
    "PC": ORANGE, "Autres": C.GRIS, "Atari": ROSE,
}
C.COULEURS_REGION = {"NA_Sales": CYAN, "EU_Sales": ROSE, "JP_Sales": ROUGE, "Other_Sales": C.GRIS}
CLAIR = "#23236B"  # éléments non sélectionnés

_POLICE = base64.b64encode((Path(__file__).parent / "assets" / "PressStart2P-Regular.ttf").read_bytes()).decode()
PIXEL = "'Press Start 2P', monospace"

CSS = f"""
<style>
@font-face {{font-family: 'Press Start 2P'; src: url(data:font/ttf;base64,{_POLICE}) format('truetype');}}
.block-container {{padding-top: 2.2rem; max-width: 1350px;}}
h1.titre {{font-family: {PIXEL}; font-size: 1.45rem; line-height: 1.6; font-weight: 400; color: {TEXTE}; margin-bottom: 0;}}
p.sous-titre {{color: {TEXTE_2}; font-size: 1.0rem; margin: 0.5rem 0 0.4rem 0;}}
/* Pac-Man et sa rangée de pac-gommes, sous chaque titre */
.pac-ligne {{position: relative; height: 18px; margin: 0.3rem 0 1.4rem 0;
  background: radial-gradient(circle, {PECHE} 2px, transparent 2.6px) 26px 50% / 18px 18px repeat-x;}}
.pac-ligne::before {{content: ""; position: absolute; left: 0; top: 0; width: 18px; height: 18px; border-radius: 50%;
  background: conic-gradient(from 90deg, transparent 0 40deg, {JAUNE} 40deg 320deg, transparent 320deg);
  animation: croque .45s steps(2) infinite;}}
@keyframes croque {{50% {{background: {JAUNE};}}}}
h2, h3 {{font-family: {PIXEL}; font-weight: 400 !important; letter-spacing: 0; line-height: 1.6;}}
h2 {{font-size: 1.05rem !important;}} h3 {{font-size: 0.85rem !important;}}
h2 span, h3 span {{font-family: {PIXEL};}}
div[data-testid="stMetric"] {{background: {NOIR}; border: 2px solid {MUR}; border-radius: 8px; padding: 0.7rem 0.9rem;}}
div[data-testid="stMetricValue"] {{font-family: {PIXEL}; font-size: 0.9rem; color: {JAUNE}; padding-top: 0.3rem;}}
div[data-testid="stMetricValue"] > div {{overflow: visible; text-overflow: clip; white-space: normal; line-height: 1.5;}}
div[data-testid="stMetricLabel"] p {{color: {TEXTE_2};}}
.encart {{background: {NUIT}; border-left: 3px solid {JAUNE}; border-radius: 4px; padding: 0.8rem 1.1rem;
         color: {TEXTE}; margin: 0.4rem 0 1.2rem 0; font-size: 0.97rem;}}
.encart ol, .encart ul {{margin: 0; padding-left: 1.2rem;}} .encart li {{margin: 0.25rem 0;}}
.carte, .zoom {{background: {NOIR}; border: 2px solid {MUR}; border-radius: 10px;
  box-shadow: inset 0 0 0 4px {NOIR}, inset 0 0 0 6px {MUR};}}
.carte {{padding: 1.1rem 1.2rem; min-height: 175px; margin-bottom: 1rem; transition: transform .15s ease, border-color .15s ease;}}
.carte:hover {{transform: translateY(-2px); border-color: {JAUNE};}}
.zoom {{padding: 1rem 1.2rem;}}
.carte-chiffre {{font-family: {PIXEL}; font-size: 1.15rem; color: {JAUNE}; line-height: 1.6;}}
.carte-titre {{font-weight: 600; color: {TEXTE}; margin: 0.35rem 0 0.3rem 0;}}
.carte-texte {{color: {TEXTE_2}; font-size: 0.92rem; line-height: 1.4;}}
section[data-testid="stSidebar"] {{border-right: 2px solid {MUR};}}
section[data-testid="stSidebar"] h3 {{font-size: 0.72rem !important; color: {JAUNE};}}
section[data-testid="stSidebar"] .note {{font-size: 0.82rem; color: {TEXTE_MUTED};}}
div[data-testid="stSidebarNav"] header, div[data-testid="stNavSectionHeader"] {{font-family: {PIXEL}; font-size: 0.6rem; color: {CYAN};}}
.astuce {{color: {TEXTE_MUTED}; font-size: 0.86rem; margin: -0.4rem 0 0.6rem 0;}}
div[data-testid="stPlotlyChart"] {{transition: opacity .2s ease;}}
</style>
"""
