/**
 * useModal — open/close/data pattern for any modal dialog.
 *
 * @example
 * const editModal = useModal<UploadRecord>()
 * // open:   editModal.open(record)
 * // read:   editModal.isOpen, editModal.data
 * // close:  editModal.close()
 */
import { useCallback, useState } from 'react'

export interface ModalState<T> {
  isOpen: boolean
  data: T | null
  open: (data?: T) => void
  close: () => void
  toggle: () => void
}

export function useModal<T = undefined>(): ModalState<T> {
  const [isOpen, setIsOpen] = useState(false)
  const [data, setData] = useState<T | null>(null)

  const open = useCallback((payload?: T) => {
    setData(payload ?? null)
    setIsOpen(true)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
    // keep data until next open so close animations don't flash empty content
  }, [])

  const toggle = useCallback(() => setIsOpen((v) => !v), [])

  return { isOpen, data, open, close, toggle }
}
