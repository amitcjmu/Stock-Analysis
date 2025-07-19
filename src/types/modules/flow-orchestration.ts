/**
 * Flow Orchestration Module
 * 
 * TypeScript module boundaries for Flow Orchestration backend services.
 * Provides type definitions for CrewAI flows, agent coordination, and flow state management.
 * 
 * This file has been modularized for better maintainability.
 * Individual modules are located in ./flow-orchestration/ directory.
 */

// Re-export everything from the modularized structure
export * from './flow-orchestration';

// For backward compatibility, also provide direct access to key types
export type {
  AgentConfiguration,
  LLMConfiguration, 
  FlowExecutionContext,
  FlowOrchestration
} from './flow-orchestration';