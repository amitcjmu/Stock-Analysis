/**
 * Select Component Types
 * 
 * Types for select components, dropdowns, and select-related functionality.
 */

import type { ReactNode, RefObject } from 'react';
import type { BaseFormProps } from './base-types';

// Select-related interfaces
export interface SelectState {
  value: unknown;
  options: SelectOption[];
  inputValue: string;
  isOpen: boolean;
  [key: string]: unknown;
}

export interface SelectActionMeta {
  action: 'select-option' | 'deselect-option' | 'remove-value' | 'pop-value' | 'set-value' | 'clear' | 'create-option';
  option?: SelectOption;
  removedValue?: SelectOption;
  [key: string]: unknown;
}

export interface SelectLabelMeta {
  context: 'menu' | 'value';
  inputValue: string;
  selectValue: unknown;
  [key: string]: unknown;
}

export interface SelectTheme {
  borderRadius: number;
  colors: Record<string, string>;
  spacing: Record<string, number>;
  [key: string]: unknown;
}

// Select component types
export interface SelectOption {
  value: unknown;
  label: ReactNode;
  disabled?: boolean;
  hidden?: boolean;
  group?: string;
  icon?: ReactNode;
  description?: ReactNode;
  metadata?: Record<string, unknown>;
}

export interface SelectProps extends BaseFormProps {
  value?: unknown;
  defaultValue?: unknown;
  placeholder?: string;
  options?: SelectOption[];
  children?: ReactNode;
  multiple?: boolean;
  searchable?: boolean;
  creatable?: boolean;
  clearable?: boolean;
  loading?: boolean;
  loadingMessage?: ReactNode;
  noOptionsMessage?: ReactNode;
  emptyMessage?: ReactNode;
  maxMenuHeight?: number;
  maxMenuWidth?: number;
  menuPlacement?: 'auto' | 'bottom' | 'top';
  menuPosition?: 'absolute' | 'fixed';
  menuIsOpen?: boolean;
  defaultMenuIsOpen?: boolean;
  closeMenuOnSelect?: boolean;
  closeMenuOnScroll?: boolean;
  hideSelectedOptions?: boolean;
  escapeClearsValue?: boolean;
  isClearable?: boolean;
  isDisabled?: boolean;
  isLoading?: boolean;
  isMulti?: boolean;
  isRtl?: boolean;
  isSearchable?: boolean;
  backspaceRemovesValue?: boolean;
  blurInputOnSelect?: boolean;
  captureMenuScroll?: boolean;
  delimiter?: string;
  inputValue?: string;
  minMenuHeight?: number;
  openMenuOnClick?: boolean;
  openMenuOnFocus?: boolean;
  pageSize?: number;
  screenReaderStatus?: (state: SelectState) => string;
  tabIndex?: number;
  tabSelectsValue?: boolean;
  onChange?: (value: unknown, actionMeta?: SelectActionMeta) => void;
  onBlur?: (event: React.FocusEvent) => void;
  onFocus?: (event: React.FocusEvent) => void;
  onInputChange?: (inputValue: string, actionMeta: SelectActionMeta) => void;
  onKeyDown?: (event: React.KeyboardEvent) => void;
  onMenuOpen?: () => void;
  onMenuClose?: () => void;
  onMenuScrollToTop?: (event: React.SyntheticEvent) => void;
  onMenuScrollToBottom?: (event: React.SyntheticEvent) => void;
  onClear?: () => void;
  onCreate?: (inputValue: string) => void;
  formatOptionLabel?: (option: SelectOption, labelMeta: SelectLabelMeta) => ReactNode;
  formatGroupLabel?: (group: string) => ReactNode;
  formatCreateLabel?: (inputValue: string) => ReactNode;
  getOptionLabel?: (option: SelectOption) => string;
  getOptionValue?: (option: SelectOption) => unknown;
  getNewOptionData?: (inputValue: string, optionLabel: ReactNode) => SelectOption;
  isOptionDisabled?: (option: SelectOption, selectValue: unknown) => boolean;
  isOptionSelected?: (option: SelectOption, selectValue: unknown) => boolean;
  isValidNewOption?: (inputValue: string, selectValue: unknown, selectOptions: SelectOption[]) => boolean;
  filterOption?: (option: SelectOption, inputValue: string) => boolean;
  sortOption?: (a: SelectOption, b: SelectOption) => number;
  groupBy?: (option: SelectOption) => string;
  virtual?: boolean;
  virtualListHeight?: number;
  virtualItemHeight?: number;
  async?: boolean;
  loadOptions?: (inputValue: string, callback: (options: SelectOption[]) => void) => void | Promise<SelectOption[]>;
  defaultOptions?: boolean | SelectOption[];
  cacheOptions?: boolean;
  loadingMessage?: (obj: { inputValue: string }) => ReactNode;
  noOptionsMessage?: (obj: { inputValue: string }) => ReactNode;
  components?: Record<string, React.ComponentType<unknown>>;
  styles?: Record<string, (base: unknown, state: unknown) => unknown>;
  theme?: (theme: SelectTheme) => SelectTheme;
  classNamePrefix?: string;
  className?: string;
  classNames?: Record<string, string>;
  unstyled?: boolean;
  controlRef?: RefObject<HTMLDivElement>;
  menuRef?: RefObject<HTMLDivElement>;
  inputRef?: RefObject<HTMLInputElement>;
  selectRef?: RefObject<HTMLSelectElement>;
}