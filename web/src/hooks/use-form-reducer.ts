/**
 * useFormReducer — form state + optional Zod validation for 5–8 field forms.
 *
 * @example
 * const { fields, errors, setField, validate, reset } = useFormReducer(
 *   { title: '', privacy: 'private', tags: '' },
 *   publishSchema,          // optional ZodSchema
 * )
 */
import { useCallback, useReducer } from 'react'
import type { ZodSchema } from 'zod'

type Fields = Record<string, string>
type Errors<T extends Fields> = Partial<Record<keyof T, string>>

interface FormState<T extends Fields> {
  fields: T
  errors: Errors<T>
  isDirty: boolean
  isValid: boolean
}

type FormAction<T extends Fields> =
  | { type: 'SET_FIELD'; key: keyof T; value: string }
  | { type: 'SET_ERRORS'; errors: Errors<T> }
  | { type: 'RESET'; initial: T }

function formReducer<T extends Fields>(
  state: FormState<T>,
  action: FormAction<T>,
): FormState<T> {
  switch (action.type) {
    case 'SET_FIELD':
      return {
        ...state,
        fields: { ...state.fields, [action.key]: action.value },
        isDirty: true,
      }
    case 'SET_ERRORS':
      return { ...state, errors: action.errors, isValid: Object.keys(action.errors).length === 0 }
    case 'RESET':
      return { fields: action.initial, errors: {}, isDirty: false, isValid: false }
    default:
      return state
  }
}

export function useFormReducer<T extends Fields>(
  initialFields: T,
  schema?: ZodSchema<Partial<T>>,
) {
  const [state, dispatch] = useReducer(formReducer<T>, {
    fields: initialFields,
    errors: {},
    isDirty: false,
    isValid: false,
  })

  const setField = useCallback((key: keyof T, value: string) => {
    dispatch({ type: 'SET_FIELD', key, value })
  }, [])

  const validate = useCallback((): boolean => {
    if (!schema) return true
    const result = schema.safeParse(state.fields)
    if (result.success) {
      dispatch({ type: 'SET_ERRORS', errors: {} })
      return true
    }
    const errors: Errors<T> = {}
    for (const issue of result.error.issues) {
      const key = issue.path[0] as keyof T
      if (key) errors[key] = issue.message
    }
    dispatch({ type: 'SET_ERRORS', errors })
    return false
  }, [schema, state.fields])

  const reset = useCallback(() => {
    dispatch({ type: 'RESET', initial: initialFields })
  }, [initialFields])

  return { ...state, setField, validate, reset }
}
