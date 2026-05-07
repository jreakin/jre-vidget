/**
 * Resolve `owner/repo` for GitHub API calls (Vite `import.meta.env.VITE_GITHUB_REPO`).
 * Used at config load time by `vite.config.ts` and `vitest.config.ts`.
 */
import { execSync } from "node:child_process";

/** Public upstream; last resort when env is unset and git has no origin. */
export const DEFAULT_GITHUB_REPO = "jreakin/jre-vidget";

function parseOwnerRepoFromRemoteUrl(url: string): string | null {
  const t = url.trim();
  if (!t) return null;
  const ssh = t.match(/^git@github\.com:([^/]+)\/([^/.]+?)(?:\.git)?$/i);
  if (ssh) return `${ssh[1]}/${ssh[2]}`;
  const https = t.match(/github\.com\/([^/]+)\/([^/.]+?)(?:\.git)?(?:\/|$)/i);
  if (https) return `${https[1]}/${https[2]}`;
  return null;
}

/**
 * @param explicitFromEnv - First non-blank `VITE_GITHUB_REPO` from `.env*` / process.env
 * @param gitWorkDir - Repository root (directory containing `.git`)
 */
export function resolveGithubRepoForVite(
  explicitFromEnv: string | undefined,
  gitWorkDir: string,
): string {
  const trimmed = explicitFromEnv?.trim();
  if (trimmed && trimmed.includes("/")) return trimmed;

  try {
    const url = execSync("git remote get-url origin", {
      cwd: gitWorkDir,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    const parsed = parseOwnerRepoFromRemoteUrl(url);
    if (parsed) return parsed;
  } catch {
    // no git, no origin, or exec failed
  }

  return DEFAULT_GITHUB_REPO;
}
