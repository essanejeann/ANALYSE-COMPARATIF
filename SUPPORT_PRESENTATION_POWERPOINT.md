# Support de Présentation PowerPoint — Soutenance de Projet
**Système d'Analyse Comparative de Marché (Abidjan)**

* **Étudiant :** ESSANE Jean-Noël
* **Filière :** Génie Logiciel — Licence 2 (L2)
* **Matière :** DA Python · Séance 3
* **Date :** Novembre 2026

---

> **Mode d'emploi :** Ce document est découpé diapositive par diapositive (Slide 1 à Slide 12).  
> Pour chaque slide, vous avez :
> 1. **Le contenu à afficher sur l'écran** (textes courts, puces, chiffres clés).
> 2. **Le discours oral suggéré** (ce que vous devez dire devant le jury / professeur).
> 3. **Une idée de visuel** (capture d'écran, tableau ou schéma).

---

## Diapositive 1 : Page de Garde (Introduction)

* **Titre principal :** Système d'Analyse Comparative de Marché
* **Sous-titre :** Traitement de données multi-sources, base relationnelle SQLite et application console
* **Étudiant :** ESSANE Jean-Noël
* **Formation :** Licence 2 Génie Logiciel
* **Cadre :** Projet DA Python — Séance 3

> **🗣️ Ce que vous dites à l'oral :**  
> *"Bonjour à tous et bienvenue. Je m'appelle Jean-Noël ESSANE, étudiant en deuxième année de Génie Logiciel. Je vous présente aujourd'hui mon projet de développement d'un système d'analyse comparative de marché pour le secteur de l'électronique et de l'électroménager à Abidjan."*

---

## Diapositive 2 : Contexte & Problématique Métier

* **Le scénario :** Un consommateur abidjanais souhaite acquérir des équipements électroniques sans surpayer.
* **3 enseignes concurrentes aux modèles économiques distincts :**
  * **Marché Lagune :** Site e-commerce (livraison gratuite incluse dans le prix affiché).
  * **Baobab Shop :** Application mobile (prix de base + frais de livraison de 1 500 à 2 500 FCFA).
  * **Comptoir Ivoire :** Boutique physique à Adjamé (tarifs catalogue négociés avec remises de 5% à 15%).
* **Le défi technique :** Les formats de données sont disparates (CSV, JSON, Excel) et les données du monde réel comportent de nombreuses anomalies.

> **🗣️ Ce que vous dites à l'oral :**  
> *"Le point de départ est très concret : comparer les offres entre un site web, une application mobile et une boutique physique à Adjamé. Chaque enseigne a sa propre tarification et ses propres formats de fichiers. Notre objectif a été de concevoir une chaîne de traitement automatisée capable de collecter, nettoyer et comparer ces offres équitablement."*

---

## Diapositive 3 : Les Objectifs du Cahier des Charges

* **1. Ingestion multi-formats :** Intégrer CSV avec séparateur point-virgule et BOM, JSON d'API et classeur Excel `.xlsx`.
* **2. Nettoyage et fiabilisation :** Détecter les prix erronés, éliminer les doublons et consigner les anomalies.
* **3. Rapprochement automatique :** Relier les désignations non standardisées au catalogue officiel (30 produits `P01` à `P30`).
* **4. Aide à la décision :** Calculer les écarts réels de prix et identifier le meilleur plan d'achat.
* **5. Analyse temporelle :** Examiner l'impact promotionnel du Black Friday sur un historique de plus de 20 000 relevés.
* **6. Qualité logicielle :** Structurer le projet avec une base relationnelle SQLite et une application console interactive.

> **🗣️ Ce que vous dites à l'oral :**  
> *"Le cahier des charges ne demandait pas un simple script de calcul, mais une véritable application logicielle robuste, capable de traiter des données hétérogènes et de fournir des réponses fiables en temps réel."*

---

## Diapositive 4 : Architecture Logicielle du Système

* **Architecture en 3 Couches (3-Tiers) :**
  * **Couche Données :** Base SQLite `boutique.db` configurée en mode **WAL** (*Write-Ahead Logging*) avec 64 Mo de cache mémoire.
  * **Couche Métier :** Algorithmes d'indexation inversée, algorithme glouton et agrégations statistiques.
  * **Couche Présentation :** Application console interactive `app_console.py` avec menu dynamique.
* **Schéma relationnel :** 4 tables normalisées (`catalogue`, `releves`, `historique`, `journal_anomalies`) et 2 vues SQL pré-compilées.

> **🗣️ Ce que vous dites à l'oral :**  
> *"En tant qu'étudiant en Génie Logiciel, j'ai veillé à séparer strictement les responsabilités. Les données nettoyées sont persistées dans SQLite avec des index B-Tree, ce qui garantit que l'interface console répond instantanément à l'utilisateur."*

---

## Diapositive 5 : Nettoyage des Données — 21 Anomalies Traitées

* **Marché Lagune (CSV) :**
  * Suppression de **2 doublons** de références (`ML-1000` et `ML-1147`).
  * Détection d'un **prix aberrant** : Tecno Spark 20 affiché par erreur à 779 000 FCFA au lieu de ~75 000 FCFA (exclu).
  * Traitement des prix non exploitables (*"Prix sur demande"* ou vide).
* **Baobab Shop (JSON) :**
  * Identification de **3 ruptures de stock** (`stock = 0`).
  * Exclusion d'un produit avec prix `null` (Fer à repasser Philips).
  * Intégration systématique des frais de port au prix final.
* **Comptoir Ivoire (Excel) :**
  * Application mathématique des **remises de 5% à 15%** sur le prix catalogue.
  * Exclusion des articles en rupture physique en rayon (`quantité = 0`).

> **🗣️ Ce que vous dites à l'oral :**  
> *"Les données brutes ne sont jamais parfaites. Notre système a détecté et tracé 21 anomalies dans un journal d'audit. Par exemple, le Tecno Spark 20 vendu à 779 000 FCFA sur Marché Lagune est une faute de saisie évidente qui aurait faussé toute la comparaison sans notre filtre automatique."*

---

## Diapositive 6 : Les Algorithmes Clés & Choix Techniques

* **1. Rapprochement par Index Inversé $O(1)$ :**
  * Les mots-clés du catalogue sont indexés dans une table de hachage.
  * Recherche directe par mot sans parcours séquentiel lent : **appariement des 3 magasins en 14 millisecondes**.
  * Filtre catégoriel pour éviter d'associer un smartphone à un appareil électroménager.
* **2. Algorithme Glouton sous Contrainte (Panier d'Achat) :**
  * Sélectionne le prix le plus bas pour chaque article avec contrainte stricte de stock (`stock > 0`).
* **3. Agrégation par Hachage (Historique) :**
  * Les 20 876 relevés sont agrégés directement en mémoire RAM et en langage C via les vues SQL de SQLite.

> **🗣️ Ce que vous dites à l'oral :**  
> *"Sur le plan algorithmique, nous avons privilégié la vitesse. Pour relier un article écrit 'Samsun A15' à notre référence officielle, nous utilisons un index inversé similaire aux moteurs de recherche. Cela évite les boucles lentes et garantit une exécution quasi-instantanée."*

---

## Diapositive 7 : Résultats du Comparatif des Prix

* **23 produits directement comparables** (disponibles chez au moins 2 enseignes avec stock).
* **Palmarès des enseignes :**
  * **1ère place : Baobab Shop** $\rightarrow$ la moins chère sur **9 produits**.
  * **2ème place : Comptoir Ivoire** $\rightarrow$ la moins chère sur **8 produits** (écart moyen le plus faible : +2.8%).
  * **3ème place : Marché Lagune** $\rightarrow$ la moins chère sur **6 produits**.
* **Top 3 des plus grandes économies :**
  1. **PC Portable HP 250 G9 :** 52 800 FCFA d'économie chez Baobab Shop (14.9%).
  2. **Apple iPhone 13 128 Go :** 26 500 FCFA d'économie chez Baobab Shop (6.4%).
  3. **Climatiseur LG 1 CV :** 26 000 FCFA d'économie chez Baobab Shop (10.3%).

> **🗣️ Ce que vous dites à l'oral :**  
> *"Le comparatif révèle que Baobab Shop propose les prix les plus agressifs sur l'informatique et les smartphones. En comparant simplement avant d'acheter, un client peut économiser plus de 50 000 FCFA sur un seul ordinateur portable."*

---

## Diapositive 8 : Simulation — Le Panier de Rentrée

* **Composition du panier étudiant :**
  * 1x Tecno Spark 20 + 1x Lenovo IdeaPad 3 + 2x Clés USB 64 Go + 1x Disque 1 To + 1x Micro-ondes.
* **Comparaison des stratégies d'achat :**
  * **Marché Lagune :** Commande impossible (Tecno Spark en rupture).
  * **Baobab Shop :** Panier complet à **491 500 FCFA**.
  * **Comptoir Ivoire :** Panier complet à **484 075 FCFA** *(meilleur magasin unique)*.
  * **Achat Panaché Optimisé :** **477 575 FCFA**.
* **Conclusion :** Acheter chaque article dans son magasin le moins cher permet d'économiser **6 500 FCFA**.

> **🗣️ Ce que vous dites à l'oral :**  
> *"Pour le cas pratique du panier de rentrée, si le client veut tout acheter au même endroit, seul Comptoir Ivoire est en mesure de le servir pour 484 075 FCFA. Mais notre algorithme glouton propose une combinaison optimisée à 477 575 FCFA, ce qui dégage une économie nette immédiate."*

---

## Diapositive 9 : Analyse Historique — L'Effet Black Friday

* **Jeu de données :** 20 876 relevés de prix quotidiens du 01/11/2025 au 31/10/2026.
* **Semaine du Black Friday :** 24 au 30 novembre 2025 vs Moyenne annuelle.
* **Résultats par enseigne :**
  * **Baobab Shop :** **-11.7%** $\rightarrow$ Vraie promotion commerciale.
  * **Marché Lagune :** **-11.3%** $\rightarrow$ Vraie promotion commerciale.
  * **Comptoir Ivoire :** **+3.8%** $\rightarrow$ Hausse tarifaire (pas de participation à l'événement en ligne).
* **Enseignement :** Les plateformes en ligne jouent le jeu des rabais, tandis que la boutique physique maintient ou durcit ses marges.

> **🗣️ Ce que vous dites à l'oral :**  
> *"L'analyse historique montre un phénomène très intéressant : le Black Friday est une véritable opportunité chez Baobab Shop et Marché Lagune avec environ 11% de baisse. En revanche, chez Comptoir Ivoire, les prix augmentent légèrement de 3,8% durant cette période."*

---

## Diapositive 10 : L'Application Console Interactive (`app_console.py`)

* **Interface en ligne de commande structurée en menu :**
  * `[1]` Synchronisation et initialisation de la base SQLite
  * `[2]` Consultation du tableau comparatif avec filtres par catégorie
  * `[3]` Recherche ciblée par produit avec conseil d'achat
  * `[4]` Simulation automatique du panier étudiant
  * `[5]` Analyse statistique de l'historique annuel
  * `[6]` Consultation du journal d'audit des anomalies
  * `[7]` Console de requêtes SQL interactives en direct

> **🗣️ Ce que vous dites à l'oral :**  
> *"Pour permettre une exploitation facile, j'ai développé une application console interactive. Elle permet à l'utilisateur de rechercher un produit, de filtrer par catégorie et même d'exécuter des requêtes SQL personnalisées en temps réel."*

---

## Diapositive 11 : Performances & Complexité Algorithmique

* **Profilage chronométrique mesuré :**
  * Rapprochement des 3 catalogues : **14 millisecondes**.
  * Nettoyage vectorisé : **63 millisecondes**.
  * Exécution du tableau comparatif : **4,15 millisecondes** *(via vue SQL)*.
  * Analyse des 20 876 lignes historiques : **22,17 millisecondes** *(via vue SQL)*.
  * **Temps total d'exécution du pipeline : < 1 seconde**.
* **Facteurs de succès :**
  * Suppression des boucles `iterrows()` au profit de matrices 2D NumPy.
  * Activation du mode WAL SQLite et d'un cache mémoire de 64 Mo.

> **🗣️ Ce que vous dites à l'oral :**  
> *"Comme demandé par la consigne de complexité, nous avons mesuré précisément les temps d'exécution. Grâce au typage catégoriel et aux vues pré-compilées de SQLite, le traitement de plus de 20 000 lignes s'exécute en seulement 22 millisecondes."*

---

## Diapositive 12 : Conclusion & Bilan d'Ingénierie

* **Objectifs atteints :**
  * 100% des articles des 3 enseignes correctement nettoyés et rapprochés.
  * Mise en place d'une base relationnelle solide et d'une application fonctionnelle.
  * Respect des critères de performance et de complexité algorithmique.
* **Compétences acquises :**
  * Manipulation avancée de données hétérogènes (CSV, JSON, Excel, SQLite).
  * Algorithmique appliquée : indexation textuelle et optimisation gloutonne.
  * Modélisation de base de données relationnelle et architecture 3-Tiers.
* **Perspectives futures :**
  * Connexion à un dashboard web (ex: Streamlit ou FastAPI).
  * Intégration d'un module d'alerte automatique en cas de baisse de prix.

> **🗣️ Ce que vous dites à l'oral pour conclure :**  
> *"En conclusion, ce projet m'a permis de mettre en pratique les principes fondamentaux du génie logiciel : la modélisation de données, l'efficacité algorithmique et la qualité du code. Je vous remercie pour votre attention et je suis prêt à répondre à vos questions."*
