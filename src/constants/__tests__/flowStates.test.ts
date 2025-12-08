import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { isFlowTerminal, KNOWN_STATUSES, TERMINAL_STATES } from '../flowStates';
import SecureLogger from '../../utils/secureLogger';

// Mock SecureLogger
vi.mock('../../utils/secureLogger', () => ({
  default: {
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    debug: vi.fn(),
  },
}));

describe('flowStates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('isFlowTerminal', () => {
    describe('terminal states', () => {
      it('should return true for all terminal states', () => {
        TERMINAL_STATES.forEach(status => {
          expect(isFlowTerminal(status)).toBe(true);
          expect(isFlowTerminal(status.toUpperCase())).toBe(true);
          expect(isFlowTerminal(status.charAt(0).toUpperCase() + status.slice(1))).toBe(true);
        });
      });

      it('should not log warnings for known terminal states', () => {
        TERMINAL_STATES.forEach(status => {
          isFlowTerminal(status);
        });
        expect(SecureLogger.warn).not.toHaveBeenCalled();
      });
    });

    describe('known non-terminal states', () => {
      const knownNonTerminalStates = [
        'running',
        'processing',
        'validating',
        'paused',
        'waiting_for_approval',
        'waiting_for_user_approval',
        'pending',
        'queued',
        'starting',
        'initializing',
        'waiting',
        'retry',
        'timeout',
        'rollback'
      ];

      it('should return false for known non-terminal states', () => {
        knownNonTerminalStates.forEach(status => {
          expect(isFlowTerminal(status)).toBe(false);
          expect(isFlowTerminal(status.toUpperCase())).toBe(false);
        });
      });

      it('should not log warnings for known non-terminal states', () => {
        knownNonTerminalStates.forEach(status => {
          isFlowTerminal(status);
        });
        expect(SecureLogger.warn).not.toHaveBeenCalled();
      });
    });

    describe('edge cases - null and undefined', () => {
      it('should return false for null', () => {
        expect(isFlowTerminal(null)).toBe(false);
        expect(SecureLogger.warn).not.toHaveBeenCalled();
      });

      it('should return false for undefined', () => {
        expect(isFlowTerminal(undefined)).toBe(false);
        expect(SecureLogger.warn).not.toHaveBeenCalled();
      });

      it('should return false for empty string', () => {
        expect(isFlowTerminal('')).toBe(false);
        // Empty string is falsy, so it returns early and doesn't log
        expect(SecureLogger.warn).not.toHaveBeenCalled();
      });
    });

    describe('unknown statuses', () => {
      const unknownStatuses = [
        'unknown_status',
        'invalid_state',
        'custom_status',
        'test_status',
        'xyz123',
        'UNKNOWN',
        'InvalidState',
        'custom-status',
        'status_with_underscores_and_numbers_123'
      ];

      it('should return false for unknown statuses', () => {
        unknownStatuses.forEach(status => {
          expect(isFlowTerminal(status)).toBe(false);
        });
      });

      it('should log warnings for unknown statuses', () => {
        unknownStatuses.forEach(status => {
          isFlowTerminal(status);
        });

        // Should be called once for each unknown status
        expect(SecureLogger.warn).toHaveBeenCalledTimes(unknownStatuses.length);

        // Verify the warning format
        unknownStatuses.forEach((status, index) => {
          const normalizedStatus = status.toLowerCase();
          expect(SecureLogger.warn).toHaveBeenNthCalledWith(
            index + 1,
            'Unknown flow status encountered',
            {
              status,
              normalizedStatus,
              context: 'terminal_state_check'
            }
          );
        });
      });

      it('should handle case-insensitive unknown statuses correctly', () => {
        const status = 'UNKNOWN_STATUS';
        isFlowTerminal(status);

        expect(SecureLogger.warn).toHaveBeenCalledWith(
          'Unknown flow status encountered',
          {
            status: 'UNKNOWN_STATUS',
            normalizedStatus: 'unknown_status',
            context: 'terminal_state_check'
          }
        );
      });
    });

    describe('case insensitivity', () => {
      it('should handle mixed case for terminal states', () => {
        expect(isFlowTerminal('COMPLETED')).toBe(true);
        expect(isFlowTerminal('Completed')).toBe(true);
        expect(isFlowTerminal('cOmPlEtEd')).toBe(true);
      });

      it('should handle mixed case for known non-terminal states', () => {
        expect(isFlowTerminal('RUNNING')).toBe(false);
        expect(isFlowTerminal('Running')).toBe(false);
        expect(isFlowTerminal('rUnNiNg')).toBe(false);
      });

      it('should normalize unknown statuses to lowercase in logs', () => {
        isFlowTerminal('UNKNOWN_STATUS');
        expect(SecureLogger.warn).toHaveBeenCalledWith(
          'Unknown flow status encountered',
          expect.objectContaining({
            normalizedStatus: 'unknown_status'
          })
        );
      });
    });

    describe('KNOWN_STATUSES constant', () => {
      it('should include all terminal states', () => {
        TERMINAL_STATES.forEach(status => {
          expect(KNOWN_STATUSES).toContain(status);
        });
      });

      it('should include common non-terminal states', () => {
        const expectedNonTerminal = [
          'running',
          'processing',
          'validating',
          'paused',
          'waiting_for_approval',
          'waiting_for_user_approval',
          'pending',
          'queued',
          'starting',
          'initializing',
          'waiting',
          'retry',
          'timeout',
          'rollback'
        ];

        expectedNonTerminal.forEach(status => {
          expect(KNOWN_STATUSES).toContain(status);
        });
      });
    });
  });
});
