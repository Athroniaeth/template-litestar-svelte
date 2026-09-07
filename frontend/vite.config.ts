import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import litestar from "litestar-vite-plugin";

import tailwindcss from "@tailwindcss/vite";

// Cible du proxy de dev : l'API Litestar lancée à part (`just dev-api`).
const API_TARGET = process.env.API_URL || "http://127.0.0.1:8000";

export default defineConfig({
  // Le bundle est servi à la racine par nginx, pas sous le préfixe d'assets de
  // Litestar : on reprend la base Vite standard au lieu du défaut du plugin.
  base: "/",
  // Assets copiés tels quels (favicon, robots.txt). Le plugin le désactive par
  // défaut, ce qui ferait disparaître silencieusement tout fichier déposé là.
  publicDir: "public",
  build: {
    outDir: "dist",
    // index.html comme entrée, pour que Vite émette un HTML complet avec les URLs
    // hashées. Avec les entrées du plugin (src/main.ts), le build ne produit qu'un
    // manifeste, à charge du backend de réécrire le HTML — ce qu'il ne fait plus.
    rolldownOptions: { input: "index.html" },
  },
  server: {
    host: "0.0.0.0",
    port: Number(process.env.VITE_PORT || "5173"),
    // Même origine qu'en production, où nginx joue ce rôle : le code client ne
    // connaît jamais l'URL de l'API, il appelle /api en relatif.
    proxy: {
      "/api": { target: API_TARGET, changeOrigin: true },
      "/schema": { target: API_TARGET, changeOrigin: true },
    },
  },
  plugins: [
    tailwindcss(),

    svelte(),
    // Conservé pour la seule génération de types ; il ne sert plus le frontend.
    litestar({
      input: ["src/main.ts", "src/tailwind.css"],

      types: "auto",
    }),
  ],
});
