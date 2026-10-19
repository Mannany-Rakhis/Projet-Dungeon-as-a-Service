# Dungeon as a Service

> API de jeu de rôle textuel avec héros, exploration, combats et classement.

## Démarrage rapide

### Prérequis

- Python 3.10 ou plus récent
- PowerShell, depuis la racine du projet

### 1. Installer les dépendances

Crée un environnement virtuel, active-le et installe les paquets du projet :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Démarrer l'API

Avec l'environnement virtuel activé, lance le serveur :

```powershell
fastapi dev app/main.py
```

L'API est disponible à l'adresse `http://127.0.0.1:8000`.

### 3. Jouer avec Swagger

Ouvre la [documentation interactive Swagger](http://127.0.0.1:8000/docs).
Pour utiliser les routes protégées, inscris-toi ou connecte-toi via
`/auth/register` ou `/auth/login`, puis clique sur **Authorize** et saisis tes
identifiants. Tu peux ensuite tester les routes directement dans Swagger.

## Notre rendu

| Élément | Résultat |
|---|---|
| **Membres du groupe** | Randriamanantenasoa Lovaniaina Sitraka, Rakhis Mannany et Eddie Chan |
| **Dépôt Git** | [Projet Dungeon as a Service](https://github.com/Mannany-Rakhis/Projet-Dungeon-as-a-Service) |
| **Palier atteint** | Palier 4 — fonctionnalités FT-1 à FT-11, authentification, propriété des héros et classement public |

### État des bonus sur `main`

| Bonus | État | Détail |
|---|---|---|
| **B-1 — Client terminal** | ✅ Terminé | Inscription, connexion, création, consultation, déplacement, attaque et repos ; jeton enregistré dans `.token`. |
| **B-2 — Classement** | ✅ Terminé | `GET /leaderboard` public, 10 héros maximum ; vainqueurs d'abord, puis quantité d'or. |
| **B-3 — Tests** | ✅ Terminé | Tests nominaux et erreurs `422`, `400`, `409` et `403`. |
| **B-4 — PostgreSQL** | ⚠️ Partiel | `DATABASE_URL` est pris en charge, mais il manque `docker-compose.yml` et le pilote PostgreSQL dans les dépendances. |
| **B-5 — Journalisation des combats** | ✅ Terminé | Les déplacements et les tours de combat sont journalisés. |

**Validation :** 61 tests réussis sur la branche `main` (commit vérifié `d880da5`).
