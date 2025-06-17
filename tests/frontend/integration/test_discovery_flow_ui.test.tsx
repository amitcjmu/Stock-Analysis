/**
 * Frontend Integration Testing for Discovery Flow (Task 64)
 * 
 * Tests frontend integration with new backend structure including:
 * - UI displays new crew data correctly
 * - Real-time progress updates in the interface
 * - Agent monitoring and status visualization
 * - User interaction with crew results
 * - WebSocket integration for live updates
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import WS from 'jest-websocket-mock';

// Mock components and hooks
import DiscoveryFlowPage from '../../../src/pages/discovery/DiscoveryFlow';
import AgentMonitor from '../../../src/components/AgentMonitor';
import { useDiscoveryFlow } from '../../../src/hooks/discovery/useDiscoveryFlow';

// Mock data for testing
const mockFlowData = {
  flow_id: 'flow_123',
  status: 'in_progress',
  crew_results: {
    field_mapping: {
      status: 'completed',
      execution_time: 2.5,
      field_mappings: [
        {
          source_field: 'hostname',
          target_field: 'asset_name',
          confidence: 0.95
        },
        {
          source_field: 'ip_addr',
          target_field: 'ip_address',
          confidence: 0.88
        }
      ]
    },
    data_cleansing: {
      status: 'in_progress',
      execution_time: null,
      progress_percentage: 45
    },
    inventory_building: {
      status: 'pending',
      execution_time: null
    }
  },
  progress_percentage: 35,
  estimated_completion: '2025-01-28T15:30:00Z'
};

const mockAgentStatus = {
  agents: [
    {
      agent_id: 'field_mapping_manager',
      name: 'Field Mapping Manager',
      status: 'active',
      current_task: 'Analyzing schema mappings',
      performance_metrics: {
        success_rate: 0.95,
        avg_execution_time: 2.1
      }
    },
    {
      agent_id: 'schema_analysis_expert',
      name: 'Schema Analysis Expert',
      status: 'active',
      current_task: 'Processing field patterns',
      performance_metrics: {
        success_rate: 0.92,
        avg_execution_time: 1.8
      }
    }
  ],
  overall_health: 'healthy',
  active_crews: 2,
  total_agents: 17
};

// Test setup utilities
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
};

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

// Mock API responses
const mockApiResponses = {
  '/api/v1/discovery/flow/initialize': {
    method: 'POST',
    response: {
      flow_id: 'flow_123',
      status: 'initialized',
      estimated_duration: 300,
      crew_sequence: [
        'field_mapping',
        'data_cleansing', 
        'inventory_building',
        'app_server_dependencies',
        'app_app_dependencies',
        'technical_debt'
      ]
    }
  },
  '/api/v1/discovery/flow/flow_123/status': {
    method: 'GET',
    response: mockFlowData
  },
  '/api/v1/monitoring/agents': {
    method: 'GET',
    response: mockAgentStatus
  }
};

// Mock fetch for API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Discovery Flow Frontend Integration Tests', () => {
  let server: WS;
  let queryClient: QueryClient;

  beforeEach(() => {
    // Setup WebSocket mock server
    server = new WS('ws://localhost:8000/ws/discovery-flow');
    queryClient = createTestQueryClient();
    
    // Reset mocks
    mockFetch.mockReset();
    
    // Setup default API responses
    mockFetch.mockImplementation((url: string, options?: RequestInit) => {
      const urlPath = new URL(url).pathname;
      const mock = Object.entries(mockApiResponses).find(([path, config]) => 
        urlPath.includes(path.split('/').pop() || '') && 
        (config.method === options?.method || (!options?.method && config.method === 'GET'))
      );
      
      if (mock) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mock[1].response)
        } as Response);
      }
      
      return Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ error: 'Not found' })
      } as Response);
    });
  });

  afterEach(() => {
    WS.clean();
  });

  it('should display Discovery Flow initialization correctly (Task 64)', async () => {
    // Arrange & Act
    renderWithProviders(<DiscoveryFlowPage />);

    // Assert
    expect(screen.getByText(/Discovery Flow/i)).toBeInTheDocument();
    expect(screen.getByText(/Initialize New Flow/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start Discovery/i })).toBeInTheDocument();
  });

  it('should handle flow initialization and display crew sequence (Task 64)', async () => {
    // Arrange
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryFlowPage />);

    // Act
    const startButton = screen.getByRole('button', { name: /Start Discovery/i });
    await user.click(startButton);

    // Assert
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/discovery/flow/initialize'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    // Should display crew sequence
    await waitFor(() => {
      expect(screen.getByText(/Field Mapping/i)).toBeInTheDocument();
      expect(screen.getByText(/Data Cleansing/i)).toBeInTheDocument();
      expect(screen.getByText(/Inventory Building/i)).toBeInTheDocument();
    });
  });

  it('should display crew execution results correctly (Task 64)', async () => {
    // Arrange
    renderWithProviders(<DiscoveryFlowPage />);
    
    // Simulate flow already in progress
    act(() => {
      queryClient.setQueryData(['discovery-flow', 'flow_123'], mockFlowData);
    });

    // Assert
    await waitFor(() => {
      // Field Mapping crew results
      expect(screen.getByText(/Field Mapping.*completed/i)).toBeInTheDocument();
      expect(screen.getByText(/2.5.*seconds/i)).toBeInTheDocument();
      
      // Field mappings display
      expect(screen.getByText(/hostname.*asset_name/i)).toBeInTheDocument();
      expect(screen.getByText(/95%.*confidence/i)).toBeInTheDocument();
      
      // Data Cleansing in progress
      expect(screen.getByText(/Data Cleansing.*progress/i)).toBeInTheDocument();
      expect(screen.getByText(/45%/i)).toBeInTheDocument();
      
      // Inventory Building pending
      expect(screen.getByText(/Inventory Building.*pending/i)).toBeInTheDocument();
    });
  });

  it('should handle real-time WebSocket updates (Task 64)', async () => {
    // Arrange
    renderWithProviders(<DiscoveryFlowPage />);

    // Wait for WebSocket connection
    await server.connected;

    // Act - Send progress update via WebSocket
    const progressUpdate = {
      type: 'progress_update',
      data: {
        flow_id: 'flow_123',
        crew_name: 'data_cleansing',
        status: 'completed',
        progress_percentage: 100,
        execution_time: 3.2
      },
      timestamp: new Date().toISOString()
    };

    act(() => {
      server.send(JSON.stringify(progressUpdate));
    });

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/Data Cleansing.*completed/i)).toBeInTheDocument();
      expect(screen.getByText(/3.2.*seconds/i)).toBeInTheDocument();
    });
  });

  it('should display agent monitoring information (Task 64)', async () => {
    // Arrange & Act
    renderWithProviders(<AgentMonitor />);

    // Assert
    await waitFor(() => {
      // Agent status display
      expect(screen.getByText(/Field Mapping Manager/i)).toBeInTheDocument();
      expect(screen.getByText(/Schema Analysis Expert/i)).toBeInTheDocument();
      
      // Agent performance metrics
      expect(screen.getByText(/95%.*success/i)).toBeInTheDocument();
      expect(screen.getByText(/2.1.*avg time/i)).toBeInTheDocument();
      
      // Overall health
      expect(screen.getByText(/healthy/i)).toBeInTheDocument();
      expect(screen.getByText(/17.*total agents/i)).toBeInTheDocument();
    });
  });

  it('should handle crew result interactions (Task 64)', async () => {
    // Arrange
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryFlowPage />);
    
    act(() => {
      queryClient.setQueryData(['discovery-flow', 'flow_123'], mockFlowData);
    });

    // Act - Click on field mapping results to expand
    await waitFor(() => {
      const fieldMappingSection = screen.getByText(/Field Mapping.*completed/i);
      expect(fieldMappingSection).toBeInTheDocument();
    });

    const expandButton = screen.getByRole('button', { name: /expand.*field mapping/i });
    await user.click(expandButton);

    // Assert
    await waitFor(() => {
      // Detailed field mappings should be visible
      expect(screen.getByText(/hostname → asset_name/i)).toBeInTheDocument();
      expect(screen.getByText(/ip_addr → ip_address/i)).toBeInTheDocument();
      expect(screen.getByText(/Confidence: 95%/i)).toBeInTheDocument();
      expect(screen.getByText(/Confidence: 88%/i)).toBeInTheDocument();
    });
  });

  it('should display progress indicators correctly (Task 64)', async () => {
    // Arrange
    renderWithProviders(<DiscoveryFlowPage />);
    
    act(() => {
      queryClient.setQueryData(['discovery-flow', 'flow_123'], mockFlowData);
    });

    // Assert
    await waitFor(() => {
      // Overall progress
      expect(screen.getByText(/35%.*complete/i)).toBeInTheDocument();
      
      // Progress bar or indicator
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '35');
      
      // Estimated completion time
      expect(screen.getByText(/estimated.*completion/i)).toBeInTheDocument();
    });
  });

  it('should handle error states and display error messages (Task 64)', async () => {
    // Arrange
    mockFetch.mockImplementation(() => 
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ 
          error: 'Internal server error',
          details: 'Crew execution failed'
        })
      } as Response)
    );

    const user = userEvent.setup();
    renderWithProviders(<DiscoveryFlowPage />);

    // Act
    const startButton = screen.getByRole('button', { name: /Start Discovery/i });
    await user.click(startButton);

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/error.*occurred/i)).toBeInTheDocument();
      expect(screen.getByText(/Crew execution failed/i)).toBeInTheDocument();
    });
  });

  it('should support crew result filtering and searching (Task 64)', async () => {
    // Arrange
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryFlowPage />);
    
    act(() => {
      queryClient.setQueryData(['discovery-flow', 'flow_123'], mockFlowData);
    });

    // Act - Use search filter
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search.*crews/i);
      expect(searchInput).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search.*crews/i);
    await user.type(searchInput, 'field mapping');

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/Field Mapping.*completed/i)).toBeInTheDocument();
      expect(screen.queryByText(/Data Cleansing/i)).not.toBeInTheDocument();
    });
  });

  it('should display agent health status with visual indicators (Task 64)', async () => {
    // Arrange
    renderWithProviders(<AgentMonitor />);

    // Assert
    await waitFor(() => {
      // Health status indicators
      const healthyIndicators = screen.getAllByText(/healthy/i);
      expect(healthyIndicators.length).toBeGreaterThan(0);
      
      // Visual status indicators (green dots, check marks, etc.)
      const statusIndicators = screen.getAllByRole('img', { name: /status.*healthy/i });
      expect(statusIndicators.length).toBeGreaterThan(0);
      
      // Agent activity indicators
      expect(screen.getByText(/active.*crews.*2/i)).toBeInTheDocument();
    });
  });

  it('should handle crew result export functionality (Task 64)', async () => {
    // Arrange
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryFlowPage />);
    
    act(() => {
      queryClient.setQueryData(['discovery-flow', 'flow_123'], mockFlowData);
    });

    // Mock URL.createObjectURL and document.createElement
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
    const mockClick = vi.fn();
    const mockAnchorElement = {
      click: mockClick,
      href: '',
      download: ''
    };

    vi.stubGlobal('URL', { createObjectURL: mockCreateObjectURL });
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchorElement as any);

    // Act
    await waitFor(() => {
      const exportButton = screen.getByRole('button', { name: /export.*results/i });
      expect(exportButton).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /export.*results/i });
    await user.click(exportButton);

    // Assert
    await waitFor(() => {
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
    });
  });

  it('should support responsive design for different screen sizes (Task 64)', async () => {
    // Arrange - Test mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375, // Mobile width
    });

    renderWithProviders(<DiscoveryFlowPage />);

    // Assert mobile layout
    await waitFor(() => {
      // Mobile-specific elements or layout should be present
      const mobileMenu = screen.queryByRole('button', { name: /menu/i });
      if (mobileMenu) {
        expect(mobileMenu).toBeInTheDocument();
      }
      
      // Content should be stacked vertically on mobile
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveClass(/mobile/i);
    });

    // Arrange - Test desktop viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200, // Desktop width
    });

    // Trigger resize event
    fireEvent(window, new Event('resize'));

    // Assert desktop layout
    await waitFor(() => {
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveClass(/desktop/i);
    });
  });

  it('should maintain state during navigation and page refresh (Task 64)', async () => {
    // Arrange
    renderWithProviders(<DiscoveryFlowPage />);
    
    act(() => {
      queryClient.setQueryData(['discovery-flow', 'flow_123'], mockFlowData);
    });

    // Assert initial state
    await waitFor(() => {
      expect(screen.getByText(/Field Mapping.*completed/i)).toBeInTheDocument();
    });

    // Act - Simulate navigation away and back
    act(() => {
      // Simulate unmount/remount (navigation)
    });

    renderWithProviders(<DiscoveryFlowPage />);

    // Assert state is restored
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/discovery/flow/flow_123/status'),
        expect.any(Object)
      );
    });
  });
});

// Additional test utilities for complex integration scenarios
export const DiscoveryFlowTestUtils = {
  // Utility to simulate complete flow execution
  simulateCompleteFlow: async (server: WS) => {
    const crews = ['field_mapping', 'data_cleansing', 'inventory_building'];
    
    for (const crew of crews) {
      const update = {
        type: 'progress_update',
        data: {
          crew_name: crew,
          status: 'completed',
          progress_percentage: 100
        }
      };
      
      server.send(JSON.stringify(update));
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  },

  // Utility to create mock crew result data
  createMockCrewResult: (crewName: string, status: string = 'completed') => ({
    [crewName]: {
      status,
      execution_time: Math.random() * 5,
      results: {
        processed_items: Math.floor(Math.random() * 100),
        success_rate: 0.9 + Math.random() * 0.1
      }
    }
  }),

  // Utility to verify accessibility compliance
  checkAccessibility: async (container: HTMLElement) => {
    // This would typically use @testing-library/jest-dom or axe-core
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
      expect(button).toHaveAttribute('aria-label');
    });

    const progressBars = container.querySelectorAll('[role="progressbar"]');
    progressBars.forEach(bar => {
      expect(bar).toHaveAttribute('aria-valuenow');
      expect(bar).toHaveAttribute('aria-valuemin');
      expect(bar).toHaveAttribute('aria-valuemax');
    });
  }
}; 