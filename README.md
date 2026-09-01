# litestar-template

[![CI](https://github.com/Athroniaeth/template-litestar-svelte/actions/workflows/ci.yml/badge.svg)](https://github.com/Athroniaeth/template-litestar-svelte/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](.python-version)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Squelette de projet Litestar + Svelte, avec le backend Python et le frontend Vite
dans deux dossiers distincts.

[litestar-vite](https://github.com/litestar-org/litestar-vite) fait le lien entre
les deux : `litestar run` démarre l'API et le serveur Vite ensemble, et une commande
dérive les types TypeScript des handlers Python.

Litestar 2.24, Svelte 5, Vite 8, Tailwind 4, pnpm, uv.

## Structure

```
backend/          application Litestar
  __init__.py     chemins et variables d'environnement
  app.py          handlers et configuration du plugin Vite
frontend/         projet Vite (racine Vite)
  src/            sources Svelte
  src/generated/  types TypeScript générés (non versionnés)
  public/         bundle de production (non versionné)
Dockerfile        image de production multi-étages (Granian)
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
| `just dev` | lance l'app en rechargement à chaud (Litestar + Vite) |
| `just lint` | ruff + pyrefly (Python), eslint + prettier + svelte-check (frontend) |
| `just format` | formate et corrige (ruff côté Python, prettier + eslint côté frontend) |
| `just test` | pytest avec couverture |
| `just build` | bundle de production du frontend |
| `just check` | tout : lint + tests (ce que lance la CI) |

Chaque recette reprend les commandes `uv`/`pnpm` sous-jacentes ; rien n'oblige à
passer par `just`, mais c'est le point d'entrée unique, aligné sur les hooks
pre-commit et la CI.

## Démarrer

```bash
just dev              # ou : uv run litestar run --reload
```

Le site répond sur http://127.0.0.1:8000. Litestar lance Vite lui-même, et le
rechargement à chaud fonctionne sur les fichiers Svelte.

Si quelque chose cloche dans la configuration :

```bash
uv run litestar assets doctor
```

## Docker

Le `Dockerfile` est multi-étages : l'étage de build embarque Python et Node (le
bundle frontend dépend du backend via `litestar assets build`), l'étage final ne
garde que l'interpréteur, le venv et les fichiers servis, sous un utilisateur non
privilégié.

```bash
docker compose up --build
```

L'app répond sur http://127.0.0.1:8000. Les variables `LITESTAR_APP` et
`VITE_DEV_MODE=false` sont déjà portées par l'image.

Sans conteneur, le build de production se fait à la main :

```bash
uv run litestar assets build
VITE_DEV_MODE=false uv run litestar run
```

Le bundle atterrit dans `frontend/public/`. Litestar le sert via le manifeste, sans
démarrer Vite.

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
uv run litestar assets generate-types
```

La commande exporte le schéma OpenAPI, puis en tire les types, les schémas Zod, un
client d'API et un helper de routage, dans `frontend/src/generated/`.

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
cd frontend
pnpm dev       # Vite seul, sans backend
pnpm build     # build puis vérification des types
```

Dans ce cas, ajoutez `VITE_API_URL` au `.env` pour pointer vers le backend lancé à
part.

## Branches et CI

Le dépôt suit [Gitflow](https://nvie.com/posts/a-successful-git-branching-model/) :
`main` (production, taguée), `develop` (intégration), et des branches `feature/*`,
`release/*`, `hotfix/*`. La CI (`.github/workflows/ci.yml`) valide lint et tests sur
`main` et `develop` ; le build de l'image Docker ne tourne que sur `main`, la branche
de release, pour garder `develop` léger.
