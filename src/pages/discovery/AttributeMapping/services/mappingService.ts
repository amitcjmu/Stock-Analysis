// API service for attribute mapping operations
export class MappingService {
  
  static async approveMapping(mappingId: string, flowId: string) {
    try {
      const response = await fetch(`/api/v1/field-mapping/approve/${mappingId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ flowId })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to approve mapping: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error approving mapping:', error);
      throw error;
    }
  }

  static async rejectMapping(mappingId: string, flowId: string, reason?: string) {
    try {
      const response = await fetch(`/api/v1/field-mapping/reject/${mappingId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ flowId, reason })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to reject mapping: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error rejecting mapping:', error);
      throw error;
    }
  }

  static async updateMapping(mappingId: string, updates: any, flowId: string) {
    try {
      const response = await fetch(`/api/v1/field-mapping/update/${mappingId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...updates, flowId })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update mapping: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating mapping:', error);
      throw error;
    }
  }

  static async updateAttribute(attributeId: string, updates: any, flowId: string) {
    try {
      const response = await fetch(`/api/v1/attribute-mapping/update/${attributeId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...updates, flowId })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update attribute: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating attribute:', error);
      throw error;
    }
  }

  static async triggerFieldMappingAnalysis(flowId: string) {
    try {
      const response = await fetch(`/api/v1/field-mapping/trigger/${flowId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to trigger field mapping analysis: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error triggering field mapping analysis:', error);
      throw error;
    }
  }

  static async getMappingProgress(flowId: string) {
    try {
      const response = await fetch(`/api/v1/field-mapping/progress/${flowId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get mapping progress: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting mapping progress:', error);
      throw error;
    }
  }

  static async getFieldMappings(flowId: string) {
    try {
      const response = await fetch(`/api/v1/field-mapping/mappings/${flowId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get field mappings: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting field mappings:', error);
      throw error;
    }
  }

  static async getCriticalAttributes(flowId: string) {
    try {
      const response = await fetch(`/api/v1/attribute-mapping/critical/${flowId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get critical attributes: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting critical attributes:', error);
      throw error;
    }
  }
}

export const mappingService = new MappingService();