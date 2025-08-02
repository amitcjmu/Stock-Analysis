/**
 * Form Hooks
 *
 * Custom hooks for form components.
 * Separated from component file to maintain react-refresh compatibility.
 */

import * as React from "react"
import { useFormContext } from "react-hook-form"
import type { FieldError } from "react-hook-form"

import { FormFieldContext, FormItemContext } from "./formContext"

export const useFormField = (): {
  id: string;
  name: string;
  formItemId: string;
  formDescriptionId: string;
  formMessageId: string;
  invalid: boolean;
  isDirty: boolean;
  isTouched: boolean;
  error?: FieldError;
} => {
  const fieldContext = React.useContext(FormFieldContext)
  const itemContext = React.useContext(FormItemContext)
  const { getFieldState, formState } = useFormContext()

  const fieldState = getFieldState(fieldContext.name, formState)

  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>")
  }

  const { id } = itemContext

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  }
}
