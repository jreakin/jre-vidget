/**
 * ErrorDisplay — visible error rendering component.
 *
 * Every caught error in the app MUST render this component.
 * Never silently log errors with console.error only.
 *
 * @example
 * {error && <ErrorDisplay message={error} onRetry={refetch} />}
 */
interface ErrorDisplayProps {
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorDisplay({ message, onRetry, className = '' }: ErrorDisplayProps) {
  return (
    <div
      role="alert"
      className={`rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800 ${className}`}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-red-500" aria-hidden="true">⚠</span>
        <div className="flex-1">
          <p className="font-medium">Something went wrong</p>
          <p className="mt-1 text-red-700">{message}</p>
        </div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded bg-red-100 px-3 py-1 text-xs font-medium text-red-800 hover:bg-red-200"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}
