# Phase 14 — Bootstrap Workflow (Repo Setup)
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

When someone clones this repo, they need four secrets and two variables configured
before anything works. Without this workflow they have to hunt through the README to
find the full list. This workflow creates placeholder secrets (`REPLACE_ME`) for any
that are missing, sets sensible defaults for non-sensitive variables, and writes a
step-by-step checklist to the Actions job summary — so cloners see a clear TODO list
the moment they look at their repo.

Cloners run this once, manually, immediately after cloning.

---

## Files

| Action | File |
|--------|------|
| Create | `.github/workflows/bootstrap.yml` |

---

## Implementation

### Step 1 — Create `.github/workflows/bootstrap.yml`

```yaml
name: Bootstrap — set up repo secrets and variables

on:
  workflow_dispatch:
    inputs:
      app_title:
        description: "Web UI title (shown in the top bar)"
        required: false
        default: "My vidget uploader"
        type: string
      force:
        description: "Overwrite existing placeholder values"
        required: false
        default: false
        type: boolean

jobs:
  bootstrap:
    runs-on: ubuntu-latest
    permissions:
      actions: write   # required for gh variable set
      secrets: write   # required for gh secret set

    steps:
      - uses: actions/checkout@v4

      - name: Configure secrets
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          FORCE: ${{ inputs.force }}
        run: |
          set_secret_if_missing() {
            local name="$1"
            local placeholder="$2"

            # gh secret list exits 0 and lists names; grep for exact match
            if gh secret list --repo "$GITHUB_REPOSITORY" | grep -qw "^${name}"; then
              if [ "$FORCE" = "true" ]; then
                echo "REPLACE_ME — ${placeholder}" | gh secret set "$name" --repo "$GITHUB_REPOSITORY"
                echo "overwritten:  $name"
              else
                echo "already set:  $name  (skipped)"
              fi
            else
              echo "REPLACE_ME — ${placeholder}" | gh secret set "$name" --repo "$GITHUB_REPOSITORY"
              echo "created:      $name"
            fi
          }

          set_secret_if_missing "VIDGET_CLIENT_ID" \
            "Google OAuth Client ID — see docs/SETUP.md"

          set_secret_if_missing "VIDGET_CLIENT_SECRET" \
            "Google OAuth Client Secret — see docs/SETUP.md"

          set_secret_if_missing "VIDGET_REFRESH_TOKEN" \
            "Run vidget auth login locally then copy from ~/.vidget/config.json"

          set_secret_if_missing "VIDGET_REPORT_TOKEN" \
            "Fine-grained GitHub token with issues:write on jreakin/jre-vidget — see docs/SETUP.md"

      - name: Configure variables
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set_variable() {
            local name="$1"
            local value="$2"
            gh variable set "$name" --body "$value" --repo "$GITHUB_REPOSITORY"
            echo "set variable: $name = $value"
          }

          # VITE_GITHUB_REPO: auto-detect from the current repo
          set_variable "VITE_GITHUB_REPO" "$GITHUB_REPOSITORY"

          # VITE_APP_TITLE: use the workflow input, falling back to a default
          TITLE="${{ inputs.app_title }}"
          set_variable "VITE_APP_TITLE" "${TITLE:-My vidget uploader}"

      - name: Check secret status
        id: check
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Record which secrets are still placeholders vs. real values.
          # We can list secret names but not values — warn on any that equal
          # the placeholder pattern by checking length via the API response size.
          # Strategy: list all secret names, mark as configured vs. needs action.
          CONFIGURED=()
          NEEDS_ACTION=()

          for name in VIDGET_CLIENT_ID VIDGET_CLIENT_SECRET VIDGET_REFRESH_TOKEN VIDGET_REPORT_TOKEN; do
            if gh secret list --repo "$GITHUB_REPOSITORY" | grep -qw "^${name}"; then
              CONFIGURED+=("$name")
            else
              NEEDS_ACTION+=("$name")
            fi
          done

          echo "configured=${CONFIGURED[*]}" >> "$GITHUB_OUTPUT"
          echo "needs_action=${NEEDS_ACTION[*]}" >> "$GITHUB_OUTPUT"

      - name: Write job summary
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          REPO_URL="https://github.com/$GITHUB_REPOSITORY"
          SECRETS_URL="${REPO_URL}/settings/secrets/actions"
          VARS_URL="${REPO_URL}/settings/variables/actions"
          PAGES_URL="${REPO_URL}/settings/pages"
          SETUP_URL="${REPO_URL}/blob/main/docs/SETUP.md"

          cat >> "$GITHUB_STEP_SUMMARY" << EOF
          # vidget setup checklist

          Run this workflow again after filling in each secret.

          ## Secrets — go to [Settings → Secrets]($SECRETS_URL)

          | Secret | Status | Instructions |
          |--------|--------|--------------|
          | \`VIDGET_CLIENT_ID\` | ⚠️ replace placeholder | [docs/SETUP.md]($SETUP_URL) — step 2 |
          | \`VIDGET_CLIENT_SECRET\` | ⚠️ replace placeholder | [docs/SETUP.md]($SETUP_URL) — step 2 |
          | \`VIDGET_REFRESH_TOKEN\` | ⚠️ replace placeholder | Run \`vidget auth login\` locally — [docs/SETUP.md]($SETUP_URL) — step 3 |
          | \`VIDGET_REPORT_TOKEN\` | ℹ️ optional | Fine-grained token to auto-report errors upstream |

          ## Variables — go to [Settings → Variables]($VARS_URL)

          | Variable | Value set | Notes |
          |----------|-----------|-------|
          | \`VITE_GITHUB_REPO\` | \`$GITHUB_REPOSITORY\` | Auto-detected ✓ |
          | \`VITE_APP_TITLE\` | \`${{ inputs.app_title }}\` | Change to your preferred title |

          ## One-time repo settings

          - [ ] Enable GitHub Pages: [Settings → Pages]($PAGES_URL) → Source: **Deploy from a branch** → Branch: **gh-pages** / **/ (root)**
          - [ ] After filling secrets, run the **Deploy web UI** workflow to publish the page
          - [ ] Trigger a test upload from the **Download & publish** workflow to verify credentials

          ## Quick links

          - [Full setup guide]($SETUP_URL)
          - [Actions tab]($REPO_URL/actions)
          - [Your web UI](https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}/)

          EOF

          echo "Summary written to job summary."
```

---

### Step 2 — Verify locally (optional)

You cannot run this workflow locally, but you can validate the YAML syntax:

```bash
# Install actionlint if available
brew install actionlint
actionlint .github/workflows/bootstrap.yml
```

Expected: no errors.

---

### Step 3 — Commit

```bash
git add .github/workflows/bootstrap.yml
git commit -m "feat: add bootstrap workflow to scaffold repo secrets and variables"
```

---

### Step 4 — Update README with cloner instructions

Add the following to the top of `README.md` under a "Getting started" section:

```markdown
## Getting started (clone & configure)

1. **Fork or clone** this repo
2. Go to **Actions** → **Bootstrap — set up repo secrets and variables** → **Run workflow**
3. Follow the checklist in the job summary to fill in your secrets
4. Enable **GitHub Pages** (Settings → Pages → gh-pages branch)
5. Done — your web UI is live at `https://YOUR_USERNAME.github.io/jre-vidget/`

See [docs/SETUP.md](docs/SETUP.md) for detailed instructions on obtaining each credential.
```

---

### Step 5 — Commit README

```bash
git add README.md
git commit -m "docs: add getting started section for cloners"
```

---

## How it works for a cloner

1. They fork/clone the repo
2. Go to Actions → "Bootstrap" → click **Run workflow**
3. Optionally type their preferred app title in the input field
4. The workflow:
   - Creates `REPLACE_ME` placeholder secrets for all 4 required secrets
   - Sets `VITE_GITHUB_REPO` to their repo name automatically
   - Sets `VITE_APP_TITLE` from the input (or the default)
   - Writes a job summary with a checklist table
5. They click through to Settings → Secrets, replace each placeholder
6. Run bootstrap again with `force: true` if they need to reset

---

## Acceptance Criteria

- [ ] `bootstrap.yml` triggers on `workflow_dispatch` with `app_title` and `force` inputs
- [ ] Missing secrets are created with `REPLACE_ME — <description>` placeholder values
- [ ] Existing secrets are skipped unless `force: true` is passed
- [ ] `VITE_GITHUB_REPO` is set to `github.repository` automatically (no user input needed)
- [ ] `VITE_APP_TITLE` is set from the `app_title` input, defaulting to `"My vidget uploader"`
- [ ] Job summary renders a checklist table with links to Settings, the setup guide, and the live web UI URL
- [ ] `VIDGET_REPORT_TOKEN` is listed as optional in the summary
- [ ] `actionlint` passes on the workflow file
- [ ] README has a "Getting started" section linking to the bootstrap workflow
