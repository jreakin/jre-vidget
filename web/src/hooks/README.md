# Shared Hooks

Check here before creating a new state pattern. If what you need is here, use it.

| Hook | Purpose | Import |
|------|---------|--------|
| `useAsyncState` | Loading / error / data triplet for any async call | `@/hooks/use-async-state` |
| `useFormReducer` | Form state + optional Zod validation (5–8 fields) | `@/hooks/use-form-reducer` |
| `useTableFilters` | Filter, sort, and paginate any collection | `@/hooks/use-table-filters` |
| `useModal` | Open / close / payload for any modal dialog | `@/hooks/use-modal` |
| `usePAT` | GitHub Personal Access Token storage and retrieval | `@/hooks/usePAT` |

## Rules

- **Before creating a new hook** — check this table first.
- **After adding a hook** — add a row to this table immediately.
- **After removing a hook** — remove the row and search for usages.
- **Naming** — `use-kebab-case.ts` (canonical hooks), `useCamelCase.ts` (project-specific legacy).
