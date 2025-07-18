/**
 * Form Component Types
 * 
 * Type definitions for form components including inputs, selects, checkboxes,
 * form validation, and form state management.
 */

import { ReactNode, RefObject } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from './shared';

// Form field control interface
export interface FormFieldControl {
  value: unknown;
  onChange: (value: unknown) => void;
  onBlur: () => void;
  onFocus: () => void;
  name: string;
  [key: string]: unknown;
}

// Mask state interface
export interface MaskState {
  value: string;
  selection: {
    start: number;
    end: number;
  };
  [key: string]: unknown;
}

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

export interface UploadFileActions {
  download?: () => void;
  preview?: () => void;
  remove?: () => void;
  [key: string]: unknown;
}

export interface ValidationOptions {
  first?: boolean;
  messages?: Record<string, string>;
  [key: string]: unknown;
}

export interface ValidationCallback {
  (error?: string | Error): void;
}

export interface FormInternalHooks {
  dispatch: (action: FormAction) => void;
  registerField: (entity: FormFieldEntity) => () => void;
  useSubscribe: (subscribable: boolean) => void;
  setInitialValues: (values: Record<string, unknown>, init: boolean) => void;
  setCallbacks: (callbacks: Record<string, unknown>) => void;
  getFields: () => FormFieldEntity[];
  setValidateMessages: (messages: Record<string, string>) => void;
  setPreserve: (preserve: boolean) => void;
  getInitialValue: (name: string | string[]) => unknown;
}

export interface FormAction {
  type: string;
  payload?: unknown;
}

export interface FormFieldEntity {
  name: string | string[];
  validateTrigger?: string | string[];
  rules?: ValidationRule[];
  dependencies?: string[][];
  initialValue?: unknown;
}

export interface FormErrorField {
  name: string | string[];
  errors: string[];
  warnings?: string[];
}

// Base form types
export interface BaseFormProps extends BaseComponentProps {
  name?: string;
  form?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  error?: string | null;
  warning?: string | null;
  success?: boolean;
  hint?: string;
  label?: ReactNode;
  labelPosition?: 'top' | 'left' | 'right' | 'bottom';
  labelWidth?: number | string;
  labelAlign?: 'left' | 'center' | 'right';
  hideLabel?: boolean;
  description?: ReactNode;
  validationTrigger?: 'onChange' | 'onBlur' | 'onSubmit' | 'manual';
  validateOnMount?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined' | 'borderless' | 'flushed';
  fullWidth?: boolean;
}

// Form container types
export interface FormProps extends BaseComponentProps {
  onSubmit?: (event: React.FormEvent<HTMLFormElement>) => void;
  onReset?: (event: React.FormEvent<HTMLFormElement>) => void;
  onInvalid?: (event: React.FormEvent<HTMLFormElement>) => void;
  autoComplete?: 'on' | 'off';
  noValidate?: boolean;
  method?: 'get' | 'post';
  action?: string;
  encType?: 'application/x-www-form-urlencoded' | 'multipart/form-data' | 'text/plain';
  target?: string;
  acceptCharset?: string;
  name?: string;
  rel?: string;
  disabled?: boolean;
  loading?: boolean;
  schema?: FormSchema;
  defaultValues?: Record<string, unknown>;
  values?: Record<string, unknown>;
  errors?: Record<string, string>;
  touched?: Record<string, boolean>;
  dirty?: boolean;
  valid?: boolean;
  submitting?: boolean;
  submitted?: boolean;
  validationMode?: 'onChange' | 'onBlur' | 'onSubmit' | 'all';
  reValidationMode?: 'onChange' | 'onBlur' | 'onSubmit';
  shouldFocusError?: boolean;
  shouldUnregister?: boolean;
  shouldUseNativeValidation?: boolean;
  criteriaMode?: 'firstError' | 'all';
  delayError?: number;
  onValuesChange?: (values: Record<string, unknown>, changedValues: Record<string, unknown>) => void;
  onFieldsChange?: (changedFields: FormField[], allFields: FormField[]) => void;
  onFinish?: (values: Record<string, unknown>) => void;
  onFinishFailed?: (errorInfo: FormErrorInfo) => void;
  validateMessages?: Record<string, string>;
  preserve?: boolean;
  requiredMark?: boolean | 'optional' | ((label: ReactNode, info: { required: boolean }) => ReactNode);
  colon?: boolean;
  scrollToFirstError?: boolean | ScrollToFirstErrorOptions;
  layout?: 'horizontal' | 'vertical' | 'inline';
  labelCol?: ColProps;
  wrapperCol?: ColProps;
  labelAlign?: 'left' | 'right';
  labelWrap?: boolean;
  size?: 'small' | 'middle' | 'large';
  component?: boolean | string | React.ComponentType<unknown>;
  fields?: FormField[];
  form?: FormInstance;
  initialValues?: Record<string, unknown>;
  validateTrigger?: string | string[];
  preserve?: boolean;
  onReset?: () => void;
}

export interface FormFieldProps extends BaseFormProps {
  fieldKey?: string | number | (string | number)[];
  dependencies?: string[][];
  getValueFromEvent?: (...args: unknown[]) => unknown;
  getValueProps?: (value: unknown) => unknown;
  normalize?: (value: unknown, prevValue: unknown, allValues: Record<string, unknown>) => unknown;
  preserve?: boolean;
  trigger?: string;
  validateFirst?: boolean;
  validateTrigger?: string | string[];
  valuePropName?: string;
  rules?: ValidationRule[];
  shouldUpdate?: boolean | ((prevValues: unknown, curValues: unknown) => boolean);
  messageVariables?: Record<string, string>;
  initialValue?: unknown;
  tooltip?: ReactNode;
  extra?: ReactNode;
  hasFeedback?: boolean;
  validateStatus?: 'success' | 'warning' | 'error' | 'validating' | '';
  noStyle?: boolean;
  hidden?: boolean;
  wrapperCol?: ColProps;
  labelCol?: ColProps;
  colon?: boolean;
  labelAlign?: 'left' | 'right';
  htmlFor?: string;
  children?: ReactNode | ((control: FormFieldControl, meta: FormFieldMeta, form: FormInstance) => ReactNode);
}

// Input component types
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

// Checkbox and radio component types
export interface CheckboxProps extends BaseFormProps {
  checked?: boolean;
  defaultChecked?: boolean;
  indeterminate?: boolean;
  value?: unknown;
  onChange?: (checked: boolean, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  children?: ReactNode;
  checkIcon?: ReactNode;
  indeterminateIcon?: ReactNode;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  rounded?: boolean;
  animation?: boolean;
  ripple?: boolean;
  autoFocus?: boolean;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLLabelElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  checkboxClassName?: string;
  labelClassName?: string;
  iconClassName?: string;
}

export interface CheckboxGroupProps extends BaseFormProps {
  value?: unknown[];
  defaultValue?: unknown[];
  options?: CheckboxOption[];
  children?: ReactNode;
  onChange?: (value: unknown[], event?: React.ChangeEvent<HTMLInputElement>) => void;
  direction?: 'horizontal' | 'vertical';
  spacing?: number | string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  color?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  checkAllEnabled?: boolean;
  checkAllText?: string;
  onCheckAll?: (checked: boolean) => void;
  groupRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  groupClassName?: string;
  itemClassName?: string;
}

export interface RadioProps extends BaseFormProps {
  checked?: boolean;
  defaultChecked?: boolean;
  value?: unknown;
  onChange?: (value: unknown, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  children?: ReactNode;
  radioIcon?: ReactNode;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  animation?: boolean;
  ripple?: boolean;
  autoFocus?: boolean;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLLabelElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  radioClassName?: string;
  labelClassName?: string;
  iconClassName?: string;
}

export interface RadioGroupProps extends BaseFormProps {
  value?: unknown;
  defaultValue?: unknown;
  options?: RadioOption[];
  children?: ReactNode;
  onChange?: (value: unknown, event: React.ChangeEvent<HTMLInputElement>) => void;
  direction?: 'horizontal' | 'vertical';
  spacing?: number | string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  color?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  groupRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  groupClassName?: string;
  itemClassName?: string;
}

// Switch component types
export interface SwitchProps extends BaseFormProps {
  checked?: boolean;
  defaultChecked?: boolean;
  value?: unknown;
  onChange?: (checked: boolean, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  children?: ReactNode;
  onLabel?: ReactNode;
  offLabel?: ReactNode;
  checkedIcon?: ReactNode;
  uncheckedIcon?: ReactNode;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  thumbColor?: string;
  trackColor?: string;
  animation?: boolean;
  ripple?: boolean;
  autoFocus?: boolean;
  loading?: boolean;
  loadingIcon?: ReactNode;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLLabelElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  switchClassName?: string;
  trackClassName?: string;
  thumbClassName?: string;
  labelClassName?: string;
  onLabelClassName?: string;
  offLabelClassName?: string;
}

// Slider component types
export interface SliderProps extends BaseFormProps {
  value?: number | number[];
  defaultValue?: number | number[];
  min?: number;
  max?: number;
  step?: number;
  marks?: boolean | SliderMark[];
  range?: boolean;
  reverse?: boolean;
  vertical?: boolean;
  included?: boolean;
  disabled?: boolean;
  dots?: boolean;
  tooltip?: boolean | 'auto' | 'always';
  tooltipFormatter?: (value: number) => ReactNode;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  onChange?: (value: number | number[]) => void;
  onAfterChange?: (value: number | number[]) => void;
  onBeforeChange?: (value: number | number[]) => void;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  trackStyle?: React.CSSProperties | React.CSSProperties[];
  railStyle?: React.CSSProperties;
  handleStyle?: React.CSSProperties | React.CSSProperties[];
  dotStyle?: React.CSSProperties;
  activeDotStyle?: React.CSSProperties;
  markStyle?: React.CSSProperties;
  className?: string;
  trackClassName?: string;
  railClassName?: string;
  handleClassName?: string;
  dotClassName?: string;
  markClassName?: string;
  sliderRef?: RefObject<HTMLDivElement>;
}

// File upload component types
export interface FileUploadProps extends BaseFormProps {
  accept?: string[];
  multiple?: boolean;
  maxSize?: number;
  maxFiles?: number;
  minSize?: number;
  preventDropOnDocument?: boolean;
  noClick?: boolean;
  noKeyboard?: boolean;
  noDrag?: boolean;
  noDragEventsBubbling?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  value?: File[];
  defaultValue?: File[];
  onChange?: (files: File[]) => void;
  onDrop?: (acceptedFiles: File[], rejectedFiles: FileRejection[]) => void;
  onDropAccepted?: (files: File[]) => void;
  onDropRejected?: (fileRejections: FileRejection[]) => void;
  onFileDialogCancel?: () => void;
  onFileDialogOpen?: () => void;
  onError?: (error: Error) => void;
  validator?: (file: File) => FileError | FileError[] | null;
  getFilesFromEvent?: (event: DragEvent | React.ChangeEvent<HTMLInputElement>) => Promise<File[]>;
  onDragEnter?: (event: React.DragEvent) => void;
  onDragLeave?: (event: React.DragEvent) => void;
  onDragOver?: (event: React.DragEvent) => void;
  useFsAccessApi?: boolean;
  autoUpload?: boolean;
  showPreview?: boolean;
  showProgress?: boolean;
  previewComponent?: React.ComponentType<FilePreviewProps>;
  uploadComponent?: React.ComponentType<FileUploadItemProps>;
  children?: ReactNode | ((props: FileUploadRenderProps) => ReactNode);
  placeholder?: ReactNode;
  uploadText?: string;
  browseText?: string;
  dragText?: string;
  dropText?: string;
  removeText?: string;
  retryText?: string;
  uploadIcon?: ReactNode;
  removeIcon?: ReactNode;
  retryIcon?: ReactNode;
  errorIcon?: ReactNode;
  successIcon?: ReactNode;
  loadingIcon?: ReactNode;
  variant?: 'default' | 'button' | 'avatar' | 'banner';
  layout?: 'vertical' | 'horizontal';
  listType?: 'text' | 'picture' | 'picture-card' | 'picture-circle';
  action?: string;
  method?: 'post' | 'put' | 'patch';
  headers?: Record<string, string>;
  withCredentials?: boolean;
  data?: Record<string, unknown> | ((file: File) => Record<string, unknown>);
  beforeUpload?: (file: File, fileList: File[]) => boolean | Promise<boolean>;
  customRequest?: (options: UploadRequestOption) => void;
  directory?: boolean;
  openFileDialogOnClick?: boolean;
  fileList?: UploadFile[];
  defaultFileList?: UploadFile[];
  onRemove?: (file: UploadFile) => boolean | Promise<boolean>;
  onPreview?: (file: UploadFile) => void;
  onDownload?: (file: UploadFile) => void;
  transformFile?: (file: File) => string | Blob | File | Promise<string | Blob | File>;
  iconRender?: (file: UploadFile, listType?: string) => ReactNode;
  isImageUrl?: (file: UploadFile) => boolean;
  progress?: UploadProgressProps;
  itemRender?: (originNode: ReactNode, file: UploadFile, fileList: UploadFile[], actions: UploadFileActions) => ReactNode;
  maxCount?: number;
  capture?: boolean | 'user' | 'environment';
  showUploadList?: boolean | ShowUploadListInterface;
  containerRef?: RefObject<HTMLDivElement>;
  inputRef?: RefObject<HTMLInputElement>;
  wrapperClassName?: string;
  listClassName?: string;
  itemClassName?: string;
  previewClassName?: string;
  progressClassName?: string;
}

// Form validation types
export interface ValidationRule {
  type?: 'string' | 'number' | 'boolean' | 'method' | 'regexp' | 'integer' | 'float' | 'array' | 'object' | 'enum' | 'date' | 'url' | 'hex' | 'email' | 'pattern' | 'unknown';
  required?: boolean;
  pattern?: RegExp;
  min?: number;
  max?: number;
  len?: number;
  enum?: unknown[];
  whitespace?: boolean;
  fields?: Record<string, ValidationRule>;
  options?: ValidationOptions;
  defaultField?: ValidationRule;
  transform?: (value: unknown) => unknown;
  message?: string | ((rule: ValidationRule, value: unknown, callback: ValidationCallback, source?: Record<string, unknown>, options?: ValidationOptions) => string);
  asyncValidator?: (rule: ValidationRule, value: unknown, callback: ValidationCallback, source?: Record<string, unknown>, options?: ValidationOptions) => void;
  validator?: (rule: ValidationRule, value: unknown, callback: ValidationCallback, source?: Record<string, unknown>, options?: ValidationOptions) => void;
}

export interface FormSchema {
  fields: Record<string, FieldSchema>;
  rules?: ValidationRule[];
  initialValues?: Record<string, unknown>;
  validateTrigger?: string | string[];
  validateMessages?: Record<string, string>;
  preserve?: boolean;
  name?: string;
}

export interface FieldSchema {
  type: string;
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  hidden?: boolean;
  rules?: ValidationRule[];
  initialValue?: unknown;
  options?: SelectOption[];
  dependencies?: string[];
  tooltip?: string;
  extra?: string;
  help?: string;
  validateTrigger?: string | string[];
  preserve?: boolean;
  component?: string | React.ComponentType<unknown>;
  componentProps?: Record<string, unknown>;
  render?: (value: unknown, record: Record<string, unknown>, index: number) => ReactNode;
  shouldUpdate?: boolean | ((prevValues: unknown, curValues: unknown) => boolean);
  getValueFromEvent?: (...args: unknown[]) => unknown;
  getValueProps?: (value: unknown) => unknown;
  normalize?: (value: unknown, prevValue: unknown, allValues: Record<string, unknown>) => unknown;
  trigger?: string;
  validateFirst?: boolean;
  valuePropName?: string;
  messageVariables?: Record<string, string>;
  wrapperCol?: ColProps;
  labelCol?: ColProps;
  noStyle?: boolean;
  hasFeedback?: boolean;
  validateStatus?: 'success' | 'warning' | 'error' | 'validating' | '';
  colon?: boolean;
  labelAlign?: 'left' | 'right';
}

// Supporting types
export interface CheckboxOption {
  label: ReactNode;
  value: unknown;
  disabled?: boolean;
  checked?: boolean;
  indeterminate?: boolean;
  color?: string;
  size?: string;
  className?: string;
  style?: React.CSSProperties;
}

export interface RadioOption {
  label: ReactNode;
  value: unknown;
  disabled?: boolean;
  color?: string;
  size?: string;
  className?: string;
  style?: React.CSSProperties;
}

export interface SliderMark {
  value: number;
  label?: ReactNode;
  style?: React.CSSProperties;
}

export interface FileRejection {
  file: File;
  errors: FileError[];
}

export interface FileError {
  code: string;
  message: string;
}

export interface FilePreviewProps {
  file: File;
  onRemove?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export interface FileUploadItemProps {
  file: UploadFile;
  onRemove?: () => void;
  onPreview?: () => void;
  onDownload?: () => void;
  onRetry?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export interface FileUploadRenderProps {
  isDragActive: boolean;
  isDragAccept: boolean;
  isDragReject: boolean;
  isFocused: boolean;
  acceptedFiles: File[];
  rejectedFiles: FileRejection[];
  getRootProps: (props?: Record<string, unknown>) => Record<string, unknown>;
  getInputProps: (props?: Record<string, unknown>) => Record<string, unknown>;
  open: () => void;
}

export interface UploadFile {
  uid: string;
  name: string;
  size?: number;
  type?: string;
  url?: string;
  status?: 'uploading' | 'done' | 'error' | 'removed';
  percent?: number;
  originFileObj?: File;
  response?: unknown;
  error?: unknown;
  linkProps?: Record<string, unknown>;
  thumbUrl?: string;
  crossOrigin?: React.ImgHTMLAttributes<HTMLImageElement>['crossOrigin'];
  preview?: string;
}

export interface UploadRequestOption {
  onProgress?: (event: { percent: number }, file: File) => void;
  onError?: (error: Error, response?: unknown) => void;
  onSuccess?: (response: unknown, file: File) => void;
  data?: Record<string, unknown>;
  filename?: string;
  file: File;
  withCredentials?: boolean;
  action: string;
  headers?: Record<string, string>;
  method?: 'post' | 'put' | 'patch';
}

export interface UploadProgressProps {
  strokeColor?: string | { from: string; to: string; direction: string };
  strokeWidth?: number;
  format?: (percent?: number, successPercent?: number) => ReactNode;
  type?: 'line' | 'circle' | 'dashboard';
  showInfo?: boolean;
  successPercent?: number;
  width?: number;
  gapDegree?: number;
  gapPosition?: 'top' | 'bottom' | 'left' | 'right';
  size?: 'default' | 'small';
  steps?: number;
  strokeLinecap?: 'round' | 'butt' | 'square';
  trailColor?: string;
}

export interface ShowUploadListInterface {
  showPreviewIcon?: boolean;
  showRemoveIcon?: boolean;
  showDownloadIcon?: boolean;
  removeIcon?: ReactNode | ((file: UploadFile) => ReactNode);
  downloadIcon?: ReactNode | ((file: UploadFile) => ReactNode);
  previewIcon?: ReactNode | ((file: UploadFile) => ReactNode);
}

export interface ColProps {
  span?: number;
  order?: number;
  offset?: number;
  push?: number;
  pull?: number;
  xs?: number | ColSize;
  sm?: number | ColSize;
  md?: number | ColSize;
  lg?: number | ColSize;
  xl?: number | ColSize;
  xxl?: number | ColSize;
  flex?: string | number;
  style?: React.CSSProperties;
  className?: string;
}

export interface ColSize {
  span?: number;
  order?: number;
  offset?: number;
  push?: number;
  pull?: number;
}

export interface FormField {
  name: string | string[];
  value?: unknown;
  touched?: boolean;
  validating?: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface FormFieldMeta {
  touched?: boolean;
  validating?: boolean;
  errors?: string[];
  warnings?: string[];
  name?: string | string[];
}

export interface FormInstance {
  getFieldValue: (name: string | string[]) => unknown;
  getFieldsValue: (nameList?: (string | string[])[] | true, filterFunc?: (meta: FormFieldMeta) => boolean) => Record<string, unknown>;
  getFieldError: (name: string | string[]) => string[];
  getFieldsError: (nameList?: (string | string[])[]) => Record<string, string[]>;
  getFieldWarning: (name: string | string[]) => string[];
  isFieldsTouched: (nameList?: (string | string[])[], allFieldsTouched?: boolean) => boolean;
  isFieldTouched: (name: string | string[]) => boolean;
  isFieldValidating: (name: string | string[]) => boolean;
  isFieldsValidating: (nameList: (string | string[])[]) => boolean;
  resetFields: (fields?: (string | string[])[]) => void;
  setFields: (fields: FormField[]) => void;
  setFieldValue: (name: string | string[], value: unknown) => void;
  setFieldsValue: (values: Record<string, unknown>) => void;
  validateFields: (nameList?: (string | string[])[]) => Promise<Record<string, unknown>>;
  submit: () => void;
  getInternalHooks: (key: string) => FormInternalHooks;
  scrollToField: (name: string | string[], options?: ScrollToFirstErrorOptions) => void;
}

export interface FormErrorInfo {
  values: Record<string, unknown>;
  errorFields: FormErrorField[];
  outOfDate: boolean;
}

export interface ScrollToFirstErrorOptions {
  behavior?: 'auto' | 'smooth';
  block?: 'start' | 'center' | 'end' | 'nearest';
  inline?: 'start' | 'center' | 'end' | 'nearest';
}