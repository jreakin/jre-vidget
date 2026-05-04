# Phase 13 — Error Reporting to Upstream Repo
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

When the publish workflow fails on a cloner's fork, automatically open an issue in
the upstream `jre-vidget` repo so the maintainer can triage and fix it — with zero
effort from the cloner. For web UI errors, show a pre-filled "Report this bug" link
instead (browser errors are often config issues; users should review before submitting).

The reporting token has *only* `issues: write` on the upstream repo — no other
permissions. Worst case is a spam issue; there is no credential or data exposure risk.

---

## Prerequisites

- Phase 11 complete (`.github/workflows/publish.yml` exists)
- Phase 12 complete (web UI exists)
- A GitHub fine-grained token with `issues: write` on `jreakin/jre-vidget` created
  and stored as `VIDGET_REPORT_TOKEN` secret in the cloner's repo

---

## Files

| Action | File |
|--------|------|
| Modify | `.github/workflows/publish.yml` |
| Create | `.github/ISSUE_TEMPLATE/bug_report_auto.yml` |
| Create | `.github/ISSUE_TEMPLATE/bug_report_manual.yml` |
| Modify | `web/src/App.tsx` |
| Create | `web/src/components/ErrorBoundary.tsx` |
| Modify | `docs/SETUP.md` |

---

## Implementation

### Step 1 — Create issue templates

`.github/ISSUE_TEMPLATE/bug_report_auto.yml`:

```yaml
name: Automated error report
description: Filed automatically by the publish workflow when a job fails.
labels: ["bug", "reported-by-clone"]
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        This issue was filed automatically. A cloner's publish workflow failed.
        No credentials or personal information are included.
  - type: input
    id: workflow_run
    attributes:
      label: Workflow run URL
      placeholder: "https://github.com/..."
    validations:
      required: true
  - type: textarea
    id: error_output
    attributes:
      label: Error output
      render: shell
    validations:
      required: true
  - type: input
    id: runner_os
    attributes:
      label: Runner OS
  - type: input
    id: vidget_version
    attributes:
      label: vidget version
```

`.github/ISSUE_TEMPLATE/bug_report_manual.yml`:

```yaml
name: Bug report
description: File a bug report.
labels: ["bug"]
body:
  - type: textarea
    id: description
    attributes:
      label: What happened?
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
    validations:
      required: true
  - type: input
    id: vidget_version
    attributes:
      label: vidget version
```

---

### Step 2 — Add failure reporting step to `publish.yml`

Add this as the **last step** in the `publish` job, after the commit step.
It only runs when any earlier step has failed:

```yaml
      - name: Report failure to upstream
        if: failure() && env.VIDGET_REPORT_TOKEN != ''
        env:
          VIDGET_REPORT_TOKEN: ${{ secrets.VIDGET_REPORT_TOKEN }}
          GH_TOKEN: ${{ secrets.VIDGET_REPORT_TOKEN }}
        run: |
          VIDGET_VERSION=$(uv run vidget --version 2>/dev/null || echo "unknown")
          RUN_URL="${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"

          BODY="## Automated error report

          **Workflow run:** ${RUN_URL}
          **Input URL:** \`${{ inputs.url }}\`
          **Step that failed:** check the run logs above
          **Runner OS:** ${{ runner.os }}
          **vidget version:** ${VIDGET_VERSION}

          ---
          *Filed automatically from a cloned instance of jre-vidget.*
          *No credentials or personal information are included.*"

          gh issue create \
            --repo jreakin/jre-vidget \
            --title "Publish workflow failure (run #${{ github.run_number }})" \
            --body "$BODY" \
            --label "bug,reported-by-clone" \
          || echo "Warning: could not create upstream issue (token may be missing or expired)"
```

The trailing `|| echo` ensures a token failure does not itself fail the workflow step.

---

### Step 3 — Create ErrorBoundary for the web UI

`web/src/components/ErrorBoundary.tsx`:

```tsx
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  repo: string;  // e.g. "jreakin/jre-vidget"
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  private buildIssueUrl(): string {
    const { error } = this.state;
    if (!error) return "#";

    const title = encodeURIComponent(`Web UI error: ${error.message.slice(0, 80)}`);
    const body = encodeURIComponent(
      `## Web UI error report\n\n` +
      `**Error:** \`${error.message}\`\n\n` +
      `**Stack:**\n\`\`\`\n${error.stack ?? "none"}\n\`\`\`\n\n` +
      `**Page:** ${window.location.href}\n\n` +
      `**User agent:** ${navigator.userAgent}\n\n` +
      `---\n*Please review and remove any personal info before submitting.*`
    );
    const labels = encodeURIComponent("bug,web-ui");
    return `https://github.com/${this.props.repo}/issues/new?title=${title}&body=${body}&labels=${labels}`;
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div style={{ maxWidth: 560, margin: "4rem auto", padding: "0 1rem" }}>
        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "1.5rem" }}>
          <div style={{ fontSize: 16, fontWeight: 500, marginBottom: "0.5rem", color: "var(--color-text-danger)" }}>
            Something went wrong
          </div>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "0.75rem" }}>
            The app encountered an unexpected error.
          </p>
          <pre style={{ fontSize: 12, fontFamily: "var(--font-mono)", background: "var(--color-background-secondary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 6, padding: "0.75rem", overflow: "auto", marginBottom: "1.25rem", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {error.message}
          </pre>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => this.setState({ error: null })}
              style={{ flex: 1 }}
            >
              Try again
            </button>
            <a
              href={this.buildIssueUrl()}
              target="_blank"
              rel="noreferrer"
              style={{ flex: 1, background: "#185FA5", color: "white", border: "none", borderRadius: 8, padding: "8px 0", fontSize: 14, fontWeight: 500, textAlign: "center", textDecoration: "none", display: "block" }}
            >
              Report this bug
            </a>
          </div>
          <p style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: "0.75rem" }}>
            Clicking "Report" opens a pre-filled GitHub issue. Review it before submitting — no personal info is included automatically.
          </p>
        </div>
      </div>
    );
  }
}
```

---

### Step 4 — Wrap App in ErrorBoundary

Update `web/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";

const REPO = import.meta.env.VITE_GITHUB_REPO ?? "jreakin/jre-vidget";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary repo={REPO}>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
```

---

### Step 5 — Update `docs/SETUP.md` with VIDGET_REPORT_TOKEN instructions

Add this section to `docs/SETUP.md` under the Secrets table:

```markdown
### Creating the VIDGET_REPORT_TOKEN

This token lets the publish workflow automatically report failures to the upstream
repo so the maintainer can fix them. It has the minimum possible permissions.

1. Go to **GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token**
2. Set:
   - **Token name:** `vidget-error-reporter`
   - **Expiration:** 1 year (or no expiration)
   - **Resource owner:** your account
   - **Repository access:** Only select repositories → `jreakin/jre-vidget`
   - **Permissions:** Repository permissions → Issues → **Read and write**
   - All other permissions: **No access**
3. Generate and copy the token
4. Add it as `VIDGET_REPORT_TOKEN` in your repo's secrets

If you prefer not to report errors automatically, skip this secret entirely.
The publish workflow prints a warning but does not fail if the token is absent.
```

---

### Step 6 — Rebuild and redeploy the web UI

```bash
cd web
npm run build
```

Push to `main` — the `deploy-web.yml` workflow will pick up the changes and redeploy.

---

### Step 7 — Commit

```bash
git add .github/workflows/publish.yml \
        .github/ISSUE_TEMPLATE/ \
        web/src/components/ErrorBoundary.tsx \
        web/src/main.tsx \
        docs/SETUP.md
git commit -m "feat: add automated error reporting to upstream repo"
```

---

## Acceptance Criteria

- [ ] `publish.yml` has an `if: failure()` step as its final step
- [ ] Failure step uses `VIDGET_REPORT_TOKEN` (not `GITHUB_TOKEN`) to create the issue
- [ ] Issue is created in `jreakin/jre-vidget`, not the cloner's repo
- [ ] Issue body contains run URL, input URL, runner OS, vidget version — no credentials
- [ ] Issue is labelled `bug` and `reported-by-clone`
- [ ] If `VIDGET_REPORT_TOKEN` is absent, the step prints a warning and exits 0 (does not block)
- [ ] `ErrorBoundary` wraps the entire React app
- [ ] On uncaught error, ErrorBoundary shows the error message + "Report this bug" button
- [ ] "Report this bug" opens a pre-filled GitHub issue URL — does not auto-submit
- [ ] Issue URL pre-fills title, body (error + stack + page URL), and labels
- [ ] `docs/SETUP.md` explains how to create the fine-grained token with minimum permissions
- [ ] `npm run build` passes with no TypeScript errors after changes
