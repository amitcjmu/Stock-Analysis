/**
 * Theme Types
 *
 * Complete theme system interfaces for design tokens and component theming.
 */

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
    defaultProps?: unknown;
    styleOverrides?: unknown;
    variants?: unknown[];
  };
}
