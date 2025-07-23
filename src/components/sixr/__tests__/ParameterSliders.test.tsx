import type React from 'react';
import type { fireEvent } from '@testing-library/react'
import { render, screen, waitFor } from '@testing-library/react'
import type userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ParameterSliders from '../ParameterSliders'
import type { type SixRParameters } from '../ParameterSliders'

// Mock the toast function
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn()
  }
}));

describe('ParameterSliders', () => {
  const defaultParameters: SixRParameters = {
    business_value: 5,
    technical_complexity: 5,
    migration_urgency: 5,
    compliance_requirements: 5,
    cost_sensitivity: 5,
    risk_tolerance: 5,
    innovation_priority: 5,
    application_type: 'custom'
  };

  const mockOnParametersChange = vi.fn();
  const mockOnSave = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all parameter sliders with correct initial values', () => {
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    // Check that all sliders are rendered
    expect(screen.getByLabelText(/business value/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/technical complexity/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/migration urgency/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/compliance requirements/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cost sensitivity/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/risk tolerance/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/innovation priority/i)).toBeInTheDocument();

    // Check initial values
    const businessValueSlider = screen.getByLabelText(/business value/i);
    expect(businessValueSlider).toHaveValue('5');
  });

  it('renders application type selector when showApplicationType is true', () => {
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
        showApplicationType={true}
      />
    );

    expect(screen.getByText(/application type/i)).toBeInTheDocument();
    expect(screen.getByText(/custom/i)).toBeInTheDocument();
    expect(screen.getByText(/cots/i)).toBeInTheDocument();
    expect(screen.getByText(/hybrid/i)).toBeInTheDocument();
  });

  it('calls onParametersChange when slider value changes', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const businessValueSlider = screen.getByLabelText(/business value/i);
    
    // Change slider value
    await user.clear(businessValueSlider);
    await user.type(businessValueSlider, '8');

    await waitFor(() => {
      expect(mockOnParametersChange).toHaveBeenCalledWith({
        ...defaultParameters,
        business_value: 8
      });
    });
  });

  it('calls onParametersChange when application type changes', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
        showApplicationType={true}
      />
    );

    // Click on COTS option
    const cotsOption = screen.getByText(/cots/i);
    await user.click(cotsOption);

    await waitFor(() => {
      expect(mockOnParametersChange).toHaveBeenCalledWith({
        ...defaultParameters,
        application_type: 'cots'
      });
    });
  });

  it('shows COTS warning when COTS application type is selected', async () => {
    const user = userEvent.setup();
    
    const cotsParameters = { ...defaultParameters, application_type: 'cots' as const };
    
    render(
      <ParameterSliders
        parameters={cotsParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
        showApplicationType={true}
      />
    );

    expect(screen.getByText(/cots applications have limited migration options/i)).toBeInTheDocument();
  });

  it('displays parameter level indicators correctly', () => {
    const highValueParameters = {
      ...defaultParameters,
      business_value: 9,
      technical_complexity: 2,
      innovation_priority: 10
    };

    render(
      <ParameterSliders
        parameters={highValueParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    // Check for high business value indicator
    expect(screen.getByText(/high/i)).toBeInTheDocument();
    
    // Check for low technical complexity indicator
    expect(screen.getByText(/low/i)).toBeInTheDocument();
  });

  it('shows tooltips on hover', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    // Find tooltip trigger (info icon)
    const tooltipTrigger = screen.getAllByRole('button')[0]; // First info icon
    
    await user.hover(tooltipTrigger);

    // Tooltip content should appear
    await waitFor(() => {
      expect(screen.getByText(/strategic importance/i)).toBeInTheDocument();
    });
  });

  it('calls onSave when save button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const saveButton = screen.getByText(/save parameters/i);
    await user.click(saveButton);

    expect(mockOnSave).toHaveBeenCalled();
  });

  it('resets parameters when reset button is clicked', async () => {
    const user = userEvent.setup();
    
    const modifiedParameters = {
      ...defaultParameters,
      business_value: 8,
      technical_complexity: 3
    };

    render(
      <ParameterSliders
        parameters={modifiedParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const resetButton = screen.getByText(/reset to defaults/i);
    await user.click(resetButton);

    expect(mockOnParametersChange).toHaveBeenCalledWith({
      business_value: 5,
      technical_complexity: 5,
      migration_urgency: 5,
      compliance_requirements: 5,
      cost_sensitivity: 5,
      risk_tolerance: 5,
      innovation_priority: 5,
      application_type: 'custom'
    });
  });

  it('disables all controls when disabled prop is true', () => {
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
        disabled={true}
      />
    );

    // All sliders should be disabled
    const sliders = screen.getAllByRole('slider');
    sliders.forEach(slider => {
      expect(slider).toBeDisabled();
    });

    // Save button should be disabled
    const saveButton = screen.getByText(/save parameters/i);
    expect(saveButton).toBeDisabled();
  });

  it('shows parameter summary with correct values', () => {
    const testParameters = {
      ...defaultParameters,
      business_value: 8,
      technical_complexity: 3,
      innovation_priority: 9
    };

    render(
      <ParameterSliders
        parameters={testParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    // Check parameter summary
    expect(screen.getByText(/parameter summary/i)).toBeInTheDocument();
    expect(screen.getByText(/8/)).toBeInTheDocument(); // Business value
    expect(screen.getByText(/3/)).toBeInTheDocument(); // Technical complexity
    expect(screen.getByText(/9/)).toBeInTheDocument(); // Innovation priority
  });

  it('validates parameter ranges', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const businessValueSlider = screen.getByLabelText(/business value/i);
    
    // Try to set value above maximum (10)
    await user.clear(businessValueSlider);
    await user.type(businessValueSlider, '15');

    // Value should be clamped to maximum
    await waitFor(() => {
      expect(mockOnParametersChange).toHaveBeenCalledWith({
        ...defaultParameters,
        business_value: 10
      });
    });
  });

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const businessValueSlider = screen.getByLabelText(/business value/i);
    
    // Focus the slider
    await user.click(businessValueSlider);
    
    // Use arrow keys to change value
    await user.keyboard('{ArrowRight}');

    await waitFor(() => {
      expect(mockOnParametersChange).toHaveBeenCalledWith({
        ...defaultParameters,
        business_value: 6
      });
    });
  });

  it('shows real-time visual feedback during parameter changes', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const businessValueSlider = screen.getByLabelText(/business value/i);
    
    // Change value and check for visual feedback
    await user.clear(businessValueSlider);
    await user.type(businessValueSlider, '9');

    // Should show high value indicator
    await waitFor(() => {
      expect(screen.getByText(/high/i)).toBeInTheDocument();
    });
  });

  it('handles edge case values correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    const businessValueSlider = screen.getByLabelText(/business value/i);
    
    // Test minimum value
    await user.clear(businessValueSlider);
    await user.type(businessValueSlider, '1');

    await waitFor(() => {
      expect(mockOnParametersChange).toHaveBeenCalledWith({
        ...defaultParameters,
        business_value: 1
      });
    });

    // Test maximum value
    await user.clear(businessValueSlider);
    await user.type(businessValueSlider, '10');

    await waitFor(() => {
      expect(mockOnParametersChange).toHaveBeenCalledWith({
        ...defaultParameters,
        business_value: 10
      });
    });
  });

  it('maintains responsive design on different screen sizes', () => {
    // Test mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(
      <ParameterSliders
        parameters={defaultParameters}
        onParametersChange={mockOnParametersChange}
        onSave={mockOnSave}
      />
    );

    // Component should still render all elements
    expect(screen.getByLabelText(/business value/i)).toBeInTheDocument();
    expect(screen.getByText(/save parameters/i)).toBeInTheDocument();
  });
}); 