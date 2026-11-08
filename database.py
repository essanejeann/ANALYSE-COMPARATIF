#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion de la base de données SQLite pour l'Analyse Boutique.
Auteur : ESSANE Jean-Noël — Génie Logiciel (Licence 2)
Date   : Novembre 2026
ULTRA-OPTIMISÉ :
  • Mode WAL (Write-Ahead Logging) + PRAGMA haute performance (cache 64MB, temp mémoire)
  • Index Inversé O(1) pour l'appariement textuel (Information Retrieval)
  • Vues SQL pré-compilées (v_comparatif, v_synthese_black_friday)
  • Index composites B-Tree sur les clés de jointure et plages de dates
"""

import sys
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
import pandas as pd

# Encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DOSSIER_RACINE  = Path(__file__).parent
DOSSIER_DONNEES = DOSSIER_RACINE / "data"
if not (DOSSIER_DONNEES / "catalogue_reference.csv").exists():
    DOSSIER_DONNEES = DOSSIER_DONNEES / "Analyse comparative - etudiants" / "donnees"

CHEMIN_BD = DOSSIER_RACINE / "boutique.db"

# Regex & constantes de nettoyage
RE_CHIFFRES = re.compile(r"\d+")
RE_PONCT    = re.compile(r'[()"\'\-/,;:.]')
RE_ESPACES  = re.compile(r"\s+")
TABLE_ACCENTS = str.maketrans({
    "É": "E", "È": "E", "Ê": "E", "Ë": "E", "À": "A", "Â": "A", "Ô": "O",
    "Ù": "U", "Û": "U", "Ç": "C", "Î": "I", "Ï": "I",
    "é": "e", "è": "e", "ê": "e", "ë": "e", "à": "a", "â": "a", "ô": "o",
    "ù": "u", "û": "u", "ç": "c", "î": "i", "ï": "i"
})
SYNONYMES = {
    "MICROWAVE": "MICRO ONDES", "FRIDGE": "REFRIGERATEUR", "BLENDER": "MIXEUR",
    "IRON": "FER REPASSER", "KETTLE": "BOUILLOIRE", "MONITOR": "ECRAN",
    "PRINTER": "IMPRIMANTE", "MOUSE": "SOURIS", "WIRELESS": "SANS FIL",
    "AIR CONDITIONER": "CLIMATISEUR"
}
MOTS_GENERIQUES = {"DE", "LE", "LA", "LES", "DU", "DES", "EN", "UN", "UNE",
                   "SSD", "HDD", "RAM", "GO", "GB", "TO", "TB", "L",
                   "PC", "PORTABLE", "FCFA", "CV", "POUCES"}
MOTS_ELEC = {"MICROWAVE", "MICRO", "ONDES", "FRIDGE", "FRIGO", "REFRIGERATEUR",
             "CONGELATEUR", "CLIMATISEUR", "CLIM", "VENTILATEUR", "VENTILO",
             "MIXEUR", "BLENDER", "FER", "IRON", "BOUILLOIRE", "KETTLE", "TV"}
MOTS_TEL  = {"GALAXY", "IPHONE", "SPARK", "CAMON", "HOT", "NOTE", "REDMI", "ITEL", "A15", "A25", "A55", "A70"}


def get_connexion(db_path=CHEMIN_BD):
    """
    Ouvre une connexion SQLite boostée avec PRAGMA haute performance :
      • WAL mode : lectures/écritures simultanées ultra-rapides
      • synchronous = NORMAL : élimine les blocages disque inutiles
      • cache_size = -64000 : 64 Mo de cache en RAM
      • temp_store = MEMORY : opérations temporaires en RAM
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def creer_schema(conn):
    """Crée les tables SQL, index composites et vues pré-compilées."""
    cursor = conn.cursor()
    cursor.executescript("""
    -- Table du catalogue de référence (30 produits)
    CREATE TABLE IF NOT EXISTS catalogue (
        produit_id TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        categorie TEXT NOT NULL,
        marque TEXT NOT NULL
    );

    -- Table des relevés de prix actuels par enseigne
    CREATE TABLE IF NOT EXISTS releves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enseigne TEXT NOT NULL,
        reference TEXT,
        designation TEXT NOT NULL,
        prix_brut REAL,
        remise_pct REAL DEFAULT 0,
        frais_livraison REAL DEFAULT 0,
        prix_net REAL,
        en_stock BOOLEAN NOT NULL DEFAULT 1,
        produit_id TEXT,
        FOREIGN KEY (produit_id) REFERENCES catalogue (produit_id)
    );

    -- Table historique des prix quotidiens (20 876 enregistrements)
    CREATE TABLE IF NOT EXISTS historique (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_releve TEXT NOT NULL,
        source TEXT NOT NULL,
        produit_id TEXT NOT NULL,
        prix_fcfa INTEGER NOT NULL,
        FOREIGN KEY (produit_id) REFERENCES catalogue (produit_id)
    );

    -- Journal des anomalies détectées pendant le nettoyage
    CREATE TABLE IF NOT EXISTS journal_anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enseigne TEXT NOT NULL,
        type_anomalie TEXT NOT NULL,
        description TEXT NOT NULL
    );

    -- Index composites B-Tree pour requêtes instantanées
    CREATE INDEX IF NOT EXISTS idx_releves_prod_ens ON releves(produit_id, enseigne, en_stock);
    CREATE INDEX IF NOT EXISTS idx_hist_source_date_prod ON historique(source, date_releve, produit_id);
    CREATE INDEX IF NOT EXISTS idx_hist_prod_date ON historique(produit_id, date_releve);

    -- VUE PRÉ-COMPILÉE : Comparatif des 3 enseignes
    DROP VIEW IF EXISTS v_comparatif;
    CREATE VIEW v_comparatif AS
    SELECT 
        c.produit_id,
        c.nom,
        c.categorie,
        c.marque,
        MAX(CASE WHEN r.enseigne = 'Marché Lagune' THEN r.prix_net END) AS prix_lagune,
        MAX(CASE WHEN r.enseigne = 'Marché Lagune' THEN r.en_stock END) AS stock_lagune,
        MAX(CASE WHEN r.enseigne = 'Baobab Shop' THEN r.prix_net END) AS prix_baobab,
        MAX(CASE WHEN r.enseigne = 'Baobab Shop' THEN r.en_stock END) AS stock_baobab,
        MAX(CASE WHEN r.enseigne = 'Comptoir Ivoire' THEN r.prix_net END) AS prix_ivoire,
        MAX(CASE WHEN r.enseigne = 'Comptoir Ivoire' THEN r.en_stock END) AS stock_ivoire
    FROM catalogue c
    LEFT JOIN releves r ON c.produit_id = r.produit_id
    GROUP BY c.produit_id;

    -- VUE PRÉ-COMPILÉE : Synthèse Black Friday vs Année
    DROP VIEW IF EXISTS v_synthese_black_friday;
    CREATE VIEW v_synthese_black_friday AS
    SELECT 
        source,
        ROUND(AVG(prix_fcfa)) AS moy_annuelle,
        ROUND(AVG(CASE WHEN date_releve BETWEEN '2025-11-24' AND '2025-11-30' THEN prix_fcfa END)) AS moy_black_friday,
        COUNT(DISTINCT produit_id) AS nb_produits,
        COUNT(*) AS total_releves
    FROM historique
    GROUP BY source;
    """)
    conn.commit()


def extraire_prix(val):
    """Extraction optimisée de prix numérique."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if val_str.lower() in ("prix sur demande", "n/a", "", "-"):
        return None
    chiffres = RE_CHIFFRES.findall(val_str)
    return float("".join(chiffres)) if chiffres else None


def normaliser(texte):
    t = str(texte).upper().translate(TABLE_ACCENTS)
    t = RE_PONCT.sub(" ", t)
    return RE_ESPACES.sub(" ", t).strip()


def tokeniser(texte):
    t = normaliser(texte)
    for eng, fr in SYNONYMES.items():
        if eng in t:
            t += " " + fr
    return set(t.split()) - MOTS_GENERIQUES


def initialiser_base():
    """Charge les données, nettoie et insère dans SQLite avec index inversé."""
    conn = get_connexion()
    creer_schema(conn)
    cursor = conn.cursor()

    # Vider les tables
    cursor.execute("DELETE FROM journal_anomalies;")
    cursor.execute("DELETE FROM releves;")
    cursor.execute("DELETE FROM historique;")
    cursor.execute("DELETE FROM catalogue;")
    conn.commit()

    anomalies = []

    # 1. CATALOGUE DE RÉFÉRENCE & CRÉATION DE L'INDEX INVERSÉ
    df_cat = pd.read_csv(DOSSIER_DONNEES / "catalogue_reference.csv")
    for _, row in df_cat.iterrows():
        cursor.execute(
            "INSERT INTO catalogue (produit_id, nom, categorie, marque) VALUES (?, ?, ?, ?)",
            (row["produit_id"], row["nom"], row["categorie"], row["marque"])
        )
    conn.commit()

    # Structure de l'Index Inversé : mot -> liste de (produit_id, info)
    index_inverse = defaultdict(list)
    cat_lookup = {}
    for _, row in df_cat.iterrows():
        pid = row["produit_id"]
        mots = tokeniser(row["nom"])
        mots.add(normaliser(row["marque"]))
        info_prod = {
            "produit_id": pid,
            "marque": normaliser(row["marque"]),
            "mots": mots,
            "est_tel": row["categorie"] == "Smartphone",
            "est_elec": row["categorie"] == "Électroménager",
        }
        cat_lookup[pid] = info_prod
        for mot in mots:
            index_inverse[mot].append(pid)

    # Fonction de matching via Index Inversé O(1)
    def matcher_index_inverse(designation, seuil=2):
        mots_item = tokeniser(designation)
        item_tel = bool(mots_item & MOTS_TEL)
        item_elec = bool(mots_item & MOTS_ELEC)

        # Récupération immédiate des candidats via l'index inversé
        candidats = set()
        for m in mots_item:
            if m in index_inverse:
                candidats.update(index_inverse[m])

        best_id, best_score = None, 0
        for pid in candidats:
            c = cat_lookup[pid]
            score = len(mots_item & c["mots"])
            if c["marque"] in mots_item:
                score += 2
            if item_tel and c["est_elec"]:
                score -= 3
            if item_elec and c["est_tel"]:
                score -= 3
            if score > best_score:
                best_score = score
                best_id = pid

        return best_id if best_score >= seuil else None

    # 2. MARCHÉ LAGUNE
    df_lagune = pd.read_csv(DOSSIER_DONNEES / "marche_lagune.csv", sep=";", encoding="utf-8-sig")
    vus_refs = set()
    for _, r in df_lagune.iterrows():
        ref = str(r["reference"]).strip()
        desig = str(r["designation"]).strip()
        p_brut = extraire_prix(r["prix"])
        dispo = r["disponibilite"] in ("En stock", "Stock limité")

        if ref in vus_refs:
            anomalies.append(("Marché Lagune", "DOUBLON", f"Référence '{ref}' en double supprimée."))
            continue
        vus_refs.add(ref)

        if p_brut and p_brut > 600000 and any(m in desig.upper() for m in ["TECNO", "INFINIX", "ITEL", "REDMI"]):
            anomalies.append(("Marché Lagune", "PRIX_ABERRANT", f"Prix erroné de {p_brut:,.0f} FCFA pour '{desig}' exclu."))
            p_brut = None

        if p_brut is None:
            anomalies.append(("Marché Lagune", "PRIX_NON_EXPLOITABLE", f"Prix invalide pour '{desig}'."))

        pid = matcher_index_inverse(desig)
        cursor.execute("""
            INSERT INTO releves (enseigne, reference, designation, prix_brut, remise_pct, frais_livraison, prix_net, en_stock, produit_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Marché Lagune", ref, desig, p_brut, 0, 0, p_brut, 1 if dispo else 0, pid))

    # 3. BAOBAB SHOP
    with open(DOSSIER_DONNEES / "baobab_shop.json", encoding="utf-8") as f:
        baobab_json = json.load(f)

    for it in baobab_json["items"]:
        sku = it["sku"]
        titre = it["title"]
        amount = it["pricing"]["amount"]
        fee = it["pricing"]["delivery_fee"]
        stock = it["stock"]
        en_stock = stock > 0
        prix_net = (amount + fee) if amount is not None else None

        if amount is None:
            anomalies.append(("Baobab Shop", "PRIX_NULL", f"Prix null pour '{titre}'. Article exclu."))
        if not en_stock:
            anomalies.append(("Baobab Shop", "RUPTURE_STOCK", f"'{titre}' en rupture (stock={stock})."))

        pid = matcher_index_inverse(titre)
        cursor.execute("""
            INSERT INTO releves (enseigne, reference, designation, prix_brut, remise_pct, frais_livraison, prix_net, en_stock, produit_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Baobab Shop", sku, titre, amount, 0, fee, prix_net, 1 if en_stock else 0, pid))

    # 4. COMPTOIR IVOIRE
    df_ivoire = pd.read_excel(DOSSIER_DONNEES / "comptoir_ivoire.xlsx", sheet_name="Tarifs octobre 2026", header=2)
    for _, r in df_ivoire.iterrows():
        code = str(r["Code"]).strip()
        art = str(r["Article"]).strip()
        p_cat = extraire_prix(r["Prix catalogue (FCFA)"])
        remise = float(r["Remise (%)"]) if pd.notna(r["Remise (%)"]) else 0.0
        qte = int(r["Quantité en rayon"]) if pd.notna(r["Quantité en rayon"]) else 0
        en_stock = qte > 0
        prix_net = round(p_cat * (1 - remise / 100)) if p_cat else None

        if remise > 0 and p_cat:
            anomalies.append(("Comptoir Ivoire", "REMISE_APPLIQUEE", f"Remise de {int(remise)}% appliquée sur '{art}'."))
        if not en_stock:
            anomalies.append(("Comptoir Ivoire", "RUPTURE_STOCK", f"'{art}' en rupture (quantité={qte})."))

        pid = matcher_index_inverse(art)
        cursor.execute("""
            INSERT INTO releves (enseigne, reference, designation, prix_brut, remise_pct, frais_livraison, prix_net, en_stock, produit_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Comptoir Ivoire", code, art, p_cat, remise, 0, prix_net, 1 if en_stock else 0, pid))

    # 5. HISTORIQUE EN BATCH RAPIDE (executemany)
    df_hist = pd.read_csv(DOSSIER_DONNEES / "historique_prix.csv")
    tuples_hist = [
        (r["date"], r["source"], r["produit_id"], int(r["prix_fcfa"]))
        for _, r in df_hist.iterrows()
    ]
    cursor.executemany("""
        INSERT INTO historique (date_releve, source, produit_id, prix_fcfa)
        VALUES (?, ?, ?, ?)
    """, tuples_hist)

    # 6. ENREGISTREMENT DES ANOMALIES
    for ens, t_anom, desc in anomalies:
        cursor.execute(
            "INSERT INTO journal_anomalies (enseigne, type_anomalie, description) VALUES (?, ?, ?)",
            (ens, t_anom, desc)
        )

    conn.commit()
    conn.close()
    return len(df_cat), len(tuples_hist), len(anomalies)


if __name__ == "__main__":
    nb_cat, nb_hist, nb_anom = initialiser_base()
    print(f"Base '{CHEMIN_BD.name}' optimisée WAL : {nb_cat} produits, {nb_hist} lignes historiques, {nb_anom} anomalies.")
