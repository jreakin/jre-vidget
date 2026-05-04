# Phase 16 — In-Browser Setup Wizard
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-04
# Maintainer: jreakin
# Status: Draft

---

## Goal

When someone forks this repo, they open the web UI and see a guided setup wizard
instead of the main app. The wizard walks them through entering their GitHub token
and Google credentials, then writes those values directly to GitHub Secrets from
the browser — no terminal, no `gh` CLI required.

After the wizard completes, the user never sees it again.

---

## Prerequisites

Phase 12 complete — `web/` Vite+React app exists, PATGate and github.ts are in place.

---

## How secrets are written from the browser

GitHub's Secrets API requires each secret value to be encrypted with the repo's
public key using libsodium's `crypto_box_seal` (NaCl sealed box). The browser
does this client-side using `libsodium-wrappers`:

1. `GET /repos/{owner}/{repo}/actions/secrets/public-key` → `{ key, key_id }`
2. Encode the plaintext value with libsodium: `crypto_box_seal(value, key)`
3. `PUT /repos/{owner}/{repo}/actions/secrets/{name}` → `{ encrypted_value, key_id }`

The PAT used must have `secrets: write` in addition to the permissions already
needed for the main app (`actions: write`, `contents: write`). One PAT covering
all permissions is the simplest approach.

---

## Files

| Action | File |
|--------|------|
| Modify | `web/package.json` — add `libsodium-wrappers` + `@types/libsodium-wrappers` |
| Create | `web/src/lib/sodium.ts` — encryption wrapper |
| Modify | `web/src/api/github.ts` — add `listSecretNames`, `getRepoPublicKey`, `setSecret` |
| Create | `web/src/components/SetupWizard.tsx` — 4-step wizard UI |
| Modify | `web/src/components/PATGate.tsx` — update required permissions description |
| Modify | `web/src/App.tsx` — route to SetupWizard when secrets are incomplete |

---

## Implementation

### Step 1 — Install libsodium

```bash
cd web
npm install libsodium-wrappers
npm install -D @types/libsodium-wrappers
```

---

### Step 2 — Encryption wrapper

`web/src/lib/sodium.ts`:

```ts
import _sodium from "libsodium-wrappers";

/**
 * Encrypts a secret value using the repo's public key.
 * GitHub requires NaCl sealed-box encryption (crypto_box_seal).
 *
 * @param publicKeyBase64 - base64-encoded repo public key from the Secrets API
 * @param secretValue     - plaintext secret to encrypt
 * @returns base64-encoded ciphertext ready for the Secrets API
 */
export async function encryptSecret(
  publicKeyBase64: string,
  secretValue: string
): Promise<string> {
  await _sodium.ready;
  const sodium = _sodium;

  const keyBytes = sodium.from_base64(
    publicKeyBase64,
    sodium.base64_variants.ORIGINAL
  );
  const messageBytes = sodium.from_string(secretValue);
  const encryptedBytes = sodium.crypto_box_seal(messageBytes, keyBytes);

  return sodium.to_base64(encryptedBytes, sodium.base64_variants.ORIGINAL);
}
```

---

### Step 3 — GitHub API additions

Add these three functions to `web/src/api/github.ts` (alongside the existing ones):

```ts
/** Returns the names of all secrets configured in this repo. */
export async function listSecretNames(pat: string): Promise<string[]> {
  const res = await fetch(
    `${API}/repos/${REPO}/actions/secrets?per_page=100`,
    { headers: headers(pat) }
  );
  if (!res.ok) throw new Error(`Failed to list secrets: ${res.status}`);
  const data = await res.json();
  return (data.secrets ?? []).map((s: { name: string }) => s.name);
}

/** Fetches the repo's libsodium public key for secret encryption. */
export async function getRepoPublicKey(
  pat: string
): Promise<{ key: string; key_id: string }> {
  const res = await fetch(
    `${API}/repos/${REPO}/actions/secrets/public-key`,
    { headers: headers(pat) }
  );
  if (!res.ok) throw new Error(`Failed to get public key: ${res.status}`);
  return res.json();
}

/**
 * Creates or updates a GitHub Secret.
 * Encrypts the value client-side before sending — the plaintext never leaves
 * the browser except as a sealed box addressed to GitHub's servers.
 */
export async function setSecret(
  pat: string,
  name: string,
  value: string
): Promise<void> {
  const { key, key_id } = await getRepoPublicKey(pat);
  const { encryptSecret } = await import("../lib/sodium");
  const encrypted_value = await encryptSecret(key, value);

  const res = await fetch(
    `${API}/repos/${REPO}/actions/secrets/${name}`,
    {
      method: "PUT",
      headers: headers(pat),
      body: JSON.stringify({ encrypted_value, key_id }),
    }
  );
  if (!res.ok) throw new Error(`Failed to set secret ${name}: ${res.status}`);
}
```

---

### Step 4 — SetupWizard component

`web/src/components/SetupWizard.tsx`:

```tsx
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { listSecretNames, setSecret } from "../api/github";

const REQUIRED_SECRETS = [
  "VIDGET_CLIENT_ID",
  "VIDGET_CLIENT_SECRET",
  "VIDGET_REFRESH_TOKEN",
] as const;

type SecretName = (typeof REQUIRED_SECRETS)[number];

interface Props {
  pat: string;
  onComplete: () => void;
}

type Step = "check" | "token-info" | "google-creds" | "refresh-token" | "saving" | "done";

export function SetupWizard({ pat, onComplete }: Props) {
  const [step, setStep] = useState<Step>("check");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [saveError, setSaveError] = useState("");

  // Check which secrets are already present
  const { data: existingSecrets = [], isLoading: checking, error: checkError } = useQuery({
    queryKey: ["secretNames"],
    queryFn: () => listSecretNames(pat),
    retry: 1,
  });

  const missing = REQUIRED_SECRETS.filter((s) => !existingSecrets.includes(s));

  // If all secrets are already configured, skip straight to done
  if (!checking && missing.length === 0 && step === "check") {
    onComplete();
    return null;
  }

  // Move past the check step once we know what's missing
  if (!checking && !checkError && step === "check") {
    setStep("token-info");
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      setSaveError("");
      const toSave: Array<[SecretName, string]> = [];
      if (!existingSecrets.includes("VIDGET_CLIENT_ID")) toSave.push(["VIDGET_CLIENT_ID", clientId]);
      if (!existingSecrets.includes("VIDGET_CLIENT_SECRET")) toSave.push(["VIDGET_CLIENT_SECRET", clientSecret]);
      if (!existingSecrets.includes("VIDGET_REFRESH_TOKEN")) toSave.push(["VIDGET_REFRESH_TOKEN", refreshToken]);
      for (const [name, value] of toSave) {
        await setSecret(pat, name, value);
      }
    },
    onSuccess: () => {
      setStep("done");
      localStorage.setItem("vidget_setup_complete", "true");
    },
    onError: (err) => setSaveError(String(err)),
  });

  // ── Shared styles ─────────────────────────────────────────────────────────
  const card: React.CSSProperties = {
    maxWidth: 520,
    margin: "4rem auto",
    padding: "2rem",
    background: "var(--color-background-primary)",
    border: "0.5px solid var(--color-border-tertiary)",
    borderRadius: 14,
  };
  const label: React.CSSProperties = {
    display: "block",
    fontSize: 13,
    color: "var(--color-text-secondary)",
    marginBottom: 5,
  };
  const input: React.CSSProperties = { width: "100%", marginBottom: 14 };
  const hint: React.CSSProperties = {
    fontSize: 12,
    color: "var(--color-text-tertiary)",
    marginTop: -10,
    marginBottom: 14,
    lineHeight: 1.5,
  };
  const row: React.CSSProperties = { display: "flex", gap: 8, marginTop: 8 };

  // ── Step: checking ────────────────────────────────────────────────────────
  if (checking || step === "check") {
    return (
      <div style={card}>
        <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>
          Checking setup…
        </h2>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>
          Connecting to GitHub to see what needs to be configured.
        </p>
        {checkError && (
          <p style={{ fontSize: 13, color: "var(--color-text-danger)", marginTop: "1rem" }}>
            {String(checkError)}. Check your token has <code>secrets: read</code> permission.
          </p>
        )}
      </div>
    );
  }

  // ── Step: token info ──────────────────────────────────────────────────────
  if (step === "token-info") {
    return (
      <div style={card}>
        <StepIndicator current={1} total={3} />
        <h2 style={{ fontSize: 18, fontWeight: 500, margin: "1rem 0 0.5rem" }}>
          Token permissions
        </h2>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          The token you entered needs one additional permission to save secrets.
          If you used a fine-grained token, edit it on GitHub and add:
        </p>
        <ul style={{ fontSize: 14, paddingLeft: "1.25rem", lineHeight: 2, marginBottom: "1.25rem" }}>
          <li><code>Actions</code> → Read and write</li>
          <li><code>Contents</code> → Read and write</li>
          <li><strong><code>Secrets</code> → Read and write</strong> ← required for setup</li>
        </ul>
        <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", marginBottom: "1.25rem" }}>
          For a classic token, <code>repo</code> scope covers everything.
          The token is stored only in your browser's localStorage and is only
          ever sent directly to GitHub's API.
        </p>
        <div style={row}>
          <button
            onClick={() => setStep("google-creds")}
            style={{ flex: 1, background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "9px 0", fontSize: 14, fontWeight: 500, cursor: "pointer" }}
          >
            My token has these permissions →
          </button>
        </div>
      </div>
    );
  }

  // ── Step: Google credentials ───────────────────────────────────────────────
  if (step === "google-creds") {
    const needsClientId = !existingSecrets.includes("VIDGET_CLIENT_ID");
    const needsClientSecret = !existingSecrets.includes("VIDGET_CLIENT_SECRET");
    if (!needsClientId && !needsClientSecret) {
      setStep("refresh-token");
      return null;
    }
    return (
      <div style={card}>
        <StepIndicator current={2} total={3} />
        <h2 style={{ fontSize: 18, fontWeight: 500, margin: "1rem 0 0.5rem" }}>
          Google OAuth credentials
        </h2>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          These come from a Google Cloud project with the YouTube Data API v3 enabled.
          See <a href="https://github.com/jreakin/jre-vidget/blob/main/docs/SETUP.md#step-2" target="_blank" rel="noreferrer" style={{ color: "#185FA5" }}>docs/SETUP.md — step 2</a> for how to create them.
        </p>

        {needsClientId && (
          <>
            <label style={label}>Client ID</label>
            <input
              type="text"
              placeholder="123456789-abc…apps.googleusercontent.com"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              style={input}
              autoComplete="off"
            />
            <p style={hint}>
              From Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs.
            </p>
          </>
        )}

        {needsClientSecret && (
          <>
            <label style={label}>Client Secret</label>
            <input
              type="password"
              placeholder="GOCSPX-…"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              style={input}
              autoComplete="off"
            />
            <p style={hint}>Found alongside the Client ID in Google Cloud Console.</p>
          </>
        )}

        <div style={row}>
          <button onClick={() => setStep("token-info")} style={{ flex: "0 0 auto" }}>
            ← Back
          </button>
          <button
            onClick={() => setStep("refresh-token")}
            disabled={
              (needsClientId && !clientId.trim()) ||
              (needsClientSecret && !clientSecret.trim())
            }
            style={{ flex: 1, background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "9px 0", fontSize: 14, fontWeight: 500, cursor: "pointer" }}
          >
            Next →
          </button>
        </div>
      </div>
    );
  }

  // ── Step: refresh token ───────────────────────────────────────────────────
  if (step === "refresh-token") {
    const needsRefresh = !existingSecrets.includes("VIDGET_REFRESH_TOKEN");
    if (!needsRefresh) {
      saveMutation.mutate();
      setStep("saving");
      return null;
    }
    return (
      <div style={card}>
        <StepIndicator current={3} total={3} />
        <h2 style={{ fontSize: 18, fontWeight: 500, margin: "1rem 0 0.5rem" }}>
          YouTube refresh token
        </h2>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          This authorises vidget to upload to your YouTube channel. You generate it
          once by running the auth flow locally with the credentials from the previous step.
        </p>

        <div style={{ background: "var(--color-background-secondary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 8, padding: "1rem", marginBottom: "1.25rem", fontFamily: "monospace", fontSize: 13 }}>
          <div style={{ color: "var(--color-text-tertiary)", marginBottom: 6 }}># Run this once on your machine:</div>
          <div>VIDGET_CLIENT_ID=<span style={{ color: "#185FA5" }}>{"<your-client-id>"}</span> \</div>
          <div>&nbsp;&nbsp;VIDGET_CLIENT_SECRET=<span style={{ color: "#185FA5" }}>{"<your-client-secret>"}</span> \</div>
          <div>&nbsp;&nbsp;vidget auth login</div>
          <div style={{ marginTop: 8 }}># Then copy the refresh_token from:</div>
          <div style={{ color: "#3B6D11" }}>~/.vidget/config.json</div>
        </div>

        <p style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginBottom: "1.25rem" }}>
          See <a href="https://github.com/jreakin/jre-vidget/blob/main/docs/SETUP.md#step-3" target="_blank" rel="noreferrer" style={{ color: "#185FA5" }}>docs/SETUP.md — step 3</a> for the full walkthrough.
          The refresh token never expires unless you revoke it in your Google account.
        </p>

        <label style={label}>Refresh Token</label>
        <input
          type="password"
          placeholder="1//0g…"
          value={refreshToken}
          onChange={(e) => setRefreshToken(e.target.value)}
          style={input}
          autoComplete="off"
        />

        {saveError && (
          <p style={{ fontSize: 13, color: "var(--color-text-danger)", marginBottom: 10 }}>
            {saveError}
          </p>
        )}

        <div style={row}>
          <button
            onClick={() => setStep("google-creds")}
            style={{ flex: "0 0 auto" }}
          >
            ← Back
          </button>
          <button
            onClick={() => { setStep("saving"); saveMutation.mutate(); }}
            disabled={!refreshToken.trim() || saveMutation.isPending}
            style={{ flex: 1, background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "9px 0", fontSize: 14, fontWeight: 500, cursor: "pointer" }}
          >
            {saveMutation.isPending ? "Saving secrets…" : "Save & finish"}
          </button>
        </div>
      </div>
    );
  }

  // ── Step: saving ──────────────────────────────────────────────────────────
  if (step === "saving") {
    return (
      <div style={card}>
        <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>
          Saving secrets…
        </h2>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>
          Encrypting and writing to GitHub Secrets. This takes a few seconds.
        </p>
        {saveError && (
          <p style={{ fontSize: 13, color: "var(--color-text-danger)", marginTop: "1rem" }}>
            {saveError}
          </p>
        )}
      </div>
    );
  }

  // ── Step: done ────────────────────────────────────────────────────────────
  return (
    <div style={card}>
      <div style={{ fontSize: 40, marginBottom: "0.75rem" }}>✅</div>
      <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>
        Setup complete
      </h2>
      <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1.5rem" }}>
        Your credentials are saved as GitHub Secrets. They're encrypted and only
        accessible by GitHub Actions workflows in your repo.
      </p>
      <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", marginBottom: "1.5rem" }}>
        You won't see this wizard again. If you ever need to update credentials,
        go to <strong>Settings → Secrets → Actions</strong> in your GitHub repo.
      </p>
      <button
        onClick={onComplete}
        style={{ width: "100%", background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "10px 0", fontSize: 14, fontWeight: 500, cursor: "pointer" }}
      >
        Open vidget →
      </button>
    </div>
  );
}

// ── Step indicator ─────────────────────────────────────────────────────────
function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          style={{
            height: 4,
            flex: 1,
            borderRadius: 2,
            background: i < current ? "#185FA5" : "var(--color-border-tertiary)",
            transition: "background 0.2s",
          }}
        />
      ))}
      <span style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginLeft: 4, whiteSpace: "nowrap" }}>
        {current}/{total}
      </span>
    </div>
  );
}
```

---

### Step 5 — Update PATGate

Update the permission description in `web/src/components/PATGate.tsx` to mention
`Secrets: read and write` (needed for the setup wizard) and update the validation
to accept both classic (`ghp_`) and fine-grained (`github_pat_`) tokens:

```tsx
// Replace the <p> description and the disabled condition:

<p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1rem" }}>
  A GitHub token for this repo. Required permissions:
  <br />• <strong>Actions</strong> — read and write
  <br />• <strong>Contents</strong> — read and write
  <br />• <strong>Secrets</strong> — read and write <em>(first-time setup only)</em>
  <br /><br />
  Stored in browser localStorage — only ever sent to GitHub's API.
</p>

// Update the disabled check:
disabled={!value.startsWith("github_pat_") && !value.startsWith("ghp_")}
```

---

### Step 6 — Update App.tsx

Replace the routing logic in `web/src/App.tsx` to check setup status after the
PAT is entered:

```tsx
import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { PATGate, usePAT } from "./components/PATGate";
import { SetupWizard } from "./components/SetupWizard";
import { TopBar } from "./components/TopBar";
import { UploadForm } from "./components/UploadForm";
import { StatusCard } from "./components/StatusCard";
import { HistoryList } from "./components/HistoryList";
import { EditModal } from "./components/EditModal";
import { listSecretNames } from "./api/github";
import type { UploadRecord } from "./types";

const REQUIRED = ["VIDGET_CLIENT_ID", "VIDGET_CLIENT_SECRET", "VIDGET_REFRESH_TOKEN"];
const queryClient = new QueryClient();

function Inner() {
  const { pat, setPAT, clearPAT } = usePAT();
  const [setupComplete, setSetupComplete] = useState(
    () => localStorage.getItem("vidget_setup_complete") === "true"
  );
  const [refreshKey, setRefreshKey] = useState(0);
  const [editRecord, setEditRecord] = useState<UploadRecord | null>(null);

  // Once we have a PAT, check if secrets are already configured.
  // Skip the check if the setup flag is already set in localStorage.
  const { data: secretNames, isLoading: checkingSecrets } = useQuery({
    queryKey: ["secretNamesCheck", pat],
    queryFn: () => listSecretNames(pat),
    enabled: !!pat && !setupComplete,
    retry: 1,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (!secretNames) return;
    const allPresent = REQUIRED.every((s) => secretNames.includes(s));
    if (allPresent) {
      localStorage.setItem("vidget_setup_complete", "true");
      setSetupComplete(true);
    }
  }, [secretNames]);

  if (!pat) return <PATGate onSave={setPAT} />;

  if (!setupComplete && checkingSecrets) {
    return (
      <div style={{ maxWidth: 520, margin: "4rem auto", padding: "0 1rem", textAlign: "center", color: "var(--color-text-secondary)", fontSize: 14 }}>
        Checking configuration…
      </div>
    );
  }

  if (!setupComplete) {
    return (
      <SetupWizard
        pat={pat}
        onComplete={() => setSetupComplete(true)}
      />
    );
  }

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <TopBar onClearPAT={() => { clearPAT(); setSetupComplete(false); localStorage.removeItem("vidget_setup_complete"); }} />
      <UploadForm pat={pat} onDispatched={() => setRefreshKey((k) => k + 1)} />
      <StatusCard pat={pat} onComplete={() => setRefreshKey((k) => k + 1)} />
      <HistoryList refreshKey={refreshKey} onEdit={setEditRecord} />
      {editRecord && <EditModal record={editRecord} onClose={() => setEditRecord(null)} />}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Inner />
    </QueryClientProvider>
  );
}
```

Note: `TopBar`'s `onClearPAT` now also clears the setup flag so the wizard
re-runs if a different user connects with a different token.

---

### Step 7 — Smoke test locally

```bash
cd web
VITE_APP_TITLE="My vidget" VITE_GITHUB_REPO="yourname/jre-vidget" npm run dev
```

Test the wizard flow:
1. Enter a token starting with `github_pat_` or `ghp_` — PATGate should accept it
2. The app fetches secret names — if your repo has all three secrets it skips to main UI
3. If secrets are missing it shows the wizard with the progress bar and steps
4. Each step's "Next" button is disabled until the field is filled
5. "Save & finish" shows "Saving secrets…" then the ✅ done screen
6. "Open vidget →" routes to the main upload form

---

### Step 8 — Commit

```bash
git add web/
git commit -m "feat(web): add in-browser setup wizard for GitHub Secrets"
```

Pushing to `main` triggers `deploy-web.yml`. After deploy, new forks of the repo
will see the wizard on first load.

---

## Security notes

- Secret values are encrypted in the browser before being sent anywhere
- The encrypted ciphertext is addressed specifically to GitHub's servers via
  the repo's public key — only GitHub can decrypt it
- The PAT and plaintext secret values exist only in JavaScript memory during
  the wizard; they are never logged, stored, or sent to any server other than
  `api.github.com`
- After setup, the PAT in localStorage is the same one used for workflow dispatch
  — if the user wants to revoke setup access, they can rotate the token on GitHub

---

## Acceptance criteria

- [ ] `npm run build` in `web/` succeeds with no TypeScript errors
- [ ] PATGate accepts both `github_pat_` and `ghp_` token prefixes
- [ ] PATGate permissions description lists Secrets: read and write
- [ ] On first load with no secrets configured, wizard shows instead of main app
- [ ] Wizard skips steps for secrets that are already present in the repo
- [ ] Step 2 fields are disabled-until-filled; Next button activates correctly
- [ ] "Save & finish" encrypts each value with libsodium and calls the Secrets API
- [ ] ✅ done screen appears on success; localStorage flag is set
- [ ] "Open vidget →" routes to the main upload form
- [ ] On subsequent loads, `vidget_setup_complete` flag skips the check entirely
- [ ] "Disconnect" clears both the PAT and the setup flag (wizard re-runs on next login)
- [ ] No secret values appear in the browser console or network tab as plaintext
