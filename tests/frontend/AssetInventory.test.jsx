/**
 * Frontend tests for enhanced Asset Inventory functionality.
 * Tests the React components with device classification and 6R readiness.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Inventory from '../../src/pages/discovery/Inventory';
import { apiCall } from '../../src/config/api';

// Mock the API module
vi.mock('../../src/config/api', () => ({
  apiCall: vi.fn(),
  API_CONFIG: {
    ENDPOINTS: {
      DISCOVERY: {
        ASSETS: '/api/v1/unified-discovery/assets'
      }
    }
  }
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Download: () => React.createElement('div', { 'data-testid': 'download-icon' }, 'Download'),
  Filter: () => React.createElement('div', { 'data-testid': 'filter-icon' }, 'Filter'),
  Database: () => React.createElement('div', { 'data-testid': 'database-icon' }, 'Database'),
  Server: () => React.createElement('div', { 'data-testid': 'server-icon' }, 'Server'),
  HardDrive: () => React.createElement('div', { 'data-testid': 'harddrive-icon' }, 'HardDrive'),
  RefreshCw: ({ className }) => React.createElement('div', { 'data-testid': 'refresh-icon', className: className }, 'Refresh'),
  Router: () => React.createElement('div', { 'data-testid': 'router-icon' }, 'Router'),
  Shield: () => React.createElement('div', { 'data-testid': 'shield-icon' }, 'Shield'),
  Cpu: () => React.createElement('div', { 'data-testid': 'cpu-icon' }, 'Cpu'),
  Cloud: () => React.createElement('div', { 'data-testid': 'cloud-icon' }, 'Cloud'),
  Zap: () => React.createElement('div', { 'data-testid': 'zap-icon' }, 'Zap')
}));

// Mock components
vi.mock('../../src/components/Sidebar', () => ({
  default: () => React.createElement('div', { 'data-testid': 'sidebar' }, 'Sidebar')
}));

vi.mock('../../src/components/FeedbackWidget', () => ({
  default: () => React.createElement('div', { 'data-testid': 'feedback-widget' }, 'Feedback Widget')
}));

// Sample test data with enhanced classifications
const mockAssetData = {
  assets: [
    {
      id: 'SRV001',
      type: 'Server',
      name: 'web-server-01',
      techStack: 'Linux Ubuntu 22.04',
      department: 'IT Operations',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'High',
      ipAddress: '192.168.1.10',
      operatingSystem: 'Linux Ubuntu 22.04',
      cpuCores: 8,
      memoryGb: 32,
      storageGb: 500,
      sixr_ready: 'Ready',
      migration_complexity: 'Medium'
    },
    {
      id: 'APP001',
      type: 'Application',
      name: 'CRM_System',
      techStack: 'Java Spring Boot',
      department: 'Sales',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'High',
      ipAddress: null,
      operatingSystem: null,
      cpuCores: null,
      memoryGb: null,
      storageGb: null,
      sixr_ready: 'Ready',
      migration_complexity: 'High'
    },
    {
      id: 'DB001',
      type: 'Database',
      name: 'mysql-prod-01',
      techStack: 'MySQL 8.0',
      department: 'Database Team',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'Critical',
      ipAddress: '192.168.1.20',
      operatingSystem: 'Linux',
      cpuCores: 16,
      memoryGb: 64,
      storageGb: 2000,
      sixr_ready: 'Ready',
      migration_complexity: 'High'
    },
    {
      id: 'NET001',
      type: 'Network Device',
      name: 'core-switch-01',
      techStack: 'Cisco IOS',
      department: 'Network Team',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'High',
      ipAddress: '192.168.1.1',
      operatingSystem: 'Cisco IOS',
      cpuCores: null,
      memoryGb: null,
      storageGb: null,
      sixr_ready: 'Not Applicable',
      migration_complexity: 'Low'
    },
    {
      id: 'STR001',
      type: 'Storage Device',
      name: 'SAN01',
      techStack: 'NetApp ONTAP',
      department: 'IT Operations',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'Critical',
      ipAddress: '192.168.1.50',
      operatingSystem: 'ONTAP',
      cpuCores: null,
      memoryGb: null,
      storageGb: 10000,
      sixr_ready: 'Not Applicable',
      migration_complexity: 'Low'
    },
    {
      id: 'SEC001',
      type: 'Security Device',
      name: 'firewall-perimeter',
      techStack: 'Palo Alto PAN-OS',
      department: 'Security Team',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'Critical',
      ipAddress: '192.168.1.2',
      operatingSystem: 'PAN-OS',
      cpuCores: null,
      memoryGb: null,
      storageGb: null,
      sixr_ready: 'Not Applicable',
      migration_complexity: 'Low'
    },
    {
      id: 'VRT001',
      type: 'Virtualization Platform',
      name: 'vmware-vcenter',
      techStack: 'VMware vSphere 7.0',
      department: 'IT Operations',
      status: 'Discovered',
      environment: 'Production',
      criticality: 'Critical',
      ipAddress: '192.168.1.60',
      operatingSystem: 'vSphere',
      cpuCores: 8,
      memoryGb: 32,
      storageGb: 500,
      sixr_ready: 'Complex Analysis Required',
      migration_complexity: 'High'
    },
    {
      id: 'UNK001',
      type: 'Unknown',
      name: 'mystery-device',
      techStack: 'Unknown',
      department: 'Unknown',
      status: 'Pending',
      environment: 'Unknown',
      criticality: 'Unknown',
      ipAddress: null,
      operatingSystem: null,
      cpuCores: null,
      memoryGb: null,
      storageGb: null,
      sixr_ready: 'Type Classification Needed',
      migration_complexity: 'Medium'
    }
  ],
  summary: {
    total: 8,
    applications: 1,
    servers: 1,
    databases: 1,
    devices: 3,
    unknown: 1,
    discovered: 7,
    pending: 1,
    device_breakdown: {
      network: 1,
      storage: 1,
      security: 1,
      infrastructure: 0,
      virtualization: 1
    }
  },
  dataSource: 'live',
  lastUpdated: '2025-01-28T15:30:00Z',
  suggestedHeaders: [
    { key: 'id', label: 'Asset ID', description: 'Unique asset identifier' },
    { key: 'type', label: 'Type', description: 'Asset type classification' },
    { key: 'name', label: 'Name', description: 'Asset name' },
    { key: 'environment', label: 'Environment', description: 'Environment (Production/Development)' },
    { key: 'criticality', label: 'Criticality', description: 'Business criticality level' },
    { key: 'sixr_ready', label: '6R Ready', description: '6R treatment readiness status' },
    { key: 'migration_complexity', label: 'Complexity', description: 'Migration complexity assessment' }
  ]
};

// Wrapper component for tests
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Asset Inventory Enhanced Features', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiCall.mockResolvedValue(mockAssetData);
  });

  describe('Component Rendering', () => {
    it('renders the main inventory page with enhanced summary', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      // Check main title
      expect(screen.getByText('Asset Inventory')).toBeInTheDocument();
      expect(screen.getByText('Comprehensive inventory of discovered IT assets')).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Live Data:')).toBeInTheDocument();
      });
    });

    it('displays enhanced summary statistics with device breakdown', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Primary asset types
        expect(screen.getByText('Applications')).toBeInTheDocument();
        expect(screen.getByText('Servers')).toBeInTheDocument();
        expect(screen.getByText('Databases')).toBeInTheDocument();

        // Enhanced categories
        expect(screen.getByText('Devices')).toBeInTheDocument();
        expect(screen.getByText('Unknown')).toBeInTheDocument();
        expect(screen.getByText('Total')).toBeInTheDocument();
      });
    });

    it('shows device breakdown widget when devices are present', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Device breakdown section
        expect(screen.getByText('Device Breakdown')).toBeInTheDocument();
        expect(screen.getByText('Network')).toBeInTheDocument();
        expect(screen.getByText('Storage')).toBeInTheDocument();
        expect(screen.getByText('Security')).toBeInTheDocument();
        expect(screen.getByText('Infrastructure')).toBeInTheDocument();
        expect(screen.getByText('Virtualization')).toBeInTheDocument();
      });
    });

    it('displays correct asset counts in summary', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check numeric values
        expect(screen.getByText('1')).toBeInTheDocument(); // Applications
        expect(screen.getByText('3')).toBeInTheDocument(); // Devices
        expect(screen.getByText('8')).toBeInTheDocument(); // Total
      });
    });
  });

  describe('Asset Table with Enhanced Classification', () => {
    it('renders assets with correct type icons', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check for various asset type icons
        expect(screen.getByTestId('server-icon')).toBeInTheDocument();
        expect(screen.getByTestId('database-icon')).toBeInTheDocument();
        expect(screen.getByTestId('router-icon')).toBeInTheDocument();
        expect(screen.getByTestId('harddrive-icon')).toBeInTheDocument();
        expect(screen.getByTestId('shield-icon')).toBeInTheDocument();
        expect(screen.getByTestId('cloud-icon')).toBeInTheDocument();
        expect(screen.getByTestId('zap-icon')).toBeInTheDocument();
      });
    });

    it('displays 6R readiness badges correctly', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check for 6R readiness indicators
        expect(screen.getAllByText('Ready')).toHaveLength(3); // Server, App, DB
        expect(screen.getAllByText('Not Applicable')).toHaveLength(3); // Devices
        expect(screen.getByText('Complex Analysis Required')).toBeInTheDocument(); // Virtualization
        expect(screen.getByText('Type Classification Needed')).toBeInTheDocument(); // Unknown
      });
    });

    it('shows migration complexity indicators', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check for complexity indicators
        expect(screen.getAllByText('Low')).toHaveLength(3); // Devices
        expect(screen.getAllByText('Medium')).toHaveLength(2); // Server, Unknown
        expect(screen.getAllByText('High')).toHaveLength(3); // App, DB, Virtualization
      });
    });

    it('displays asset details correctly', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check asset names
        expect(screen.getByText('web-server-01')).toBeInTheDocument();
        expect(screen.getByText('CRM_System')).toBeInTheDocument();
        expect(screen.getByText('mysql-prod-01')).toBeInTheDocument();
        expect(screen.getByText('core-switch-01')).toBeInTheDocument();
        expect(screen.getByText('SAN01')).toBeInTheDocument();
        expect(screen.getByText('firewall-perimeter')).toBeInTheDocument();
        expect(screen.getByText('vmware-vcenter')).toBeInTheDocument();
        expect(screen.getByText('mystery-device')).toBeInTheDocument();

        // Check asset types
        expect(screen.getByText('Server')).toBeInTheDocument();
        expect(screen.getByText('Application')).toBeInTheDocument();
        expect(screen.getByText('Database')).toBeInTheDocument();
        expect(screen.getByText('Network Device')).toBeInTheDocument();
        expect(screen.getByText('Storage Device')).toBeInTheDocument();
        expect(screen.getByText('Security Device')).toBeInTheDocument();
        expect(screen.getByText('Virtualization Platform')).toBeInTheDocument();
        expect(screen.getByText('Unknown')).toBeInTheDocument();
      });
    });
  });

  describe('Enhanced Filtering', () => {
    it('includes all device types in filter dropdown', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        const filterSelect = screen.getByDisplayValue('All Types');
        expect(filterSelect).toBeInTheDocument();

        // Check that all device type options exist
        fireEvent.click(filterSelect);
        expect(screen.getByText('Network Devices')).toBeInTheDocument();
        expect(screen.getByText('Storage Devices')).toBeInTheDocument();
        expect(screen.getByText('Security Devices')).toBeInTheDocument();
        expect(screen.getByText('Infrastructure')).toBeInTheDocument();
        expect(screen.getByText('Virtualization')).toBeInTheDocument();
        expect(screen.getByText('Unknown')).toBeInTheDocument();
      });
    });

    it('filters assets correctly by device type', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        const filterSelect = screen.getByDisplayValue('All Types');

        // Filter by Network Devices
        fireEvent.change(filterSelect, { target: { value: 'network_device' } });

        // Should only show network devices
        expect(screen.getByText('core-switch-01')).toBeInTheDocument();
        expect(screen.queryByText('web-server-01')).not.toBeInTheDocument();
        expect(screen.queryByText('SAN01')).not.toBeInTheDocument();
      });
    });

    it('filters assets by security devices', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        const filterSelect = screen.getByDisplayValue('All Types');

        // Filter by Security Devices
        fireEvent.change(filterSelect, { target: { value: 'security_device' } });

        // Should only show security devices
        expect(screen.getByText('firewall-perimeter')).toBeInTheDocument();
        expect(screen.queryByText('core-switch-01')).not.toBeInTheDocument();
        expect(screen.queryByText('web-server-01')).not.toBeInTheDocument();
      });
    });
  });

  describe('Data Source Indicators', () => {
    it('shows live data indicator correctly', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Live Data:/)).toBeInTheDocument();
        expect(screen.getByText(/Showing 8 processed assets from CMDB import/)).toBeInTheDocument();
      });
    });

    it('displays last updated timestamp', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('has a refresh button that calls the API', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        const refreshButton = screen.getByText('Refresh');
        expect(refreshButton).toBeInTheDocument();
      });

      // Click refresh button
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      // Should call API again
      await waitFor(() => {
        expect(apiCall).toHaveBeenCalledTimes(2); // Once on mount, once on refresh
      });
    });

    it('shows loading state during refresh', async () => {
      // Mock a delayed response
      apiCall.mockImplementation(() => new Promise(resolve =>
        setTimeout(() => resolve(mockAssetData), 1000)
      ));

      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      // Click refresh button
      const refreshButton = await screen.findByText('Refresh');
      fireEvent.click(refreshButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByTestId('refresh-icon')).toHaveClass('animate-spin');
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      apiCall.mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument();
        expect(screen.getByText(/Unable to load data/)).toBeInTheDocument();
      });
    });

    it('shows empty state when no assets found', async () => {
      apiCall.mockResolvedValue({
        assets: [],
        summary: {
          total: 0,
          applications: 0,
          servers: 0,
          databases: 0,
          devices: 0,
          unknown: 0,
          discovered: 0,
          pending: 0,
          device_breakdown: {
            network: 0,
            storage: 0,
            security: 0,
            infrastructure: 0,
            virtualization: 0
          }
        },
        dataSource: 'live',
        lastUpdated: null
      });

      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('No assets found')).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    it('has an export CSV button', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        const exportButton = screen.getByText('Export CSV');
        expect(exportButton).toBeInTheDocument();
        expect(screen.getByTestId('download-icon')).toBeInTheDocument();
      });
    });
  });

  describe('Suggested Headers', () => {
    it('displays AI-generated headers information', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Should show the header information even for live data
        const headers = mockAssetData.suggestedHeaders.map(h => h.label).join(', ');
        // Check if any of the header labels are displayed
        expect(screen.getByText('Asset ID')).toBeInTheDocument();
        expect(screen.getByText('Type')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    it('maintains layout structure', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check main layout elements
        expect(screen.getByTestId('sidebar')).toBeInTheDocument();
        expect(screen.getByTestId('feedback-widget')).toBeInTheDocument();

        // Check responsive grid classes exist
        const summarySection = screen.getByText('Applications').closest('div');
        expect(summarySection).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check table structure
        const table = screen.getByRole('table');
        expect(table).toBeInTheDocument();

        // Check buttons
        const refreshButton = screen.getByRole('button', { name: /refresh/i });
        expect(refreshButton).toBeInTheDocument();

        const exportButton = screen.getByRole('button', { name: /export csv/i });
        expect(exportButton).toBeInTheDocument();
      });
    });

    it('has proper form controls', async () => {
      render(
        <TestWrapper>
          <Inventory />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check select elements
        const typeFilter = screen.getByDisplayValue('All Types');
        expect(typeFilter).toBeInTheDocument();

        const deptFilter = screen.getByDisplayValue('All Departments');
        expect(deptFilter).toBeInTheDocument();
      });
    });
  });
});

describe('Asset Inventory Agentic Workflow Preservation', () => {
  it('does not override agentic classification with hard-coded rules', async () => {
    // Mock data with agentic classifications
    const agenticData = {
      ...mockAssetData,
      assets: [
        {
          id: 'AGT001',
          type: 'Custom_Application_Type',
          name: 'agentic-classified-asset',
          techStack: 'Unknown',
          department: 'AI Team',
          status: 'Discovered',
          environment: 'Production',
          criticality: 'Medium',
          sixr_ready: 'Ready',
          migration_complexity: 'Low',
          agentic_confidence: 0.95
        }
      ]
    };

    apiCall.mockResolvedValue(agenticData);

    render(
      <TestWrapper>
        <Inventory />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should display agentic classification as-is
      expect(screen.getByText('Custom_Application_Type')).toBeInTheDocument();
      expect(screen.getByText('agentic-classified-asset')).toBeInTheDocument();
    });
  });

  it('supports extensible asset types from agentic learning', async () => {
    const extensibleData = {
      ...mockAssetData,
      assets: [
        {
          id: 'EXT001',
          type: 'IoT_Sensor_Network',
          name: 'temperature-sensors',
          techStack: 'Custom IoT Platform',
          department: 'Facilities',
          status: 'Discovered',
          environment: 'Production',
          criticality: 'Low',
          sixr_ready: 'Not Applicable',
          migration_complexity: 'Low'
        }
      ]
    };

    apiCall.mockResolvedValue(extensibleData);

    render(
      <TestWrapper>
        <Inventory />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should handle unknown asset types gracefully
      expect(screen.getByText('IoT_Sensor_Network')).toBeInTheDocument();
    });
  });
});
