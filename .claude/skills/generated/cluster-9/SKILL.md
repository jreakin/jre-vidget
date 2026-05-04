---
name: cluster-9
description: "Skill for the Cluster_9 area of jre-vidget. 3 symbols across 1 files."
---

# Cluster_9

3 symbols | 1 files | Cohesion: 100%

## When to Use

- Working with code in `worker/`
- Understanding how corsHeaders, json, error work
- Modifying cluster_9-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `worker/src/index.ts` | corsHeaders, json, error |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `corsHeaders` | Function | `worker/src/index.ts` | 119 |
| `json` | Function | `worker/src/index.ts` | 128 |
| `error` | Function | `worker/src/index.ts` | 138 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Error → CorsHeaders` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "corsHeaders"})` — see callers and callees
2. `gitnexus_query({query: "cluster_9"})` — find related execution flows
3. Read key files listed above for implementation details
