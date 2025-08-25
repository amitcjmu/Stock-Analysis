// API service for attribute mapping operations
import { apiCall } from '@/config/api';

export class MappingService {

  static async approveMapping(mappingId: string, flowId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/field-mapping/approve/${mappingId}`, {
        method: 'POST',
        body: JSON.stringify({ flowId })
      });

      return response;
    } catch (error) {
      console.error('Error approving mapping:', error);
      throw error;
    }
  }

  static async rejectMapping(mappingId: string, flowId: string, reason?: string): Promise<unknown> {
    try {
      const response = await apiCall(`/field-mapping/reject/${mappingId}`, {
        method: 'POST',
        body: JSON.stringify({ flowId, reason })
      });

      return response;
    } catch (error) {
      console.error('Error rejecting mapping:', error);
      throw error;
    }
  }

  static async updateMapping(mappingId: string, updates: unknown, flowId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/field-mapping/update/${mappingId}`, {
        method: 'PUT',
        body: JSON.stringify({ ...updates, flowId })
      });

      return response;
    } catch (error) {
      console.error('Error updating mapping:', error);
      throw error;
    }
  }

  static async updateAttribute(attributeId: string, updates: unknown, flowId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/attribute-mapping/update/${attributeId}`, {
        method: 'PUT',
        body: JSON.stringify({ ...updates, flowId })
      });

      return response;
    } catch (error) {
      console.error('Error updating attribute:', error);
      throw error;
    }
  }

  static async triggerFieldMappingAnalysis(flowId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/field-mapping/trigger/${flowId}`, {
        method: 'POST'
      });

      return response;
    } catch (error) {
      console.error('Error triggering field mapping analysis:', error);
      throw error;
    }
  }

  static async getMappingProgress(flowId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/field-mapping/progress/${flowId}`);

      return response;
    } catch (error) {
      console.error('Error getting mapping progress:', error);
      throw error;
    }
  }

  static async getFieldMappings(importId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/data-import/field-mappings/imports/${importId}/field-mappings`);

      return response;
    } catch (error) {
      console.error('Error getting field mappings:', error);
      throw error;
    }
  }

  static async getCriticalAttributes(flowId: string): Promise<unknown> {
    try {
      const response = await apiCall(`/attribute-mapping/critical/${flowId}`);

      return response;
    } catch (error) {
      console.error('Error getting critical attributes:', error);
      throw error;
    }
  }
}

export const mappingService = new MappingService();
