/**
 * useAsyncState — replaces the loading/error/data useState triplet.
 *
 * @example
 * const { data, loading, error, run } = useAsyncState(fetchVideoInfo)
 * // trigger:  run(url)
 * // read:     if (loading) …   if (error) …   data?.title
 */
import { useCallback, useState } from 'react'

export type AsyncState<T> =
  | { status: 'idle'; data: null; error: null; loading: false }
  | { status: 'loading'; data: null; error: null; loading: true }
  | { status: 'success'; data: T; error: null; loading: false }
  | { status: 'error'; data: null; error: Error; loading: false }

const idle = <T>(): AsyncState<T> => ({
  status: 'idle',
  data: null,
  error: null,
  loading: false,
})

export function useAsyncState<T, Args extends unknown[]>(
  fn: (...args: Args) => Promise<T>,
): AsyncState<T> & { run: (...args: Args) => Promise<void>; reset: () => void } {
  const [state, setState] = useState<AsyncState<T>>(idle<T>())

  const run = useCallback(
    async (...args: Args) => {
      setState({ status: 'loading', data: null, error: null, loading: true })
      try {
        const data = await fn(...args)
        setState({ status: 'success', data, error: null, loading: false })
      } catch (err) {
        setState({
          status: 'error',
          data: null,
          error: err instanceof Error ? err : new Error(String(err)),
          loading: false,
        })
      }
    },
    [fn],
  )

  const reset = useCallback(() => setState(idle<T>()), [])

  return { ...state, run, reset }
}
