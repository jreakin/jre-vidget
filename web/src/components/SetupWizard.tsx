import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { listSecretNames, setSecret } from "../api/github";
import {
  CANONICAL_CLIENT_ID_SECRET,
  CANONICAL_CLIENT_SECRET,
  CANONICAL_REFRESH_TOKEN,
  GCLOUD_CLIENT_ID_KEYS,
  GCLOUD_CLIENT_SECRET_KEYS,
  GCLOUD_REFRESH_TOKEN_KEYS,
  hasAnySecret,
} from "../lib/google-oauth-secrets";

function oauthSecretsComplete(names: string[]): boolean {
  return (
    hasAnySecret(GCLOUD_CLIENT_ID_KEYS, names) &&
    hasAnySecret(GCLOUD_CLIENT_SECRET_KEYS, names) &&
    hasAnySecret(GCLOUD_REFRESH_TOKEN_KEYS, names)
  );
}

interface SetupWizardProps {
  pat: string;
  onComplete: () => void;
}

type Step = "check" | "token-info" | "google-creds" | "refresh-token" | "saving" | "done";

export function SetupWizard({ pat, onComplete }: SetupWizardProps) {
  const [step, setStep] = useState<Step>("check");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [saveError, setSaveError] = useState("");
  const autoRefreshSaveRef = useRef(false);

  const { data: existingSecrets = [], isLoading: checking, error: checkError } = useQuery({
    queryKey: ["secretNamesWizard", pat],
    queryFn: () => listSecretNames(pat),
    retry: 1,
  });

  const oauthComplete = oauthSecretsComplete(existingSecrets);

  useEffect(() => {
    if (checking || checkError) return;
    if (!oauthComplete) return;
    if (step !== "check") return;
    queueMicrotask(() => {
      onComplete();
    });
  }, [checking, checkError, oauthComplete, onComplete, step]);

  useEffect(() => {
    if (checking || checkError) return;
    if (oauthComplete) return;
    if (step !== "check") return;
    queueMicrotask(() => {
      setStep("token-info");
    });
  }, [checking, checkError, oauthComplete, step]);

  useEffect(() => {
    if (step !== "google-creds") return;
    const needsClientId = !hasAnySecret(GCLOUD_CLIENT_ID_KEYS, existingSecrets);
    const needsClientSecret = !hasAnySecret(GCLOUD_CLIENT_SECRET_KEYS, existingSecrets);
    if (needsClientId || needsClientSecret) return;
    queueMicrotask(() => {
      setStep("refresh-token");
    });
  }, [step, existingSecrets]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      setSaveError("");
      const toSave: Array<[string, string]> = [];
      if (!hasAnySecret(GCLOUD_CLIENT_ID_KEYS, existingSecrets)) {
        toSave.push([CANONICAL_CLIENT_ID_SECRET, clientId]);
      }
      if (!hasAnySecret(GCLOUD_CLIENT_SECRET_KEYS, existingSecrets)) {
        toSave.push([CANONICAL_CLIENT_SECRET, clientSecret]);
      }
      if (!hasAnySecret(GCLOUD_REFRESH_TOKEN_KEYS, existingSecrets)) {
        toSave.push([CANONICAL_REFRESH_TOKEN, refreshToken]);
      }
      for (const [name, value] of toSave) {
        await setSecret(pat, name, value);
      }
    },
    onSuccess: () => {
      setStep("done");
      localStorage.setItem("vidget_setup_complete", "true");
    },
    onError: (err: unknown) => {
      setSaveError(String(err));
    },
  });

  useEffect(() => {
    if (step !== "refresh-token") return;
    const needsRefresh = !hasAnySecret(GCLOUD_REFRESH_TOKEN_KEYS, existingSecrets);
    if (needsRefresh) return;
    if (autoRefreshSaveRef.current) return;
    autoRefreshSaveRef.current = true;
    queueMicrotask(() => {
      setStep("saving");
      saveMutation.mutate();
    });
  }, [step, existingSecrets, saveMutation]);

  const card: CSSProperties = {
    maxWidth: 520,
    margin: "4rem auto",
    padding: "2rem",
    background: "var(--color-background-primary)",
    border: "0.5px solid var(--color-border-tertiary)",
    borderRadius: 14,
  };
  const label: CSSProperties = {
    display: "block",
    fontSize: 13,
    color: "var(--color-text-secondary)",
    marginBottom: 5,
  };
  const input: CSSProperties = { width: "100%", marginBottom: 14 };
  const hint: CSSProperties = {
    fontSize: 12,
    color: "var(--color-text-tertiary)",
    marginTop: -10,
    marginBottom: 14,
    lineHeight: 1.5,
  };
  const row: CSSProperties = { display: "flex", gap: 8, marginTop: 8 };

  if (checking || step === "check") {
    return (
      <div style={card}>
        <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>Checking setup…</h2>
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

  if (step === "token-info") {
    return (
      <div style={card}>
        <StepIndicator current={1} total={3} />
        <h2 style={{ fontSize: 18, fontWeight: 500, margin: "1rem 0 0.5rem" }}>Token permissions</h2>
        <p
          style={{
            fontSize: 14,
            color: "var(--color-text-secondary)",
            marginBottom: "1.25rem",
          }}
        >
          The token you entered needs one additional permission to save secrets. If you used a
          fine-grained token, edit it on GitHub and add:
        </p>
        <ul
          style={{
            fontSize: 14,
            paddingLeft: "1.25rem",
            lineHeight: 2,
            marginBottom: "1.25rem",
          }}
        >
          <li>
            <code>Actions</code> → Read and write
          </li>
          <li>
            <code>Contents</code> → Read and write
          </li>
          <li>
            <strong>
              <code>Secrets</code> → Read and write
            </strong>{" "}
            ← required for setup
          </li>
        </ul>
        <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", marginBottom: "1.25rem" }}>
          For a classic token, <code>repo</code> scope covers everything. The token is stored only
          in your browser&apos;s localStorage and is only ever sent directly to GitHub&apos;s API.
        </p>
        <div style={row}>
          <button
            type="button"
            onClick={() => setStep("google-creds")}
            style={{
              flex: 1,
              background: "#185FA5",
              color: "white",
              border: "none",
              borderRadius: 8,
              padding: "9px 0",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            My token has these permissions →
          </button>
        </div>
      </div>
    );
  }

  if (step === "google-creds") {
    const needsClientId = !hasAnySecret(GCLOUD_CLIENT_ID_KEYS, existingSecrets);
    const needsClientSecret = !hasAnySecret(GCLOUD_CLIENT_SECRET_KEYS, existingSecrets);
    return (
      <div style={card}>
        <StepIndicator current={2} total={3} />
        <h2 style={{ fontSize: 18, fontWeight: 500, margin: "1rem 0 0.5rem" }}>Google OAuth credentials</h2>
        <p
          style={{
            fontSize: 14,
            color: "var(--color-text-secondary)",
            marginBottom: "1.25rem",
          }}
        >
          These come from a Google Cloud project with the YouTube Data API v3 enabled. See{" "}
          <a
            href="https://github.com/jreakin/jre-vidget/blob/main/docs/SETUP.md#step-2"
            target="_blank"
            rel="noreferrer"
            style={{ color: "#185FA5" }}
          >
            docs/SETUP.md — step 2
          </a>{" "}
          for how to create them.
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
              From Google Cloud Console → APIs &amp; Services → Credentials → OAuth 2.0 Client IDs.
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
          <button type="button" onClick={() => setStep("token-info")} style={{ flex: "0 0 auto" }}>
            ← Back
          </button>
          <button
            type="button"
            onClick={() => setStep("refresh-token")}
            disabled={
              (needsClientId && !clientId.trim()) || (needsClientSecret && !clientSecret.trim())
            }
            style={{
              flex: 1,
              background: "#185FA5",
              color: "white",
              border: "none",
              borderRadius: 8,
              padding: "9px 0",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Next →
          </button>
        </div>
      </div>
    );
  }

  if (step === "refresh-token") {
    const needsRefresh = !hasAnySecret(GCLOUD_REFRESH_TOKEN_KEYS, existingSecrets);
    if (!needsRefresh) {
      return (
        <div style={card}>
          <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>Saving secrets…</h2>
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
    return (
      <div style={card}>
        <StepIndicator current={3} total={3} />
        <h2 style={{ fontSize: 18, fontWeight: 500, margin: "1rem 0 0.5rem" }}>YouTube refresh token</h2>
        <p
          style={{
            fontSize: 14,
            color: "var(--color-text-secondary)",
            marginBottom: "1.25rem",
          }}
        >
          This authorises vidget to upload to your YouTube channel. You generate it once by running
          the auth flow locally with the credentials from the previous step.
        </p>

        <div
          style={{
            background: "var(--color-background-secondary)",
            border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 8,
            padding: "1rem",
            marginBottom: "1.25rem",
            fontFamily: "monospace",
            fontSize: 13,
          }}
        >
          <div style={{ color: "var(--color-text-tertiary)", marginBottom: 6 }}>
            # Run this once on your machine:
          </div>
          <div>
            GCLOUD_CLIENT_ID=<span style={{ color: "#185FA5" }}>&lt;your-client-id&gt;</span> \
          </div>
          <div>
            &nbsp;&nbsp;VIDGET_CLIENT_SECRET=<span style={{ color: "#185FA5" }}>
              &lt;your-client-secret&gt;
            </span>{" "}
            \
          </div>
          <div>&nbsp;&nbsp;vidget auth login</div>
          <div style={{ marginTop: 8 }}># Then copy the refresh_token from:</div>
          <div style={{ color: "#3B6D11" }}>~/.vidget/config.json</div>
        </div>

        <p style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginBottom: "1.25rem" }}>
          See{" "}
          <a
            href="https://github.com/jreakin/jre-vidget/blob/main/docs/SETUP.md#step-3"
            target="_blank"
            rel="noreferrer"
            style={{ color: "#185FA5" }}
          >
            docs/SETUP.md — step 3
          </a>{" "}
          for the full walkthrough. The refresh token never expires unless you revoke it in your
          Google account.
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
          <button type="button" onClick={() => setStep("google-creds")} style={{ flex: "0 0 auto" }}>
            ← Back
          </button>
          <button
            type="button"
            onClick={() => {
              setStep("saving");
              saveMutation.mutate();
            }}
            disabled={!refreshToken.trim() || saveMutation.isPending}
            style={{
              flex: 1,
              background: "#185FA5",
              color: "white",
              border: "none",
              borderRadius: 8,
              padding: "9px 0",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            {saveMutation.isPending ? "Saving secrets…" : "Save & finish"}
          </button>
        </div>
      </div>
    );
  }

  if (step === "saving") {
    return (
      <div style={card}>
        <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>Saving secrets…</h2>
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

  return (
    <div style={card}>
      <div style={{ fontSize: 40, marginBottom: "0.75rem" }}>✅</div>
      <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.5rem" }}>Setup complete</h2>
      <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1.5rem" }}>
        Your credentials are saved as GitHub Secrets. They&apos;re encrypted and only accessible by
        GitHub Actions workflows in your repo.
      </p>
      <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", marginBottom: "1.5rem" }}>
        You won&apos;t see this wizard again. If you ever need to update credentials, go to{" "}
        <strong>Settings → Secrets → Actions</strong> in your GitHub repo.
      </p>
      <button
        type="button"
        onClick={onComplete}
        style={{
          width: "100%",
          background: "#185FA5",
          color: "white",
          border: "none",
          borderRadius: 8,
          padding: "10px 0",
          fontSize: 14,
          fontWeight: 500,
          cursor: "pointer",
        }}
      >
        Open vidget →
      </button>
    </div>
  );
}

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
      <span
        style={{
          fontSize: 12,
          color: "var(--color-text-tertiary)",
          marginLeft: 4,
          whiteSpace: "nowrap",
        }}
      >
        {current}/{total}
      </span>
    </div>
  );
}
