/**
 * Shared Component Types
 * 
 * Common component type definitions that are used across multiple modules.
 * Provides base interfaces and shared component patterns.
 */

import { ReactNode, RefObject } from 'react';

// Base shared component types
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  id?: string;
  style?: React.CSSProperties;
  'data-testid'?: string;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  role?: string;
  tabIndex?: number;
  onFocus?: (event: React.FocusEvent) => void;
  onBlur?: (event: React.FocusEvent) => void;
  onKeyDown?: (event: React.KeyboardEvent) => void;
  onKeyUp?: (event: React.KeyboardEvent) => void;
  onMouseEnter?: (event: React.MouseEvent) => void;
  onMouseLeave?: (event: React.MouseEvent) => void;
  onClick?: (event: React.MouseEvent) => void;
  onDoubleClick?: (event: React.MouseEvent) => void;
  onContextMenu?: (event: React.MouseEvent) => void;
}

export interface InteractiveComponentProps extends BaseComponentProps {
  disabled?: boolean;
  loading?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  error?: string | null;
  warning?: string | null;
  success?: boolean;
  tooltip?: string;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: string;
  color?: string;
  theme?: 'light' | 'dark' | 'auto';
}

export interface ContainerComponentProps extends BaseComponentProps {
  padding?: number | string;
  margin?: number | string;
  width?: number | string;
  height?: number | string;
  minWidth?: number | string;
  minHeight?: number | string;
  maxWidth?: number | string;
  maxHeight?: number | string;
  overflow?: 'visible' | 'hidden' | 'scroll' | 'auto';
  position?: 'static' | 'relative' | 'absolute' | 'fixed' | 'sticky';
  zIndex?: number;
  background?: string;
  border?: string;
  borderRadius?: number | string;
  shadow?: boolean | string;
  responsive?: boolean;
  breakpoint?: string;
}

// Layout component types
export interface LayoutProps extends ContainerComponentProps {
  direction?: 'row' | 'column';
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  wrap?: boolean;
  gap?: number | string;
  flex?: number | string;
  grow?: number;
  shrink?: number;
  basis?: number | string;
}

export interface GridProps extends ContainerComponentProps {
  columns?: number | string;
  rows?: number | string;
  gap?: number | string;
  columnGap?: number | string;
  rowGap?: number | string;
  templateColumns?: string;
  templateRows?: string;
  templateAreas?: string;
  autoColumns?: string;
  autoRows?: string;
  autoFlow?: 'row' | 'column' | 'row dense' | 'column dense';
  alignItems?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  alignContent?: 'start' | 'center' | 'end' | 'stretch' | 'space-between' | 'space-around' | 'space-evenly';
  justifyItems?: 'start' | 'center' | 'end' | 'stretch';
  justifyContent?: 'start' | 'center' | 'end' | 'stretch' | 'space-between' | 'space-around' | 'space-evenly';
  placeItems?: string;
  placeContent?: string;
}

export interface GridItemProps extends BaseComponentProps {
  column?: number | string;
  row?: number | string;
  columnSpan?: number;
  rowSpan?: number;
  columnStart?: number;
  columnEnd?: number;
  rowStart?: number;
  rowEnd?: number;
  area?: string;
  alignSelf?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  justifySelf?: 'start' | 'center' | 'end' | 'stretch';
  placeSelf?: string;
}

// Typography component types
export interface TypographyProps extends BaseComponentProps {
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption' | 'overline' | 'subtitle1' | 'subtitle2';
  component?: keyof JSX.IntrinsicElements;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'text' | 'muted' | string;
  align?: 'left' | 'center' | 'right' | 'justify';
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold' | number;
  size?: number | string;
  lineHeight?: number | string;
  letterSpacing?: number | string;
  textTransform?: 'none' | 'capitalize' | 'uppercase' | 'lowercase';
  decoration?: 'none' | 'underline' | 'overline' | 'line-through';
  italic?: boolean;
  monospace?: boolean;
  truncate?: boolean;
  maxLines?: number;
  ellipsis?: boolean;
  wrap?: boolean;
  selectable?: boolean;
  copyable?: boolean;
  onCopy?: (text: string) => void;
  highlight?: string | string[];
  highlightColor?: string;
  link?: boolean;
  href?: string;
  target?: string;
  rel?: string;
  download?: boolean | string;
}

// Button component types
export interface ButtonProps extends InteractiveComponentProps {
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'danger' | 'success' | 'warning';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  block?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  iconOnly?: boolean;
  loading?: boolean;
  loadingText?: string;
  loadingIcon?: ReactNode;
  href?: string;
  target?: string;
  rel?: string;
  download?: boolean | string;
  as?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  form?: string;
  formAction?: string;
  formEncType?: string;
  formMethod?: string;
  formNoValidate?: boolean;
  formTarget?: string;
  name?: string;
  value?: string;
  autoFocus?: boolean;
  active?: boolean;
  pressed?: boolean;
  group?: boolean;
  toggle?: boolean;
  onToggle?: (pressed: boolean) => void;
  badge?: string | number;
  badgeColor?: string;
  badgePosition?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export interface ButtonGroupProps extends BaseComponentProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  attached?: boolean;
  spacing?: number | string;
  wrap?: boolean;
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  disabled?: boolean;
  loading?: boolean;
  exclusive?: boolean;
  multiple?: boolean;
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  renderButton?: (button: ReactNode, index: number) => ReactNode;
}

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

// Loading and feedback component types
export interface LoadingSpinnerProps extends BaseComponentProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  color?: string;
  thickness?: number;
  speed?: 'slow' | 'normal' | 'fast' | number;
  variant?: 'spinner' | 'dots' | 'pulse' | 'wave' | 'bars';
  label?: string;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right';
  overlay?: boolean;
  backdrop?: boolean;
  backdropOpacity?: number;
  zIndex?: number;
  absolute?: boolean;
  center?: boolean;
}

export interface ProgressProps extends BaseComponentProps {
  value?: number;
  max?: number;
  min?: number;
  indeterminate?: boolean;
  variant?: 'linear' | 'circular';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  thickness?: number;
  color?: string;
  trackColor?: string;
  showLabel?: boolean;
  label?: string;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  formatLabel?: (value: number, max: number) => string;
  striped?: boolean;
  animated?: boolean;
  rounded?: boolean;
}

export interface SkeletonProps extends BaseComponentProps {
  variant?: 'text' | 'rectangular' | 'circular';
  width?: number | string;
  height?: number | string;
  animation?: 'pulse' | 'wave' | 'none';
  speed?: 'slow' | 'normal' | 'fast';
  lines?: number;
  lineHeight?: number | string;
  spacing?: number | string;
  rounded?: boolean;
  borderRadius?: number | string;
}

// Modal and overlay component types
export interface ModalProps extends BaseComponentProps {
  open?: boolean;
  onClose?: () => void;
  onOpen?: () => void;
  closeOnEsc?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnDocumentClick?: boolean;
  showCloseButton?: boolean;
  closeButtonPosition?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  closeButtonIcon?: ReactNode;
  title?: ReactNode;
  subtitle?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  centered?: boolean;
  scrollable?: boolean;
  backdrop?: boolean;
  backdropOpacity?: number;
  backdropBlur?: boolean;
  focusTrap?: boolean;
  restoreFocus?: boolean;
  preventScroll?: boolean;
  lockScroll?: boolean;
  zIndex?: number;
  animation?: 'fade' | 'scale' | 'slide' | 'none';
  animationDuration?: number;
  overlay?: boolean;
  overlayClassName?: string;
  contentClassName?: string;
  headerClassName?: string;
  bodyClassName?: string;
  footerClassName?: string;
  onAnimationStart?: () => void;
  onAnimationEnd?: () => void;
  onOverlayClick?: (event: React.MouseEvent) => void;
  onEscapeKeyDown?: (event: KeyboardEvent) => void;
  initialFocus?: RefObject<HTMLElement>;
  finalFocus?: RefObject<HTMLElement>;
  container?: HTMLElement | (() => HTMLElement);
  portal?: boolean;
  portalClassName?: string;
}

export interface TooltipProps extends BaseComponentProps {
  content: ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'top-start' | 'top-end' | 'bottom-start' | 'bottom-end' | 'left-start' | 'left-end' | 'right-start' | 'right-end';
  trigger?: 'hover' | 'focus' | 'click' | 'manual';
  delay?: number | { show: number; hide: number };
  offset?: number | [number, number];
  arrow?: boolean;
  interactive?: boolean;
  disabled?: boolean;
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  maxWidth?: number | string;
  zIndex?: number;
  animation?: boolean;
  animationDuration?: number;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'info' | 'success' | 'warning' | 'error';
  followCursor?: boolean;
  hideOnClick?: boolean;
  sticky?: boolean;
  boundary?: 'clippingParents' | 'document' | 'viewport' | HTMLElement;
  fallbackPlacements?: string[];
  flip?: boolean;
  preventOverflow?: boolean;
  strategy?: 'absolute' | 'fixed';
  onShow?: () => void;
  onHide?: () => void;
  onMount?: () => void;
  onUnmount?: () => void;
  reference?: RefObject<HTMLElement>;
  floating?: RefObject<HTMLElement>;
  portal?: boolean;
  portalContainer?: HTMLElement;
  middlewares?: any[];
}

// Card component types
export interface CardProps extends ContainerComponentProps {
  variant?: 'elevated' | 'outlined' | 'filled' | 'flat';
  clickable?: boolean;
  hoverable?: boolean;
  selected?: boolean;
  disabled?: boolean;
  loading?: boolean;
  header?: ReactNode;
  title?: ReactNode;
  subtitle?: ReactNode;
  media?: ReactNode;
  content?: ReactNode;
  actions?: ReactNode;
  footer?: ReactNode;
  orientation?: 'vertical' | 'horizontal';
  aspectRatio?: number | string;
  borderless?: boolean;
  rounded?: boolean;
  elevated?: boolean;
  shadow?: boolean | string;
  gradient?: boolean | string;
  blur?: boolean;
  headerClassName?: string;
  titleClassName?: string;
  subtitleClassName?: string;
  mediaClassName?: string;
  contentClassName?: string;
  actionsClassName?: string;
  footerClassName?: string;
  onCardClick?: (event: React.MouseEvent) => void;
  onHeaderClick?: (event: React.MouseEvent) => void;
  onMediaClick?: (event: React.MouseEvent) => void;
  onContentClick?: (event: React.MouseEvent) => void;
  onActionsClick?: (event: React.MouseEvent) => void;
  onFooterClick?: (event: React.MouseEvent) => void;
}

// Alert and notification component types
export interface AlertProps extends BaseComponentProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  title?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  closable?: boolean;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  banner?: boolean;
  border?: boolean;
  borderPosition?: 'top' | 'bottom' | 'left' | 'right';
  filled?: boolean;
  outlined?: boolean;
  rounded?: boolean;
  shadow?: boolean;
  elevation?: number;
  animation?: boolean;
  autoClose?: boolean;
  autoCloseDelay?: number;
  persistent?: boolean;
  onAutoClose?: () => void;
  iconClassName?: string;
  titleClassName?: string;
  descriptionClassName?: string;
  actionClassName?: string;
  closeButtonClassName?: string;
}

export interface ToastProps extends BaseComponentProps {
  type?: 'info' | 'success' | 'warning' | 'error' | 'loading';
  title?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  duration?: number;
  closable?: boolean;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  animation?: 'slide' | 'fade' | 'scale' | 'bounce';
  pauseOnHover?: boolean;
  pauseOnFocusLoss?: boolean;
  closeOnClick?: boolean;
  newestOnTop?: boolean;
  rtl?: boolean;
  limit?: number;
  progress?: boolean;
  progressColor?: string;
  toastId?: string | number;
  updateId?: string | number;
  data?: any;
  role?: 'alert' | 'status';
  containerId?: string;
  onOpen?: () => void;
  hideProgressBar?: boolean;
  theme?: 'light' | 'dark' | 'colored';
  transition?: any;
  style?: React.CSSProperties;
  toastClassName?: string;
  bodyClassName?: string;
  progressClassName?: string;
  closeButton?: boolean | ((closeToast: () => void) => ReactNode);
}

// Badge and chip component types
export interface BadgeProps extends BaseComponentProps {
  variant?: 'solid' | 'subtle' | 'outline' | 'soft';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
  dot?: boolean;
  pulse?: boolean;
  placement?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  offset?: [number, number];
  max?: number;
  showZero?: boolean;
  invisible?: boolean;
  overlap?: 'rectangular' | 'circular';
  anchorOrigin?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'right';
  };
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  slotProps?: {
    root?: any;
    badge?: any;
  };
}

export interface ChipProps extends InteractiveComponentProps {
  label: ReactNode;
  variant?: 'filled' | 'outlined' | 'soft';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
  clickable?: boolean;
  deletable?: boolean;
  selected?: boolean;
  icon?: ReactNode;
  avatar?: ReactNode;
  deleteIcon?: ReactNode;
  onDelete?: (event: React.MouseEvent) => void;
  onIconClick?: (event: React.MouseEvent) => void;
  onAvatarClick?: (event: React.MouseEvent) => void;
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  href?: string;
  target?: string;
  rel?: string;
  skipFocusWhenDisabled?: boolean;
  focusVisibleClassName?: string;
  iconClassName?: string;
  avatarClassName?: string;
  labelClassName?: string;
  deleteIconClassName?: string;
}

// Avatar component types
export interface AvatarProps extends BaseComponentProps {
  src?: string;
  alt?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  variant?: 'circular' | 'rounded' | 'square';
  color?: string;
  backgroundColor?: string;
  name?: string;
  initials?: string;
  icon?: ReactNode;
  badge?: ReactNode;
  badgeColor?: string;
  badgePlacement?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  badgeOffset?: [number, number];
  fallback?: ReactNode;
  loading?: boolean;
  loadingIcon?: ReactNode;
  clickable?: boolean;
  bordered?: boolean;
  borderColor?: string;
  borderWidth?: number;
  shadow?: boolean;
  online?: boolean;
  onlineColor?: string;
  offline?: boolean;
  offlineColor?: string;
  status?: 'online' | 'offline' | 'away' | 'busy' | 'invisible';
  statusColor?: string;
  statusPlacement?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  statusSize?: number;
  group?: boolean;
  groupMax?: number;
  groupSpacing?: number;
  imgProps?: React.ImgHTMLAttributes<HTMLImageElement>;
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  onError?: (event: React.SyntheticEvent<HTMLImageElement>) => void;
  onLoad?: (event: React.SyntheticEvent<HTMLImageElement>) => void;
  onImageLoad?: () => void;
  onImageError?: () => void;
  generateInitials?: (name: string) => string;
  generateColor?: (name: string) => string;
}

// Divider component types
export interface DividerProps extends BaseComponentProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted' | 'double';
  color?: string;
  thickness?: number;
  length?: number | string;
  spacing?: number | string;
  children?: ReactNode;
  textAlign?: 'left' | 'center' | 'right';
  absolute?: boolean;
  inset?: boolean;
  flexItem?: boolean;
  light?: boolean;
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
}

// Shared utility types
export interface Spacing {
  top?: number | string;
  right?: number | string;
  bottom?: number | string;
  left?: number | string;
  x?: number | string;
  y?: number | string;
  all?: number | string;
}

export interface BorderRadius {
  topLeft?: number | string;
  topRight?: number | string;
  bottomLeft?: number | string;
  bottomRight?: number | string;
  top?: number | string;
  right?: number | string;
  bottom?: number | string;
  left?: number | string;
  all?: number | string;
}

export interface Shadow {
  x?: number;
  y?: number;
  blur?: number;
  spread?: number;
  color?: string;
  inset?: boolean;
}

export interface Animation {
  name?: string;
  duration?: number | string;
  timingFunction?: string;
  delay?: number | string;
  iterationCount?: number | string;
  direction?: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
  fillMode?: 'none' | 'forwards' | 'backwards' | 'both';
  playState?: 'running' | 'paused';
}

export interface Transition {
  property?: string;
  duration?: number | string;
  timingFunction?: string;
  delay?: number | string;
}

export interface Transform {
  translate?: [number, number] | string;
  translateX?: number | string;
  translateY?: number | string;
  translateZ?: number | string;
  scale?: number | [number, number] | string;
  scaleX?: number | string;
  scaleY?: number | string;
  scaleZ?: number | string;
  rotate?: number | string;
  rotateX?: number | string;
  rotateY?: number | string;
  rotateZ?: number | string;
  skew?: [number, number] | string;
  skewX?: number | string;
  skewY?: number | string;
  matrix?: number[] | string;
  perspective?: number | string;
  transformOrigin?: string;
  transformStyle?: 'flat' | 'preserve-3d';
}

// Theme types
export interface Theme {
  colors: ThemeColors;
  typography: ThemeTypography;
  spacing: ThemeSpacing;
  breakpoints: ThemeBreakpoints;
  shadows: ThemeShadows;
  borderRadius: ThemeBorderRadius;
  transitions: ThemeTransitions;
  zIndex: ThemeZIndex;
  components?: ThemeComponents;
}

export interface ThemeColors {
  primary: ColorPalette;
  secondary: ColorPalette;
  success: ColorPalette;
  warning: ColorPalette;
  error: ColorPalette;
  info: ColorPalette;
  neutral: ColorPalette;
  background: BackgroundColors;
  text: TextColors;
  border: BorderColors;
}

export interface ColorPalette {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
  950: string;
}

export interface BackgroundColors {
  default: string;
  paper: string;
  overlay: string;
  disabled: string;
}

export interface TextColors {
  primary: string;
  secondary: string;
  disabled: string;
  hint: string;
}

export interface BorderColors {
  default: string;
  light: string;
  dark: string;
  focus: string;
  error: string;
  success: string;
  warning: string;
  info: string;
}

export interface ThemeTypography {
  fontFamily: string;
  fontSize: Record<string, string>;
  fontWeight: Record<string, number>;
  lineHeight: Record<string, number | string>;
  letterSpacing: Record<string, string>;
}

export interface ThemeSpacing {
  unit: number;
  scale: number[];
}

export interface ThemeBreakpoints {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

export interface ThemeShadows {
  none: string;
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  xxl: string;
  inner: string;
}

export interface ThemeBorderRadius {
  none: string;
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  xxl: string;
  full: string;
}

export interface ThemeTransitions {
  duration: Record<string, string>;
  easing: Record<string, string>;
}

export interface ThemeZIndex {
  hide: number;
  auto: number;
  base: number;
  docked: number;
  dropdown: number;
  sticky: number;
  banner: number;
  overlay: number;
  modal: number;
  popover: number;
  skipLink: number;
  toast: number;
  tooltip: number;
}

export interface ThemeComponents {
  [componentName: string]: {
    defaultProps?: any;
    styleOverrides?: any;
    variants?: any[];
  };
}