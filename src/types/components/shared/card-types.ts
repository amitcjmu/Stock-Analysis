/**
 * Card Component Types
 * 
 * Card component interfaces and related types.
 */

import { ReactNode } from 'react';
import { ContainerComponentProps } from './base-props';

// Card component types
export interface CardProps extends ContainerComponentProps {
  variant?: 'elevated' | 'outlined' | 'filled' | 'flat';
  clickable?: boolean;
  hoverable?: boolean;
  selected?: boolean;
  disabled?: boolean;
  loading?: boolean;
  header?: ReactNode;
  title?: ReactNode;
  subtitle?: ReactNode;
  media?: ReactNode;
  content?: ReactNode;
  actions?: ReactNode;
  footer?: ReactNode;
  orientation?: 'vertical' | 'horizontal';
  aspectRatio?: number | string;
  borderless?: boolean;
  rounded?: boolean;
  elevated?: boolean;
  shadow?: boolean | string;
  gradient?: boolean | string;
  blur?: boolean;
  headerClassName?: string;
  titleClassName?: string;
  subtitleClassName?: string;
  mediaClassName?: string;
  contentClassName?: string;
  actionsClassName?: string;
  footerClassName?: string;
  onCardClick?: (event: React.MouseEvent) => void;
  onHeaderClick?: (event: React.MouseEvent) => void;
  onMediaClick?: (event: React.MouseEvent) => void;
  onContentClick?: (event: React.MouseEvent) => void;
  onActionsClick?: (event: React.MouseEvent) => void;
  onFooterClick?: (event: React.MouseEvent) => void;
}