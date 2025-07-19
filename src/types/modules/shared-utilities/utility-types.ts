/**
 * Utility Function Types
 * 
 * Types for common utility services including date, string, number, array, object, and color utilities.
 */

// Utility service interfaces
export interface DateUtilityService {
  formatDate: (date: Date | string, format: string) => string;
  parseDate: (dateString: string, format?: string) => Date;
  addDays: (date: Date, days: number) => Date;
  subtractDays: (date: Date, days: number) => Date;
  diffDays: (date1: Date, date2: Date) => number;
  isValidDate: (date: unknown) => boolean;
  getTimeAgo: (date: Date) => string;
  getTimezone: () => string;
  convertTimezone: (date: Date, timezone: string) => Date;
}

export interface StringUtilityService {
  capitalize: (str: string) => string;
  camelCase: (str: string) => string;
  kebabCase: (str: string) => string;
  snakeCase: (str: string) => string;
  truncate: (str: string, length: number, suffix?: string) => string;
  slugify: (str: string) => string;
  stripHtml: (html: string) => string;
  escapeHtml: (html: string) => string;
  unescapeHtml: (html: string) => string;
  isEmail: (email: string) => boolean;
  isUrl: (url: string) => boolean;
  generateId: (prefix?: string) => string;
  generateSlug: (text: string) => string;
}

export interface NumberUtilityService {
  formatNumber: (num: number, options?: NumberFormatOptions) => string;
  formatCurrency: (amount: number, currency: string, options?: CurrencyFormatOptions) => string;
  formatPercentage: (value: number, decimals?: number) => string;
  formatBytes: (bytes: number, decimals?: number) => string;
  clamp: (value: number, min: number, max: number) => number;
  round: (value: number, decimals: number) => number;
  isNumber: (value: unknown) => boolean;
  isInteger: (value: unknown) => boolean;
  isFloat: (value: unknown) => boolean;
  randomInt: (min: number, max: number) => number;
  randomFloat: (min: number, max: number) => number;
}

export interface ArrayUtilityService {
  chunk: <T>(array: T[], size: number) => T[][];
  flatten: <T>(array: (T | T[])[], depth?: number) => T[];
  unique: <T>(array: T[], key?: keyof T) => T[];
  groupBy: <T>(array: T[], key: keyof T) => Record<string, T[]>;
  sortBy: <T>(array: T[], key: keyof T, order?: 'asc' | 'desc') => T[];
  shuffle: <T>(array: T[]) => T[];
  sample: <T>(array: T[], count?: number) => T | T[];
  difference: <T>(array1: T[], array2: T[]) => T[];
  intersection: <T>(array1: T[], array2: T[]) => T[];
  union: <T>(array1: T[], array2: T[]) => T[];
  isEmpty: (array: unknown[]) => boolean;
  isEqual: (array1: unknown[], array2: unknown[]) => boolean;
}

export interface ObjectUtilityService {
  clone: <T>(obj: T) => T;
  merge: <T>(target: T, ...sources: Partial<T>[]) => T;
  pick: <T, K extends keyof T>(obj: T, keys: K[]) => Pick<T, K>;
  omit: <T, K extends keyof T>(obj: T, keys: K[]) => Omit<T, K>;
  has: (obj: unknown, path: string) => boolean;
  get: (obj: unknown, path: string, defaultValue?: unknown) => unknown;
  set: (obj: unknown, path: string, value: unknown) => void;
  isEmpty: (obj: unknown) => boolean;
  isEqual: (obj1: unknown, obj2: unknown) => boolean;
  keys: (obj: unknown) => string[];
  values: (obj: unknown) => unknown[];
  entries: (obj: unknown) => [string, unknown][];
  invert: (obj: Record<string, unknown>) => Record<string, string>;
}

export interface ColorUtilityService {
  hexToRgb: (hex: string) => RGB;
  rgbToHex: (rgb: RGB) => string;
  hslToRgb: (hsl: HSL) => RGB;
  rgbToHsl: (rgb: RGB) => HSL;
  lighten: (color: string, amount: number) => string;
  darken: (color: string, amount: number) => string;
  isValidColor: (color: string) => boolean;
  getContrast: (color1: string, color2: string) => number;
  generatePalette: (baseColor: string, count: number) => string[];
}

// Supporting types
export interface NumberFormatOptions {
  locale?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  useGrouping?: boolean;
}

export interface CurrencyFormatOptions extends NumberFormatOptions {
  display?: 'symbol' | 'code' | 'name';
}

export interface RGB {
  r: number;
  g: number;
  b: number;
  a?: number;
}

export interface HSL {
  h: number;
  s: number;
  l: number;
  a?: number;
}