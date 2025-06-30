/**
 * Session to Flow Migration Utilities
 * 
 * Provides utilities for migrating from session-based to flow-based storage
 * and handling backward compatibility during the transition period.
 */

import { MigrationContext, FlowIdentifier, LegacySessionData, FlowData } from '../../types/discovery';

export class SessionToFlowMigration {
  private static readonly FEATURE_FLAG_KEY = 'REACT_APP_USE_FLOW_ID';
  private static readonly MIGRATION_COMPLETE_KEY = 'session_to_flow_migration_complete';
  
  // localStorage key mappings
  private static readonly SESSION_KEYS = {
    CURRENT_SESSION: 'current_discovery_session_id',
    AUTH_SESSION: 'auth_session',
    USER_CONTEXT: 'user_context_selection',
    FLOW_STATE: 'discovery_flow_state',
    PROCESSING_STATUS: 'processing_status'
  };
  
  private static readonly FLOW_KEYS = {
    CURRENT_FLOW: 'current_discovery_flow_id',
    AUTH_SESSION: 'auth_session', // Keep the same for auth
    USER_CONTEXT: 'user_context_selection', // Keep the same for context
    FLOW_STATE: 'discovery_flow_state', // Keep the same
    PROCESSING_STATUS: 'processing_status' // Keep the same
  };

  /**
   * Check if flow ID should be used based on feature flag
   */
  static shouldUseFlowId(): boolean {
    // Check environment variable
    if (process.env.REACT_APP_USE_FLOW_ID === 'true') {
      return true;
    }
    
    // Check localStorage override
    const localOverride = localStorage.getItem('use_flow_id_override');
    if (localOverride === 'true') {
      return true;
    }
    
    return false;
  }

  /**
   * Get migration context for current environment
   */
  static getMigrationContext(identifier?: string): MigrationContext {
    const useFlowId = this.shouldUseFlowId();
    
    return {
      useFlowId,
      identifier: identifier || '',
      legacySessionId: useFlowId ? undefined : identifier
    };
  }

  /**
   * Migrate localStorage data from session to flow keys
   */
  static migrateLocalStorage(): void {
    try {
      console.log('🔄 Starting localStorage migration from session to flow keys...');
      
      let migrationCount = 0;
      
      // Migrate current session ID to flow ID
      const currentSessionId = localStorage.getItem(this.SESSION_KEYS.CURRENT_SESSION);
      if (currentSessionId && !localStorage.getItem(this.FLOW_KEYS.CURRENT_FLOW)) {
        // Try to convert session ID to flow ID format
        const flowId = this.convertSessionToFlowId(currentSessionId);
        localStorage.setItem(this.FLOW_KEYS.CURRENT_FLOW, flowId);
        migrationCount++;
        console.log(`✅ Migrated current session ID to flow ID: ${currentSessionId} -> ${flowId}`);
      }
      
      // Migrate any session-prefixed keys
      const sessionPrefixKeys = Object.keys(localStorage).filter(key => 
        key.startsWith('session_') || key.includes('_session_')
      );
      
      for (const sessionKey of sessionPrefixKeys) {
        const flowKey = sessionKey
          .replace(/^session_/, 'flow_')
          .replace(/_session_/, '_flow_');
        
        if (!localStorage.getItem(flowKey)) {
          const value = localStorage.getItem(sessionKey);
          if (value) {
            localStorage.setItem(flowKey, value);
            migrationCount++;
            console.log(`✅ Migrated localStorage key: ${sessionKey} -> ${flowKey}`);
          }
        }
      }
      
      // Mark migration as complete
      localStorage.setItem(this.MIGRATION_COMPLETE_KEY, 'true');
      
      console.log(`🎉 localStorage migration completed. ${migrationCount} keys migrated.`);
      
    } catch (error) {
      console.error('❌ Error during localStorage migration:', error);
    }
  }

  /**
   * Convert session ID to flow ID format if needed
   * Handles various session ID formats and converts them to UUIDs
   */
  static convertSessionToFlowId(sessionId: string): string {
    // If it's already a UUID format, return as-is
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidRegex.test(sessionId)) {
      return sessionId;
    }
    
    // If it starts with 'disc_session_', extract the UUID part
    if (sessionId.startsWith('disc_session_')) {
      const uuidPart = sessionId.replace('disc_session_', '');
      if (uuidRegex.test(uuidPart)) {
        return uuidPart;
      }
    }
    
    // If it's in format 'session-{uuid}', extract UUID
    if (sessionId.startsWith('session-')) {
      const uuidPart = sessionId.replace('session-', '');
      if (uuidRegex.test(uuidPart)) {
        return uuidPart;
      }
    }
    
    // For any other format, generate a deterministic UUID based on session ID
    // This ensures consistency across page reloads
    return this.generateDeterministicUUID(sessionId);
  }

  /**
   * Generate a deterministic UUID from a string
   * This ensures the same session ID always maps to the same flow ID
   */
  static generateDeterministicUUID(input: string): string {
    // Simple hash function to create deterministic UUID
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    
    // Convert hash to UUID format
    const hashStr = Math.abs(hash).toString(16).padStart(8, '0');
    return `${hashStr.slice(0, 8)}-${hashStr.slice(0, 4)}-4${hashStr.slice(1, 4)}-a${hashStr.slice(1, 4)}-${hashStr.slice(0, 12).padStart(12, '0')}`;
  }

  /**
   * Check if migration is needed
   */
  static isMigrationNeeded(): boolean {
    // Check if migration is already complete
    if (localStorage.getItem(this.MIGRATION_COMPLETE_KEY) === 'true') {
      return false;
    }
    
    // Check if there are session-based keys that need migration
    const hasSessionKeys = Object.keys(localStorage).some(key => 
      key.includes('session') && !key.includes('flow')
    );
    
    return hasSessionKeys;
  }

  /**
   * Get the appropriate identifier based on migration context
   */
  static getIdentifier(flowId?: string, sessionId?: string): string {
    const context = this.getMigrationContext();
    
    if (context.useFlowId) {
      // Prefer flowId, fallback to converted sessionId
      if (flowId) return flowId;
      if (sessionId) return this.convertSessionToFlowId(sessionId);
      
      // Try to get from localStorage
      const storedFlowId = localStorage.getItem(this.FLOW_KEYS.CURRENT_FLOW);
      if (storedFlowId) return storedFlowId;
      
      const storedSessionId = localStorage.getItem(this.SESSION_KEYS.CURRENT_SESSION);
      if (storedSessionId) return this.convertSessionToFlowId(storedSessionId);
    } else {
      // Use sessionId for backward compatibility
      if (sessionId) return sessionId;
      if (flowId) return flowId; // Keep flowId if that's all we have
      
      // Try to get from localStorage
      const storedSessionId = localStorage.getItem(this.SESSION_KEYS.CURRENT_SESSION);
      if (storedSessionId) return storedSessionId;
      
      const storedFlowId = localStorage.getItem(this.FLOW_KEYS.CURRENT_FLOW);
      if (storedFlowId) return storedFlowId;
    }
    
    throw new Error('No valid identifier found for discovery flow');
  }

  /**
   * Store identifier in appropriate localStorage key
   */
  static storeIdentifier(identifier: string, isFlowId: boolean = this.shouldUseFlowId()): void {
    if (isFlowId) {
      localStorage.setItem(this.FLOW_KEYS.CURRENT_FLOW, identifier);
      console.log(`💾 Stored flow ID: ${identifier}`);
    } else {
      localStorage.setItem(this.SESSION_KEYS.CURRENT_SESSION, identifier);
      console.log(`💾 Stored session ID: ${identifier}`);
    }
  }

  /**
   * Clear all session/flow identifiers from localStorage
   */
  static clearIdentifiers(): void {
    localStorage.removeItem(this.SESSION_KEYS.CURRENT_SESSION);
    localStorage.removeItem(this.FLOW_KEYS.CURRENT_FLOW);
    console.log('🧹 Cleared all session and flow identifiers');
  }

  /**
   * Log deprecation warning for session ID usage
   */
  static logDeprecationWarning(component: string, sessionId: string): void {
    console.warn(
      `🚨 DEPRECATION WARNING: Component '${component}' is using session_id '${sessionId}'. ` +
      `Please migrate to use flow_id instead. Session-based methods will be removed in Phase 2.`
    );
  }

  /**
   * Create FlowIdentifier object with proper migration handling
   */
  static createFlowIdentifier(identifier: string): FlowIdentifier {
    const context = this.getMigrationContext(identifier);
    
    if (context.useFlowId) {
      return {
        flowId: this.convertSessionToFlowId(identifier),
        sessionId: identifier.includes('session') ? identifier : undefined
      };
    } else {
      return {
        flowId: this.convertSessionToFlowId(identifier),
        sessionId: identifier
      };
    }
  }

  /**
   * Convert legacy session data to flow data
   */
  static convertLegacyData(legacyData: LegacySessionData): FlowData {
    return {
      flowId: this.convertSessionToFlowId(legacyData.sessionId),
      flowData: legacyData.sessionData,
      sessionId: legacyData.sessionId
    };
  }

  /**
   * Get URL parameter name based on migration context
   */
  static getUrlParamName(): string {
    return this.shouldUseFlowId() ? 'flowId' : 'sessionId';
  }

  /**
   * Get localStorage key for current identifier
   */
  static getCurrentIdentifierKey(): string {
    return this.shouldUseFlowId() 
      ? this.FLOW_KEYS.CURRENT_FLOW 
      : this.SESSION_KEYS.CURRENT_SESSION;
  }

  /**
   * Initialize migration on app startup
   */
  static initialize(): void {
    console.log('🚀 Initializing session-to-flow migration...');
    
    // Check migration status
    if (this.isMigrationNeeded()) {
      console.log('📋 Migration needed, starting localStorage migration...');
      this.migrateLocalStorage();
    } else {
      console.log('✅ Migration already complete or not needed');
    }
    
    // Log current configuration
    console.log(`🔧 Using ${this.shouldUseFlowId() ? 'flow_id' : 'session_id'} as primary identifier`);
  }

  /**
   * Force enable flow ID usage (for testing)
   */
  static enableFlowId(): void {
    localStorage.setItem('use_flow_id_override', 'true');
    console.log('✅ Flow ID usage enabled');
  }

  /**
   * Force disable flow ID usage (for testing)
   */
  static disableFlowId(): void {
    localStorage.removeItem('use_flow_id_override');
    console.log('✅ Flow ID usage disabled, using session ID');
  }

  /**
   * Get migration status for debugging
   */
  static getMigrationStatus(): {
    useFlowId: boolean;
    migrationComplete: boolean;
    sessionKeysFound: string[];
    flowKeysFound: string[];
    currentIdentifier?: string;
  } {
    const sessionKeys = Object.keys(localStorage).filter(key => 
      key.includes('session') && !key.includes('flow')
    );
    
    const flowKeys = Object.keys(localStorage).filter(key => 
      key.includes('flow')
    );
    
    const currentIdentifier = this.shouldUseFlowId() 
      ? localStorage.getItem(this.FLOW_KEYS.CURRENT_FLOW)
      : localStorage.getItem(this.SESSION_KEYS.CURRENT_SESSION);
    
    return {
      useFlowId: this.shouldUseFlowId(),
      migrationComplete: localStorage.getItem(this.MIGRATION_COMPLETE_KEY) === 'true',
      sessionKeysFound: sessionKeys,
      flowKeysFound: flowKeys,
      currentIdentifier: currentIdentifier || undefined
    };
  }
}