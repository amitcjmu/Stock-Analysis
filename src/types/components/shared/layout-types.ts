/**
 * Layout Component Types
 * 
 * Layout-related component interfaces including flexbox and grid layouts.
 */

import { BaseComponentProps, ContainerComponentProps } from './base-props';

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