# litestar-template

[![CI](https://github.com/Athroniaeth/template-litestar-svelte/actions/workflows/ci.yml/badge.svg)](https://github.com/Athroniaeth/template-litestar-svelte/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](.python-version)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Squelette de projet Litestar + Svelte, avec le backend Python et le frontend Vite
découplés : deux images Docker, deux cycles de déploiement, deux dimensionnements.

Le contrat entre les deux est `openapi.json`, versionné à la racine. Le backend
l'exporte depuis ses handlers, le frontend en dérive ses types TypeScript sans avoir
besoin de Python. En production, nginx sert le bundle et proxifie `/api` vers
Litestar : une seule origine côté navigateur, donc pas de CORS ni d'URL d'API dans
le bundle.

Litestar 2.24, Svelte 5, Vite 8, Tailwind 4, nginx, pnpm, uv.

## Structure

```
backend/          application Litestar — sert /api, rien d'autre
  __init__.py     chemins du projet
  app.py          handlers et configuration des plugins
frontend/         projet Vite (racine Vite)
  src/            sources Svelte
  src/generated/  client TypeScript généré (non versionné)
  dist/           bundle de production (non versionné)
deploy/nginx.conf reverse proxy : bundle + /api sur une seule origine
openapi.json      contrat d'API versionné, exporté depuis les handlers
Dockerfile.api    image de l'API (Python seul)
Dockerfile.web    image du frontend (bundle Vite + nginx)
justfile          raccourcis des tâches courantes
```

## Installation

Il faut [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/) et Node `^20.19`
ou `>=22.12`, contrainte de Vite 8. [`just`](https://github.com/casey/just) est
recommandé (`uv tool install rust-just`) mais facultatif.

```bash
cp .env.example .env
just install          # uv sync + litestar assets install
```

Sans `just`, la même chose à la main :

```bash
uv sync
uv run litestar assets install
```

Ne sautez pas la copie du `.env` : il définit `LITESTAR_APP`. Sans lui, la CLI
cherche l'application à la racine et ne la trouve pas, puisque le code est dans
`backend/`.

## Commandes

Les tâches courantes passent par `just` ; `just` seul liste les recettes.

| Commande | Effet |
|----------|-------|
| `just dev` | lance l'API (:8000) et le frontend (:5173) ensemble |
| `just dev-api` | l'API seule, en rechargement à chaud |
| `just dev-front` | le frontend seul, avec HMR |
| `just types` | exporte `openapi.json` et régénère le client TypeScript |
| `just lint` | ruff + pyrefly (Python), eslint + prettier + svelte-check (frontend) |
| `just format` | formate et corrige (ruff côté Python, prettier + eslint côté frontend) |
| `just test` | pytest avec couverture |
| `just build` | bundle de production du frontend |
| `just check` | tout : contrat + lint + tests (ce que lance la CI) |

Chaque recette reprend les commandes `uv`/`pnpm` sous-jacentes ; rien n'oblige à
passer par `just`, mais c'est le point d'entrée unique, aligné sur les hooks
pre-commit et la CI.

## Démarrer

```bash
just dev
```

Deux process démarrent : l'API sur le port 8000 et le dev server Vite sur 5173.
**Le site se consulte sur http://127.0.0.1:5173** — Vite proxifie `/api` vers
l'API, exactement comme nginx le fera en production. Le code client appelle donc
`/api` en relatif et ignore où vit le backend, en dev comme en production.

L'API seule ne sert aucune page : `http://127.0.0.1:8000/` répond 404, par
construction. Un test le vérifie.

Si quelque chose cloche dans la configuration :

```bash
uv run litestar assets doctor
```

## Docker

Deux images, chacune buildable sans l'autre :

- `Dockerfile.api` — Python seul, sans Node ni outils de build. Ne contient que
  l'interpréteur, le venv et `backend/`, sous un utilisateur non privilégié.
- `Dockerfile.web` — étage Node qui dérive les types de `openapi.json` et build le
  bundle, puis nginx sans privilèges qui le sert.

```bash
docker compose up --build
```

L'app répond sur http://127.0.0.1:8000, servie par nginx. L'API n'est pas exposée
sur l'hôte : seul `web` l'atteint, par le réseau interne de compose. Le service
`web` attend que le healthcheck de `api` passe avant de démarrer.

### Dimensionner

L'API porte la charge : le frontend est un bundle statique qu'un visiteur télécharge
une fois, puis met en cache (les noms sont hashés, nginx les sert en `immutable`).
C'est donc l'API qu'on dimensionne.

```bash
WEB_CONCURRENCY=4 docker compose up -d    # 4 workers Granian
```

Passer à l'horizontal ensuite ne demande que des répliques d'`api` derrière nginx —
à condition de n'avoir mis aucun état en mémoire dans le processus.

## Qualité

Le lint, le typage et les tests couvrent backend et frontend d'un seul point :

```bash
just lint             # ruff, pyrefly, eslint, prettier, svelte-check
just test             # pytest + couverture
```

Les mêmes vérifications tournent à chaque commit via [prek](https://github.com/j178/prek)
(ou pre-commit) — lancez `prek install` une fois — et dans la CI GitHub Actions.

## Développement

Lancez toujours `litestar` depuis la racine du dépôt. Depuis `frontend/`, Python ne
trouve pas le package `backend` et la commande échoue.

### Types TypeScript

Après avoir touché à une route ou à un type de réponse :

```bash
just types      # uv run litestar assets generate-types
```

La commande écrit `openapi.json` à la racine, puis en tire les types, les schémas
Zod, un client d'API et un helper de routage dans `frontend/src/generated/`.

**Committez `openapi.json`.** C'est le contrat : il rend le frontend buildable sans
Python, et tout changement d'API devient un diff lisible en revue. `just check`
(donc la CI) régénère le fichier et échoue s'il a dérivé des handlers.

Le frontend peut se régénérer seul, sans Python :

```bash
pnpm -C frontend generate-types
```

Un détail qui compte : annotez les réponses avec une dataclass ou un
`msgspec.Struct`. Un `dict[str, str]` donne un `{ [key: string]: string }`,
c'est-à-dire à peu près rien.

### Commits

Commits au format [Conventional Commits](https://www.conventionalcommits.org), via
[Commitizen](https://commitizen-tools.github.io/commitizen/) configuré dans `cz.toml`.

```bash
uv run cz commit     # rédaction guidée
uv run cz bump       # version, tag et CHANGELOG
```

Le format est aussi vérifié automatiquement à chaque commit : le hook `commitizen`
(étape `commit-msg`) rejette un message non conforme. Il s'installe avec le reste
via `prek install` (voir `default_install_hook_types` dans `.pre-commit-config.yaml`).

`cz bump` lit et écrit la version dans `pyproject.toml` via uv. Tant que
`major_version_zero` est actif, le projet ne dépasse pas `0.x`.

### Travailler sur le frontend seul

```bash
just dev-front            # Vite seul, sans backend
just build                # bundle de production dans frontend/dist
```

Les appels `/api` sont proxifiés vers `http://127.0.0.1:8000`. Si l'API écoute
ailleurs, pointez `API_URL` dessus dans le `.env`. Sans API lancée, l'app s'affiche
et les appels échouent — le frontend reste développable seul.

## Branches et CI

Le dépôt suit [Gitflow](https://nvie.com/posts/a-successful-git-branching-model/) :
`main` (production, taguée), `develop` (intégration), et des branches `feature/*`,
`release/*`, `hotfix/*`. La CI (`.github/workflows/ci.yml`) valide le contrat, le lint
et les tests sur `main` et `develop` ; le build des deux images Docker ne tourne que
sur `main`, la branche de release, pour garder `develop` léger.
