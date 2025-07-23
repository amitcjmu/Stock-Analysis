/**
 * Advanced Form Component Types
 * 
 * Types for sliders, file uploads, and other advanced form components.
 */

import type { ReactNode, RefObject } from 'react';
import type { BaseFormProps, UploadFileActions } from './base-types';

// Slider component types
export interface SliderProps extends BaseFormProps {
  value?: number | number[];
  defaultValue?: number | number[];
  min?: number;
  max?: number;
  step?: number;
  marks?: boolean | SliderMark[];
  range?: boolean;
  reverse?: boolean;
  vertical?: boolean;
  included?: boolean;
  disabled?: boolean;
  dots?: boolean;
  tooltip?: boolean | 'auto' | 'always';
  tooltipFormatter?: (value: number) => ReactNode;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  onChange?: (value: number | number[]) => void;
  onAfterChange?: (value: number | number[]) => void;
  onBeforeChange?: (value: number | number[]) => void;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  trackStyle?: React.CSSProperties | React.CSSProperties[];
  railStyle?: React.CSSProperties;
  handleStyle?: React.CSSProperties | React.CSSProperties[];
  dotStyle?: React.CSSProperties;
  activeDotStyle?: React.CSSProperties;
  markStyle?: React.CSSProperties;
  className?: string;
  trackClassName?: string;
  railClassName?: string;
  handleClassName?: string;
  dotClassName?: string;
  markClassName?: string;
  sliderRef?: RefObject<HTMLDivElement>;
}

// File upload component types
export interface FileUploadProps extends BaseFormProps {
  accept?: string[];
  multiple?: boolean;
  maxSize?: number;
  maxFiles?: number;
  minSize?: number;
  preventDropOnDocument?: boolean;
  noClick?: boolean;
  noKeyboard?: boolean;
  noDrag?: boolean;
  noDragEventsBubbling?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  value?: File[];
  defaultValue?: File[];
  onChange?: (files: File[]) => void;
  onDrop?: (acceptedFiles: File[], rejectedFiles: FileRejection[]) => void;
  onDropAccepted?: (files: File[]) => void;
  onDropRejected?: (fileRejections: FileRejection[]) => void;
  onFileDialogCancel?: () => void;
  onFileDialogOpen?: () => void;
  onError?: (error: Error) => void;
  validator?: (file: File) => FileError | FileError[] | null;
  getFilesFromEvent?: (event: DragEvent | React.ChangeEvent<HTMLInputElement>) => Promise<File[]>;
  onDragEnter?: (event: React.DragEvent) => void;
  onDragLeave?: (event: React.DragEvent) => void;
  onDragOver?: (event: React.DragEvent) => void;
  useFsAccessApi?: boolean;
  autoUpload?: boolean;
  showPreview?: boolean;
  showProgress?: boolean;
  previewComponent?: React.ComponentType<FilePreviewProps>;
  uploadComponent?: React.ComponentType<FileUploadItemProps>;
  children?: ReactNode | ((props: FileUploadRenderProps) => ReactNode);
  placeholder?: ReactNode;
  uploadText?: string;
  browseText?: string;
  dragText?: string;
  dropText?: string;
  removeText?: string;
  retryText?: string;
  uploadIcon?: ReactNode;
  removeIcon?: ReactNode;
  retryIcon?: ReactNode;
  errorIcon?: ReactNode;
  successIcon?: ReactNode;
  loadingIcon?: ReactNode;
  variant?: 'default' | 'button' | 'avatar' | 'banner';
  layout?: 'vertical' | 'horizontal';
  listType?: 'text' | 'picture' | 'picture-card' | 'picture-circle';
  action?: string;
  method?: 'post' | 'put' | 'patch';
  headers?: Record<string, string>;
  withCredentials?: boolean;
  data?: Record<string, unknown> | ((file: File) => Record<string, unknown>);
  beforeUpload?: (file: File, fileList: File[]) => boolean | Promise<boolean>;
  customRequest?: (options: UploadRequestOption) => void;
  directory?: boolean;
  openFileDialogOnClick?: boolean;
  fileList?: UploadFile[];
  defaultFileList?: UploadFile[];
  onRemove?: (file: UploadFile) => boolean | Promise<boolean>;
  onPreview?: (file: UploadFile) => void;
  onDownload?: (file: UploadFile) => void;
  transformFile?: (file: File) => string | Blob | File | Promise<string | Blob | File>;
  iconRender?: (file: UploadFile, listType?: string) => ReactNode;
  isImageUrl?: (file: UploadFile) => boolean;
  progress?: UploadProgressProps;
  itemRender?: (originNode: ReactNode, file: UploadFile, fileList: UploadFile[], actions: UploadFileActions) => ReactNode;
  maxCount?: number;
  capture?: boolean | 'user' | 'environment';
  showUploadList?: boolean | ShowUploadListInterface;
  containerRef?: RefObject<HTMLDivElement>;
}

// Supporting types
export interface SliderMark {
  value: number;
  label?: ReactNode;
  style?: React.CSSProperties;
}

export interface FileRejection {
  file: File;
  errors: FileError[];
}

export interface FileError {
  code: string;
  message: string;
}

export interface FilePreviewProps {
  file: File | UploadFile;
  onRemove?: () => void;
  onPreview?: () => void;
}

export interface FileUploadItemProps {
  file: UploadFile;
  onRemove?: () => void;
  onRetry?: () => void;
  onPreview?: () => void;
  onDownload?: () => void;
}

export interface FileUploadRenderProps {
  isDragActive: boolean;
  isDragAccept: boolean;
  isDragReject: boolean;
  isFocused: boolean;
  acceptedFiles: File[];
  rejectedFiles: FileRejection[];
  getRootProps: () => Record<string, unknown>;
  getInputProps: () => Record<string, unknown>;
  open: () => void;
}

export interface UploadFile {
  uid: string;
  name: string;
  status?: 'uploading' | 'done' | 'error' | 'removed';
  url?: string;
  preview?: string;
  originFileObj?: File;
  size?: number;
  type?: string;
  percent?: number;
  thumbUrl?: string;
  error?: Error;
  response?: unknown;
  linkProps?: Record<string, unknown>;
}

export interface UploadRequestOption {
  action: string;
  filename?: string;
  file: File;
  data?: Record<string, unknown>;
  headers?: Record<string, string>;
  withCredentials?: boolean;
  onProgress?: (event: UploadProgressEvent) => void;
  onSuccess?: (body: unknown, xhr: XMLHttpRequest) => void;
  onError?: (error: Error) => void;
}

export interface UploadProgressEvent {
  percent: number;
}

export interface UploadProgressProps {
  strokeColor?: string;
  strokeWidth?: number;
  format?: (percent: number, successPercent?: number) => ReactNode;
  showInfo?: boolean;
}

export interface ShowUploadListInterface {
  showRemoveIcon?: boolean;
  showPreviewIcon?: boolean;
  showDownloadIcon?: boolean;
  removeIcon?: ReactNode;
  downloadIcon?: ReactNode;
  previewIcon?: ReactNode;
}