/**
 * Responsive Layout Hook
 * Provides responsive layout utilities for observability components
 * Part of the Agent Observability Enhancement Phase 4A
 */

import { useState } from 'react'
import { useEffect } from 'react'

export interface ResponsiveBreakpoints {
  sm: number;
  md: number;
  lg: number;
  xl: number;
  '2xl': number;
}

export interface ResponsiveState {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeDesktop: boolean;
  breakpoint: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

const defaultBreakpoints: ResponsiveBreakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
};

export const useResponsiveLayout = (customBreakpoints?: Partial<ResponsiveBreakpoints>) => {
  const breakpoints = { ...defaultBreakpoints, ...customBreakpoints };
  
  const [responsiveState, setResponsiveState] = useState<ResponsiveState>(() => {
    if (typeof window === 'undefined') {
      return {
        width: 1024,
        height: 768,
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        isLargeDesktop: false,
        breakpoint: 'lg'
      };
    }

    const width = window.innerWidth;
    const height = window.innerHeight;
    
    return {
      width,
      height,
      isMobile: width < breakpoints.md,
      isTablet: width >= breakpoints.md && width < breakpoints.lg,
      isDesktop: width >= breakpoints.lg && width < breakpoints.xl,
      isLargeDesktop: width >= breakpoints.xl,
      breakpoint: getBreakpoint(width, breakpoints)
    };
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      setResponsiveState({
        width,
        height,
        isMobile: width < breakpoints.md,
        isTablet: width >= breakpoints.md && width < breakpoints.lg,
        isDesktop: width >= breakpoints.lg && width < breakpoints.xl,
        isLargeDesktop: width >= breakpoints.xl,
        breakpoint: getBreakpoint(width, breakpoints)
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [breakpoints]);

  return responsiveState;
};

function getBreakpoint(width: number, breakpoints: ResponsiveBreakpoints): ResponsiveState['breakpoint'] {
  if (width >= breakpoints['2xl']) return '2xl';
  if (width >= breakpoints.xl) return 'xl';
  if (width >= breakpoints.lg) return 'lg';
  if (width >= breakpoints.md) return 'md';
  return 'sm';
}

// Grid layout utilities
export const useGridLayout = (baseColumns: number = 4) => {
  const { isMobile, isTablet, isDesktop, isLargeDesktop } = useResponsiveLayout();

  const getGridColumns = () => {
    if (isMobile) return 1;
    if (isTablet) return Math.min(2, baseColumns);
    if (isDesktop) return Math.min(3, baseColumns);
    return baseColumns;
  };

  const getGridClass = () => {
    const columns = getGridColumns();
    return `grid grid-cols-1 md:grid-cols-${Math.min(2, columns)} lg:grid-cols-${Math.min(3, columns)} xl:grid-cols-${columns}`;
  };

  return {
    columns: getGridColumns(),
    gridClass: getGridClass(),
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop
  };
};

// Component visibility utilities
export const useComponentVisibility = () => {
  const { isMobile, isTablet } = useResponsiveLayout();

  return {
    showFilters: !isMobile,
    showSidebar: !isMobile,
    showDetailedCards: !isMobile,
    showCharts: !isMobile,
    compactMode: isMobile || isTablet,
    stackedLayout: isMobile
  };
};