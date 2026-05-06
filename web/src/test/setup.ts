import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// `api/github.ts` reads `import.meta.env.VITE_GITHUB_REPO` at load time; tests must not hit real GitHub.
vi.stubEnv("VITE_GITHUB_REPO", "jreakin/jre-vidget");

afterEach(() => {
  cleanup();
});
