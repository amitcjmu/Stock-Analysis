/**
 * Collection Flow API - Main Entry Point
 *
 * This module provides a unified API for all collection flow operations using the composition pattern.
 * All 49 methods from the original CollectionFlowApi class are preserved for 100% backward compatibility.
 *
 * Architecture:
 * - FlowsApi: Flow CRUD operations (create, read, update, delete, execute)
 * - QuestionnairesApi: Questionnaire and gap analysis operations
 * - SubmissionsApi: Response submission and transition operations
 * - ValidationApi: Governance, exceptions, and conflict resolution
 *
 * Usage:
 * ```typescript
 * import { collectionFlowApi } from '@/services/api/collection-flow';
 *
 * // All original methods are available
 * const flow = await collectionFlowApi.createFlow(data);
 * const questionnaires = await collectionFlowApi.getFlowQuestionnaires(flowId);
 * ```
 */

import { FlowsApi } from "./flows";
import { QuestionnairesApi } from "./questionnaires";
import { SubmissionsApi } from "./submissions";
import { ValidationApi } from "./validation";
import { AdaptiveApi } from "./adaptive";

/**
 * Main CollectionFlowAPI class using composition pattern
 * Aggregates all sub-API instances and delegates method calls to them
 */
class CollectionFlowApi {
  private flows: FlowsApi;
  private questionnaires: QuestionnairesApi;
  private submissions: SubmissionsApi;
  private validation: ValidationApi;
  private adaptive: AdaptiveApi;

  constructor() {
    this.flows = new FlowsApi();
    this.questionnaires = new QuestionnairesApi();
    this.submissions = new SubmissionsApi();
    this.validation = new ValidationApi();
    this.adaptive = new AdaptiveApi();
  }

  // ========================================
  // Flow CRUD Operations (FlowsApi)
  // ========================================

  async getFlowStatus() {
    return this.flows.getFlowStatus();
  }

  async createFlow(data: Parameters<FlowsApi["createFlow"]>[0]) {
    return this.flows.createFlow(data);
  }

  async ensureFlow(missing_attributes?: Record<string, string[]>) {
    return this.flows.ensureFlow(missing_attributes);
  }

  async getFlowDetails(flowId: string) {
    return this.flows.getFlowDetails(flowId);
  }

  async getFlowReadiness(flowId: string) {
    return this.flows.getFlowReadiness(flowId);
  }

  async updateFlow(flowId: string, data: Parameters<FlowsApi["updateFlow"]>[1]) {
    return this.flows.updateFlow(flowId, data);
  }

  async getIncompleteFlows() {
    return this.flows.getIncompleteFlows();
  }

  async getFlow(flowId: string) {
    return this.flows.getFlow(flowId);
  }

  async getAllFlows() {
    return this.flows.getAllFlows();
  }

  async continueFlow(flowId: string, resumeContext?: Record<string, unknown>) {
    return this.flows.continueFlow(flowId, resumeContext);
  }

  async deleteFlow(flowId: string, force: boolean = false) {
    return this.flows.deleteFlow(flowId, force);
  }

  async batchDeleteFlows(flowIds: string[], force: boolean = false) {
    return this.flows.batchDeleteFlows(flowIds, force);
  }

  async cleanupFlows(
    expirationHours: number = 72,
    dryRun: boolean = true,
    includeFailedFlows: boolean = true,
    includeCancelledFlows: boolean = true,
  ) {
    return this.flows.cleanupFlows(
      expirationHours,
      dryRun,
      includeFailedFlows,
      includeCancelledFlows,
    );
  }

  async executeFlowPhase(flowId: string, phaseInput?: Record<string, unknown>) {
    return this.flows.executeFlowPhase(flowId, phaseInput);
  }

  async updateFlowApplications(flowId: string, applicationIds: string[]) {
    return this.flows.updateFlowApplications(flowId, applicationIds);
  }

  async getFlowHealthStatus() {
    return this.flows.getFlowHealthStatus();
  }

  async getCleanupRecommendations() {
    return this.flows.getCleanupRecommendations();
  }

  // ========================================
  // Questionnaire Operations (QuestionnairesApi)
  // ========================================

  async getFlowQuestionnaires(flowId: string) {
    return this.questionnaires.getFlowQuestionnaires(flowId);
  }

  async getQuestionnaireResponses(flowId: string, questionnaireId: string) {
    return this.questionnaires.getQuestionnaireResponses(flowId, questionnaireId);
  }

  async getFlowGaps(flowId: string) {
    return this.questionnaires.getFlowGaps(flowId);
  }

  async getCompletenessMetrics(flowId: string) {
    return this.questionnaires.getCompletenessMetrics(flowId);
  }

  async refreshCompletenessMetrics(flowId: string, categoryId?: string) {
    return this.questionnaires.refreshCompletenessMetrics(flowId, categoryId);
  }

  async getGaps(flowId: string) {
    return this.questionnaires.getGaps(flowId);
  }

  async scanGaps(flowId: string, selectedAssetIds: string[]) {
    return this.questionnaires.scanGaps(flowId, selectedAssetIds);
  }

  async analyzeGaps(flowId: string, gaps: Parameters<QuestionnairesApi["analyzeGaps"]>[1], selectedAssetIds: string[]) {
    return this.questionnaires.analyzeGaps(flowId, gaps, selectedAssetIds);
  }

  async getEnhancementProgress(flowId: string) {
    return this.questionnaires.getEnhancementProgress(flowId);
  }

  async updateGaps(flowId: string, updates: Parameters<QuestionnairesApi["updateGaps"]>[1]) {
    return this.questionnaires.updateGaps(flowId, updates);
  }

  // ========================================
  // Submission Operations (SubmissionsApi)
  // ========================================

  async submitQuestionnaireResponse(
    flowId: string,
    questionnaireId: string,
    requestData: Parameters<SubmissionsApi["submitQuestionnaireResponse"]>[2],
  ) {
    return this.submissions.submitQuestionnaireResponse(flowId, questionnaireId, requestData);
  }

  async submitBulkResponses(
    flowId: string,
    questionnaireId: string,
    responses: Record<string, unknown>,
  ) {
    return this.submissions.submitBulkResponses(flowId, questionnaireId, responses);
  }

  async transitionToAssessment(flowId: string) {
    return this.submissions.transitionToAssessment(flowId);
  }

  async getMaintenanceWindows(scopeType?: string, scopeId?: string) {
    return this.submissions.getMaintenanceWindows(scopeType, scopeId);
  }

  async createMaintenanceWindow(data: Parameters<SubmissionsApi["createMaintenanceWindow"]>[0]) {
    return this.submissions.createMaintenanceWindow(data);
  }

  async updateMaintenanceWindow(
    windowId: string,
    data: Parameters<SubmissionsApi["updateMaintenanceWindow"]>[1],
  ) {
    return this.submissions.updateMaintenanceWindow(windowId, data);
  }

  async deleteMaintenanceWindow(windowId: string) {
    return this.submissions.deleteMaintenanceWindow(windowId);
  }

  async searchTechnologyOptions(query: string, category?: string) {
    return this.submissions.searchTechnologyOptions(query, category);
  }

  async normalizeTechnologyEntry(vendorName: string, productName: string, version?: string) {
    return this.submissions.normalizeTechnologyEntry(vendorName, productName, version);
  }

  async getScopeTargets(scopeType: "tenant" | "application" | "asset") {
    return this.submissions.getScopeTargets(scopeType);
  }

  async getVendorProducts(searchQuery?: string, category?: string) {
    return this.submissions.getVendorProducts(searchQuery, category);
  }

  async createVendorProduct(data: Parameters<SubmissionsApi["createVendorProduct"]>[0]) {
    return this.submissions.createVendorProduct(data);
  }

  async updateVendorProduct(
    productId: string,
    data: Parameters<SubmissionsApi["updateVendorProduct"]>[1],
  ) {
    return this.submissions.updateVendorProduct(productId, data);
  }

  async deleteVendorProduct(productId: string) {
    return this.submissions.deleteVendorProduct(productId);
  }

  async normalizeVendorProduct(vendorName: string, productName: string, version?: string) {
    return this.submissions.normalizeVendorProduct(vendorName, productName, version);
  }

  // ========================================
  // Validation Operations (ValidationApi)
  // ========================================

  async getGovernanceRequirements() {
    return this.validation.getGovernanceRequirements();
  }

  async getMigrationExceptions() {
    return this.validation.getMigrationExceptions();
  }

  async createMigrationException(data: Parameters<ValidationApi["createMigrationException"]>[0]) {
    return this.validation.createMigrationException(data);
  }

  async getApprovalRequests() {
    return this.validation.getApprovalRequests();
  }

  async createApprovalRequest(data: Parameters<ValidationApi["createApprovalRequest"]>[0]) {
    return this.validation.createApprovalRequest(data);
  }

  async getMaintenanceConflicts() {
    return this.validation.getMaintenanceConflicts();
  }

  async startAssetCollection(data: Parameters<ValidationApi["startAssetCollection"]>[0]) {
    return this.validation.startAssetCollection(data);
  }

  async getAssetConflicts(asset_id: string) {
    return this.validation.getAssetConflicts(asset_id);
  }

  async resolveAssetConflict(
    asset_id: string,
    field_name: string,
    resolution: Parameters<ValidationApi["resolveAssetConflict"]>[2],
  ) {
    return this.validation.resolveAssetConflict(asset_id, field_name, resolution);
  }

  // ========================================
  // Adaptive Questionnaire Operations (AdaptiveApi)
  // ========================================

  async getFilteredQuestions(request: Parameters<AdaptiveApi["getFilteredQuestions"]>[0]) {
    return this.adaptive.getFilteredQuestions(request);
  }

  async handleDependencyChange(request: Parameters<AdaptiveApi["handleDependencyChange"]>[0]) {
    return this.adaptive.handleDependencyChange(request);
  }

  async previewBulkAnswers(request: Parameters<AdaptiveApi["previewBulkAnswers"]>[0]) {
    return this.adaptive.previewBulkAnswers(request);
  }

  async submitBulkAnswers(request: Parameters<AdaptiveApi["submitBulkAnswers"]>[0]) {
    return this.adaptive.submitBulkAnswers(request);
  }

  async analyzeImportFile(file: File, import_type: "application" | "server" | "database") {
    return this.adaptive.analyzeImportFile(file, import_type);
  }

  async executeImport(request: Parameters<AdaptiveApi["executeImport"]>[0]) {
    return this.adaptive.executeImport(request);
  }

  async getImportTaskStatus(task_id: string) {
    return this.adaptive.getImportTaskStatus(task_id);
  }
}

// Export singleton instance for backward compatibility
export const collectionFlowApi = new CollectionFlowApi();

// Export all types for convenience
export type {
  ApiError,
  CollectionFlowConfiguration,
  ValidationRuleConfig,
  NotificationConfig,
  CollectionFlowCreateRequest,
  CollectionFlowResponse,
  CollectionGapAnalysisResponse,
  GapTargetInfo,
  QuestionnaireQuestion,
  ConditionalLogic,
  QuestionnaireResponse,
  FlowUpdateData,
  AdaptiveQuestionnaireResponse,
  CollectionFlowStatusResponse,
  TransitionResult,
  DataGap,
  GapScanSummary,
  ScanGapsResponse,
  AnalysisSummary,
  AnalyzeGapsResponse,
  GapUpdate,
  UpdateGapsResponse,
  CollectionFlow,
  CleanupResult,
  FlowContinueResult,
  MaintenanceWindow,
  VendorProduct,
  CompletenessMetrics,
} from "./types";

// Export adaptive questionnaire types
export type {
  QuestionDetail,
  DynamicQuestionsRequest,
  DynamicQuestionsResponse,
  DependencyChangeRequest,
  DependencyChangeResponse,
  AnswerInput,
  BulkAnswerPreviewRequest,
  ConflictDetail,
  BulkAnswerPreviewResponse,
  BulkAnswerSubmitRequest,
  ChunkError,
  BulkAnswerSubmitResponse,
  FieldMappingSuggestion,
  ImportAnalysisResponse,
  ImportExecutionRequest,
  ImportTaskResponse,
  ImportTaskDetailResponse,
} from "./adaptive";

// Export sub-API classes for advanced usage
export { FlowsApi, QuestionnairesApi, SubmissionsApi, ValidationApi, AdaptiveApi };
