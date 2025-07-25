/**
 * Tree Component Types
 *
 * Type definitions for tree components including tree nodes, drag and drop,
 * selection, expansion, and tree configuration options.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../shared';

export interface TreeSwitcherProps {
  expanded: boolean;
  loading: boolean;
  [key: string]: unknown;
}

export interface TreeMotionConfig {
  motionName: string;
  motionAppear: boolean;
  motionEnter: boolean;
  motionLeave: boolean;
  [key: string]: unknown;
}

export interface TreeNodePosition {
  node: TreeNode;
  pos: string;
  [key: string]: unknown;
}

export interface TreeProps extends BaseComponentProps {
  data: TreeNode[];
  loading?: boolean;
  error?: string | null;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'bordered' | 'card' | 'minimal';
  selectable?: boolean;
  multiple?: boolean;
  checkable?: boolean;
  draggable?: boolean;
  expandable?: boolean;
  searchable?: boolean;
  filterable?: boolean;
  showLine?: boolean;
  showIcon?: boolean;
  showLeafIcon?: boolean;
  defaultExpandAll?: boolean;
  defaultExpandParent?: boolean;
  autoExpandParent?: boolean;
  defaultExpandedKeys?: string[];
  expandedKeys?: string[];
  defaultSelectedKeys?: string[];
  selectedKeys?: string[];
  defaultCheckedKeys?: string[];
  checkedKeys?: string[] | { checked: string[]; halfChecked: string[] };
  checkStrictly?: boolean;
  disabled?: boolean;
  virtual?: boolean;
  virtualListHeight?: number;
  virtualItemHeight?: number;
  blockNode?: boolean;
  titleRender?: (node: TreeNode) => ReactNode;
  loadData?: (node: TreeNode) => Promise<void>;
  onExpand?: (expandedKeys: string[], info: TreeExpandInfo) => void;
  onSelect?: (selectedKeys: string[], info: TreeSelectInfo) => void;
  onCheck?: (checkedKeys: string[] | { checked: string[]; halfChecked: string[] }, info: TreeCheckInfo) => void;
  onLoad?: (loadedKeys: string[], info: TreeLoadInfo) => void;
  onRightClick?: (info: TreeRightClickInfo) => void;
  onDragStart?: (info: TreeDragInfo) => void;
  onDragEnter?: (info: TreeDragInfo) => void;
  onDragOver?: (info: TreeDragInfo) => void;
  onDragLeave?: (info: TreeDragInfo) => void;
  onDragEnd?: (info: TreeDragInfo) => void;
  onDrop?: (info: TreeDropInfo) => void;
  allowDrop?: (info: TreeAllowDropInfo) => boolean;
  filterTreeNode?: (node: TreeNode) => boolean;
  treeData?: TreeNode[];
  replaceFields?: TreeFieldNames;
  height?: number;
  itemHeight?: number;
  motion?: TreeMotionConfig;
  switcherIcon?: ReactNode | ((props: TreeSwitcherProps) => ReactNode);
  showSearch?: boolean;
  searchValue?: string;
  onSearch?: (value: string) => void;
  searchPlaceholder?: string;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
}

export interface TreeNode {
  key: string;
  title: ReactNode;
  children?: TreeNode[];
  disabled?: boolean;
  disableCheckbox?: boolean;
  selectable?: boolean;
  checkable?: boolean;
  isLeaf?: boolean;
  loading?: boolean;
  expanded?: boolean;
  selected?: boolean;
  checked?: boolean;
  halfChecked?: boolean;
  icon?: ReactNode;
  switcherIcon?: ReactNode;
  className?: string;
  style?: React.CSSProperties;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

// Tree event info types
export interface TreeExpandInfo {
  node: TreeNode;
  expanded: boolean;
  nativeEvent: MouseEvent;
}

export interface TreeSelectInfo {
  event: 'select';
  selected: boolean;
  node: TreeNode;
  selectedNodes: TreeNode[];
  nativeEvent: MouseEvent;
}

export interface TreeCheckInfo {
  event: 'check';
  node: TreeNode;
  checked: boolean;
  nativeEvent: MouseEvent;
  checkedNodes: TreeNode[];
  checkedNodesPositions?: TreeNodePosition[];
  halfCheckedKeys?: string[];
}

export interface TreeLoadInfo {
  event: 'load';
  node: TreeNode;
}

export interface TreeRightClickInfo {
  event: React.MouseEvent;
  node: TreeNode;
}

export interface TreeDragInfo {
  event: React.DragEvent;
  node: TreeNode;
  dragNode: TreeNode;
  dragNodesKeys: string[];
  dropPosition: number;
  dropToGap: boolean;
}

export interface TreeDropInfo extends TreeDragInfo {
  dropNode: TreeNode;
}

export interface TreeAllowDropInfo {
  dragNode: TreeNode;
  dropNode: TreeNode;
  dropPosition: number;
}

export interface TreeFieldNames {
  title?: string;
  key?: string;
  children?: string;
}
