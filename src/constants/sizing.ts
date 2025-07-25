/**
 * Sizing constants for consistent spacing and dimensions
 */

// Spacing scale (based on 4px grid)
export const SPACING = {
  NONE: 0,
  XXS: 2,   // 2px
  XS: 4,    // 4px
  SM: 8,    // 8px
  MD: 16,   // 16px
  LG: 24,   // 24px
  XL: 32,   // 32px
  XXL: 48,  // 48px
  XXXL: 64  // 64px
} as const;

// Component sizes
export const SIZES = {
  // Button sizes
  BUTTON: {
    SMALL: {
      HEIGHT: 32,
      PADDING_X: 12,
      FONT_SIZE: 14
    },
    MEDIUM: {
      HEIGHT: 40,
      PADDING_X: 16,
      FONT_SIZE: 16
    },
    LARGE: {
      HEIGHT: 48,
      PADDING_X: 24,
      FONT_SIZE: 18
    }
  },

  // Input sizes
  INPUT: {
    SMALL: {
      HEIGHT: 32,
      PADDING_X: 12,
      FONT_SIZE: 14
    },
    MEDIUM: {
      HEIGHT: 40,
      PADDING_X: 16,
      FONT_SIZE: 16
    },
    LARGE: {
      HEIGHT: 48,
      PADDING_X: 20,
      FONT_SIZE: 18
    }
  },

  // Icon sizes
  ICON: {
    XS: 12,
    SM: 16,
    MD: 20,
    LG: 24,
    XL: 32,
    XXL: 48
  },

  // Avatar sizes
  AVATAR: {
    XS: 24,
    SM: 32,
    MD: 40,
    LG: 48,
    XL: 64,
    XXL: 96
  },

  // Modal sizes
  MODAL: {
    SM: 400,
    MD: 600,
    LG: 800,
    XL: 1000,
    FULL: '90vw'
  },

  // Drawer sizes
  DRAWER: {
    SM: 320,
    MD: 480,
    LG: 640,
    XL: 800
  }
} as const;

// Typography sizes
export const TYPOGRAPHY = {
  // Font sizes
  FONT_SIZE: {
    XS: 12,
    SM: 14,
    BASE: 16,
    LG: 18,
    XL: 20,
    XXL: 24,
    XXXL: 30,
    XXXXL: 36,
    XXXXXL: 48
  },

  // Line heights
  LINE_HEIGHT: {
    TIGHT: 1.25,
    NORMAL: 1.5,
    RELAXED: 1.75,
    LOOSE: 2
  },

  // Font weights
  FONT_WEIGHT: {
    THIN: 100,
    LIGHT: 300,
    NORMAL: 400,
    MEDIUM: 500,
    SEMIBOLD: 600,
    BOLD: 700,
    EXTRABOLD: 800,
    BLACK: 900
  },

  // Letter spacing
  LETTER_SPACING: {
    TIGHT: '-0.05em',
    NORMAL: '0',
    WIDE: '0.05em',
    WIDER: '0.1em',
    WIDEST: '0.2em'
  }
} as const;

// Border radius
export const RADIUS = {
  NONE: 0,
  SM: 2,
  MD: 4,
  LG: 8,
  XL: 12,
  XXL: 16,
  FULL: 9999
} as const;

// Breakpoints for responsive design
export const BREAKPOINTS = {
  XS: 0,      // Mobile portrait
  SM: 576,    // Mobile landscape
  MD: 768,    // Tablet portrait
  LG: 992,    // Tablet landscape / Desktop
  XL: 1200,   // Desktop
  XXL: 1400   // Large desktop
} as const;

// Container widths
export const CONTAINER = {
  SM: 540,
  MD: 720,
  LG: 960,
  XL: 1140,
  XXL: 1320,
  FLUID: '100%'
} as const;

// Grid configuration
export const GRID = {
  COLUMNS: 12,
  GUTTER: {
    XS: SPACING.SM,
    SM: SPACING.SM,
    MD: SPACING.MD,
    LG: SPACING.LG,
    XL: SPACING.LG,
    XXL: SPACING.XL
  }
} as const;

// Shadow depths
export const SHADOWS = {
  NONE: 'none',
  XS: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  SM: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  MD: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  LG: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  XL: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  XXL: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  INNER: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)'
} as const;

// Transition durations
export const TRANSITIONS = {
  FAST: '150ms',
  NORMAL: '300ms',
  SLOW: '500ms',
  VERY_SLOW: '1000ms'
} as const;

// Layout constants
export const LAYOUT = {
  HEADER_HEIGHT: 64,
  SIDEBAR_WIDTH: 240,
  SIDEBAR_COLLAPSED_WIDTH: 64,
  FOOTER_HEIGHT: 48,
  PAGE_PADDING: {
    XS: SPACING.SM,
    SM: SPACING.MD,
    MD: SPACING.LG,
    LG: SPACING.XL,
    XL: SPACING.XXL
  }
} as const;
