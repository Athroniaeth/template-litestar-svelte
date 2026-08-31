import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import litestar from "litestar-vite-plugin";

import tailwindcss from "@tailwindcss/vite";


export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: Number(process.env.VITE_PORT || "5173"),
    cors: true,
    ws: {
      host: "localhost",
    },
  },
  plugins: [

    tailwindcss(),

    svelte(),
    litestar({
      input: ["src/main.ts", "src/tailwind.css"],

      types: "auto",

    }),
  ],
});
