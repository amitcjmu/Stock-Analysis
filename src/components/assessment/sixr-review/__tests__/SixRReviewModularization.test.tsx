/**
 * Test suite to verify the modularized SixRReviewPage maintains identical behavior
 * Created by CC to ensure backward compatibility after modularization
 */

import React from 'react';
import type { fireEvent, waitFor } from '@testing-library/react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SixROverallStats } from '../SixROverallStats';
import type { SixRAppDecisionSummary } from '../SixRAppDecisionSummary';
import { SixRActionButtons } from '../SixRActionButtons';
import { SixRStatusAlert } from '../SixRStatusAlert';

// Mock the UI components
interface MockComponentProps {
  children?: React.ReactNode;
  className?: string;
  [key: string]: unknown;
}

interface MockButtonProps extends MockComponentProps {
  onClick?: () => void;
  disabled?: boolean;
}

jest.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: MockComponentProps) => <div data-testid="card" {...props}>{children}</div>,
  CardContent: ({ children, ...props }: MockComponentProps) => <div data-testid="card-content" {...props}>{children}</div>,
  CardDescription: ({ children, ...props }: MockComponentProps) => <div data-testid="card-description" {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: MockComponentProps) => <div data-testid="card-header" {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: MockComponentProps) => <div data-testid="card-title" {...props}>{children}</div>,
}));

jest.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className, ...props }: MockComponentProps) => <span className={className} data-testid="badge" {...props}>{children}</span>
}));

jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, ...props }: MockButtonProps) => (
    <button onClick={onClick} disabled={disabled} data-testid="button" {...props}>
      {children}
    </button>
  )
}));

jest.mock('@/components/assessment/ConfidenceScoreIndicator', () => ({
  ConfidenceScoreIndicator: ({ score }: { score: number }) => <div data-testid="confidence-indicator">{score}</div>
}));

describe('SixR Review Modularization', () => {
  const mockStatistics = {
    totalApps: 5,
    assessed: 3,
    avgConfidence: 0.85,
    needsReview: 1,
    hasIssues: 0,
    strategyCount: {
      rehost: 1,
      replatform: 1,
      refactor: 1,
      repurchase: 0,
      retire: 0,
      retain: 0
    }
  };

  const mockDecision = {
    overall_strategy: 'rehost',
    confidence_score: 0.8,
    rationale: 'Test rationale',
    risk_factors: ['High complexity', 'Legacy dependencies'],
    architecture_exceptions: ['Custom networking'],
    move_group_hints: ['Database cluster'],
    component_treatments: []
  };

  describe('SixROverallStats Component', () => {
    it('should render statistics correctly', () => {
      render(<SixROverallStats statistics={mockStatistics} />);
      
      expect(screen.getByText('3/5')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('6R Strategy Overview')).toBeInTheDocument();
    });

    it('should display strategy distribution', () => {
      render(<SixROverallStats statistics={mockStatistics} />);
      
      expect(screen.getByText('Rehost (Lift & Shift)')).toBeInTheDocument();
      expect(screen.getByText('Replatform (Lift & Reshape)')).toBeInTheDocument();
    });
  });

  describe('SixRAppDecisionSummary Component', () => {
    it('should render application decision details', () => {
      render(\n        <SixRAppDecisionSummary \n          selectedApp=\"test-app\" \n          decision={mockDecision} \n        />\n      );\n      \n      expect(screen.getByText('test-app Strategy')).toBeInTheDocument();\n      expect(screen.getByText('Test rationale')).toBeInTheDocument();\n      expect(screen.getByText('High complexity')).toBeInTheDocument();\n      expect(screen.getByText('Legacy dependencies')).toBeInTheDocument();\n    });\n\n    it('should display confidence score', () => {\n      render(\n        <SixRAppDecisionSummary \n          selectedApp=\"test-app\" \n          decision={mockDecision} \n        />\n      );\n      \n      expect(screen.getByTestId('confidence-indicator')).toHaveTextContent('0.8');\n    });\n  });\n\n  describe('SixRActionButtons Component', () => {\n    const mockProps = {\n      isDraft: false,\n      isSubmitting: false,\n      isLoading: false,\n      selectedApp: 'test-app',\n      onSaveDraft: jest.fn(),\n      onSubmit: jest.fn()\n    };\n\n    beforeEach(() => {\n      jest.clearAllMocks();\n    });\n\n    it('should render save and submit buttons', () => {\n      render(<SixRActionButtons {...mockProps} />);\n      \n      expect(screen.getByText('Save Progress')).toBeInTheDocument();\n      expect(screen.getByText('Continue to Application Review')).toBeInTheDocument();\n    });\n\n    it('should call onSaveDraft when save button is clicked', () => {\n      render(<SixRActionButtons {...mockProps} />);\n      \n      fireEvent.click(screen.getByText('Save Progress'));\n      expect(mockProps.onSaveDraft).toHaveBeenCalledTimes(1);\n    });\n\n    it('should call onSubmit when submit button is clicked', () => {\n      render(<SixRActionButtons {...mockProps} />);\n      \n      fireEvent.click(screen.getByText('Continue to Application Review'));\n      expect(mockProps.onSubmit).toHaveBeenCalledTimes(1);\n    });\n\n    it('should disable buttons when submitting', () => {\n      render(<SixRActionButtons {...mockProps} isSubmitting={true} />);\n      \n      const submitButton = screen.getByText('Processing...');\n      expect(submitButton.closest('button')).toBeDisabled();\n    });\n  });\n\n  describe('SixRStatusAlert Component', () => {\n    it('should render error alert', () => {\n      render(<SixRStatusAlert status=\"error\" error=\"Test error message\" />);\n      \n      expect(screen.getByText('Test error message')).toBeInTheDocument();\n    });\n\n    it('should render processing alert', () => {\n      render(<SixRStatusAlert status=\"processing\" />);\n      \n      expect(screen.getByText(/AI agents are analyzing/)).toBeInTheDocument();\n    });\n\n    it('should render nothing for idle status', () => {\n      const { container } = render(<SixRStatusAlert status=\"idle\" />);\n      \n      expect(container.firstChild).toBeNull();\n    });\n  });\n});"