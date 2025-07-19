/**
 * Discovery Analysis Hook Types
 * 
 * Type definitions for data analysis hooks including analysis types,
 * findings, comparisons, and training configurations.
 */

import { BaseHookParams, BaseHookReturn } from './base-hooks';
import { ReactNode } from 'react';

// Analysis Types
export interface AnalysisType {
  id: string;
  name: string;
  description?: string;
  parameters?: AnalysisParameter[];
  icon?: ReactNode;
}

export interface AnalysisParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect';
  label: string;
  description?: string;
  required?: boolean;
  defaultValue?: any;
  options?: { value: any; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}

export interface AnalysisFinding {
  type: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
  impact: string;
  confidence: number;
  metadata?: Record<string, any>;
}

export interface AnalysisFilter {
  field: string;
  operator: string;
  value: any;
  label?: string;
  enabled?: boolean;
}

export interface AnalysisComparison {
  analyses: CrewAnalysis[];
  similarities: AnalysisSimilarity[];
  differences: AnalysisDifference[];
  summary: string;
  confidence: number;
}

export interface AnalysisSimilarity {
  field: string;
  value: any;
  confidence: number;
  description: string;
}

export interface AnalysisDifference {
  field: string;
  values: Record<string, any>;
  significance: 'high' | 'medium' | 'low';
  description: string;
}

// Training Types
export interface TrainingProgress {
  totalSamples: number;
  processedSamples: number;
  accuracy: number;
  lastTrainingRun: string;
  modelVersion: string;
  status: 'idle' | 'training' | 'paused' | 'completed' | 'failed';
  elapsedTime: number;
  estimatedTimeRemaining?: number;
  currentEpoch: number;
  totalEpochs: number;
  loss: number;
  validationLoss?: number;
  metrics: Record<string, number>;
}

export interface TrainingMetrics {
  accuracy: number;
  loss: number;
  validationAccuracy?: number;
  validationLoss?: number;
  precision?: number;
  recall?: number;
  f1Score?: number;
  customMetrics?: Record<string, number>;
  history: MetricHistory[];
}

export interface MetricHistory {
  epoch: number;
  timestamp: string;
  metrics: Record<string, number>;
}

export interface TrainingLog {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  message: string;
  source?: string;
  metadata?: Record<string, any>;
}

export interface TrainingStatus {
  status: 'idle' | 'training' | 'paused' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  progress: number;
  currentEpoch: number;
  totalEpochs: number;
  message?: string;
}

export interface TrainingConfig {
  modelType: string;
  datasetId: string;
  hyperparameters: Hyperparameters;
  validationConfig: ValidationConfig;
  outputConfig: OutputConfig;
  schedulingConfig: SchedulingConfig;
  monitoringConfig: MonitoringConfig;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  description?: string;
  architecture: string;
  parameters: number;
  trainingData?: string;
  accuracy?: number;
  size: number;
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  size: number;
  recordCount: number;
  features: number;
  labels?: string[];
  splitRatio?: { train: number; validation: number; test: number };
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface Hyperparameters {
  learningRate: number;
  batchSize: number;
  epochs: number;
  optimizer: string;
  momentum?: number;
  weightDecay?: number;
  dropout?: number;
  hiddenLayers?: number;
  hiddenUnits?: number;
  activationFunction?: string;
  lossFunction?: string;
  customParameters?: Record<string, any>;
}

export interface ValidationConfig {
  enabled: boolean;
  splitRatio: number;
  stratified: boolean;
  crossValidation: boolean;
  folds?: number;
  metrics: string[];
  earlyStoppingEnabled: boolean;
  patience?: number;
  minDelta?: number;
}

export interface OutputConfig {
  saveModel: boolean;
  saveMetrics: boolean;
  saveLogs: boolean;
  outputPath: string;
  format: 'pickle' | 'onnx' | 'tensorflow' | 'pytorch';
  compression: boolean;
}

export interface SchedulingConfig {
  priority: 'low' | 'medium' | 'high';
  maxDuration: number;
  retryAttempts: number;
  scheduling: 'immediate' | 'queued' | 'scheduled';
  scheduledTime?: string;
}

export interface MonitoringConfig {
  enabled: boolean;
  metricsEnabled: boolean;
  logsEnabled: boolean;
  alertsEnabled: boolean;
  alertThresholds: Record<string, number>;
  notificationChannels: string[];
}

export interface ModelComparison {
  models: ModelInfo[];
  metrics: ModelComparisonMetric[];
  summary: string;
  recommendation: string;
  confidence: number;
}

export interface ModelComparisonMetric {
  name: string;
  values: Record<string, number>;
  winner: string;
  significance: 'high' | 'medium' | 'low';
  description: string;
}

// Placeholder for CrewAnalysis - needs to be imported from appropriate API types
export interface CrewAnalysis {
  id: string;
  name: string;
  // Add other properties as needed
}