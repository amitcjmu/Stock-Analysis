/**
 * Input Component Types
 * 
 * Input and form control component interfaces.
 */

import { ReactNode, RefObject } from 'react';
import { InteractiveComponentProps } from './base-props';

// Input component types
export interface InputProps extends InteractiveComponentProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search' | 'date' | 'time' | 'datetime-local' | 'month' | 'week';
  name?: string;
  value?: string | number;
  defaultValue?: string | number;
  placeholder?: string;
  autoComplete?: string;
  autoFocus?: boolean;
  readOnly?: boolean;
  spellCheck?: boolean;
  min?: number | string;
  max?: number | string;
  step?: number | string;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  inputMode?: 'none' | 'text' | 'tel' | 'url' | 'email' | 'numeric' | 'decimal' | 'search';
  enterKeyHint?: 'enter' | 'done' | 'go' | 'next' | 'previous' | 'search' | 'send';
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onInput?: (event: React.FormEvent<HTMLInputElement>) => void;
  onSelect?: (event: React.SyntheticEvent<HTMLInputElement>) => void;
  onPaste?: (event: React.ClipboardEvent<HTMLInputElement>) => void;
  onCut?: (event: React.ClipboardEvent<HTMLInputElement>) => void;
  onCopy?: (event: React.ClipboardEvent<HTMLInputElement>) => void;
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
  beforeMaskedValueChange?: (newState: any, oldState: any, userInput: string) => any;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  prefixClassName?: string;
  suffixClassName?: string;
  addonBeforeClassName?: string;
  addonAfterClassName?: string;
}