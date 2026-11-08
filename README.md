# Système d'Analyse Comparative de Marché — Abidjan
**Projet DA Python · L2 Génie Logiciel**

* **Étudiant :** ESSANE Jean-Noël
* **Filière :** Génie Logiciel — Licence 2
* **Date :** Novembre 2026

Ce projet permet de collecter, nettoyer et comparer les prix d'articles électroniques et électroménagers entre trois magasins d'Abidjan :
* **Marché Lagune** (site web, livraison incluse dans le prix)
* **Baobab Shop** (application mobile, prix article + frais de livraison)
* **Comptoir Ivoire** (boutique physique à Adjamé, prix catalogue avec remises)

Le projet contient un script d'analyse complète, une base de données **SQLite** (`boutique.db`) et une **application console** interactive.

---

## 1. Types d'Algorithmes Utilisés

Trois algorithmes sont mis en œuvre dans ce projet :

### A. Index Inversé (Rapprochement des noms de produits)
* **Problème** : Chaque magasin écrit les noms à sa façon (par exemple *"Samsun Galaxy A15"* ou *"Galaxy A15 128GB"*).
* **Solution** : Les mots-clés du catalogue sont indexés dans un dictionnaire. Dès qu'un article se présente, l'algorithme retrouve le bon produit en temps constant $O(1)$ sans devoir relire tout le catalogue.

### B. Algorithme Glouton sous Contrainte (Panier de Rentrée)
* **Principe** : Pour chaque article du panier, le programme choisit automatiquement le magasin le moins cher parmi ceux qui ont du stock. Si un magasin est en rupture, il est ignoré.

### C. Agrégation par Hachage (Analyse Historique des Prix)
* **Principe** : Le fichier d'historique contient **20 876 lignes**. Pour calculer la moyenne de l'année et celle du Black Friday, les données sont regroupées en mémoire par table de hachage (`GROUP BY` en SQL). L'analyse complète tourne en **22 millisecondes**.

---

## 2. Structure du Projet

```text
ANALYSE BOUTIQUE/
├── README.md               # Documentation du projet
├── analyse_comparative.py  # Script de traitement et des 8 étapes
├── database.py             # Création et alimentation de la base SQLite
├── app_console.py          # Application console avec menu interactif
├── boutique.db             # Base de données SQLite (4 tables)
├── data/                   # Fichiers de données (CSV, JSON, Excel)
└── resultats/              # Exports CSV et rapports générés
```

---

## 3. Résultats Clés

* **Magasin le moins cher le plus souvent** : **Baobab Shop** (9 produits sur 23), suivi de Comptoir Ivoire (8 produits) et Marché Lagune (6 produits).
* **Panier de rentrée (5 articles scolaires)** :
  * Achat groupé chez Comptoir Ivoire (seul magasin ayant tout en stock) : **484 075 FCFA**.
  * Achat optimisé (meilleur magasin par produit) : **477 575 FCFA**.
  * **Économie réalisée** : **6 500 FCFA**.
* **Effet du Black Friday** : Baobab Shop (-11.7%) et Marché Lagune (-11.3%) baissent leurs prix, alors que Comptoir Ivoire augmente légèrement ses tarifs (+3.8%).

---

## 4. Lancement du Projet

### Installation des bibliothèques nécessaires :
```bash
pip install pandas openpyxl
```

### Lancer l'analyse complète :
```bash
python analyse_comparative.py
```

### Lancer l'application console interactive :
```bash
python app_console.py
```
