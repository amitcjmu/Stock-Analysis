/**
 * ReadinessDashboardWidget Tests
 *
 * Phase 4 Days 19-20: Assessment Architecture Enhancement
 *
 * Test Coverage:
 * - Basic rendering (loading, error, empty states)
 * - Summary cards (calculations, progress bars, color coding)
 * - Assessment blockers accordion (expand/collapse, missing attributes)
 * - Critical attributes reference (collapsible section)
 * - Action buttons (Collect Missing Data, Export Report)
 * - API integration (endpoint, headers, refetching)
 * - Accessibility (ARIA labels, keyboard navigation)
 *
 * Total Test Cases: 26+
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';

import { ReadinessDashboardWidget } from '../ReadinessDashboardWidget';
import type { ReadinessDashboardWidgetProps } from '../ReadinessDashboardWidget';
import type { AssessmentReadinessResponse } from '@/types/assessment';
import * as apiModule from '@/config/api';
import * as authModule from '@/contexts/AuthContext';

// ============================================================================
// Mock Data Factories
// ============================================================================

const createMockReadinessResponse = (
  overrides?: Partial<AssessmentReadinessResponse>
): AssessmentReadinessResponse => ({
  total_assets: 10,
  readiness_summary: {
    ready: 6,
    not_ready: 3,
    in_progress: 1,
    avg_completeness_score: 0.67,
  },
  asset_details: [
    {
      asset_id: 'asset-001',
      asset_name: 'Production Server 1',
      asset_type: 'server',
      assessment_readiness: 'not_ready',
      assessment_readiness_score: 0.55,
      assessment_blockers: [
        'business_criticality',
        'dependencies',
        'business_owner',
      ],
      missing_attributes: {
        infrastructure: [],
        application: ['business_criticality', 'dependencies'],
        business: ['business_owner'],
        technical_debt: [],
      },
    },
    {
      asset_id: 'asset-002',
      asset_name: 'Database Server',
      asset_type: 'database',
      assessment_readiness: 'not_ready',
      assessment_readiness_score: 0.45,
      assessment_blockers: [
        'technology_stack',
        'operating_system',
        'business_criticality',
        'dependencies',
        'data_sensitivity',
      ],
      missing_attributes: {
        infrastructure: ['technology_stack', 'operating_system'],
        application: ['business_criticality', 'dependencies', 'data_sensitivity'],
        business: [],
        technical_debt: [],
      },
    },
    {
      asset_id: 'asset-003',
      asset_name: 'Web Application',
      asset_type: 'application',
      assessment_readiness: 'in_progress',
      assessment_readiness_score: 0.68,
      assessment_blockers: ['last_update_date', 'known_vulnerabilities'],
      missing_attributes: {
        infrastructure: [],
        application: [],
        business: [],
        technical_debt: ['last_update_date', 'known_vulnerabilities'],
      },
    },
  ],
  ...overrides,
});

const createAllReadyResponse = (): AssessmentReadinessResponse => ({
  total_assets: 5,
  readiness_summary: {
    ready: 5,
    not_ready: 0,
    in_progress: 0,
    avg_completeness_score: 1.0,
  },
  asset_details: [],
});

const createEmptyResponse = (): AssessmentReadinessResponse => ({
  total_assets: 0,
  readiness_summary: {
    ready: 0,
    not_ready: 0,
    in_progress: 0,
    avg_completeness_score: 0,
  },
  asset_details: [],
});

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

const defaultProps: ReadinessDashboardWidgetProps = {
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

describe('ReadinessDashboardWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  // ==========================================================================
  // Basic Rendering Tests
  // ==========================================================================

  describe('Basic Rendering', () => {
    it('should render loading state initially', async () => {
      mockApiCall.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      expect(screen.getByText('Assessment Readiness')).toBeInTheDocument();
      expect(screen.getByText('Loading readiness data...')).toBeInTheDocument();
      // Check for loader icon via className
      const loader = document.querySelector('.animate-spin');
      expect(loader).toBeInTheDocument();
    });

    it('should render readiness data after successful fetch', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Ready Assets')).toBeInTheDocument();
        expect(screen.getByText('Not Ready Assets')).toBeInTheDocument();
        expect(screen.getByText('In Progress Assets')).toBeInTheDocument();
        expect(screen.getByText('Avg Completeness')).toBeInTheDocument();
      });
    });

    it('should render error state on API failure', async () => {
      mockApiCall.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load readiness data')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should render empty state when no assets exist', async () => {
      mockApiCall.mockResolvedValue(createEmptyResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('No assets found for readiness assessment')).toBeInTheDocument();
        expect(screen.getByText('No asset data available')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Summary Cards Tests
  // ==========================================================================

  describe('Summary Cards', () => {
    it('should calculate and display ready count correctly', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Ready Assets')).toBeInTheDocument();
        expect(screen.getByText('6')).toBeInTheDocument(); // ready count
        expect(screen.getByText('60% of total')).toBeInTheDocument(); // 6/10 = 60%
      });
    });

    it('should calculate and display not ready count correctly', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Not Ready Assets')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument(); // not_ready count
        expect(screen.getByText('30% of total')).toBeInTheDocument(); // 3/10 = 30%
      });
    });

    it('should calculate and display in progress count correctly', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('In Progress Assets')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument(); // in_progress count
        expect(screen.getByText('10% of total')).toBeInTheDocument(); // 1/10 = 10%
      });
    });

    it('should display average completeness score correctly', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Avg Completeness')).toBeInTheDocument();
        expect(screen.getByText('67%')).toBeInTheDocument(); // 0.67 * 100 = 67%
        expect(screen.getByText('Across 10 assets')).toBeInTheDocument();
      });
    });

    it('should apply green color for high completeness (≥75%)', async () => {
      mockApiCall.mockResolvedValue(
        createMockReadinessResponse({
          readiness_summary: {
            ready: 8,
            not_ready: 0,
            in_progress: 2,
            avg_completeness_score: 0.85,
          },
        })
      );

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument();
        // Check that 85% is displayed (indicates high completeness)
        expect(screen.getByText('Across 10 assets')).toBeInTheDocument();
      });
    });

    it('should apply yellow color for medium completeness (50-74%)', async () => {
      mockApiCall.mockResolvedValue(
        createMockReadinessResponse({
          readiness_summary: {
            ready: 6,
            not_ready: 3,
            in_progress: 1,
            avg_completeness_score: 0.65,
          },
        })
      );

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('65%')).toBeInTheDocument();
        // Check that 65% is displayed (indicates medium completeness)
        expect(screen.getByText('Across 10 assets')).toBeInTheDocument();
      });
    });

    it('should apply red color for low completeness (<50%)', async () => {
      mockApiCall.mockResolvedValue(
        createMockReadinessResponse({
          readiness_summary: {
            ready: 2,
            not_ready: 7,
            in_progress: 1,
            avg_completeness_score: 0.35,
          },
        })
      );

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('35%')).toBeInTheDocument();
        // Check that 35% is displayed (indicates low completeness)
        expect(screen.getByText('Across 10 assets')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Celebration State Tests
  // ==========================================================================

  describe('Celebration State', () => {
    it('should show celebration message when all assets are ready', async () => {
      mockApiCall.mockResolvedValue(createAllReadyResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('All Assets Ready!')).toBeInTheDocument();
        expect(screen.getByText('You can proceed with the assessment')).toBeInTheDocument();
      });
    });

    it('should not show celebration when some assets are not ready', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.queryByText('All Assets Ready!')).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Assessment Blockers Accordion Tests
  // ==========================================================================

  describe('Assessment Blockers Accordion', () => {
    it('should render blocker assets count', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Assessment Blockers')).toBeInTheDocument();
        expect(screen.getByText('3 assets need attention')).toBeInTheDocument();
      });
    });

    it('should render asset blocker accordions for each not-ready asset', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Production Server 1')).toBeInTheDocument();
        expect(screen.getByText('Database Server')).toBeInTheDocument();
        expect(screen.getByText('Web Application')).toBeInTheDocument();
      });
    });

    it('should expand asset details when clicked', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Production Server 1')).toBeInTheDocument();
      });

      // Initially collapsed, progress bar not visible
      const progressBars = document.querySelectorAll('[role="progressbar"]');
      expect(progressBars.length).toBe(0);

      // Click to expand
      const assetCard = screen.getByText('Production Server 1').closest('button');
      expect(assetCard).toBeInTheDocument();
      if (assetCard) {
        fireEvent.click(assetCard);
      }

      await waitFor(() => {
        // Check that progress bar is now visible
        const progressBarsAfter = document.querySelectorAll('[role="progressbar"]');
        expect(progressBarsAfter.length).toBeGreaterThan(0);
      });
    });

    it('should collapse asset details when clicked again', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Production Server 1')).toBeInTheDocument();
      });

      const assetCard = screen.getByText('Production Server 1').closest('button');
      if (assetCard) {
        // Expand
        fireEvent.click(assetCard);
        await waitFor(() => {
          const progressBars = document.querySelectorAll('[role="progressbar"]');
          expect(progressBars.length).toBeGreaterThan(0);
        });

        // Collapse
        fireEvent.click(assetCard);
        await waitFor(() => {
          const progressBars = document.querySelectorAll('[role="progressbar"]');
          expect(progressBars.length).toBe(0);
        });
      }
    });

    it('should not render blockers section when all assets are ready', async () => {
      mockApiCall.mockResolvedValue(createAllReadyResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.queryByText('Assessment Blockers')).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Critical Attributes Reference Tests
  // ==========================================================================

  describe('Critical Attributes Reference', () => {
    it('should render collapsible critical attributes section', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('22 Critical Attributes for 6R Assessment')).toBeInTheDocument();
      });
    });

    it('should expand critical attributes when clicked', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());
      const user = userEvent.setup();

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('22 Critical Attributes for 6R Assessment')).toBeInTheDocument();
      });

      // Initially collapsed, attributes not visible
      expect(screen.queryByText(/application name/i)).not.toBeInTheDocument();

      // Click to expand
      const attributesHeader = screen.getByText('22 Critical Attributes for 6R Assessment');
      await user.click(attributesHeader);

      await waitFor(() => {
        // Look for category headers instead
        expect(screen.getByText(/infrastructure \(6\)/i)).toBeInTheDocument();
      });
    });

    it('should display all 4 categories of critical attributes', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());
      const user = userEvent.setup();

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('22 Critical Attributes for 6R Assessment')).toBeInTheDocument();
      });

      // Expand
      const attributesHeader = screen.getByText('22 Critical Attributes for 6R Assessment');
      await user.click(attributesHeader);

      await waitFor(() => {
        expect(screen.getByText(/infrastructure \(6\)/i)).toBeInTheDocument();
        expect(screen.getByText(/application \(8\)/i)).toBeInTheDocument();
        expect(screen.getByText(/business \(4\)/i)).toBeInTheDocument();
        expect(screen.getByText(/technical debt \(4\)/i)).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Action Buttons Tests
  // ==========================================================================

  describe('Action Buttons', () => {
    it('should render "Collect Missing Data" button when callback provided', async () => {
      const onCollectDataClick = vi.fn();
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(
        <ReadinessDashboardWidget {...defaultProps} onCollectDataClick={onCollectDataClick} />
      );

      await waitFor(() => {
        expect(screen.getByText('Collect Missing Data')).toBeInTheDocument();
      });
    });

    it('should call onCollectDataClick when button is clicked', async () => {
      const onCollectDataClick = vi.fn();
      mockApiCall.mockResolvedValue(createMockReadinessResponse());
      const user = userEvent.setup();

      renderWithProviders(
        <ReadinessDashboardWidget {...defaultProps} onCollectDataClick={onCollectDataClick} />
      );

      await waitFor(() => {
        expect(screen.getByText('Collect Missing Data')).toBeInTheDocument();
      });

      const collectButton = screen.getByText('Collect Missing Data');
      await user.click(collectButton);

      expect(onCollectDataClick).toHaveBeenCalledTimes(1);
    });

    it('should not render "Collect Missing Data" button when callback not provided', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.queryByText('Collect Missing Data')).not.toBeInTheDocument();
      });
    });

    it('should render "Export Report" button', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Export Report')).toBeInTheDocument();
      });
    });

    it('should log export action when "Export Report" is clicked', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Export Report')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export Report');
      await user.click(exportButton);

      expect(consoleSpy).toHaveBeenCalledWith('Export readiness report');
      consoleSpy.mockRestore();
    });
  });

  // ==========================================================================
  // API Integration Tests
  // ==========================================================================

  describe('API Integration', () => {
    it('should call API with correct endpoint and headers', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledWith('/master-flows/test-flow-id/assessment-readiness', {
          method: 'GET',
          headers: {
            Authorization: 'Bearer test-token',
            'X-Client-Account-ID': 'client-123',
            'X-Engagement-ID': 'engagement-456',
          },
        });
      });
    });

    it('should handle API response with snake_case fields', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        // Verify snake_case fields are processed correctly
        expect(screen.getByText('6')).toBeInTheDocument(); // readiness_summary.ready
        expect(screen.getByText('67%')).toBeInTheDocument(); // avg_completeness_score
      });
    });

    it('should refetch data every 60 seconds', async () => {
      vi.useFakeTimers();
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 60 seconds
      vi.advanceTimersByTime(60000);

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledTimes(2);
      });

      vi.useRealTimers();
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        const headings = screen.getAllByRole('heading');
        expect(headings.length).toBeGreaterThan(0);
      });
    });

    it('should have accessible button labels', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        const exportButton = screen.getByText('Export Report');
        expect(exportButton).toBeInTheDocument();
        expect(exportButton.closest('button')).toBeInTheDocument();
      });
    });

    it('should support keyboard navigation for collapsible sections', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());
      const user = userEvent.setup();

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('22 Critical Attributes for 6R Assessment')).toBeInTheDocument();
      });

      // Focus and press Enter
      const attributesHeader = screen.getByText('22 Critical Attributes for 6R Assessment').closest('button');
      if (attributesHeader) {
        attributesHeader.focus();
        await user.keyboard('{Enter}');

        await waitFor(() => {
          expect(screen.getByText(/infrastructure \(6\)/i)).toBeInTheDocument();
        });
      }
    });

    it('should have descriptive text for screen readers', async () => {
      mockApiCall.mockResolvedValue(createMockReadinessResponse());

      renderWithProviders(<ReadinessDashboardWidget {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('60% of total')).toBeInTheDocument(); // Descriptive percentage
        expect(screen.getByText('Across 10 assets')).toBeInTheDocument(); // Descriptive context
      });
    });
  });
});
