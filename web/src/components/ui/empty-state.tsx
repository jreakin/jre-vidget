/**
 * EmptyState — placeholder for empty data states.
 *
 * @example
 * {uploads.length === 0 && (
 *   <EmptyState
 *     title="No uploads yet"
 *     description="Paste a YouTube URL above to get started."
 *     action={<button onClick={focusInput}>Add first upload</button>}
 *   />
 * )}
 */
import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 px-6 py-12 text-center ${className}`}
    >
      <div className="text-4xl text-gray-400" aria-hidden="true">📭</div>
      <h3 className="mt-4 text-sm font-semibold text-gray-900">{title}</h3>
      {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
