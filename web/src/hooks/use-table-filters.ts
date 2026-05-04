/**
 * useTableFilters — filter, sort, and paginate any collection.
 *
 * @example
 * const { items, search, setSearch, page, setPage, totalPages } =
 *   useTableFilters(uploads, {
 *     searchFields: ['title', 'status'],
 *     pageSize: 20,
 *   })
 */
import { useMemo, useState } from 'react'

export type SortDirection = 'asc' | 'desc'

export interface TableFiltersOptions<T> {
  /** Object keys to include in text search */
  searchFields?: (keyof T)[]
  /** Initial page size (default: 25) */
  pageSize?: number
}

export function useTableFilters<T extends Record<string, unknown>>(
  items: T[],
  options: TableFiltersOptions<T> = {},
) {
  const { searchFields = [], pageSize: defaultPageSize = 25 } = options

  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<keyof T | null>(null)
  const [sortDir, setSortDir] = useState<SortDirection>('asc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPageSize)

  const filtered = useMemo(() => {
    let result = items
    if (search.trim() && searchFields.length > 0) {
      const q = search.toLowerCase()
      result = result.filter((item) =>
        searchFields.some((field) => String(item[field] ?? '').toLowerCase().includes(q)),
      )
    }
    if (sortKey !== null) {
      result = [...result].sort((a, b) => {
        const av = a[sortKey]
        const bv = b[sortKey]
        const cmp = String(av ?? '').localeCompare(String(bv ?? ''))
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return result
  }, [items, search, searchFields, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const safePage = Math.min(page, totalPages)

  const paginated = useMemo(
    () => filtered.slice((safePage - 1) * pageSize, safePage * pageSize),
    [filtered, safePage, pageSize],
  )

  const toggleSort = (key: keyof T) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
    setPage(1)
  }

  return {
    items: paginated,
    allFiltered: filtered,
    search,
    setSearch: (v: string) => { setSearch(v); setPage(1) },
    sortKey,
    sortDir,
    toggleSort,
    page: safePage,
    setPage,
    pageSize,
    setPageSize,
    totalPages,
    totalItems: filtered.length,
  }
}
