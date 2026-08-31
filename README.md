# litestar-template

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
```

## Installation

Il faut [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/) et Node `^20.19`
ou `>=22.12`, contrainte de Vite 8.

```bash
cp .env.example .env
uv sync
uv run litestar assets install
```

Ne sautez pas la copie du `.env` : il définit `LITESTAR_APP`. Sans lui, la CLI
cherche l'application à la racine et ne la trouve pas, puisque le code est dans
`backend/`.

## Démarrer

```bash
uv run litestar run --reload
```

Le site répond sur http://127.0.0.1:8000. Litestar lance Vite lui-même, et le
rechargement à chaud fonctionne sur les fichiers Svelte.

Si quelque chose cloche dans la configuration :

```bash
uv run litestar assets doctor
```

## Production

```bash
uv run litestar assets build
VITE_DEV_MODE=false uv run litestar run
```

Le build atterrit dans `frontend/public/`. Litestar le sert via le manifeste, sans
démarrer Vite.

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
