/**
 * Utility Types
 *
 * Shared utility types for styling, spacing, and component configurations.
 */

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
