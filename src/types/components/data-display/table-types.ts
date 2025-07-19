/**
 * Table Component Types
 * 
 * Type definitions for table components including columns, filters,
 * sorting, pagination, and table configuration options.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

// Basic table data types
export interface TableRowData {
  id?: string | number;
  [key: string]: unknown;
}

export interface TableFilterDropdownProps {
  prefixCls: string;
  setSelectedKeys: (keys: string[]) => void;
  selectedKeys: string[];
  confirm: (param?: { closeDropdown?: boolean }) => void;
  clearFilters?: () => void;
  filters?: TableFilter[];
  visible: boolean;
  column: TableColumn;
  [key: string]: unknown;
}

export interface TableChangeExtra {
  currentDataSource: TableRowData[];
  action: 'paginate' | 'sort' | 'filter';
  [key: string]: unknown;
}

export interface TableExpandIconProps {
  prefixCls: string;
  expanded: boolean;
  onExpand: (expanded: boolean, record: TableRowData) => void;
  record: TableRowData;
  expandable: boolean;
  [key: string]: unknown;
}

export interface TableProps<TData extends TableRowData = TableRowData> extends BaseComponentProps {
  data: TData[];
  columns: TableColumn[];
  loading?: boolean;
  error?: string | null;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'bordered' | 'striped' | 'hover' | 'compact';
  bordered?: boolean;
  striped?: boolean;
  hover?: boolean;
  compact?: boolean;
  responsive?: boolean;
  sticky?: boolean;
  stickyHeader?: boolean;
  stickyColumns?: string[];
  virtualized?: boolean;
  virtualizedHeight?: number;
  virtualizedItemHeight?: number;
  virtualizedOverscan?: number;
  rowHeight?: number | ((index: number) => number);
  estimatedRowHeight?: number;
  selection?: TableSelectionConfig;
  sorting?: TableSortConfig;
  filtering?: TableFilterConfig;
  pagination?: TablePaginationConfig;
  grouping?: TableGroupConfig;
  expansion?: TableExpansionConfig;
  resizing?: TableResizeConfig;
  reordering?: TableReorderConfig;
  editing?: TableEditConfig;
  export?: TableExportConfig;
  search?: TableSearchConfig;
  toolbar?: TableToolbarConfig;
  footer?: TableFooterConfig;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  onRowClick?: (row: TData, index: number) => void;
  onRowDoubleClick?: (row: TData, index: number) => void;
  onRowContextMenu?: (row: TData, index: number, event: React.MouseEvent) => void;
  onCellClick?: (row: TData, column: TableColumn, value: unknown, rowIndex: number, columnIndex: number) => void;
  onCellDoubleClick?: (row: TData, column: TableColumn, value: unknown, rowIndex: number, columnIndex: number) => void;
  onCellContextMenu?: (row: TData, column: TableColumn, value: unknown, rowIndex: number, columnIndex: number, event: React.MouseEvent) => void;
  onStateChange?: (state: TableState) => void;
  getRowId?: (row: TData, index: number) => string;
  getRowClassName?: (row: TData, index: number) => string;
  getRowStyle?: (row: TData, index: number) => React.CSSProperties;
  getCellClassName?: (row: TData, column: TableColumn, value: unknown, rowIndex: number, columnIndex: number) => string;
  getCellStyle?: (row: TData, column: TableColumn, value: unknown, rowIndex: number, columnIndex: number) => React.CSSProperties;
  renderRow?: (row: TData, index: number, defaultRender: () => ReactNode) => ReactNode;
  renderCell?: (row: TData, column: TableColumn, value: unknown, rowIndex: number, columnIndex: number, defaultRender: () => ReactNode) => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
}

export interface TableColumn<TData extends TableRowData = TableRowData> {
  id: string;
  key?: string;
  title: ReactNode;
  dataIndex?: string | string[];
  accessor?: string | ((row: TData) => unknown);
  width?: number | string;
  minWidth?: number;
  maxWidth?: number;
  flex?: number;
  align?: 'left' | 'center' | 'right';
  verticalAlign?: 'top' | 'middle' | 'bottom';
  fixed?: boolean | 'left' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  resizable?: boolean;
  reorderable?: boolean;
  editable?: boolean;
  visible?: boolean;
  frozen?: boolean;
  ellipsis?: boolean;
  tooltip?: boolean | string | ((value: unknown, row: TData) => string);
  className?: string;
  headerClassName?: string;
  cellClassName?: string | ((value: unknown, row: TData, index: number) => string);
  style?: React.CSSProperties;
  headerStyle?: React.CSSProperties;
  cellStyle?: React.CSSProperties | ((value: unknown, row: TData, index: number) => React.CSSProperties);
  render?: (value: unknown, row: TData, index: number) => ReactNode;
  renderHeader?: (column: TableColumn<TData>) => ReactNode;
  renderFilter?: (column: TableColumn<TData>, value: unknown, onChange: (value: unknown) => void) => ReactNode;
  renderEditor?: (value: unknown, row: TData, index: number, onChange: (value: unknown) => void) => ReactNode;
  formatValue?: (value: unknown, row: TData, index: number) => string;
  parseValue?: (value: string, row: TData, index: number) => unknown;
  validateValue?: (value: unknown, row: TData, index: number) => boolean | string;
  sorter?: boolean | ((a: TData, b: TData) => number);
  sortOrder?: 'asc' | 'desc' | null;
  sortDirections?: ('asc' | 'desc')[];
  defaultSortOrder?: 'asc' | 'desc';
  filters?: TableFilter[];
  filterDropdown?: ReactNode | ((props: TableFilterDropdownProps) => ReactNode);
  filterIcon?: ReactNode | ((filtered: boolean) => ReactNode);
  filterMultiple?: boolean;
  filteredValue?: unknown[];
  defaultFilteredValue?: unknown[];
  onFilter?: (value: unknown, record: TData) => boolean;
  onFilterDropdownVisibleChange?: (visible: boolean) => void;
  groupBy?: boolean;
  aggregate?: 'sum' | 'avg' | 'min' | 'max' | 'count' | ((values: unknown[]) => unknown);
  editorType?: 'text' | 'number' | 'select' | 'checkbox' | 'date' | 'custom';
  editorProps?: Record<string, unknown>;
  validation?: TableColumnValidation;
  meta?: Record<string, unknown>;
}

// Table configuration types
export interface TableSelectionConfig {
  type?: 'checkbox' | 'radio';
  selectedRowKeys?: string[];
  defaultSelectedRowKeys?: string[];
  onChange?: (selectedRowKeys: string[], selectedRows: TableRowData[]) => void;
  onSelect?: (record: TableRowData, selected: boolean, selectedRows: TableRowData[], nativeEvent: Event) => void;
  onSelectAll?: (selected: boolean, selectedRows: TableRowData[], changeRows: TableRowData[]) => void;
  onSelectInvert?: (selectedRowKeys: string[]) => void;
  getCheckboxProps?: (record: TableRowData) => Record<string, unknown>;
  hideSelectAll?: boolean;
  preserveSelectedRowKeys?: boolean;
  columnWidth?: number | string;
  columnTitle?: ReactNode;
  fixed?: boolean;
  renderCell?: (checked: boolean, record: TableRowData, index: number, originNode: ReactNode) => ReactNode;
}

export interface TableSortConfig {
  sortedInfo?: TableSortInfo;
  onChange?: (pagination: TablePaginationState, filters: TableFilterInfo, sorter: TableSortInfo, extra: TableChangeExtra) => void;
  multiple?: boolean;
  showSorterTooltip?: boolean | TableSorterTooltip;
}

export interface TableFilterConfig {
  filteredInfo?: TableFilterInfo;
  onChange?: (pagination: TablePaginationState, filters: TableFilterInfo, sorter: TableSortInfo, extra: TableChangeExtra) => void;
  filterDropdownVisible?: boolean;
  onFilterDropdownVisibleChange?: (visible: boolean) => void;
}

export interface TablePaginationConfig {
  current?: number;
  pageSize?: number;
  total?: number;
  defaultCurrent?: number;
  defaultPageSize?: number;
  pageSizeOptions?: string[];
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: (total: number, range: [number, number]) => ReactNode;
  size?: 'default' | 'small';
  simple?: boolean;
  hideOnSinglePage?: boolean;
  position?: ('topLeft' | 'topCenter' | 'topRight' | 'bottomLeft' | 'bottomCenter' | 'bottomRight')[];
  onChange?: (page: number, pageSize: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
}

export interface TableGroupConfig {
  groupBy?: string | ((record: TableRowData) => string);
  expandable?: boolean;
  defaultExpandedGroups?: string[];
  expandedGroups?: string[];
  onGroupExpand?: (expanded: boolean, group: string) => void;
  renderGroupHeader?: (group: string, records: TableRowData[]) => ReactNode;
  renderGroupFooter?: (group: string, records: TableRowData[]) => ReactNode;
}

export interface TableExpansionConfig {
  expandable?: (record: TableRowData) => boolean;
  expandedRowKeys?: string[];
  defaultExpandedRowKeys?: string[];
  expandedRowRender?: (record: TableRowData, index: number, indent: number, expanded: boolean) => ReactNode;
  expandIcon?: (props: TableExpandIconProps) => ReactNode;
  expandIconColumnIndex?: number;
  expandRowByClick?: boolean;
  indentSize?: number;
  onExpand?: (expanded: boolean, record: TableRowData) => void;
  onExpandedRowsChange?: (expandedRows: string[]) => void;
  childrenColumnName?: string;
  rowExpandable?: (record: TableRowData) => boolean;
  fixed?: boolean | 'left' | 'right';
  columnWidth?: number;
  columnTitle?: ReactNode;
}

export interface TableResizeConfig {
  enabled?: boolean;
  onResize?: (columnId: string, width: number) => void;
  onResizeStart?: (columnId: string) => void;
  onResizeEnd?: (columnId: string, width: number) => void;
  minWidth?: number;
  maxWidth?: number;
  handleStyle?: React.CSSProperties;
  handleClassName?: string;
}

export interface TableReorderConfig {
  enabled?: boolean;
  onReorder?: (fromIndex: number, toIndex: number) => void;
  onReorderStart?: (columnId: string) => void;
  onReorderEnd?: (columnId: string, fromIndex: number, toIndex: number) => void;
  handleStyle?: React.CSSProperties;
  handleClassName?: string;
}

// Placeholder types - need to be defined based on actual implementation
export interface TableFilter {
  text: string;
  value: unknown;
}

export interface TableEditConfig {
  enabled?: boolean;
  // Add edit config properties as needed
}

export interface TableExportConfig {
  enabled?: boolean;
  // Add export config properties as needed
}

export interface TableSearchConfig {
  enabled?: boolean;
  // Add search config properties as needed
}

export interface TableToolbarConfig {
  enabled?: boolean;
  // Add toolbar config properties as needed
}

export interface TableFooterConfig {
  enabled?: boolean;
  // Add footer config properties as needed
}

export interface TableState {
  // Add state properties as needed
}

export interface TableColumnValidation {
  // Add validation properties as needed
}

export interface TableSortInfo {
  // Add sort info properties as needed
}

export interface TableFilterInfo {
  // Add filter info properties as needed
}

export interface TablePaginationState {
  // Add pagination state properties as needed
}

export interface TableSorterTooltip {
  // Add sorter tooltip properties as needed
}