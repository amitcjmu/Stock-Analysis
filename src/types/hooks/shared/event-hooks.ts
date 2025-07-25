/**
 * Event Hook Types
 *
 * Hook interfaces for event handling including keyboard, click-away, hover, and focus hooks.
 */

// Event hooks
export interface UseKeyboardParams {
  keys: string | string[];
  onKeyDown?: (event: KeyboardEvent) => void;
  onKeyUp?: (event: KeyboardEvent) => void;
  preventDefault?: boolean;
  stopPropagation?: boolean;
  target?: EventTarget | null;
  enabled?: boolean;
}

export interface UseKeyboardReturn {
  isPressed: boolean;
  pressedKeys: Set<string>;
  addKey: (key: string) => void;
  removeKey: (key: string) => void;
  clearKeys: () => void;
}

export interface UseClickAwayParams {
  onClickAway: (event: Event) => void;
  mouseEvent?: 'click' | 'mousedown' | 'mouseup';
  touchEvent?: 'touchstart' | 'touchend';
  enabled?: boolean;
}

export interface UseClickAwayReturn {
  ref: React.RefObject<HTMLElement>;
}

export interface UseHoverParams {
  onHoverStart?: (event: MouseEvent) => void;
  onHoverEnd?: (event: MouseEvent) => void;
  delay?: number;
  restMs?: number;
}

export interface UseHoverReturn {
  ref: React.RefObject<HTMLElement>;
  isHovered: boolean;
}

export interface UseFocusParams {
  onFocus?: (event: FocusEvent) => void;
  onBlur?: (event: FocusEvent) => void;
  within?: boolean;
}

export interface UseFocusReturn {
  ref: React.RefObject<HTMLElement>;
  isFocused: boolean;
  isFocusedWithin: boolean;
}
