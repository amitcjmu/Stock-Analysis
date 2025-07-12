/**
 * Data Display Component Types
 * 
 * Type definitions for data display components including tables, lists,
 * charts, trees, and data visualization components.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from './shared';

// Table component types
export interface TableProps extends BaseComponentProps {
  data: any[];
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
  onRowClick?: (row: any, index: number) => void;
  onRowDoubleClick?: (row: any, index: number) => void;
  onRowContextMenu?: (row: any, index: number, event: React.MouseEvent) => void;
  onCellClick?: (row: any, column: TableColumn, value: any, rowIndex: number, columnIndex: number) => void;
  onCellDoubleClick?: (row: any, column: TableColumn, value: any, rowIndex: number, columnIndex: number) => void;
  onCellContextMenu?: (row: any, column: TableColumn, value: any, rowIndex: number, columnIndex: number, event: React.MouseEvent) => void;
  onStateChange?: (state: TableState) => void;
  getRowId?: (row: any, index: number) => string;
  getRowClassName?: (row: any, index: number) => string;
  getRowStyle?: (row: any, index: number) => React.CSSProperties;
  getCellClassName?: (row: any, column: TableColumn, value: any, rowIndex: number, columnIndex: number) => string;
  getCellStyle?: (row: any, column: TableColumn, value: any, rowIndex: number, columnIndex: number) => React.CSSProperties;
  renderRow?: (row: any, index: number, defaultRender: () => ReactNode) => ReactNode;
  renderCell?: (row: any, column: TableColumn, value: any, rowIndex: number, columnIndex: number, defaultRender: () => ReactNode) => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
}

export interface TableColumn {
  id: string;
  key?: string;
  title: ReactNode;
  dataIndex?: string | string[];
  accessor?: string | ((row: any) => any);
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
  tooltip?: boolean | string | ((value: any, row: any) => string);
  className?: string;
  headerClassName?: string;
  cellClassName?: string | ((value: any, row: any, index: number) => string);
  style?: React.CSSProperties;
  headerStyle?: React.CSSProperties;
  cellStyle?: React.CSSProperties | ((value: any, row: any, index: number) => React.CSSProperties);
  render?: (value: any, row: any, index: number) => ReactNode;
  renderHeader?: (column: TableColumn) => ReactNode;
  renderFilter?: (column: TableColumn, value: any, onChange: (value: any) => void) => ReactNode;
  renderEditor?: (value: any, row: any, index: number, onChange: (value: any) => void) => ReactNode;
  formatValue?: (value: any, row: any, index: number) => string;
  parseValue?: (value: string, row: any, index: number) => any;
  validateValue?: (value: any, row: any, index: number) => boolean | string;
  sorter?: boolean | ((a: any, b: any) => number);
  sortOrder?: 'asc' | 'desc' | null;
  sortDirections?: ('asc' | 'desc')[];
  defaultSortOrder?: 'asc' | 'desc';
  filters?: TableFilter[];
  filterDropdown?: ReactNode | ((props: any) => ReactNode);
  filterIcon?: ReactNode | ((filtered: boolean) => ReactNode);
  filterMultiple?: boolean;
  filteredValue?: any[];
  defaultFilteredValue?: any[];
  onFilter?: (value: any, record: any) => boolean;
  onFilterDropdownVisibleChange?: (visible: boolean) => void;
  groupBy?: boolean;
  aggregate?: 'sum' | 'avg' | 'min' | 'max' | 'count' | ((values: any[]) => any);
  editorType?: 'text' | 'number' | 'select' | 'checkbox' | 'date' | 'custom';
  editorProps?: any;
  validation?: TableColumnValidation;
  meta?: Record<string, any>;
}

// List component types
export interface ListProps extends BaseComponentProps {
  data: any[];
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
  selectedItems?: any[];
  onSelectionChange?: (selectedItems: any[]) => void;
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
  renderItem: (item: any, index: number) => ReactNode;
  renderGroup?: (group: string, items: any[]) => ReactNode;
  renderHeader?: () => ReactNode;
  renderFooter?: () => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  onItemClick?: (item: any, index: number) => void;
  onItemDoubleClick?: (item: any, index: number) => void;
  onItemContextMenu?: (item: any, index: number, event: React.MouseEvent) => void;
  getItemId?: (item: any, index: number) => string;
  getItemClassName?: (item: any, index: number) => string;
  getItemStyle?: (item: any, index: number) => React.CSSProperties;
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
  motion?: any;
  switcherIcon?: ReactNode | ((props: any) => ReactNode);
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
  data?: any;
  [key: string]: any;
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
  onDataPointClick?: (data: any, index: number) => void;
  onDataPointHover?: (data: any, index: number) => void;
  onLegendClick?: (legendItem: any) => void;
  onLegendHover?: (legendItem: any) => void;
  onZoom?: (domain: any) => void;
  onBrush?: (domain: any) => void;
  renderTooltip?: (data: any) => ReactNode;
  renderLegend?: (legendItems: any[]) => ReactNode;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
}

// Supporting types for complex components
export interface TableSelectionConfig {
  type?: 'checkbox' | 'radio';
  selectedRowKeys?: string[];
  defaultSelectedRowKeys?: string[];
  onChange?: (selectedRowKeys: string[], selectedRows: any[]) => void;
  onSelect?: (record: any, selected: boolean, selectedRows: any[], nativeEvent: Event) => void;
  onSelectAll?: (selected: boolean, selectedRows: any[], changeRows: any[]) => void;
  onSelectInvert?: (selectedRowKeys: string[]) => void;
  getCheckboxProps?: (record: any) => any;
  hideSelectAll?: boolean;
  preserveSelectedRowKeys?: boolean;
  columnWidth?: number | string;
  columnTitle?: ReactNode;
  fixed?: boolean;
  renderCell?: (checked: boolean, record: any, index: number, originNode: ReactNode) => ReactNode;
}

export interface TableSortConfig {
  sortedInfo?: TableSortInfo;
  onChange?: (pagination: any, filters: any, sorter: any, extra: any) => void;
  multiple?: boolean;
  showSorterTooltip?: boolean | TableSorterTooltip;
}

export interface TableFilterConfig {
  filteredInfo?: TableFilterInfo;
  onChange?: (pagination: any, filters: any, sorter: any, extra: any) => void;
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
  groupBy?: string | ((record: any) => string);
  expandable?: boolean;
  defaultExpandedGroups?: string[];
  expandedGroups?: string[];
  onGroupExpand?: (expanded: boolean, group: string) => void;
  renderGroupHeader?: (group: string, records: any[]) => ReactNode;
  renderGroupFooter?: (group: string, records: any[]) => ReactNode;
}

export interface TableExpansionConfig {
  expandable?: (record: any) => boolean;
  expandedRowKeys?: string[];
  defaultExpandedRowKeys?: string[];
  expandedRowRender?: (record: any, index: number, indent: number, expanded: boolean) => ReactNode;
  expandIcon?: (props: any) => ReactNode;
  expandIconColumnIndex?: number;
  expandRowByClick?: boolean;
  indentSize?: number;
  onExpand?: (expanded: boolean, record: any) => void;
  onExpandedRowsChange?: (expandedRows: string[]) => void;
  childrenColumnName?: string;
  rowExpandable?: (record: any) => boolean;
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
  onEdit?: (record: any, rowIndex: number) => void;
  onSave?: (record: any, rowIndex: number) => void | Promise<void>;
  onCancel?: (record: any, rowIndex: number) => void;
  onDelete?: (record: any, rowIndex: number) => void | Promise<void>;
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
  onExport?: (format: ExportFormat, data: any[]) => void;
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
  selectedRows: any[];
  sortedInfo: TableSortInfo;
  filteredInfo: TableFilterInfo;
  pagination: TablePaginationState;
  expandedRowKeys: string[];
  expandedGroups: string[];
  columnWidths: Record<string, number>;
  columnOrder: string[];
  columnVisibility: Record<string, boolean>;
  searchValue: string;
  filters: Record<string, any>;
}

// Additional supporting interfaces
export interface TableFilter {
  text: ReactNode;
  value: any;
  children?: TableFilter[];
}

export interface TableColumnValidation {
  required?: boolean;
  pattern?: RegExp;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  validator?: (value: any, record: any) => boolean | string | Promise<boolean | string>;
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
  onChange?: (filters: Record<string, any>) => void;
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
  groupBy?: string | ((item: any) => string);
  renderGroup?: (group: string, items: any[]) => ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export interface ListActionConfig {
  enabled?: boolean;
  actions?: ListAction[];
  onAction?: (action: string, item: any, index: number) => void;
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
  checkedNodesPositions?: any[];
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
  data: any[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number;
  pointHoverRadius?: number;
  [key: string]: any;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  aspectRatio?: number;
  resizeDelay?: number;
  devicePixelRatio?: number;
  locale?: string;
  interaction?: any;
  onHover?: (event: any, elements: any[]) => void;
  onClick?: (event: any, elements: any[]) => void;
  onResize?: (chart: any, size: any) => void;
  plugins?: any;
  scales?: any;
  elements?: any;
  layout?: any;
  animation?: any;
  animations?: any;
  transitions?: any;
  [key: string]: any;
}

export interface ChartTooltipConfig {
  enabled?: boolean;
  position?: string;
  filter?: (tooltipItem: any) => boolean;
  itemSort?: (a: any, b: any) => number;
  external?: (context: any) => void;
  callbacks?: any;
  displayColors?: boolean;
  backgroundColor?: string;
  titleColor?: string;
  bodyColor?: string;
  borderColor?: string;
  borderWidth?: number;
  cornerRadius?: number;
  caretPadding?: number;
  caretSize?: number;
  titleFont?: any;
  bodyFont?: any;
  footerFont?: any;
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
  onClick?: (event: any, legendItem: any, legend: any) => void;
  onHover?: (event: any, legendItem: any, legend: any) => void;
  onLeave?: (event: any, legendItem: any, legend: any) => void;
  reverse?: boolean;
  labels?: any;
  rtl?: boolean;
  textDirection?: string;
  title?: any;
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
  title?: any;
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
  ticks?: any;
  grid?: any;
  border?: any;
  time?: any;
  adapters?: any;
  afterBuildTicks?: (scale: any) => void;
  beforeCalculateLabelRotation?: (scale: any) => void;
  afterCalculateLabelRotation?: (scale: any) => void;
  beforeFit?: (scale: any) => void;
  afterFit?: (scale: any) => void;
  afterTickToLabelConversion?: (scale: any) => void;
  beforeSetDimensions?: (scale: any) => void;
  afterSetDimensions?: (scale: any) => void;
  beforeDataLimits?: (scale: any) => void;
  afterDataLimits?: (scale: any) => void;
  beforeTickToLabelConversion?: (scale: any) => void;
  beforeUpdate?: (scale: any) => void;
  afterUpdate?: (scale: any) => void;
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
  rangeMin?: any;
  rangeMax?: any;
  speed?: number;
  threshold?: number;
  sensitivity?: number;
  onZoom?: (context: any) => void;
  onZoomComplete?: (context: any) => void;
  onZoomRejected?: (context: any) => void;
  onZoomStart?: (context: any) => void;
}

export interface ChartBrushConfig {
  enabled?: boolean;
  mode?: 'x' | 'y' | 'xy';
  onBrush?: (domain: any) => void;
  onBrushEnd?: (domain: any) => void;
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
  render?: (data: any[]) => ReactNode;
  columns?: TableSummaryColumn[];
}

export interface TableSummaryColumn {
  key: string;
  aggregate: 'sum' | 'avg' | 'min' | 'max' | 'count' | ((values: any[]) => any);
  format?: (value: any) => ReactNode;
  precision?: number;
}

export interface ListFilter {
  key: string;
  label: string;
  type: 'select' | 'multiselect' | 'range' | 'text' | 'date';
  options?: { label: string; value: any }[];
  value?: any;
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
  onClick?: (item: any, index: number) => void;
  disabled?: boolean | ((item: any, index: number) => boolean);
  visible?: boolean | ((item: any, index: number) => boolean);
}

export type ChartType = 'line' | 'bar' | 'pie' | 'doughnut' | 'scatter' | 'bubble' | 'radar' | 'polarArea' | 'area';