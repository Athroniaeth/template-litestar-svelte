import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  // Le contrat vit à la racine du dépôt et y est versionné : le frontend se génère
  // sans Python, et tout changement d'API apparaît en diff dans la revue.
  input: "../openapi.json",
  output: "./src/generated/api",
  plugins: [
    "@hey-api/typescript",
    "@hey-api/schemas",
    "@hey-api/sdk",
    "@hey-api/client-fetch",
    "zod",
  ],
});
