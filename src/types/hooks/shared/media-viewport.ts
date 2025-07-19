/**
 * Media and Viewport Hook Types
 * 
 * Hook interfaces for media queries, breakpoints, and viewport management.
 */

// Media and viewport hooks
export interface UseMediaQueryParams {
  query: string;
  defaultMatches?: boolean;
  noSsr?: boolean;
}

export interface UseMediaQueryReturn {
  matches: boolean;
  media: string;
}

export interface UseBreakpointParams {
  breakpoints?: Record<string, number>;
  defaultBreakpoint?: string;
}

export interface UseBreakpointReturn {
  breakpoint: string;
  isAbove: (breakpoint: string) => boolean;
  isBelow: (breakpoint: string) => boolean;
  isOnly: (breakpoint: string) => boolean;
  isBetween: (min: string, max: string) => boolean;
}

export interface UseViewportParams {
  debounce?: number;
}

export interface UseViewportReturn {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  orientation: 'portrait' | 'landscape';
}