import { apiCall } from "@/lib/api/apiClient";
import { CollectionFlowClient } from "./client";
import type {
  TransitionResult,
  MaintenanceWindow,
  VendorProduct,
} from "./types";

/**
 * Submission handling
 * Handles questionnaire submissions, transitions, and data submission workflows
 */
export class SubmissionsApi extends CollectionFlowClient {
  async submitQuestionnaireResponse(
    flowId: string,
    questionnaireId: string,
    requestData: {
      responses: Record<string, unknown>;
      form_metadata?: Record<string, unknown>;
      validation_results?: Record<string, unknown>;
    },
  ): Promise<{
    status: string;
    message: string;
    questionnaire_id: string;
    flow_id: string;
    progress: number;
  }> {
    return await apiCall(
      `${this.baseUrl}/flows/${flowId}/questionnaires/${questionnaireId}/submit`,
      {
        method: "POST",
        body: JSON.stringify(requestData),
      },
    );
  }

  async submitBulkResponses(
    flowId: string,
    questionnaireId: string,
    responses: Record<string, unknown>,
  ): Promise<{
    status: string;
    processed_count: number;
    success_count: number;
    error_count: number;
    errors: Array<{ field_id: string; error: string }>;
  }> {
    return await apiCall(
      `${this.baseUrl}/flows/${flowId}/questionnaires/${questionnaireId}/responses/bulk`,
      {
        method: "POST",
        body: JSON.stringify(responses),
      },
    );
  }

  // Phase 3: Collection to Assessment Transition
  async transitionToAssessment(flowId: string): Promise<TransitionResult> {
    return await apiCall(
      `${this.baseUrl}/flows/${flowId}/transition-to-assessment`,
      {
        method: "POST",
      },
    );
  }

  // Phase 1: Collection Gaps - Maintenance Windows
  async getMaintenanceWindows(
    scopeType?: string,
    scopeId?: string,
  ): Promise<MaintenanceWindow[]> {
    const params = new URLSearchParams();
    if (scopeType) params.append("scope_type", scopeType);
    if (scopeId) params.append("scope_id", scopeId);

    const query = params.toString();
    return await apiCall(
      `${this.baseUrl}/maintenance-windows${query ? `?${query}` : ""}`,
      {
        method: "GET",
      },
    );
  }

  async createMaintenanceWindow(
    data: Omit<MaintenanceWindow, "id" | "created_at" | "updated_at">,
  ): Promise<MaintenanceWindow> {
    return await apiCall(`${this.baseUrl}/maintenance-windows`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateMaintenanceWindow(
    windowId: string,
    data: Partial<MaintenanceWindow>,
  ): Promise<MaintenanceWindow> {
    return await apiCall(`${this.baseUrl}/maintenance-windows/${windowId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteMaintenanceWindow(
    windowId: string,
  ): Promise<{ status: string; message: string }> {
    return await apiCall(`${this.baseUrl}/maintenance-windows/${windowId}`, {
      method: "DELETE",
    });
  }

  // Phase 1: Collection Gaps - Technology/Vendor Products
  async searchTechnologyOptions(
    query: string,
    category?: string,
  ): Promise<VendorProduct[]> {
    const params = new URLSearchParams({ query });
    if (category) params.append("category", category);

    return await apiCall(`${this.baseUrl}/technology-search?${params}`, {
      method: "GET",
    });
  }

  async normalizeTechnologyEntry(
    vendorName: string,
    productName: string,
    version?: string,
  ): Promise<VendorProduct> {
    return await apiCall(`${this.baseUrl}/technology-normalize`, {
      method: "POST",
      body: JSON.stringify({
        vendor_name: vendorName,
        product_name: productName,
        product_version: version,
      }),
    });
  }

  // Phase 1: Collection Gaps - Scope Target Options
  async getScopeTargets(
    scopeType: "tenant" | "application" | "asset",
  ): Promise<Array<{ value: string; label: string; type: string }>> {
    return await apiCall(`${this.baseUrl}/scope-targets/${scopeType}`, {
      method: "GET",
    });
  }

  // Phase 2: Collection Gaps - Vendor Products Management
  async getVendorProducts(
    searchQuery?: string,
    category?: string,
  ): Promise<VendorProduct[]> {
    const params = new URLSearchParams();
    if (searchQuery) params.append("search", searchQuery);
    if (category) params.append("category", category);

    const query = params.toString();
    return await apiCall(
      `${this.baseUrl}/vendor-products${query ? `?${query}` : ""}`,
      {
        method: "GET",
      },
    );
  }

  async createVendorProduct(
    data: Omit<VendorProduct, "id">,
  ): Promise<VendorProduct> {
    return await apiCall(`${this.baseUrl}/vendor-products`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateVendorProduct(
    productId: string,
    data: Partial<VendorProduct>,
  ): Promise<VendorProduct> {
    return await apiCall(`${this.baseUrl}/vendor-products/${productId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteVendorProduct(
    productId: string,
  ): Promise<{ status: string; message: string }> {
    return await apiCall(`${this.baseUrl}/vendor-products/${productId}`, {
      method: "DELETE",
    });
  }

  async normalizeVendorProduct(
    vendorName: string,
    productName: string,
    version?: string,
  ): Promise<VendorProduct> {
    return await apiCall(`${this.baseUrl}/vendor-products/normalize`, {
      method: "POST",
      body: JSON.stringify({
        vendor_name: vendorName,
        product_name: productName,
        product_version: version,
      }),
    });
  }
}
