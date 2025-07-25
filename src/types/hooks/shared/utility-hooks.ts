/**
 * Utility Hook Types
 *
 * Hook interfaces for utility functions including previous values, constants, force updates, and controllable state.
 */

// Utility hooks
export interface UsePreviousReturn<T> {
  previous: T | undefined;
}

export interface UseLatestReturn<T> {
  current: T;
}

export interface UseConstantReturn<T> {
  value: T;
}

export interface UseForceUpdateReturn {
  forceUpdate: () => void;
  updateCount: number;
}

export type UseIsomorphicLayoutEffectReturn = void;

export interface UseComposedRefsReturn<T = unknown> {
  composedRef: React.RefCallback<T>;
}

export interface UseControllableStateParams<T> {
  value?: T;
  defaultValue?: T;
  onChange?: (value: T) => void;
  shouldUpdate?: (prev: T, next: T) => boolean;
}

export interface UseControllableStateReturn<T> {
  value: T;
  setValue: (value: T | ((prev: T) => T)) => void;
  isControlled: boolean;
}
