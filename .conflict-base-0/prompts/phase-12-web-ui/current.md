# Phase 12 — Web UI (Vite + React + TanStack)
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

Build a GitHub Pages web UI that lets anyone who clones the repo trigger download-and-upload
jobs, watch live status, and browse upload history — all from a browser, no local CLI needed.
Stack: Vite + React + TanStack Query (polling) + TanStack Router (SPA routing).
Deployed automatically to the `gh-pages` branch via a GitHub Actions workflow whenever
`web/src/**` changes on `main`.

---

## Spec Reference

`docs/superpowers/specs/2026-05-03-youtube-publish-design.md` — CLI Commands section.
UI mockup agreed in conversation (2026-05-03): upload form, live status card, upload history.

---

## Prerequisites

- Phase 11 complete (`uploads.json` exists, `publish.yml` workflow exists)
- GitHub Pages enabled in repo settings: Source = `gh-pages` branch, `/ (root)`
- `VITE_APP_TITLE` and `VITE_GITHUB_REPO` set as GitHub Actions variables (not secrets)
- Node.js 20+ available locally for development

---

## Files

| Action | File |
|--------|------|
| Create | `web/package.json` |
| Create | `web/vite.config.ts` |
| Create | `web/tsconfig.json` |
| Create | `web/index.html` |
| Create | `web/src/env.d.ts` |
| Create | `web/src/main.tsx` |
| Create | `web/src/App.tsx` |
| Create | `web/src/types.ts` |
| Create | `web/src/api/github.ts` |
| Create | `web/src/components/TopBar.tsx` |
| Create | `web/src/components/UploadForm.tsx` |
| Create | `web/src/components/StatusCard.tsx` |
| Create | `web/src/components/HistoryList.tsx` |
| Create | `web/src/components/EditModal.tsx` |
| Create | `web/src/components/PATGate.tsx` |
| Create | `.github/workflows/deploy-web.yml` |

---

## Implementation

### Step 1 — Scaffold the Vite + React project

```bash
cd web
npm create vite@latest . -- --template react-ts
npm install
npm install @tanstack/react-query @tanstack/react-router
npm install -D @types/node
```

---

### Step 2 — Configure Vite for GitHub Pages

`web/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // gh-pages serves at /REPO_NAME/ — keep as "/" for custom domain or root pages
  base: "./",
});
```

---

### Step 3 — Declare VITE_ env var types

`web/src/env.d.ts`:

```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string;
  readonly VITE_GITHUB_REPO: string;  // e.g. "jreakin/jre-vidget"
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

### Step 4 — Define shared types

`web/src/types.ts`:

```ts
export interface UploadRecord {
  video_id: string;
  url: string;
  title: string;
  source_url: string;
  privacy: "public" | "unlisted" | "private";
  uploaded_at: string;   // ISO 8601
  run_id: string;
}

export interface WorkflowRun {
  id: number;
  status: "queued" | "in_progress" | "completed";
  conclusion: "success" | "failure" | "cancelled" | null;
  html_url: string;
  created_at: string;
}

export interface DispatchInputs {
  url: string;
  title: string;
  description: string;
  privacy: "public" | "unlisted" | "private";
  remove_after_upload: boolean;
}
```

---

### Step 5 — GitHub API module

`web/src/api/github.ts`:

```ts
const REPO = import.meta.env.VITE_GITHUB_REPO;          // "owner/repo"
const API  = "https://api.github.com";
const RAW  = "https://raw.githubusercontent.com";

function headers(pat: string) {
  return {
    Authorization: `Bearer ${pat}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

/** Trigger the publish workflow_dispatch. */
export async function dispatchPublish(
  pat: string,
  inputs: import("../types").DispatchInputs
): Promise<void> {
  const res = await fetch(
    `${API}/repos/${REPO}/actions/workflows/publish.yml/dispatches`,
    {
      method: "POST",
      headers: headers(pat),
      body: JSON.stringify({ ref: "main", inputs: { ...inputs, remove_after_upload: String(inputs.remove_after_upload) } }),
    }
  );
  if (!res.ok) throw new Error(`Dispatch failed: ${res.status} ${await res.text()}`);
}

/** Fetch the most recent workflow run for the publish workflow. */
export async function fetchLatestRun(
  pat: string
): Promise<import("../types").WorkflowRun | null> {
  const res = await fetch(
    `${API}/repos/${REPO}/actions/workflows/publish.yml/runs?per_page=1`,
    { headers: headers(pat) }
  );
  if (!res.ok) return null;
  const data = await res.json();
  return data.workflow_runs?.[0] ?? null;
}

/** Fetch uploads.json from the main branch. No auth needed for public repos. */
export async function fetchUploads(): Promise<import("../types").UploadRecord[]> {
  const [owner, repo] = REPO.split("/");
  const res = await fetch(`${RAW}/${owner}/${repo}/main/uploads.json`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.uploads ?? [];
}
```

---

### Step 6 — PAT gate component

Users enter their GitHub PAT once; it is stored in `localStorage`. All pages are
wrapped in this component — if no PAT is stored, the form is shown first.

`web/src/components/PATGate.tsx`:

```tsx
import { useState } from "react";

const KEY = "vidget_gh_pat";

export function usePAT() {
  const [pat, setPATState] = useState(() => localStorage.getItem(KEY) ?? "");
  const setPAT = (v: string) => {
    localStorage.setItem(KEY, v);
    setPATState(v);
  };
  const clearPAT = () => {
    localStorage.removeItem(KEY);
    setPATState("");
  };
  return { pat, setPAT, clearPAT };
}

interface Props {
  onSave: (pat: string) => void;
}

export function PATGate({ onSave }: Props) {
  const [value, setValue] = useState("");
  return (
    <div style={{ maxWidth: 480, margin: "4rem auto", padding: "0 1rem" }}>
      <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "1rem" }}>
        Enter your GitHub token
      </h2>
      <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1rem" }}>
        A fine-grained token with <code>Actions: write</code> and <code>Contents: write</code>{" "}
        on this repo. Stored in browser localStorage — never sent anywhere except GitHub's API.
      </p>
      <input
        type="password"
        placeholder="github_pat_..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={{ width: "100%", marginBottom: "0.75rem" }}
      />
      <button
        disabled={!value.startsWith("github_")}
        onClick={() => onSave(value)}
        style={{ width: "100%" }}
      >
        Save token
      </button>
    </div>
  );
}
```

---

### Step 7 — TopBar component

`web/src/components/TopBar.tsx`:

```tsx
interface Props {
  onClearPAT: () => void;
}

export function TopBar({ onClearPAT }: Props) {
  const title = import.meta.env.VITE_APP_TITLE || "vidget";

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ width: 28, height: 28, background: "#185FA5", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="white">
            <path d="M8 1L1 14h14L8 1zm0 3l4.5 8h-9L8 4z" />
          </svg>
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 500, lineHeight: 1.2 }}>{title}</div>
          <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", lineHeight: 1.2 }}>powered by vidget</div>
        </div>
      </div>
      <button onClick={onClearPAT} style={{ fontSize: 13 }}>
        Disconnect
      </button>
    </div>
  );
}
```

---

### Step 8 — UploadForm component

`web/src/components/UploadForm.tsx`:

```tsx
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { dispatchPublish } from "../api/github";
import type { DispatchInputs } from "../types";

interface Props {
  pat: string;
  onDispatched: () => void;
}

export function UploadForm({ pat, onDispatched }: Props) {
  const [form, setForm] = useState<DispatchInputs>({
    url: "",
    title: "",
    description: "",
    privacy: "public",
    remove_after_upload: false,
  });

  const mutation = useMutation({
    mutationFn: () => dispatchPublish(pat, form),
    onSuccess: () => {
      onDispatched();
      setForm((f) => ({ ...f, url: "", title: "", description: "" }));
    },
  });

  return (
    <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "1.25rem", marginBottom: "1rem" }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "1rem" }}>
        New upload
      </div>

      <label style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}>Video URL</label>
      <input
        type="url"
        placeholder="https://twitter.com/…"
        value={form.url}
        onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
        style={{ width: "100%", marginBottom: 14 }}
      />

      <label style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}>Title</label>
      <input
        type="text"
        placeholder="Leave blank to use scraped title"
        value={form.title}
        onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
        style={{ width: "100%", marginBottom: 14 }}
      />

      <label style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}>Description</label>
      <textarea
        value={form.description}
        onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
        style={{ width: "100%", height: 72, resize: "none", marginBottom: 14, fontFamily: "inherit" }}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
        <div>
          <label style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}>Privacy</label>
          <select
            value={form.privacy}
            onChange={(e) => setForm((f) => ({ ...f, privacy: e.target.value as DispatchInputs["privacy"] }))}
            style={{ width: "100%" }}
          >
            <option value="public">Public</option>
            <option value="unlisted">Unlisted</option>
            <option value="private">Private</option>
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}>After upload</label>
          <select
            value={form.remove_after_upload ? "remove" : "keep"}
            onChange={(e) => setForm((f) => ({ ...f, remove_after_upload: e.target.value === "remove" }))}
            style={{ width: "100%" }}
          >
            <option value="keep">Keep local file</option>
            <option value="remove">Delete local file</option>
          </select>
        </div>
      </div>

      {mutation.isError && (
        <p style={{ fontSize: 13, color: "var(--color-text-danger)", marginBottom: 10 }}>
          {String(mutation.error)}
        </p>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button
          onClick={() => mutation.mutate()}
          disabled={!form.url || mutation.isPending}
          style={{ background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "8px 18px", fontSize: 14, fontWeight: 500, cursor: "pointer" }}
        >
          {mutation.isPending ? "Queuing…" : "Download & upload"}
        </button>
        <button onClick={() => setForm({ url: "", title: "", description: "", privacy: "public", remove_after_upload: false })}>
          Reset
        </button>
        <span style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginLeft: "auto" }}>~2–4 min for 1080p</span>
      </div>
    </div>
  );
}
```

---

### Step 9 — StatusCard component

Polls the GitHub Actions API every 5 seconds while a run is active.

`web/src/components/StatusCard.tsx`:

```tsx
import { useQuery } from "@tanstack/react-query";
import { fetchLatestRun } from "../api/github";
import type { WorkflowRun } from "../types";

interface Props {
  pat: string;
  onComplete: () => void;
}

export function StatusCard({ pat, onComplete }: Props) {
  const { data: run } = useQuery<WorkflowRun | null>({
    queryKey: ["latestRun"],
    queryFn: () => fetchLatestRun(pat),
    refetchInterval: (query) => {
      const run = query.state.data;
      if (!run || run.status === "completed") {
        if (run?.status === "completed") onComplete();
        return false;
      }
      return 5_000;
    },
  });

  if (!run || run.status === "completed") return null;

  const label = run.status === "queued" ? "Queued" : "Running";

  return (
    <div style={{ background: "var(--color-background-secondary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "1.25rem", marginBottom: "1rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 16, height: 16, border: "2px solid var(--color-border-secondary)", borderTopColor: "#185FA5", borderRadius: "50%", animation: "spin 0.8s linear infinite", flexShrink: 0 }} />
        <div>
          <div style={{ fontSize: 14 }}>{label} · <a href={run.html_url} target="_blank" rel="noreferrer" style={{ color: "#185FA5" }}>run #{run.id}</a></div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 3 }}>
            Started {new Date(run.created_at).toLocaleTimeString()}
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
```

---

### Step 10 — HistoryList component

`web/src/components/HistoryList.tsx`:

```tsx
import { useQuery } from "@tanstack/react-query";
import { fetchUploads } from "../api/github";
import type { UploadRecord } from "../types";

const PRIVACY_STYLE: Record<string, { color: string; background: string; border: string }> = {
  public:   { color: "#3B6D11", background: "#EAF3DE", border: "#97C459" },
  unlisted: { color: "#5F5E5A", background: "#F1EFE8", border: "#B4B2A9" },
  private:  { color: "#533A89", background: "#EEEDFE", border: "#AFA9EC" },
};

interface Props {
  refreshKey: number;
  onEdit: (record: UploadRecord) => void;
}

export function HistoryList({ refreshKey, onEdit }: Props) {
  const { data: uploads = [] } = useQuery<UploadRecord[]>({
    queryKey: ["uploads", refreshKey],
    queryFn: fetchUploads,
    staleTime: 30_000,
  });

  if (uploads.length === 0) return null;

  return (
    <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "1.25rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Upload history</span>
        <span style={{ fontSize: 12, background: "var(--color-background-secondary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 10, padding: "1px 7px", color: "var(--color-text-tertiary)" }}>{uploads.length}</span>
      </div>
      {uploads.map((u, i) => {
        const ps = PRIVACY_STYLE[u.privacy] ?? PRIVACY_STYLE.public;
        return (
          <div
            key={u.video_id}
            style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "12px 0", borderBottom: i < uploads.length - 1 ? "0.5px solid var(--color-border-tertiary)" : "none" }}
          >
            <div style={{ width: 72, height: 42, background: "var(--color-background-secondary)", borderRadius: 4, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" opacity={0.3}><path d="M8 5v14l11-7z" /></svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{u.title}</div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 3 }}>
                {new Date(u.uploaded_at).toLocaleString()}
              </div>
              <div style={{ display: "flex", gap: 6, marginTop: 6, alignItems: "center" }}>
                <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 6, border: `0.5px solid ${ps.border}`, color: ps.color, background: ps.background }}>{u.privacy}</span>
                <a href={u.url} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: "#185FA5" }}>youtu.be/{u.video_id}</a>
                <button onClick={() => onEdit(u)} style={{ fontSize: 12, padding: "3px 8px", marginLeft: 2 }}>Edit metadata</button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

---

### Step 11 — EditModal component

Opens when the user clicks "Edit metadata." Links directly to YouTube Studio for
the specific video. Browser-side YouTube API editing is deferred to a future phase.

`web/src/components/EditModal.tsx`:

```tsx
import type { UploadRecord } from "../types";

interface Props {
  record: UploadRecord;
  onClose: () => void;
}

export function EditModal({ record, onClose }: Props) {
  const studioUrl = `https://studio.youtube.com/video/${record.video_id}/edit`;

  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "1.5rem", maxWidth: 420, width: "90%" }}
      >
        <div style={{ fontSize: 16, fontWeight: 500, marginBottom: "0.5rem" }}>Edit metadata</div>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1rem" }}>
          <strong>{record.title}</strong>
        </p>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          Title and description can be edited directly in YouTube Studio.
          In-page editing via the YouTube API will be added in a future update.
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <a
            href={studioUrl}
            target="_blank"
            rel="noreferrer"
            style={{ flex: 1, background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "8px 0", fontSize: 14, fontWeight: 500, textAlign: "center", textDecoration: "none" }}
          >
            Open in YouTube Studio
          </a>
          <button onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
```

---

### Step 12 — App entry point

`web/src/App.tsx`:

```tsx
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PATGate, usePAT } from "./components/PATGate";
import { TopBar } from "./components/TopBar";
import { UploadForm } from "./components/UploadForm";
import { StatusCard } from "./components/StatusCard";
import { HistoryList } from "./components/HistoryList";
import { EditModal } from "./components/EditModal";
import type { UploadRecord } from "./types";

const queryClient = new QueryClient();

export default function App() {
  const { pat, setPAT, clearPAT } = usePAT();
  const [refreshKey, setRefreshKey] = useState(0);
  const [editRecord, setEditRecord] = useState<UploadRecord | null>(null);

  if (!pat) return <PATGate onSave={setPAT} />;

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ maxWidth: 680, margin: "0 auto", padding: "1.5rem 1rem" }}>
        <TopBar onClearPAT={clearPAT} />
        <UploadForm pat={pat} onDispatched={() => setRefreshKey((k) => k + 1)} />
        <StatusCard pat={pat} onComplete={() => setRefreshKey((k) => k + 1)} />
        <HistoryList refreshKey={refreshKey} onEdit={setEditRecord} />
        {editRecord && <EditModal record={editRecord} onClose={() => setEditRecord(null)} />}
      </div>
    </QueryClientProvider>
  );
}
```

`web/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

`web/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>vidget</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

### Step 13 — Deploy workflow

`.github/workflows/deploy-web.yml`:

```yaml
name: Deploy web UI to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - "web/**"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: web/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: web

      - name: Build
        env:
          VITE_APP_TITLE: ${{ vars.VITE_APP_TITLE }}
          VITE_GITHUB_REPO: ${{ vars.VITE_GITHUB_REPO }}
        run: npm run build
        working-directory: web

      - name: Deploy to gh-pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: web/dist
          force_orphan: true
```

---

### Step 14 — Local dev smoke test

```bash
cd web
VITE_APP_TITLE="My Uploader" VITE_GITHUB_REPO="owner/repo" npm run dev
```

Open `http://localhost:5173` — enter any `github_pat_...` string, verify the form
renders. Network calls to GitHub will fail locally (no real PAT / repo), which is
expected.

---

### Step 15 — Commit

```bash
git add web/ .github/workflows/deploy-web.yml
git commit -m "feat: add Vite+React+TanStack web UI with gh-pages deployment"
```

Pushing to `main` triggers `deploy-web.yml` automatically. After it completes, the
app is live at `https://USERNAME.github.io/jre-vidget/`.

---

## Acceptance Criteria

- [ ] `npm run build` in `web/` succeeds with no TypeScript errors
- [ ] `VITE_APP_TITLE` env var populates the TopBar title at build time
- [ ] `VITE_GITHUB_REPO` env var is used in all GitHub API calls
- [ ] PATGate shows on first visit; PAT stored in `localStorage`; "Disconnect" clears it
- [ ] UploadForm dispatches `workflow_dispatch` to `publish.yml` on submit
- [ ] StatusCard polls every 5 seconds while a run is active; disappears on completion
- [ ] HistoryList reads `uploads.json` from the main branch and renders all records
- [ ] Privacy badge colors: public=green, unlisted=gray, private=purple
- [ ] "Edit metadata" opens EditModal with YouTube Studio deep link
- [ ] `deploy-web.yml` triggers on changes to `web/**` on `main`
- [ ] Deployed app is accessible at `https://USERNAME.github.io/REPO/`
