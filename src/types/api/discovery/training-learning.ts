/**
 * Discovery Training and Learning API Types
 * 
 * Type definitions for AI model training, learning operations,
 * and model management within the discovery flow.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  GetRequest,
  GetResponse,
  MultiTenantContext
} from '../shared';

// Training and Learning APIs
export interface GetTrainingProgressRequest extends GetRequest {
  flowId: string;
  modelId?: string;
  includeMetrics?: boolean;
  includeLogs?: boolean;
  includeHistory?: boolean;
}

export interface GetTrainingProgressResponse extends GetResponse<TrainingProgressDetail> {
  data: TrainingProgressDetail;
  performanceMetrics?: TrainingMetrics;
  logs?: TrainingLog[];
  history?: TrainingHistory[];
}

export interface StartTrainingRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  modelConfig: ModelConfiguration;
  trainingConfig: TrainingConfiguration;
  datasetConfig: DatasetConfiguration;
}

export interface StartTrainingResponse extends BaseApiResponse<TrainingJob> {
  data: TrainingJob;
  trainingId: string;
  estimatedDuration?: number;
  resourceAllocation?: ResourceAllocation;
}

export interface StopTrainingRequest extends BaseApiRequest {
  trainingId: string;
  context: MultiTenantContext;
  saveProgress?: boolean;
  reason?: string;
}

export interface StopTrainingResponse extends BaseApiResponse<TrainingStopResult> {
  data: TrainingStopResult;
  finalMetrics?: TrainingMetrics;
  savedModel?: ModelInfo;
}

// Training and Learning Models
export interface TrainingProgressDetail {
  trainingId: string;
  flowId: string;
  modelId: string;
  status: TrainingStatus;
  currentEpoch: number;
  totalEpochs: number;
  progress: number;
  startTime: string;
  estimatedEndTime?: string;
  currentLoss: number;
  bestLoss: number;
  currentAccuracy: number;
  bestAccuracy: number;
  learningRate: number;
  batchSize: number;
  samplesProcessed: number;
  totalSamples: number;
  validationMetrics?: ValidationMetrics;
  earlyStoppingCriteria?: EarlyStoppingCriteria;
  checkpoints: TrainingCheckpoint[];
}

export interface TrainingMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  loss: number;
  validationAccuracy: number;
  validationLoss: number;
  confusionMatrix: number[][];
  learningCurve: LearningCurvePoint[];
  performanceByClass: Record<string, ClassMetrics>;
  convergenceStatus: ConvergenceStatus;
}

export interface ValidationMetrics {
  accuracy: number;
  loss: number;
  precision: number;
  recall: number;
  f1Score: number;
  auc: number;
  confusionMatrix: number[][];
}

export interface EarlyStoppingCriteria {
  monitor: string;
  patience: number;
  threshold: number;
  mode: 'min' | 'max';
  enabled: boolean;
}

export interface TrainingCheckpoint {
  epoch: number;
  timestamp: string;
  loss: number;
  accuracy: number;
  modelPath: string;
  size: number;
  description?: string;
}

export interface LearningCurvePoint {
  epoch: number;
  trainLoss: number;
  validationLoss: number;
  trainAccuracy: number;
  validationAccuracy: number;
  timestamp: string;
}

export interface ClassMetrics {
  precision: number;
  recall: number;
  f1Score: number;
  support: number;
  accuracy: number;
}

export interface ConvergenceStatus {
  converged: boolean;
  plateauDetected: boolean;
  lastImprovement: number;
  stabilityScore: number;
  recommendation: 'continue' | 'stop' | 'adjust_lr' | 'regularize';
}

export interface TrainingLog {
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  epoch?: number;
  metrics?: Record<string, number>;
  context?: Record<string, any>;
}

export interface TrainingHistory {
  trainingId: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  status: TrainingStatus;
  finalMetrics?: TrainingMetrics;
  modelVersion: string;
  datasetVersion: string;
  configHash: string;
  notes?: string;
}

export interface ModelConfiguration {
  modelType: ModelType;
  architecture: ModelArchitecture;
  hyperparameters: ModelHyperparameters;
  features: FeatureConfiguration;
  outputClasses: string[];
  pretrainedModel?: string;
  customLayers?: LayerConfiguration[];
}

export interface ModelArchitecture {
  layers: LayerDefinition[];
  inputShape: number[];
  outputShape: number[];
  totalParameters: number;
  trainableParameters: number;
}

export interface ModelHyperparameters {
  learningRate: number;
  batchSize: number;
  epochs: number;
  optimizer: OptimizerConfig;
  lossFunction: string;
  metrics: string[];
  regularization?: RegularizationConfig;
  dropout?: number;
}

export interface OptimizerConfig {
  type: 'adam' | 'sgd' | 'rmsprop' | 'adagrad';
  parameters: Record<string, number>;
}

export interface RegularizationConfig {
  l1?: number;
  l2?: number;
  elasticNet?: ElasticNetConfig;
}

export interface ElasticNetConfig {
  l1Ratio: number;
  alpha: number;
}

export interface FeatureConfiguration {
  inputFeatures: FeatureDefinition[];
  targetFeature: FeatureDefinition;
  preprocessing: PreprocessingConfig;
  featureEngineering?: FeatureEngineeringConfig;
}

export interface FeatureDefinition {
  name: string;
  type: FeatureType;
  encoding: EncodingType;
  scaling?: ScalingType;
  required: boolean;
  description?: string;
}

export interface PreprocessingConfig {
  normalization: boolean;
  standardization: boolean;
  outlierRemoval: boolean;
  missingValueStrategy: MissingValueStrategy;
  categoricalEncoding: CategoricalEncodingStrategy;
}

export interface FeatureEngineeringConfig {
  polynomialFeatures?: PolynomialConfig;
  interactions?: InteractionConfig;
  transformations?: TransformationConfig[];
}

export interface LayerConfiguration {
  type: LayerType;
  parameters: Record<string, any>;
  activation?: ActivationType;
  regularization?: RegularizationConfig;
}

export interface LayerDefinition {
  name: string;
  type: LayerType;
  inputShape?: number[];
  outputShape: number[];
  parameters: number;
  activation?: ActivationType;
}

export interface TrainingConfiguration {
  batchSize: number;
  epochs: number;
  validationSplit: number;
  shuffle: boolean;
  earlyStoppingConfig?: EarlyStoppingConfig;
  checkpointConfig?: CheckpointConfig;
  schedulerConfig?: SchedulerConfig;
  augmentationConfig?: AugmentationConfig;
}

export interface EarlyStoppingConfig {
  monitor: string;
  patience: number;
  threshold: number;
  mode: 'min' | 'max';
  restoreBestWeights: boolean;
}

export interface CheckpointConfig {
  saveFrequency: number;
  saveBestOnly: boolean;
  monitor: string;
  mode: 'min' | 'max';
  saveFormat: 'full' | 'weights_only';
}

export interface SchedulerConfig {
  type: SchedulerType;
  parameters: Record<string, any>;
}

export interface AugmentationConfig {
  enabled: boolean;
  techniques: AugmentationTechnique[];
  probability: number;
}

export interface DatasetConfiguration {
  trainingDataPath: string;
  validationDataPath?: string;
  testDataPath?: string;
  dataFormat: DataFormat;
  sampling: SamplingConfig;
  balancing?: BalancingConfig;
  qualityChecks: QualityCheckConfig;
}

export interface SamplingConfig {
  strategy: SamplingStrategy;
  sampleSize?: number;
  stratify: boolean;
  randomSeed: number;
}

export interface BalancingConfig {
  method: BalancingMethod;
  targetRatio?: number;
  oversampleMinority: boolean;
  undersampleMajority: boolean;
}

export interface QualityCheckConfig {
  duplicateRemoval: boolean;
  outlierDetection: boolean;
  consistencyChecks: boolean;
  completenessThreshold: number;
  qualityThreshold: number;
}

export interface TrainingJob {
  id: string;
  flowId: string;
  status: TrainingStatus;
  modelConfig: ModelConfiguration;
  trainingConfig: TrainingConfiguration;
  datasetConfig: DatasetConfiguration;
  startTime: string;
  endTime?: string;
  estimatedDuration: number;
  actualDuration?: number;
  resourceAllocation: ResourceAllocation;
  priority: JobPriority;
  createdBy: string;
  notes?: string;
}

export interface ResourceAllocation {
  cpuCores: number;
  memoryGB: number;
  gpuCount: number;
  gpuType?: string;
  storageGB: number;
  estimatedCost: number;
  maxDuration: number;
}

export interface TrainingStopResult {
  trainingId: string;
  stopped: boolean;
  reason: StopReason;
  finalEpoch: number;
  savedModel: boolean;
  modelPath?: string;
  finalMetrics?: TrainingMetrics;
  duration: number;
  resourceUsage: ResourceUsage;
}

export interface ResourceUsage {
  cpuHours: number;
  memoryGBHours: number;
  gpuHours: number;
  storageGBHours: number;
  totalCost: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  type: ModelType;
  size: number;
  accuracy: number;
  trainingDate: string;
  modelPath: string;
  configPath: string;
  metadata: ModelMetadata;
}

export interface ModelMetadata {
  framework: string;
  frameworkVersion: string;
  pythonVersion: string;
  dependencies: Record<string, string>;
  trainingDuration: number;
  datasetFingerprint: string;
  performanceBenchmarks: PerformanceBenchmark[];
}

export interface PerformanceBenchmark {
  metric: string;
  value: number;
  context: string;
  timestamp: string;
}

// Configuration Interfaces
export interface PolynomialConfig {
  degree: number;
  interactionOnly: boolean;
  includeBias: boolean;
}

export interface InteractionConfig {
  maxDegree: number;
  includeOriginal: boolean;
  specificPairs?: string[][];
}

export interface TransformationConfig {
  type: TransformationType;
  parameters: Record<string, any>;
  applyTo: string[];
}

// Enums and Types
export type TrainingStatus = 'queued' | 'initializing' | 'running' | 'completed' | 'failed' | 'stopped' | 'paused';
export type ModelType = 'classification' | 'regression' | 'clustering' | 'neural_network' | 'ensemble' | 'transformer';
export type FeatureType = 'numerical' | 'categorical' | 'boolean' | 'text' | 'datetime' | 'binary';
export type EncodingType = 'one_hot' | 'label' | 'target' | 'binary' | 'ordinal' | 'embedding';
export type ScalingType = 'standard' | 'minmax' | 'robust' | 'quantile' | 'power' | 'none';
export type MissingValueStrategy = 'drop' | 'mean' | 'median' | 'mode' | 'forward_fill' | 'backward_fill' | 'interpolate';
export type CategoricalEncodingStrategy = 'one_hot' | 'label' | 'target' | 'leave_one_out' | 'catboost';
export type LayerType = 'dense' | 'conv1d' | 'conv2d' | 'lstm' | 'gru' | 'attention' | 'embedding' | 'dropout' | 'batch_norm';
export type ActivationType = 'relu' | 'sigmoid' | 'tanh' | 'softmax' | 'leaky_relu' | 'elu' | 'swish' | 'linear';
export type SchedulerType = 'step' | 'exponential' | 'cosine' | 'plateau' | 'linear' | 'polynomial';
export type AugmentationTechnique = 'noise' | 'scaling' | 'rotation' | 'shift' | 'dropout' | 'mixup';
export type DataFormat = 'csv' | 'json' | 'parquet' | 'avro' | 'orc' | 'feather';
export type SamplingStrategy = 'random' | 'stratified' | 'systematic' | 'cluster' | 'reservoir';
export type BalancingMethod = 'oversample' | 'undersample' | 'smote' | 'adasyn' | 'tomek' | 'enn';
export type JobPriority = 'low' | 'normal' | 'high' | 'urgent';
export type StopReason = 'user_requested' | 'completed' | 'error' | 'timeout' | 'resource_limit' | 'early_stopping';
export type TransformationType = 'log' | 'sqrt' | 'square' | 'reciprocal' | 'box_cox' | 'yeo_johnson';