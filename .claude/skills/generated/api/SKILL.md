---
name: api
description: "Skill for the Api area of jre-vidget. 16 symbols across 7 files."
---

# Api

16 symbols | 7 files | Cohesion: 100%

## When to Use

- Working with code in `web/`
- Understanding how encryptSecret, HomePage, usePAT work
- Modifying api-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `web/src/api/github.ts` | requireRepo, headers, dispatchPublish, fetchLatestRun, fetchUploads (+3) |
| `web/src/hooks/usePAT.ts` | usePAT, clearPAT |
| `web/src/components/StatusCard.tsx` | isActiveStatus, StatusCard |
| `web/src/lib/sodium.ts` | encryptSecret |
| `web/src/pages/HomePage.tsx` | HomePage |
| `web/src/components/UploadForm.tsx` | UploadForm |
| `web/src/components/SetupWizard.tsx` | SetupWizard |

## Entry Points

Start here when exploring this area:

- **`encryptSecret`** (Function) — `web/src/lib/sodium.ts:10`
- **`HomePage`** (Function) — `web/src/pages/HomePage.tsx:15`
- **`usePAT`** (Function) — `web/src/hooks/usePAT.ts:4`
- **`clearPAT`** (Function) — `web/src/hooks/usePAT.ts:14`
- **`UploadForm`** (Function) — `web/src/components/UploadForm.tsx:10`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `encryptSecret` | Function | `web/src/lib/sodium.ts` | 10 |
| `HomePage` | Function | `web/src/pages/HomePage.tsx` | 15 |
| `usePAT` | Function | `web/src/hooks/usePAT.ts` | 4 |
| `clearPAT` | Function | `web/src/hooks/usePAT.ts` | 14 |
| `UploadForm` | Function | `web/src/components/UploadForm.tsx` | 10 |
| `dispatchPublish` | Function | `web/src/api/github.ts` | 24 |
| `fetchLatestRun` | Function | `web/src/api/github.ts` | 46 |
| `fetchUploads` | Function | `web/src/api/github.ts` | 59 |
| `listSecretNames` | Function | `web/src/api/github.ts` | 69 |
| `getRepoPublicKey` | Function | `web/src/api/github.ts` | 82 |
| `setSecret` | Function | `web/src/api/github.ts` | 98 |
| `StatusCard` | Function | `web/src/components/StatusCard.tsx` | 14 |
| `SetupWizard` | Function | `web/src/components/SetupWizard.tsx` | 19 |
| `requireRepo` | Function | `web/src/api/github.ts` | 6 |
| `headers` | Function | `web/src/api/github.ts` | 15 |
| `isActiveStatus` | Function | `web/src/components/StatusCard.tsx` | 10 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `SetupWizard → RequireRepo` | intra_community | 4 |
| `SetupWizard → Headers` | intra_community | 4 |
| `HomePage → RequireRepo` | intra_community | 3 |
| `HomePage → Headers` | intra_community | 3 |
| `StatusCard → RequireRepo` | intra_community | 3 |
| `StatusCard → Headers` | intra_community | 3 |
| `SetupWizard → EncryptSecret` | intra_community | 3 |
| `UploadForm → RequireRepo` | intra_community | 3 |
| `UploadForm → Headers` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "encryptSecret"})` — see callers and callees
2. `gitnexus_query({query: "api"})` — find related execution flows
3. Read key files listed above for implementation details
