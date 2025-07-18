/**
 * Data Display Component Types
 * 
 * Type definitions for data display components including tables, lists,
 * charts, trees, and data visualization components.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from './shared';

// Generic data types for table and list components
export interface TableRowData {
  id?: string | number;
  [key: string]: unknown;
}

export interface ListItemData {
  id?: string | number;
  [key: string]: unknown;
}

export interface ChartDataPoint {
  x?: number | string;
  y?: number | string;
  [key: string]: unknown;
}

export interface ChartLegendItem {
  text: string;
  fillStyle?: string;
  strokeStyle?: string;
  lineWidth?: number;
  hidden?: boolean;
  [key: string]: unknown;
}

export interface ChartTooltipItem {
  label: string;
  value: string | number;
  color?: string;
  [key: string]: unknown;
}

export interface ChartDomain {
  min?: number;
  max?: number;
  [key: string]: unknown;
}

export interface ChartScale {
  id: string;
  type: string;
  options: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChartContext {
  chart: {
    canvas: HTMLCanvasElement;
    width: number;
    height: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ChartEvent {
  native: Event;
  x: number;
  y: number;
  [key: string]: unknown;
}

export interface ChartSize {
  width: number;
  height: number;
  [key: string]: unknown;
}

export interface ChartFont {
  family: string;
  size: number;
  style: string;
  weight: string;
  [key: string]: unknown;
}

export interface ChartLabels {
  boxWidth: number;
  color: string;
  font: ChartFont;
  padding: number;
  [key: string]: unknown;
}

export interface ChartTitle {
  display: boolean;
  text: string;
  font: ChartFont;
  [key: string]: unknown;
}

export interface ChartTicks {
  display: boolean;
  color: string;
  font: ChartFont;
  [key: string]: unknown;
}

export interface ChartGrid {
  display: boolean;
  color: string;
  lineWidth: number;
  [key: string]: unknown;
}

export interface ChartBorder {
  display: boolean;
  color: string;
  width: number;
  [key: string]: unknown;
}

export interface ChartTimeOptions {
  unit: 'millisecond' | 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';
  displayFormats: Record<string, string>;
  [key: string]: unknown;
}

export interface ChartAdapters {
  date: {
    locale: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

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

export interface TreeNodePosition {
  node: TreeNode;
  pos: string;
  [key: string]: unknown;
}

export interface ChartInteractionOptions {
  intersect?: boolean;
  mode?: 'point' | 'nearest' | 'index' | 'dataset' | 'x' | 'y';
  axis?: 'x' | 'y' | 'xy';
  [key: string]: unknown;
}

// Table component types
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

// List component types
export interface ListProps<TData extends ListItemData = ListItemData> extends BaseComponentProps {
  data: TData[];
  loading?: boolean;
  error?: string | null;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'bordered' | 'divided' | 'card' | 'inline';
  bordered?: boolean;
  divided?: boolean;
  striped?: boolean;
  hover?: boolean;
  selectable?: boolean;
  multiple?: boolean;
  selectedItems?: TData[];
  onSelectionChange?: (selectedItems: TData[]) => void;
  virtualized?: boolean;
  virtualizedHeight?: number;
  virtualizedItemHeight?: number | ((index: number) => number);
  virtualizedOverscan?: number;
  estimatedItemHeight?: number;
  pagination?: ListPaginationConfig;
  search?: ListSearchConfig;
  filtering?: ListFilterConfig;
  sorting?: ListSortConfig;
  grouping?: ListGroupConfig;
  actions?: ListActionConfig;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  renderItem: (item: TData, index: number) => ReactNode;
  renderGroup?: (group: string, items: TData[]) => ReactNode;
  renderHeader?: () => ReactNode;
  renderFooter?: () => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  onItemClick?: (item: TData, index: number) => void;
  onItemDoubleClick?: (item: TData, index: number) => void;
  onItemContextMenu?: (item: TData, index: number, event: React.MouseEvent) => void;
  getItemId?: (item: TData, index: number) => string;
  getItemClassName?: (item: TData, index: number) => string;
  getItemStyle?: (item: TData, index: number) => React.CSSProperties;
}

export interface ListItemProps extends InteractiveComponentProps {
  selected?: boolean;
  active?: boolean;
  divider?: boolean;
  inset?: boolean;
  dense?: boolean;
  avatar?: ReactNode;
  icon?: ReactNode;
  primary?: ReactNode;
  secondary?: ReactNode;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  button?: boolean;
  href?: string;
  component?: React.ElementType;
  alignItems?: 'flex-start' | 'center';
  disableGutters?: boolean;
  disablePadding?: boolean;
  onActionClick?: (event: React.MouseEvent) => void;
  onSecondaryActionClick?: (event: React.MouseEvent) => void;
  avatarClassName?: string;
  iconClassName?: string;
  primaryClassName?: string;
  secondaryClassName?: string;
  actionClassName?: string;
  secondaryActionClassName?: string;
}

// Tree component types
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

// Chart component types
export interface ChartProps extends BaseComponentProps {
  type: ChartType;
  data: ChartData;
  options?: ChartOptions;
  width?: number | string;
  height?: number | string;
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  loading?: boolean;
  error?: string | null;
  theme?: 'light' | 'dark' | 'auto';
  colorScheme?: string[];
  animation?: boolean;
  animationDuration?: number;
  interaction?: boolean;
  tooltip?: ChartTooltipConfig;
  legend?: ChartLegendConfig;
  axes?: ChartAxesConfig;
  grid?: ChartGridConfig;
  zoom?: ChartZoomConfig;
  brush?: ChartBrushConfig;
  export?: ChartExportConfig;
  onDataPointClick?: (data: ChartDataPoint, index: number) => void;
  onDataPointHover?: (data: ChartDataPoint, index: number) => void;
  onLegendClick?: (legendItem: ChartLegendItem) => void;
  onLegendHover?: (legendItem: ChartLegendItem) => void;
  onZoom?: (domain: ChartDomain) => void;
  onBrush?: (domain: ChartDomain) => void;
  renderTooltip?: (data: ChartTooltipItem) => ReactNode;
  renderLegend?: (legendItems: ChartLegendItem[]) => ReactNode;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
}

// Supporting types for complex components
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
  onReorder?: (columns: TableColumn[]) => void;
  onReorderStart?: (columnId: string) => void;
  onReorderEnd?: (columnId: string, newIndex: number) => void;
  dragHandle?: boolean;
  dragHandleIcon?: ReactNode;
}

export interface TableEditConfig {
  enabled?: boolean;
  mode?: 'inline' | 'modal' | 'drawer';
  triggerType?: 'click' | 'doubleClick';
  onEdit?: (record: TableRowData, rowIndex: number) => void;
  onSave?: (record: TableRowData, rowIndex: number) => void | Promise<void>;
  onCancel?: (record: TableRowData, rowIndex: number) => void;
  onDelete?: (record: TableRowData, rowIndex: number) => void | Promise<void>;
  validateOnSave?: boolean;
  confirmOnDelete?: boolean;
  deleteConfirmText?: string;
  editIcon?: ReactNode;
  saveIcon?: ReactNode;
  cancelIcon?: ReactNode;
  deleteIcon?: ReactNode;
}

export interface TableExportConfig {
  enabled?: boolean;
  formats?: ExportFormat[];
  onExport?: (format: ExportFormat, data: TableRowData[]) => void;
  filename?: string;
  includeHeaders?: boolean;
  selectedOnly?: boolean;
  visibleOnly?: boolean;
}

export interface TableSearchConfig {
  enabled?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  debounce?: number;
  searchableColumns?: string[];
  highlightResults?: boolean;
  caseSensitive?: boolean;
  exactMatch?: boolean;
}

export interface TableToolbarConfig {
  enabled?: boolean;
  title?: ReactNode;
  actions?: ReactNode;
  filters?: ReactNode;
  search?: boolean | TableSearchConfig;
  export?: boolean | TableExportConfig;
  refresh?: boolean | (() => void);
  settings?: boolean | TableSettingsConfig;
  density?: boolean;
  fullscreen?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export interface TableFooterConfig {
  enabled?: boolean;
  summary?: TableSummaryConfig;
  pagination?: boolean | TablePaginationConfig;
  className?: string;
  style?: React.CSSProperties;
}

export interface TableState {
  selectedRowKeys: string[];
  selectedRows: TableRowData[];
  sortedInfo: TableSortInfo;
  filteredInfo: TableFilterInfo;
  pagination: TablePaginationState;
  expandedRowKeys: string[];
  expandedGroups: string[];
  columnWidths: Record<string, number>;
  columnOrder: string[];
  columnVisibility: Record<string, boolean>;
  searchValue: string;
  filters: Record<string, unknown>;
}

// Additional supporting interfaces
export interface TableFilter {
  text: ReactNode;
  value: unknown;
  children?: TableFilter[];
}

export interface TableColumnValidation {
  required?: boolean;
  pattern?: RegExp;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  validator?: (value: unknown, record: TableRowData) => boolean | string | Promise<boolean | string>;
  message?: string;
}

export interface ListPaginationConfig {
  current?: number;
  pageSize?: number;
  total?: number;
  onChange?: (page: number, pageSize: number) => void;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  size?: 'small' | 'default';
  simple?: boolean;
}

export interface ListSearchConfig {
  enabled?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  searchKey?: string | string[];
  caseSensitive?: boolean;
  highlightResults?: boolean;
}

export interface ListFilterConfig {
  enabled?: boolean;
  filters?: ListFilter[];
  onChange?: (filters: Record<string, unknown>) => void;
}

export interface ListSortConfig {
  enabled?: boolean;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  options?: ListSortOption[];
}

export interface ListGroupConfig {
  enabled?: boolean;
  groupBy?: string | ((item: ListItemData) => string);
  renderGroup?: (group: string, items: ListItemData[]) => ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export interface ListActionConfig {
  enabled?: boolean;
  actions?: ListAction[];
  onAction?: (action: string, item: ListItemData, index: number) => void;
  position?: 'start' | 'end';
  trigger?: 'hover' | 'always';
}

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

export interface ChartData {
  labels?: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label?: string;
  data: ChartDataPoint[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number;
  pointHoverRadius?: number;
  [key: string]: unknown;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  aspectRatio?: number;
  resizeDelay?: number;
  devicePixelRatio?: number;
  locale?: string;
  interaction?: ChartInteractionOptions;
  onHover?: (event: ChartEvent, elements: ChartDataPoint[]) => void;
  onClick?: (event: ChartEvent, elements: ChartDataPoint[]) => void;
  onResize?: (chart: ChartContext, size: ChartSize) => void;
  plugins?: Record<string, unknown>;
  scales?: Record<string, ChartScale>;
  elements?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  animation?: Record<string, unknown>;
  animations?: Record<string, unknown>;
  transitions?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChartTooltipConfig {
  enabled?: boolean;
  position?: string;
  filter?: (tooltipItem: ChartTooltipItem) => boolean;
  itemSort?: (a: ChartTooltipItem, b: ChartTooltipItem) => number;
  external?: (context: ChartContext) => void;
  callbacks?: Record<string, unknown>;
  displayColors?: boolean;
  backgroundColor?: string;
  titleColor?: string;
  bodyColor?: string;
  borderColor?: string;
  borderWidth?: number;
  cornerRadius?: number;
  caretPadding?: number;
  caretSize?: number;
  titleFont?: ChartFont;
  bodyFont?: ChartFont;
  footerFont?: ChartFont;
  titleAlign?: string;
  bodyAlign?: string;
  footerAlign?: string;
  titleSpacing?: number;
  titleMarginBottom?: number;
  bodySpacing?: number;
  footerSpacing?: number;
  footerMarginTop?: number;
  padding?: number;
  xPadding?: number;
  yPadding?: number;
  multiKeyBackground?: string;
  usePointStyle?: boolean;
  boxWidth?: number;
  boxHeight?: number;
  boxPadding?: number;
}

export interface ChartLegendConfig {
  display?: boolean;
  position?: 'top' | 'left' | 'bottom' | 'right' | 'chartArea';
  align?: 'start' | 'center' | 'end';
  maxHeight?: number;
  maxWidth?: number;
  fullSize?: boolean;
  onClick?: (event: ChartEvent, legendItem: ChartLegendItem, legend: ChartLegendConfig) => void;
  onHover?: (event: ChartEvent, legendItem: ChartLegendItem, legend: ChartLegendConfig) => void;
  onLeave?: (event: ChartEvent, legendItem: ChartLegendItem, legend: ChartLegendConfig) => void;
  reverse?: boolean;
  labels?: ChartLabels;
  rtl?: boolean;
  textDirection?: string;
  title?: ChartTitle;
}

export interface ChartAxesConfig {
  x?: ChartAxisConfig;
  y?: ChartAxisConfig;
  [key: string]: ChartAxisConfig | undefined;
}

export interface ChartAxisConfig {
  type?: string;
  position?: string;
  display?: boolean | string;
  title?: ChartTitle;
  min?: number;
  max?: number;
  suggestedMin?: number;
  suggestedMax?: number;
  beginAtZero?: boolean;
  bounds?: string;
  clip?: boolean;
  grace?: number | string;
  stack?: string;
  stackWeight?: number;
  axis?: string;
  offset?: boolean;
  reverse?: boolean;
  ticks?: ChartTicks;
  grid?: ChartGrid;
  border?: ChartBorder;
  time?: ChartTimeOptions;
  adapters?: ChartAdapters;
  afterBuildTicks?: (scale: ChartScale) => void;
  beforeCalculateLabelRotation?: (scale: ChartScale) => void;
  afterCalculateLabelRotation?: (scale: ChartScale) => void;
  beforeFit?: (scale: ChartScale) => void;
  afterFit?: (scale: ChartScale) => void;
  afterTickToLabelConversion?: (scale: ChartScale) => void;
  beforeSetDimensions?: (scale: ChartScale) => void;
  afterSetDimensions?: (scale: ChartScale) => void;
  beforeDataLimits?: (scale: ChartScale) => void;
  afterDataLimits?: (scale: ChartScale) => void;
  beforeTickToLabelConversion?: (scale: ChartScale) => void;
  beforeUpdate?: (scale: ChartScale) => void;
  afterUpdate?: (scale: ChartScale) => void;
}

export interface ChartGridConfig {
  display?: boolean;
  circular?: boolean;
  color?: string | string[];
  lineWidth?: number | number[];
  drawBorder?: boolean;
  drawOnChartArea?: boolean;
  drawTicks?: boolean;
  tickBorderDash?: number[];
  tickBorderDashOffset?: number;
  tickColor?: string | string[];
  tickLength?: number;
  tickWidth?: number;
  offset?: boolean;
  z?: number;
}

export interface ChartZoomConfig {
  enabled?: boolean;
  mode?: 'x' | 'y' | 'xy';
  rangeMin?: ChartDomain;
  rangeMax?: ChartDomain;
  speed?: number;
  threshold?: number;
  sensitivity?: number;
  onZoom?: (context: ChartContext) => void;
  onZoomComplete?: (context: ChartContext) => void;
  onZoomRejected?: (context: ChartContext) => void;
  onZoomStart?: (context: ChartContext) => void;
}

export interface ChartBrushConfig {
  enabled?: boolean;
  mode?: 'x' | 'y' | 'xy';
  onBrush?: (domain: ChartDomain) => void;
  onBrushEnd?: (domain: ChartDomain) => void;
  brushStyle?: React.CSSProperties;
  handleStyle?: React.CSSProperties;
}

export interface ChartExportConfig {
  enabled?: boolean;
  formats?: ExportFormat[];
  onExport?: (format: ExportFormat, dataUrl: string) => void;
  filename?: string;
  backgroundColor?: string;
  width?: number;
  height?: number;
  pixelRatio?: number;
}

// Shared utility types
export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
}

export interface TableSortInfo {
  columnKey?: string;
  order?: 'ascend' | 'descend';
  field?: string;
  column?: TableColumn;
}

export interface TableFilterInfo {
  [key: string]: string[] | null;
}

export interface TablePaginationState {
  current: number;
  pageSize: number;
  total: number;
}

export interface TableSorterTooltip {
  target?: 'sorter-icon' | 'full-header';
}

export interface TableSettingsConfig {
  columns?: boolean;
  density?: boolean;
  reload?: boolean;
  fullscreen?: boolean;
  export?: boolean;
}

export interface TableSummaryConfig {
  enabled?: boolean;
  position?: 'top' | 'bottom';
  render?: (data: TableRowData[]) => ReactNode;
  columns?: TableSummaryColumn[];
}

export interface TableSummaryColumn {
  key: string;
  aggregate: 'sum' | 'avg' | 'min' | 'max' | 'count' | ((values: unknown[]) => unknown);
  format?: (value: unknown) => ReactNode;
  precision?: number;
}

export interface ListFilter {
  key: string;
  label: string;
  type: 'select' | 'multiselect' | 'range' | 'text' | 'date';
  options?: { label: string; value: unknown }[];
  value?: unknown;
}

export interface ListSortOption {
  label: string;
  value: string;
  order?: 'asc' | 'desc';
}

export interface ListAction {
  key: string;
  label: string;
  icon?: ReactNode;
  onClick?: (item: ListItemData, index: number) => void;
  disabled?: boolean | ((item: ListItemData, index: number) => boolean);
  visible?: boolean | ((item: ListItemData, index: number) => boolean);
}

export type ChartType = 'line' | 'bar' | 'pie' | 'doughnut' | 'scatter' | 'bubble' | 'radar' | 'polarArea' | 'area';