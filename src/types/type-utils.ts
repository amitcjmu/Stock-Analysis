/**
 * Type Utils - CC utility types for the stock analysis platform
 */

// Utility for creating branded types
export type Brand<T, B> = T & { __brand: B };

// Flow ID branded type
export type FlowId = Brand<string, 'FlowId'>;
export type UserId = Brand<string, 'UserId'>;
export type ClientAccountId = Brand<string, 'ClientAccountId'>;
export type EngagementId = Brand<string, 'EngagementId'>;

// Common utility types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;

// Deep partial type
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Deep readonly type
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};

// Exact type (prevents excess properties)
export type Exact<T, U> = T & Record<Exclude<keyof U, keyof T>, never>;

// Extract function parameter types
export type Parameters<T> = T extends (...args: infer P) => unknown ? P : never;

// Extract function return type
export type ReturnType<T> = T extends (...args: unknown[]) => infer R ? R : unknown;

// Extract promise type
export type PromiseType<T> = T extends Promise<infer P> ? P : T;

// Extract array element type
export type ArrayElement<T> = T extends Array<infer U> ? U : never;

// Create union from object values
export type ValueOf<T> = T[keyof T];

// Create union from object keys
export type KeyOf<T> = keyof T;

// Non-nullable version of a type
export type NonNullable<T> = T extends null | undefined ? never : T;

// Required version of optional properties
export type RequireFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Optional version of required properties
export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Mutable version of readonly type
export type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

// Deep mutable version
export type DeepMutable<T> = {
  -readonly [P in keyof T]: T[P] extends object ? DeepMutable<T[P]> : T[P];
};
