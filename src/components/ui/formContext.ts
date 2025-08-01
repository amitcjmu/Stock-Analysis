/**
 * Form Context
 * 
 * Context providers for form components.
 * Separated from component file to maintain react-refresh compatibility.
 */

import * as React from "react"
import type { FieldValues, FieldPath } from "react-hook-form"

export interface FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> {
  name: TName
}

export const FormFieldContext = React.createContext<FormFieldContextValue>(
  {} as FormFieldContextValue
)

export interface FormItemContextValue {
  id: string
}

export const FormItemContext = React.createContext<FormItemContextValue>(
  {} as FormItemContextValue
)