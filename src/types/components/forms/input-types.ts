/**
 * Input Component Types
 * 
 * Types for text inputs, number inputs, textareas, and related input components.
 */

import { ReactNode, RefObject } from 'react';
import { BaseFormProps, MaskState } from './base-types';

// Text input types
export interface TextInputProps extends BaseFormProps {
  type?: 'text' | 'email' | 'password' | 'tel' | 'url' | 'search';
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  autoComplete?: string;
  autoFocus?: boolean;
  spellCheck?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  inputMode?: 'none' | 'text' | 'tel' | 'url' | 'email' | 'numeric' | 'decimal' | 'search';
  enterKeyHint?: 'enter' | 'done' | 'go' | 'next' | 'previous' | 'search' | 'send';
  onChange?: (value: string, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onInput?: (event: React.FormEvent<HTMLInputElement>) => void;
  onSelect?: (event: React.SyntheticEvent<HTMLInputElement>) => void;
  onPaste?: (event: React.ClipboardEvent<HTMLInputElement>) => void;
  onCut?: (event: React.ClipboardEvent<HTMLInputElement>) => void;
  onCopy?: (event: React.ClipboardEvent<HTMLInputElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyPress?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  prefix?: ReactNode;
  suffix?: ReactNode;
  addonBefore?: ReactNode;
  addonAfter?: ReactNode;
  clearable?: boolean;
  onClear?: () => void;
  showPasswordToggle?: boolean;
  allowRevealPassword?: boolean;
  showWordCount?: boolean;
  showCharacterCount?: boolean;
  debounce?: number;
  onDebounceChange?: (value: string) => void;
  mask?: string | ((value: string) => string);
  maskChar?: string;
  formatChars?: Record<string, string>;
  beforeMaskedValueChange?: (newState: MaskState, oldState: MaskState, userInput: string) => MaskState;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  prefixClassName?: string;
  suffixClassName?: string;
  addonBeforeClassName?: string;
  addonAfterClassName?: string;
}

// Number input types
export interface NumberInputProps extends BaseFormProps {
  value?: number;
  defaultValue?: number;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  precision?: number;
  decimalScale?: number;
  fixedDecimalScale?: boolean;
  allowNegative?: boolean;
  allowLeadingZeros?: boolean;
  thousandSeparator?: boolean | string;
  decimalSeparator?: string;
  prefix?: string;
  suffix?: string;
  format?: string | ((value: number) => string);
  parse?: (value: string) => number;
  onChange?: (value: number | undefined, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyPress?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  controls?: boolean;
  upIcon?: ReactNode;
  downIcon?: ReactNode;
  onStep?: (value: number, direction: 'up' | 'down') => void;
  keyboard?: boolean;
  stringMode?: boolean;
  changeOnWheel?: boolean;
  autoFocus?: boolean;
  bordered?: boolean;
  clearable?: boolean;
  onClear?: () => void;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  controlsClassName?: string;
  upButtonClassName?: string;
  downButtonClassName?: string;
}

// Textarea types
export interface TextareaProps extends BaseFormProps {
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  rows?: number;
  cols?: number;
  minRows?: number;
  maxRows?: number;
  autoSize?: boolean | { minRows?: number; maxRows?: number };
  resize?: 'none' | 'both' | 'horizontal' | 'vertical';
  wrap?: 'hard' | 'soft' | 'off';
  minLength?: number;
  maxLength?: number;
  spellCheck?: boolean;
  autoComplete?: string;
  autoFocus?: boolean;
  onChange?: (value: string, event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  onInput?: (event: React.FormEvent<HTMLTextAreaElement>) => void;
  onSelect?: (event: React.SyntheticEvent<HTMLTextAreaElement>) => void;
  onPaste?: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  onCut?: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  onCopy?: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onKeyPress?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onResize?: (size: { width: number; height: number }) => void;
  showWordCount?: boolean;
  showCharacterCount?: boolean;
  clearable?: boolean;
  onClear?: () => void;
  debounce?: number;
  onDebounceChange?: (value: string) => void;
  textareaRef?: RefObject<HTMLTextAreaElement>;
  containerRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  textareaClassName?: string;
  counterClassName?: string;
}

// Mask state interface (re-export from base)
export interface MaskState {
  value: string;
  selection: {
    start: number;
    end: number;
  };
  [key: string]: unknown;
}