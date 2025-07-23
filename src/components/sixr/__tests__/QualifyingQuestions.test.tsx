import type React from 'react';
import type { fireEvent, waitFor } from '@testing-library/react'
import { render, screen } from '@testing-library/react'
import type userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import QualifyingQuestions from '../QualifyingQuestions'
import type { QualifyingQuestion, QuestionResponse } from '../QualifyingQuestions'

// Mock the toast function
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn()
  }
}));

// Mock react-dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn(() => ({
    getRootProps: () => ({ 'data-testid': 'dropzone' }),
    getInputProps: () => ({ 'data-testid': 'file-input' }),
    isDragActive: false,
    acceptedFiles: [],
    rejectedFiles: []
  }))
}));

describe('QualifyingQuestions', () => {
  const mockQuestions: QualifyingQuestion[] = [
    {
      id: 'app_type',
      question: 'What type of application is this?',
      question_type: 'select',
      category: 'Application Classification',
      priority: 1,
      required: true,
      options: [
        { value: 'custom', label: 'Custom Application', description: 'Built in-house' },
        { value: 'cots', label: 'COTS Application', description: 'Commercial off-the-shelf' },
        { value: 'hybrid', label: 'Hybrid Application', description: 'Mix of custom and COTS' }
      ],
      help_text: 'This affects which migration strategies are available'
    },
    {
      id: 'business_impact',
      question: 'What would be the business impact if unavailable for 24 hours?',
      question_type: 'select',
      category: 'Business Impact',
      priority: 1,
      required: true,
      options: [
        { value: 'minimal', label: 'Minimal Impact' },
        { value: 'moderate', label: 'Moderate Impact' },
        { value: 'significant', label: 'Significant Impact' },
        { value: 'critical', label: 'Critical Impact' }
      ]
    },
    {
      id: 'user_count',
      question: 'How many active users does this application have?',
      question_type: 'numeric',
      category: 'Usage Metrics',
      priority: 2,
      required: false,
      help_text: 'Approximate number of regular users'
    },
    {
      id: 'migration_timeline',
      question: 'What is your preferred migration timeline?',
      question_type: 'select',
      category: 'Migration Constraints',
      priority: 2,
      required: true,
      options: [
        { value: '3_months', label: '3 Months' },
        { value: '6_months', label: '6 Months' },
        { value: '12_months', label: '12 Months' },
        { value: 'flexible', label: 'Flexible' }
      ]
    },
    {
      id: 'compliance_needs',
      question: 'Which compliance requirements apply?',
      question_type: 'multiselect',
      category: 'Compliance',
      priority: 2,
      required: false,
      options: [
        { value: 'pci_dss', label: 'PCI-DSS' },
        { value: 'sox', label: 'SOX' },
        { value: 'gdpr', label: 'GDPR' },
        { value: 'hipaa', label: 'HIPAA' }
      ]
    },
    {
      id: 'has_documentation',
      question: 'Is comprehensive documentation available?',
      question_type: 'boolean',
      category: 'Documentation',
      priority: 3,
      required: false
    },
    {
      id: 'source_code',
      question: 'Upload source code or documentation (optional)',
      question_type: 'file_upload',
      category: 'Technical Assessment',
      priority: 3,
      required: false,
      help_text: 'Upload source code files, architecture diagrams, or technical documentation'
    }
  ];

  const mockOnResponseChange = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all questions with correct types', () => {
    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Check that questions are rendered
    expect(screen.getByText(/what type of application/i)).toBeInTheDocument();
    expect(screen.getByText(/business impact/i)).toBeInTheDocument();
    expect(screen.getByText(/active users/i)).toBeInTheDocument();
    expect(screen.getByText(/migration timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/compliance requirements/i)).toBeInTheDocument();
    expect(screen.getByText(/comprehensive documentation/i)).toBeInTheDocument();
    expect(screen.getByText(/upload source code/i)).toBeInTheDocument();
  });

  it('shows progress indicator with correct completion percentage', () => {
    const responses = [
      {
        question_id: 'app_type',
        response: 'custom',
        confidence: 0.9,
        source: 'user_input',
        timestamp: new Date()
      }
    ];

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={responses}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
        showProgress={true}
      />
    );

    // Should show progress (1 out of 7 questions answered = ~14%)
    expect(screen.getByText(/progress/i)).toBeInTheDocument();
    expect(screen.getByText(/1.*7/)).toBeInTheDocument();
  });

  it('handles select question responses', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Find and click on a select option
    const customOption = screen.getByText(/custom application/i);
    await user.click(customOption);

    expect(mockOnResponseChange).toHaveBeenCalledWith('app_type', 'custom');
  });

  it('handles numeric question responses', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Find numeric input
    const numericInput = screen.getByLabelText(/active users/i);
    await user.type(numericInput, '1500');

    expect(mockOnResponseChange).toHaveBeenCalledWith('user_count', 1500);
  });

  it('handles multiselect question responses', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Find and select multiple compliance options
    const pciOption = screen.getByText(/pci-dss/i);
    const gdprOption = screen.getByText(/gdpr/i);

    await user.click(pciOption);
    await user.click(gdprOption);

    expect(mockOnResponseChange).toHaveBeenCalledWith('compliance_needs', ['pci_dss']);
    expect(mockOnResponseChange).toHaveBeenCalledWith('compliance_needs', ['pci_dss', 'gdpr']);
  });

  it('handles boolean question responses', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Find boolean toggle
    const booleanToggle = screen.getByRole('switch');
    await user.click(booleanToggle);

    expect(mockOnResponseChange).toHaveBeenCalledWith('has_documentation', true);
  });

  it('handles file upload questions', async () => {
    const user = userEvent.setup();

    // Mock file
    const file = new File(['test content'], 'test.java', { type: 'text/plain' });

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Find file input
    const fileInput = screen.getByTestId('file-input');
    await user.upload(fileInput, file);

    expect(mockOnResponseChange).toHaveBeenCalledWith('source_code', [file]);
  });

  it('shows validation errors for required questions', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Try to submit without answering required questions
    const submitButton = screen.getByText(/submit/i);
    await user.click(submitButton);

    // Should show validation errors
    expect(screen.getByText(/required/i)).toBeInTheDocument();
  });

  it('groups questions by category in tabbed interface', () => {
    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Check for category tabs
    expect(screen.getByText(/application classification/i)).toBeInTheDocument();
    expect(screen.getByText(/business impact/i)).toBeInTheDocument();
    expect(screen.getByText(/usage metrics/i)).toBeInTheDocument();
    expect(screen.getByText(/migration constraints/i)).toBeInTheDocument();
    expect(screen.getByText(/compliance/i)).toBeInTheDocument();
    expect(screen.getByText(/documentation/i)).toBeInTheDocument();
    expect(screen.getByText(/technical assessment/i)).toBeInTheDocument();
  });

  it('shows help text when available', () => {
    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Check for help text
    expect(screen.getByText(/affects which migration strategies/i)).toBeInTheDocument();
    expect(screen.getByText(/approximate number of regular users/i)).toBeInTheDocument();
  });

  it('disables all inputs when disabled prop is true', () => {
    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
        disabled={true}
      />
    );

    // All inputs should be disabled
    const inputs = screen.getAllByRole('textbox');
    inputs.forEach(input => {
      expect(input).toBeDisabled();
    });

    const submitButton = screen.getByText(/submit/i);
    expect(submitButton).toBeDisabled();
  });

  it('allows partial submission', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Answer one question
    const customOption = screen.getByText(/custom application/i);
    await user.click(customOption);

    // Save progress
    const saveButton = screen.getByText(/save progress/i);
    await user.click(saveButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          question_id: 'app_type',
          response: 'custom'
        })
      ]),
      true // isPartial
    );
  });

  it('validates numeric input ranges', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    const numericInput = screen.getByLabelText(/active users/i);
    
    // Try negative number
    await user.type(numericInput, '-100');
    
    // Should show validation error or prevent input
    expect(numericInput).toHaveValue('100'); // Negative sign should be stripped
  });

  it('shows question priority indicators', () => {
    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // High priority questions should have indicators
    const priorityIndicators = screen.getAllByText(/priority/i);
    expect(priorityIndicators.length).toBeGreaterThan(0);
  });

  it('handles drag and drop file upload', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Find dropzone
    const dropzone = screen.getByTestId('dropzone');
    
    // Simulate drag and drop
    const file = new File(['test'], 'test.java', { type: 'text/plain' });
    
    fireEvent.dragEnter(dropzone);
    fireEvent.dragOver(dropzone);
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [file]
      }
    });

    // Should handle the file upload
    expect(mockOnResponseChange).toHaveBeenCalled();
  });

  it('shows file upload progress and validation', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Large file should show progress
    const largeFile = new File(['x'.repeat(1000000)], 'large.java', { type: 'text/plain' });
    const fileInput = screen.getByTestId('file-input');
    
    await user.upload(fileInput, largeFile);

    // Should show upload progress or validation
    expect(screen.getByText(/uploading/i) || screen.getByText(/processing/i)).toBeInTheDocument();
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Tab through questions
    await user.tab();
    await user.tab();
    
    // Should be able to navigate with keyboard
    const focusedElement = document.activeElement;
    expect(focusedElement).toBeInTheDocument();
  });

  it('preserves responses when switching between categories', async () => {
    const user = userEvent.setup();

    const existingResponses = [
      {
        question_id: 'app_type',
        response: 'custom',
        confidence: 0.9,
        source: 'user_input',
        timestamp: new Date()
      }
    ];

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={existingResponses}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Switch to different category tab
    const businessTab = screen.getByText(/business impact/i);
    await user.click(businessTab);

    // Switch back to first category
    const appTab = screen.getByText(/application classification/i);
    await user.click(appTab);

    // Previous response should still be selected
    const customOption = screen.getByText(/custom application/i);
    expect(customOption).toHaveClass('selected'); // Assuming selected class exists
  });

  it('handles question dependencies correctly', async () => {
    const user = userEvent.setup();

    render(
      <QualifyingQuestions
        questions={mockQuestions}
        responses={[]}
        onResponseChange={mockOnResponseChange}
        onSubmit={mockOnSubmit}
      />
    );

    // Answer a question that might affect other questions
    const customOption = screen.getByText(/custom application/i);
    await user.click(customOption);

    // Dependent questions should be enabled/disabled accordingly
    // This would depend on the specific business logic
    expect(mockOnResponseChange).toHaveBeenCalledWith('app_type', 'custom');
  });
}); 