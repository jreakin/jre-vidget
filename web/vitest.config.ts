import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

import { resolveGithubRepoForVite } from "./resolve-github-repo";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "");
  const explicit =
    env.VITE_GITHUB_REPO || process.env.VITE_GITHUB_REPO || undefined;
  const viteGithubRepo = resolveGithubRepoForVite(explicit, repoRoot);

  return {
    plugins: [react()],
    base: "./",
    define: {
      "import.meta.env.VITE_GITHUB_REPO": JSON.stringify(viteGithubRepo),
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
    },
  };
});
