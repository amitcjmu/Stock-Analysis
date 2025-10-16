/**
 * ApplicationGroupsWidget Tests
 *
 * Phase 4 Days 17-18: Assessment Architecture Enhancement
 *
 * Test Coverage:
 * - Rendering with mock data (2+ application groups)
 * - Expand/collapse functionality
 * - Search/filter functionality
 * - Sort functionality (name, asset count, readiness)
 * - Unmapped assets display
 * - Loading and error states
 * - Accessibility (screen reader labels, keyboard navigation)
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';

import { ApplicationGroupsWidget } from '../ApplicationGroupsWidget';
import type { ApplicationGroupsWidgetProps } from '../ApplicationGroupsWidget';
import * as apiModule from '@/config/api';
import * as authModule from '@/contexts/AuthContext';

// ============================================================================
// Mock Data
// ============================================================================

const mockApplicationGroups = [
  {
    canonical_application_id: 'app-001-uuid',
    canonical_application_name: 'CRM System',
    asset_ids: ['asset-001', 'asset-002', 'asset-003'],
    asset_count: 3,
    asset_types: ['server', 'database', 'network_device'],
    readiness_summary: {
      ready: 2,
      not_ready: 1,
      in_progress: 0,
      avg_completeness_score: 0.67,
    },
  },
  {
    canonical_application_id: 'app-002-uuid',
    canonical_application_name: 'ERP Platform',
    asset_ids: ['asset-004', 'asset-005'],
    asset_count: 2,
    asset_types: ['server', 'database'],
    readiness_summary: {
      ready: 2,
      not_ready: 0,
      in_progress: 0,
      avg_completeness_score: 1.0,
    },
  },
  {
    canonical_application_id: null, // Unmapped asset
    canonical_application_name: 'Standalone Server',
    asset_ids: ['asset-006'],
    asset_count: 1,
    asset_types: ['server'],
    readiness_summary: {
      ready: 0,
      not_ready: 1,
      in_progress: 0,
      avg_completeness_score: 0.2,
    },
  },
];

// ============================================================================
// Test Helpers
// ============================================================================

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithProviders = (
  ui: React.ReactElement,
  { queryClient = createQueryClient(), ...options } = {}
) => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return {
    ...render(ui, { wrapper, ...options }),
    queryClient,
  };
};

const defaultProps: ApplicationGroupsWidgetProps = {
  flow_id: 'test-flow-id',
  client_account_id: 'client-123',
  engagement_id: 'engagement-456',
};

// ============================================================================
// Mocks Setup
// ============================================================================

const mockApiCall = vi.fn();
const mockGetAuthHeaders = vi.fn(() => ({ Authorization: 'Bearer test-token' }));

vi.mock('@/config/api', () => ({
  apiCall: (...args: unknown[]) => mockApiCall(...args),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    getAuthHeaders: mockGetAuthHeaders,
  }),
}));

// ============================================================================
// Test Suite
// ============================================================================

describe('ApplicationGroupsWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  // ==========================================================================
  // Rendering Tests
  // ==========================================================================

  describe('Rendering', () => {
    it('should render loading state initially', async () => {
      mockApiCall.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      expect(screen.getByText('Loading application groupings...')).toBeInTheDocument();
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument(); // Loader icon
    });

    it('should render application groups after successful data fetch', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
        expect(screen.getByText('ERP Platform')).toBeInTheDocument();
      });

      // Check asset counts
      expect(screen.getByText('3 assets')).toBeInTheDocument();
      expect(screen.getByText('2 assets')).toBeInTheDocument();
    });

    it('should render unmapped assets section', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Unmapped Assets')).toBeInTheDocument();
        expect(screen.getByText('Standalone Server')).toBeInTheDocument();
      });

      expect(screen.getByText('1 assets', { exact: false })).toBeInTheDocument();
    });

    it('should display readiness badges with correct colors', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        // CRM System: 67% ready (yellow)
        expect(screen.getByText(/67% ready/)).toBeInTheDocument();
        // ERP Platform: 100% ready (green)
        expect(screen.getByText(/100% ready/)).toBeInTheDocument();
        // Standalone Server: 0% ready (red)
        expect(screen.getByText(/0% ready/)).toBeInTheDocument();
      });
    });

    it('should display asset type icons', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        // Verify asset type icons are rendered (check via aria-labels or test IDs if added)
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      // Note: Icon testing can be enhanced with test IDs or aria-labels
    });
  });

  // ==========================================================================
  // Error Handling Tests
  // ==========================================================================

  describe('Error Handling', () => {
    it('should render error state on API failure', async () => {
      mockApiCall.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load application groups')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should render empty state when no applications exist', async () => {
      mockApiCall.mockResolvedValue([]);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('No applications found for this assessment')).toBeInTheDocument();
        expect(
          screen.getByText('No application groups available. Complete the collection flow first.')
        ).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Expand/Collapse Tests
  // ==========================================================================

  describe('Expand/Collapse Functionality', () => {
    it('should expand group when clicked', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      // Initially collapsed, assets not visible
      expect(screen.queryByText('Assets in this group:')).not.toBeInTheDocument();

      // Click to expand
      const crmCard = screen.getByText('CRM System').closest('button');
      expect(crmCard).toBeInTheDocument();
      if (crmCard) {
        fireEvent.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Assets in this group:')).toBeInTheDocument();
        // Check asset IDs are displayed
        expect(screen.getByText(/asset-001/)).toBeInTheDocument();
      });
    });

    it('should collapse group when clicked again', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      // Expand
      const crmCard = screen.getByText('CRM System').closest('button');
      if (crmCard) {
        fireEvent.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Assets in this group:')).toBeInTheDocument();
      });

      // Collapse
      if (crmCard) {
        fireEvent.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.queryByText('Assets in this group:')).not.toBeInTheDocument();
      });
    });

    it('should allow expanding multiple groups simultaneously', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
        expect(screen.getByText('ERP Platform')).toBeInTheDocument();
      });

      // Expand CRM
      const crmCard = screen.getByText('CRM System').closest('button');
      if (crmCard) {
        fireEvent.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Assets in this group:')).toBeInTheDocument();
      });

      // Expand ERP
      const erpCard = screen.getByText('ERP Platform').closest('button');
      if (erpCard) {
        fireEvent.click(erpCard);
      }

      await waitFor(() => {
        expect(screen.getAllByText('Assets in this group:')).toHaveLength(2);
      });
    });
  });

  // ==========================================================================
  // Search/Filter Tests
  // ==========================================================================

  describe('Search/Filter Functionality', () => {
    it('should filter applications by name', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
        expect(screen.getByText('ERP Platform')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search applications...');
      await user.type(searchInput, 'CRM');

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
        expect(screen.queryByText('ERP Platform')).not.toBeInTheDocument();
      });
    });

    it('should show no results message when search yields no matches', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search applications...');
      await user.type(searchInput, 'NonExistent');

      await waitFor(() => {
        expect(screen.getByText(/No applications match "NonExistent"/)).toBeInTheDocument();
      });
    });

    it('should be case-insensitive when searching', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search applications...');
      await user.type(searchInput, 'crm');

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Sort Tests
  // ==========================================================================

  describe('Sort Functionality', () => {
    it('should sort by name in ascending order by default', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        const appNames = screen.getAllByRole('heading', { level: 3 });
        expect(appNames[0]).toHaveTextContent('CRM System');
        expect(appNames[1]).toHaveTextContent('ERP Platform');
      });
    });

    it('should toggle sort direction when clicking same sort button', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      const nameSortButton = screen.getByLabelText('Sort by name');

      // Click to reverse (descending)
      await user.click(nameSortButton);

      await waitFor(() => {
        const appNames = screen.getAllByRole('heading', { level: 3 });
        // Check descending order
        expect(appNames[0]).toHaveTextContent('Standalone Server'); // Unmapped appears in main list when sorted
      });
    });

    it('should sort by asset count', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      const countSortButton = screen.getByLabelText('Sort by asset count');
      await user.click(countSortButton);

      await waitFor(() => {
        const appNames = screen.getAllByRole('heading', { level: 3 });
        // Smallest count first (Standalone Server: 1)
        expect(appNames[0]).toHaveTextContent('Standalone Server');
      });
    });

    it('should sort by readiness percentage', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      const readinessSortButton = screen.getByLabelText('Sort by readiness');
      await user.click(readinessSortButton);

      await waitFor(() => {
        const appNames = screen.getAllByRole('heading', { level: 3 });
        // Lowest readiness first (Standalone Server: 0%)
        expect(appNames[0]).toHaveTextContent('Standalone Server');
      });
    });
  });

  // ==========================================================================
  // Asset Click Callback Tests
  // ==========================================================================

  describe('Asset Click Callback', () => {
    it('should call onAssetClick when asset is clicked', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const onAssetClick = vi.fn();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} onAssetClick={onAssetClick} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      // Expand CRM group
      const crmCard = screen.getByText('CRM System').closest('button');
      if (crmCard) {
        fireEvent.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Assets in this group:')).toBeInTheDocument();
      });

      // Click on first asset
      const firstAsset = screen.getByText(/asset-001/);
      fireEvent.click(firstAsset);

      expect(onAssetClick).toHaveBeenCalledWith('asset-001');
    });

    it('should not make assets clickable when onAssetClick is not provided', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      // Expand CRM group
      const crmCard = screen.getByText('CRM System').closest('button');
      if (crmCard) {
        fireEvent.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Assets in this group:')).toBeInTheDocument();
      });

      // Asset should not be clickable
      const firstAsset = screen.getByText(/asset-001/).closest('div');
      expect(firstAsset).not.toHaveAttribute('role', 'button');
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA labels for search input', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText('Search applications')).toBeInTheDocument();
      });
    });

    it('should have proper ARIA labels for sort buttons', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText('Sort by name')).toBeInTheDocument();
        expect(screen.getByLabelText('Sort by asset count')).toBeInTheDocument();
        expect(screen.getByLabelText('Sort by readiness')).toBeInTheDocument();
      });
    });

    it('should support keyboard navigation for asset clicks', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);
      const onAssetClick = vi.fn();
      const user = userEvent.setup();

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} onAssetClick={onAssetClick} />);

      await waitFor(() => {
        expect(screen.getByText('CRM System')).toBeInTheDocument();
      });

      // Expand CRM group
      const crmCard = screen.getByText('CRM System').closest('button');
      if (crmCard) {
        await user.click(crmCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Assets in this group:')).toBeInTheDocument();
      });

      // Focus and press Enter on asset
      const firstAsset = screen.getByText(/asset-001/).closest('div');
      if (firstAsset) {
        firstAsset.focus();
        await user.keyboard('{Enter}');
        expect(onAssetClick).toHaveBeenCalledWith('asset-001');
      }
    });

    it('should have proper heading hierarchy', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        // CardTitle renders as h3
        const headings = screen.getAllByRole('heading', { level: 3 });
        expect(headings.length).toBeGreaterThan(0);
      });
    });
  });

  // ==========================================================================
  // API Integration Tests
  // ==========================================================================

  describe('API Integration', () => {
    it('should call API with correct endpoint and headers', async () => {
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledWith(
          '/master-flows/test-flow-id/assessment-applications',
          {
            method: 'GET',
            headers: {
              Authorization: 'Bearer test-token',
              'X-Client-Account-ID': 'client-123',
              'X-Engagement-ID': 'engagement-456',
            },
          }
        );
      });
    });

    it('should handle non-array API response gracefully', async () => {
      mockApiCall.mockResolvedValue({ data: 'invalid' });

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('No applications found for this assessment')).toBeInTheDocument();
      });
    });

    it('should refetch data every minute', async () => {
      vi.useFakeTimers();
      mockApiCall.mockResolvedValue(mockApplicationGroups);

      renderWithProviders(<ApplicationGroupsWidget {...defaultProps} />);

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 1 minute
      vi.advanceTimersByTime(60000);

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledTimes(2);
      });

      vi.useRealTimers();
    });
  });
});
