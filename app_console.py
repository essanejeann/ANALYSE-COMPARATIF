#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Console Interactive — Système d'Analyse Comparative Boutique
Connectée à la base de données SQLite 'boutique.db'.

Permet d'interroger la base, comparer les enseignes, simuler des paniers,
analyser les promotions historiques et exécuter du SQL directement en console.

Auteur : ESSANE Jean-Noël — Génie Logiciel (Licence 2)
Date   : Novembre 2026
"""

import sys
import os
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

# Encodage console Windows UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import database

CHEMIN_BD = Path(__file__).parent / "boutique.db"


def cls():
    """Efface l'écran console si possible."""
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    """Attend que l'utilisateur appuie sur Entrée."""
    input("\nAppuyez sur [Entrée] pour continuer...")


def formater_prix(val):
    """Formate un prix en FCFA avec séparateurs d'espaces."""
    if val is None or pd.isna(val) or val == "":
        return "         -"
    return f"{int(val):>10,}".replace(",", " ") + " F"


def menu_1_reinitialiser():
    """Option 1 : Réinitialiser la base SQLite."""
    print("\n" + "=" * 65)
    print(" [1] SYNCHRONISATION ET INITIALISATION DE LA BASE SQL")
    print("=" * 65)
    print("Lecture des fichiers (CSV, JSON, Excel) et nettoyage...")
    nb_cat, nb_hist, nb_anom = database.initialiser_base()
    print("\n✓ Base de données 'boutique.db' synchronisée avec succès !")
    print(f"  • Produits dans le catalogue    : {nb_cat}")
    print(f"  • Historique annuel des prix   : {nb_hist:,} lignes".replace(",", " "))
    print(f"  • Anomalies répertoriées en BD : {nb_anom}")
    pause()


def menu_2_comparatif():
    """Option 2 : Tableau comparatif avec filtre de catégorie."""
    print("\n" + "=" * 65)
    print(" [2] TABLEAU COMPARATIF DES PRIX")
    print("=" * 65)
    print("Filtrer par catégorie :")
    print("  1. Tous les produits")
    print("  2. Smartphones uniquement")
    print("  3. Informatique uniquement")
    print("  4. Électroménager uniquement")
    choix_cat = input("\nVotre choix (1-4) [Défaut: 1] : ").strip()

    filtre_sql = ""
    if choix_cat == "2":
        filtre_sql = "WHERE categorie = 'Smartphone'"
    elif choix_cat == "3":
        filtre_sql = "WHERE categorie = 'Informatique'"
    elif choix_cat == "4":
        filtre_sql = "WHERE categorie = 'Électroménager'"

    conn = database.get_connexion()

    # Requête instantanée sur la vue SQL pré-compilée
    sql = f"""
    SELECT 
        produit_id,
        nom,
        categorie,
        marque,
        prix_lagune,
        stock_lagune,
        prix_baobab,
        stock_baobab,
        prix_ivoire,
        stock_ivoire
    FROM v_comparatif
    {filtre_sql}
    ORDER BY produit_id;
    """

    df = pd.read_sql_query(sql, conn)
    conn.close()

    if df.empty:
        print("\nAucun produit trouvé pour ce filtre.")
        pause()
        return

    print("\n" + "-" * 115)
    print(f"{'ID':<4} {'Nom du produit':<36} {'M. Lagune':>13} {'Baobab Shop':>13} {'C. Ivoire':>13} {'Moins cher':<18} {'Écart %':>8}")
    print("-" * 115)

    compteur_moins_cher = {"Marché Lagune": 0, "Baobab Shop": 0, "Comptoir Ivoire": 0}

    for _, row in df.iterrows():
        prix_dispos = {}
        # Marché Lagune
        if pd.notna(row["prix_lagune"]):
            s = "(rupture)" if not row["stock_lagune"] else formater_prix(row["prix_lagune"])
            if row["stock_lagune"]:
                prix_dispos["Marché Lagune"] = row["prix_lagune"]
        else:
            s = "      -"
        ml_str = s

        # Baobab Shop
        if pd.notna(row["prix_baobab"]):
            s = "(rupture)" if not row["stock_baobab"] else formater_prix(row["prix_baobab"])
            if row["stock_baobab"]:
                prix_dispos["Baobab Shop"] = row["prix_baobab"]
        else:
            s = "      -"
        bb_str = s

        # Comptoir Ivoire
        if pd.notna(row["prix_ivoire"]):
            s = "(rupture)" if not row["stock_ivoire"] else formater_prix(row["prix_ivoire"])
            if row["stock_ivoire"]:
                prix_dispos["Comptoir Ivoire"] = row["prix_ivoire"]
        else:
            s = "      -"
        ci_str = s

        if len(prix_dispos) >= 2:
            ens_min = min(prix_dispos, key=prix_dispos.get)
            p_min = prix_dispos[ens_min]
            p_max = max(prix_dispos.values())
            pct = round(((p_max - p_min) / p_min) * 100, 1)
            moins_cher_str = ens_min
            ecart_str = f"+{pct}%"
            compteur_moins_cher[ens_min] += 1
        elif len(prix_dispos) == 1:
            moins_cher_str = list(prix_dispos.keys())[0] + " (seul dispo)"
            ecart_str = "-"
        else:
            moins_cher_str = "Rupture totale"
            ecart_str = "-"

        print(f"{row['produit_id']:<4} {row['nom'][:35]:<36} {ml_str:>13} {bb_str:>13} {ci_str:>13} {moins_cher_str:<18} {ecart_str:>8}")

    print("-" * 115)
    print("RÉSUMÉ :")
    for ens, nb in compteur_moins_cher.items():
        print(f"  • {ens:<18} : {nb} fois le moins cher sur cette sélection")
    pause()


def menu_3_recherche():
    """Option 3 : Rechercher un produit spécifique."""
    print("\n" + "=" * 65)
    print(" [3] RECHERCHER UN PRODUIT")
    print("=" * 65)
    terme = input("Entrez un mot-clé ou un identifiant (ex: 'Galaxy', 'Lenovo', 'P04') : ").strip()
    if not terme:
        return

    conn = database.get_connexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.produit_id, c.nom, c.categorie, c.marque
        FROM catalogue c
        WHERE c.produit_id LIKE ? OR c.nom LIKE ? OR c.marque LIKE ?
    """, (f"%{terme}%", f"%{terme}%", f"%{terme}%"))
    produits = cursor.fetchall()

    if not produits:
        print(f"\nAucun produit ne correspond à '{terme}'.")
        conn.close()
        pause()
        return

    print(f"\n{len(produits)} produit(s) trouvé(s) :\n")
    for prod in produits:
        pid = prod["produit_id"]
        print(f"============================================================")
        print(f" [{pid}] {prod['nom']} ({prod['categorie']} - Marque: {prod['marque']})")
        print(f"============================================================")

        cursor.execute("""
            SELECT enseigne, designation, prix_brut, remise_pct, frais_livraison, prix_net, en_stock
            FROM releves
            WHERE produit_id = ?
        """, (pid,))
        releves = cursor.fetchall()

        if not releves:
            print("  Aucun relevé disponible pour cet article.")
            continue

        prix_valides = {}
        for r in releves:
            ens = r["enseigne"]
            p_net = r["prix_net"]
            stock = "EN STOCK" if r["en_stock"] else "RUPTURE DE STOCK"
            detail_prix = ""
            if r["remise_pct"] > 0:
                detail_prix = f"(Prix catalogue: {r['prix_brut']:,.0f} F - Remise: {int(r['remise_pct'])}%)"
            elif r["frais_livraison"] > 0:
                detail_prix = f"(Article: {r['prix_brut']:,.0f} F + Livraison: {r['frais_livraison']:,.0f} F)"

            if p_net and r["en_stock"]:
                prix_valides[ens] = p_net
                prix_str = f"{p_net:,.0f} FCFA".replace(",", " ")
            elif p_net:
                prix_str = f"{p_net:,.0f} FCFA (non commandable)".replace(",", " ")
            else:
                prix_str = "Prix non disponible"

            print(f"  • {ens:<16} : {prix_str:<25} [{stock}] {detail_prix}")

        if prix_valides:
            meilleur_ens = min(prix_valides, key=prix_valides.get)
            print(f"\n  ★ CONSEIL D'ACHAT : Achetez chez '{meilleur_ens}' à {prix_valides[meilleur_ens]:,.0f} FCFA !".replace(",", " "))
        else:
            print("\n  ⚠ Produit actuellement introuvable ou en rupture partout.")
        print()

    conn.close()
    pause()


def menu_4_panier():
    """Option 4 : Simulation du panier de rentrée."""
    print("\n" + "=" * 65)
    print(" [4] SIMULATION DU PANIER DE RENTRÉE")
    print("=" * 65)
    print("Composition du panier demandé par le sujet :")
    print("  • 1x Tecno Spark 20 (P04)")
    print("  • 1x Lenovo IdeaPad 3 (P12)")
    print("  • 2x Clés USB SanDisk 64 Go (P14)")
    print("  • 1x Disque dur externe Seagate 1 To (P15)")
    print("  • 1x Micro-ondes Samsung 23 L (P28)")
    print("-" * 65)

    panier_articles = [
        ("P04", "Tecno Spark 20 128 Go", 1),
        ("P12", "Lenovo IdeaPad 3 Core i3", 1),
        ("P14", "Clé USB SanDisk 64 Go", 2),
        ("P15", "Disque dur externe Seagate 1 To", 1),
        ("P28", "Micro-ondes Samsung 23 L", 1),
    ]

    conn = database.get_connexion()
    cursor = conn.cursor()

    enseignes = ["Marché Lagune", "Baobab Shop", "Comptoir Ivoire"]
    totaux = {e: 0 for e in enseignes}
    complets = {e: True for e in enseignes}
    total_optimise = 0

    print(f"\n{'Article':<32} {'Qté':>3} {'M. Lagune':>12} {'Baobab':>12} {'C. Ivoire':>12} {'Meilleur':>12}")
    print("-" * 88)

    for pid, nom, qte in panier_articles:
        cursor.execute("SELECT enseigne, prix_net, en_stock FROM releves WHERE produit_id = ?", (pid,))
        lignes = {r["enseigne"]: (r["prix_net"], r["en_stock"]) for r in cursor.fetchall()}

        prix_dispos = {}
        str_cols = []
        for ens in enseignes:
            if ens in lignes and lignes[ens][0] is not None and lignes[ens][1]:
                p = lignes[ens][0] * qte
                prix_dispos[ens] = p
                totaux[ens] += p
                str_cols.append(f"{int(p):>10,}".replace(",", " ") + " F")
            else:
                complets[ens] = False
                str_cols.append("    rupture")

        if prix_dispos:
            best = min(prix_dispos.values())
            total_optimise += best
            best_str = f"{int(best):>10,}".replace(",", " ") + " F"
        else:
            best_str = "        N/A"

        print(f"{nom:<32} {qte:>3} {' '.join(str_cols)} {best_str}")

    conn.close()

    print("-" * 88)
    print("RÉSULTAT TOTAL PAR ENSEIGNE :")
    for ens in enseignes:
        if complets[ens]:
            print(f"  • {ens:<20} : {totaux[ens]:>11,} FCFA  (Commande complète en 1 fois)".replace(",", " "))
        else:
            print(f"  • {ens:<20} : COMMANDE INCOMPLÈTE (Articles en rupture de stock)")

    print(f"\n  ★ TOTAL PANIER OPTIMISÉ (en achetant chaque article au moins cher) :")
    print(f"    👉 {total_optimise:>11,} FCFA".replace(",", " "))

    magasins_complets = {e: t for e, t in totaux.items() if complets[e]}
    if magasins_complets:
        meilleur_mag = min(magasins_complets, key=magasins_complets.get)
        gain = magasins_complets[meilleur_mag] - total_optimise
        print(f"    👉 Économie réalisée par rapport à {meilleur_mag} : {gain:>8,} FCFA !".replace(",", " "))

    pause()


def menu_5_historique():
    """Option 5 : Analyse historique et promotion Black Friday."""
    print("\n" + "=" * 65)
    print(" [5] ANALYSE HISTORIQUE & EFFET BLACK FRIDAY (20 876 LIGNES)")
    print("=" * 65)
    print("Période Black Friday analysée : du 24 au 30 novembre 2025")
    print("Calcul des prix moyens annuels vs prix de la semaine de promo...\n")

    conn = database.get_connexion()

    # Requête instantanée sur la vue SQL pré-compilée
    sql = "SELECT source, moy_annuelle, moy_black_friday, nb_produits, total_releves FROM v_synthese_black_friday;"
    df = pd.read_sql_query(sql, conn)
    conn.close()

    print(f"{'Enseigne':<20} {'Moy. Année':>14} {'Moy. Black Friday':>18} {'Variation %':>13}")
    print("-" * 68)

    for _, row in df.iterrows():
        annee = row["moy_annuelle"]
        bf = row["moy_black_friday"]
        diff_pct = round(((bf - annee) / annee) * 100, 1)
        signe = "+" if diff_pct > 0 else ""
        verdict = "Vraie promotion" if diff_pct < 0 else "HAUSSE DE PRIX (Piège !)"

        print(f"{row['source']:<20} {int(annee):>12,} F {int(bf):>16,} F {signe}{diff_pct:>10}%  ({verdict})".replace(",", " "))

    print("-" * 68)
    print("\nCONCLUSION DU SUJET :")
    print("  • Baobab Shop (-11.7%) et Marché Lagune (-11.3%) appliquent de vrais rabais.")
    print("  • Comptoir Ivoire (boutique d'Adjamé) n'organise pas de Black Friday et augmente même ses tarifs (+3.8%).")
    pause()


def menu_6_journal():
    """Option 6 : Consulter le journal des anomalies de données."""
    print("\n" + "=" * 65)
    print(" [6] JOURNAL DES ANOMALIES DE DONNÉES (NETTOYAGE)")
    print("=" * 65)

    conn = database.get_connexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, enseigne, type_anomalie, description FROM journal_anomalies ORDER BY id")
    anomalies = cursor.fetchall()
    conn.close()

    print(f"Total : {len(anomalies)} anomalies détectées et corrigées\n")
    for anom in anomalies:
        print(f"  [{anom['id']:>2}] {anom['enseigne']:<16} | {anom['type_anomalie']:<20} | {anom['description']}")

    pause()


def menu_7_sql_libre():
    """Option 7 : Console SQL libre."""
    print("\n" + "=" * 65)
    print(" [7] CONSOLE REQUÊTE SQL LIBRE")
    print("=" * 65)
    print("Tables disponibles : catalogue, releves, historique, journal_anomalies")
    print("Exemple : SELECT produit_id, nom, categorie FROM catalogue LIMIT 5;")
    print("Tapez 'exit' pour revenir au menu.\n")

    conn = database.get_connexion()

    while True:
        req = input("SQL > ").strip()
        if not req:
            continue
        if req.lower() in ("exit", "quit", "q"):
            break

        try:
            df = pd.read_sql_query(req, conn)
            print()
            print(df.to_string(index=False))
            print(f"\n({len(df)} ligne(s) retournée(s))\n")
        except Exception as e:
            print(f"Erreur SQL : {e}\n")

    conn.close()


def main():
    """Boucle principale de l'application console."""
    # Vérifier que la base existe, sinon l'initialiser
    if not CHEMIN_BD.exists():
        print("Première exécution détectée. Initialisation de la base SQLite...")
        database.initialiser_base()

    while True:
        cls()
        print("=" * 70)
        print("       SYSTÈME D'ANALYSE COMPARATIVE BOUTIQUE (ABIDJAN)")
        print("       Projet DA Python L2 — Connecté à SQLite (boutique.db)")
        print("=" * 70)
        print("  [1] Synchroniser / Réinitialiser la base de données SQL")
        print("  [2] Afficher le tableau comparatif des 3 enseignes")
        print("  [3] Rechercher un produit précis (prix, stock, magasin recommandé)")
        print("  [4] Simuler le panier de rentrée (5 articles)")
        print("  [5] Analyser l'historique annuel & l'effet Black Friday")
        print("  [6] Consulter le journal des anomalies de nettoyage")
        print("  [7] Exécuter une requête SQL libre (console interactive)")
        print("  [0] Quitter l'application")
        print("=" * 70)

        choix = input("Votre choix (0-7) : ").strip()

        if choix == "1":
            menu_1_reinitialiser()
        elif choix == "2":
            menu_2_comparatif()
        elif choix == "3":
            menu_3_recherche()
        elif choix == "4":
            menu_4_panier()
        elif choix == "5":
            menu_5_historique()
        elif choix == "6":
            menu_6_journal()
        elif choix == "7":
            menu_7_sql_libre()
        elif choix == "0":
            print("\nMerci d'avoir utilisé le Système d'Analyse Boutique. À bientôt !\n")
            sys.exit(0)
        else:
            print("\nChoix invalide. Veuillez réessayer.")
            pause()


if __name__ == "__main__":
    main()

