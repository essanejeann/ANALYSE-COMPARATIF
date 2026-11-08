# Documentation Technique & Démarche d'Ingénierie Logicielle
**Projet d'Analyse Comparative de Marché — DA Python & Génie Logiciel**

* **Étudiant :** ESSANE Jean-Noël
* **Filière :** Génie Logiciel — Licence 2 (L2)
* **Date :** Novembre 2026

---

## 1. Démarche Globale du Projet

Le développement de ce système d'analyse suit les principes fondamentaux du génie logiciel : séparer clairement la gestion des données, le traitement algorithmique et l'interface utilisateur.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        1. SOURCES DE DONNÉES                           │
│   • marche_lagune.csv (CSV / BOM)      • baobab_shop.json (JSON API)   │
│   • comptoir_ivoire.xlsx (Excel)       • historique_prix.csv (20 876 l)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Ingestion & Nettoyage
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  2. COUCHE ACCÈS AUX DONNÉES (SQLITE)                  │
│   • Base : boutique.db (Mode WAL, Cache 64 Mo en RAM)                 │
│   • Tables : catalogue, releves, historique, journal_anomalies        │
│   • Vues pré-compilées : v_comparatif, v_synthese_black_friday         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Requêtes SQL optimisées
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     3. LOGIQUE MÉTIER & ALGORITHMES                    │
│   • Index Inversé O(1) (Appariement de catalogue)                     │
│   • Algorithme Glouton (Optimisation du panier sous contrainte stock) │
│   • Agrégations temporelles (Comparaison Black Friday vs Année)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Présentation
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  4. INTERFACES D'UTILISATION (CLI)                     │
│   • app_console.py : Menu interactif en ligne de commande              │
│   • analyse_comparative.py : Pipeline d'export autonome (CSV, stats)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Méthodes de Connexion SQL & Bonnes Pratiques

### A. Connexion SQLite en Python (Implémentée dans `database.py`)

SQLite est un moteur relationnel sans serveur (*serverless*). Les données sont stockées dans un fichier unique (`boutique.db`).

#### Code de connexion optimisé :
```python
import sqlite3

def get_connexion(db_path="boutique.db"):
    # 1. Établissement de la connexion
    conn = sqlite3.connect(db_path)
    
    # 2. Activation du mode WAL (Write-Ahead Logging)
    # Permet les lectures et écritures simultanées sans verrouiller la base
    conn.execute("PRAGMA journal_mode = WAL;")
    
    # 3. Synchronisation assouplie (évite les attentes d'écriture disque bloquantes)
    conn.execute("PRAGMA synchronous = NORMAL;")
    
    # 4. Allocation de 64 Mo de cache en mémoire vive
    conn.execute("PRAGMA cache_size = -64000;")
    
    # 5. Stockage des tables et tris temporaires en RAM
    conn.execute("PRAGMA temp_store = MEMORY;")
    
    # 6. Activation de l'intégrité référentielle (clés étrangères)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # 7. Accès aux colonnes par leur nom (dictionnaire) en plus de l'index
    conn.row_factory = sqlite3.Row
    
    return conn
```

#### Bonnes pratiques appliquées :
1. **Requêtes paramétrées anti-injection SQL** : Toujours utiliser des points d'interrogation `?` pour injecter des valeurs utilisateur :
   ```python
   # BON : Sécurisé contre l'injection SQL
   cursor.execute("SELECT * FROM catalogue WHERE produit_id = ?", (pid,))
   
   # MAUVAIS : Vulnérable à l'injection SQL
   # cursor.execute(f"SELECT * FROM catalogue WHERE produit_id = '{pid}'")
   ```
2. **Gestion des transactions** : Utiliser `conn.commit()` pour valider les modifications (`INSERT`, `UPDATE`, `DELETE`) et `conn.close()` pour libérer le descripteur de fichier.
3. **Vues SQL pré-compilées** : Déporter le calcul lourd des jointures directement dans le moteur C de SQLite plutôt qu'en Python :
   ```sql
   CREATE VIEW v_comparatif AS
   SELECT c.produit_id, c.nom,
          MAX(CASE WHEN r.enseigne = 'Marché Lagune' THEN r.prix_net END) AS prix_lagune,
          MAX(CASE WHEN r.enseigne = 'Baobab Shop' THEN r.prix_net END) AS prix_baobab,
          MAX(CASE WHEN r.enseigne = 'Comptoir Ivoire' THEN r.prix_net END) AS prix_ivoire
   FROM catalogue c
   LEFT JOIN releves r ON c.produit_id = r.produit_id
   GROUP BY c.produit_id;
   ```

---

### B. Comparaison avec les autres Systèmes de Bases de Données

En milieu d'entreprise ou en projet d'envergure supérieure, d'autres SGBD et connecteurs sont utilisés :

| SGBD | Type d'architecture | Pilote / Bibliothèque Python | Exemple de chaîne de connexion | Cas d'usage typique |
|---|---|---|---|---|
| **SQLite** | Embarqué (fichier local) | `sqlite3` (standard) | `"boutique.db"` | Embarqué, tests, applications locales légères |
| **PostgreSQL** | Client-Serveur | `psycopg2` ou `asyncpg` | `"postgresql://user:mdp@localhost:5432/boutique"` | Production web, gros volumes, forte concurrence |
| **MySQL / MariaDB** | Client-Serveur | `mysql-connector` / `pymysql` | `"mysql+pymysql://user:mdp@127.0.0.1/boutique"` | Applications web standard (WordPress, e-commerce) |
| **SQL Server (Microsoft)** | Client-Serveur d'entreprise | `pyodbc` (Python) / `ADO.NET` (C#) | `"DRIVER={ODBC};SERVER=localhost;DATABASE=dbL2;"` | Systèmes d'information d'entreprise, écosystème .NET |

#### Parallèle avec C# / ADO.NET (Vu en cours de Génie Logiciel) :
En Python avec `sqlite3`, la logique est identique à l'architecture C# / ADO.NET :
* `sqlite3.connect()` $\leftrightarrow$ `new SqlConnection(chaineConnexion)`
* `conn.cursor()` $\leftrightarrow$ `new SqlCommand(sql, connexion)`
* `cursor.fetchall()` $\leftrightarrow$ `command.ExecuteReader()` avec boucle `reader.Read()`
* `conn.commit()` $\leftrightarrow$ `transaction.Commit()`

---

## 3. Conception de l'Application Console (`app_console.py`)

L'application console repose sur le patron d'architecture en trois couches (**3-Tiers**) :

```text
┌────────────────────────────────────────────────────────┐
│     Couche Présentation (Interface Console Utilisateur) │
│     Boucle principale, saisie sécurisée, affichage tab  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         Couche Métier (Logique de Décision)            │
│     Détection de stock, choix du moins cher, panier     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│      Couche d'Accès aux Données (DAL - database.py)    │
│     Requêtes SQL sur les tables et vues SQLite         │
└────────────────────────────────────────────────────────┘
```

### Mécanismes de la Console :
1. **Boucle événementielle (`while True`)** : L'application ne s'arrête pas après une commande. Elle présente le menu, attend un choix, traite l'action, attend une validation (`input("Appuyez sur Entrée...")`) et réaffiche le menu.
2. **Nettoyage de l'écran (`cls` / `clear`)** : Permet de garder un terminal toujours lisible.
3. **Formatage tabulaire aligné** : Utilisation du formateur de chaîne Python (`{val:>10,}`) avec séparation des milliers par des espaces pour une lecture rapide des montants en FCFA.

---

## 4. Comparatif des Types de Systèmes Logiciels

En génie logiciel, le choix du type d'interface dépend des utilisateurs et de l'environnement :

### A. Application Console (CLI - Notre solution actuelle)
* **Avantages** : Très rapide à développer, consomme extrêmement peu de mémoire (quelques mégaoctets de RAM), fonctionne sans interface graphique même sur un serveur distant via SSH.
* **Inconvénients** : Moins conviviale pour le grand public, pas de visuels graphiques (boutons, images).
* **Usage** : Outils de maintenance, scripts de gestion, traitement par lots (*batch*), terminaux de caisse.

### B. Application Desktop (GUI - Interface Graphique Lourde)
* **Technologies courantes** : C# Windows Forms / WPF, Python PyQt / Tkinter.
* **Avantages** : Interaction à la souris, formulaires riches, fenêtres modales, accès direct au matériel local.
* **Inconvénients** : Nécessite une installation sur chaque machine cliente, dépendance au système d'exploitation (Windows/Linux/Mac).

### C. Application Web (SaaS / Dashboard)
* **Technologies courantes** : Python (Streamlit / Flask / FastAPI) + Frontend (React / HTML-CSS).
* **Avantages** : Accessible depuis n'importe quel navigateur (ordinateur, smartphone), aucune installation sur le poste client, centralisation des mises à jour.
* **Inconvénients** : Nécessite un serveur web hôte, gestion complexe de l'authentification et de la sécurité réseau.

---

## 5. Détail Algorithmique des Traitements Métier

### A. Rapprochement par Index Inversé $O(1)$
Le problème consiste à relier par exemple `"Samsun A15 128Go"` à `"P01"`.
1. **Étape 1** : Nettoyage de la chaîne (suppression de la ponctuation, conversion majuscule, retrait des accents).
2. **Étape 2** : Élimination des mots vides sans valeur distinctive (`"DE"`, `"LE"`, `"PORTABLE"`, `"FCFA"`).
3. **Étape 3** : Recherche dans l'Index Inversé. Chaque mot clé pointe directement sur l'identifiant produit.
4. **Étape 4** : Scoring de similarité avec bonus de marque et pénalité en cas d'incompatibilité de catégorie (un téléphone ne peut pas être un réfrigérateur).

### B. Algorithme Glouton sous Contrainte (Panier de Rentrée)
Le panier contient 5 articles spécifiques.
Pour chaque article $i$ :
$$\text{Prix retenu}_i = \min \{ \text{Prix}(i, e) \mid e \in \text{Enseignes}, \text{Stock}(i, e) > 0 \}$$
* Si une enseigne propose le prix le plus bas mais que son stock est nul, elle est rejetée.
* Le total optimisé panaché est calculé et comparé au total de la meilleure enseigne complète unique.

### C. Traitement Analytique de l'Historique (20 876 lignes)
Le relevé de prix sur 365 jours est traité en utilisant :
1. Les colonnes sous forme de types `category` en mémoire.
2. Un filtre direct sur chaînes de dates (`'2025-11-24' <= date <= '2025-11-30'`).
3. Une agrégation SQL en C par la vue `v_synthese_black_friday`.
Temps total mesuré : **22 millisecondes** pour 20 876 enregistrements.

---

## 6. Guide de Démarrage Rapide

```bash
# 1. Installer les dépendances Python
pip install pandas openpyxl

# 2. Initialiser la base de données SQLite
python database.py

# 3. Lancer l'application console
python app_console.py

# 4. (Optionnel) Exécuter le pipeline complet autonome
python analyse_comparative.py
```
