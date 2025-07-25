/**
 * Test suite to verify the modularized SixRReviewPage maintains identical behavior
 * Created by CC to ensure backward compatibility after modularization
 */

import React from 'react';
import { fireEvent, waitFor } from '@testing-library/react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SixROverallStats } from '../SixROverallStats';
import { SixRAppDecisionSummary } from '../SixRAppDecisionSummary';
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
      render(
        <SixRAppDecisionSummary
          selectedApp="test-app"
          decision={mockDecision}
        />
      );

      expect(screen.getByText('test-app Strategy')).toBeInTheDocument();
      expect(screen.getByText('Test rationale')).toBeInTheDocument();
      expect(screen.getByText('High complexity')).toBeInTheDocument();
      expect(screen.getByText('Legacy dependencies')).toBeInTheDocument();
    });

    it('should display confidence score', () => {
      render(
        <SixRAppDecisionSummary
          selectedApp="test-app"
          decision={mockDecision}
        />
      );

      expect(screen.getByTestId('confidence-indicator')).toHaveTextContent('0.8');
    });
  });

  describe('SixRActionButtons Component', () => {
    const mockProps = {
      isDraft: false,
      isSubmitting: false,
      isLoading: false,
      selectedApp: 'test-app',
      onSaveDraft: jest.fn(),
      onSubmit: jest.fn()
    };

    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('should render save and submit buttons', () => {
      render(<SixRActionButtons {...mockProps} />);

      expect(screen.getByText('Save Progress')).toBeInTheDocument();
      expect(screen.getByText('Continue to Application Review')).toBeInTheDocument();
    });

    it('should call onSaveDraft when save button is clicked', () => {
      render(<SixRActionButtons {...mockProps} />);

      fireEvent.click(screen.getByText('Save Progress'));
      expect(mockProps.onSaveDraft).toHaveBeenCalledTimes(1);
    });

    it('should call onSubmit when submit button is clicked', () => {
      render(<SixRActionButtons {...mockProps} />);

      fireEvent.click(screen.getByText('Continue to Application Review'));
      expect(mockProps.onSubmit).toHaveBeenCalledTimes(1);
    });

    it('should disable buttons when submitting', () => {
      render(<SixRActionButtons {...mockProps} isSubmitting={true} />);

      const submitButton = screen.getByText('Processing...');
      expect(submitButton.closest('button')).toBeDisabled();
    });
  });

  describe('SixRStatusAlert Component', () => {
    it('should render error alert', () => {
      render(<SixRStatusAlert status="error" error="Test error message" />);

      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('should render processing alert', () => {
      render(<SixRStatusAlert status="processing" />);

      expect(screen.getByText(/AI agents are analyzing/)).toBeInTheDocument();
    });

    it('should render nothing for idle status', () => {
      const { container } = render(<SixRStatusAlert status="idle" />);

      expect(container.firstChild).toBeNull();
    });
  });
});
