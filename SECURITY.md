# Security policy

This document describes how we handle security issues for **jre-vidget** and how it fits together with GitHub **Dependabot** and **CodeQL**.

## Supported versions

We ship security fixes only for the **latest minor release** on the default branch (`main`) and the most recent **GitHub release** tag.

| Range        | Supported |
| ------------ | --------- |
| Latest `0.x` release / `main` | Yes       |
| Older tags   | Best effort — upgrade to the latest release |

## Reporting a vulnerability

**Please do not open a public issue** for undisclosed security problems (that includes avoiding details in issue titles or PR descriptions).

1. **Preferred:** use GitHub [**Private vulnerability reporting**](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) for this repository (**Security** tab → **Report a vulnerability**). Maintainers can triage, request CVE assignment, and coordinate disclosure from there.
2. **Alternative:** email **johnreakin@gmail.com** with subject line `[SECURITY] jre-vidget` and enough detail to reproduce or assess impact (version or commit, component, steps, impact).

### What helps us respond quickly

- Affected component (CLI, GitHub Actions workflow, `web/` UI, `worker/`, etc.)
- Minimal reproduction or proof-of-concept where safe to share
- Whether secrets, tokens, or user data are involved

### Our commitment

- We aim to acknowledge reports within **several business days** and will work toward a fix and advisory where appropriate.
- We follow **coordinated disclosure**: we do not publish exploit details until a fix is available (or an agreed timeline).

## Automated security tooling (this repository)

| Tool | Role |
| ---- | ---- |
| **Dependabot** | Weekly dependency updates for **pip** (`/`), **npm** (`/web`), and **GitHub Actions** (`/`). Review and merge Dependabot PRs promptly; they often carry security patches. |
| **CodeQL** | Enable **Code scanning** with GitHub’s [**Default setup**](https://docs.github.com/en/code-security/code-scanning/enabling-code-scanning/configuring-default-setup-for-code-scanning) (recommended). It analyzes **Python** and **JavaScript/TypeScript** from this repo and shows results under **Security** → **Code scanning**. **Do not** turn on default setup *and* a separate “advanced” CodeQL Actions workflow that uploads SARIF — GitHub rejects the upload with *“CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled.”* If you need a custom workflow instead, disable default setup first, then add the workflow. |

Repository maintainers should keep **Code scanning** (default setup) and **Dependabot** enabled under **Settings → Code security and analysis**, and turn on **Private vulnerability reporting** under **Settings → Security** so the flow above works end-to-end.

## Out of scope

- Vulnerabilities in **upstream** projects only (e.g. yt-dlp, ffmpeg, Google APIs) — report those to the respective projects; we still welcome heads-up if a bump in our declared dependency range fixes a CVE.
- Misuse of **user-controlled** secrets (tokens in `localStorage`, fork secrets, PAT handling) where behavior matches documented risk in [docs/SETUP.md](docs/SETUP.md).
- **Denial of service** against GitHub Actions or third-party APIs without a practical impact on jre-vidget users.

Thank you for helping keep users and forks safe.
