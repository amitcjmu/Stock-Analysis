/**
 * Health Check API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * Baseline contract test for the health check endpoint.
 * This is the simplest contract and validates the basic setup works.
 *
 * Run: npx vitest tests/contract/
 * Pacts output: tests/contract/pacts/
 */

import { describe, it, expect } from 'vitest';
import { PactV4, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';

const { like } = MatchersV3;

const CONSUMER = 'migrate-ui-frontend';
const PROVIDER = 'migrate-api-backend';

describe('Health Check API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('GET /api/v1/health', () => {
    it('returns healthy status', async () => {
      await provider
        .addInteraction()
        .given('the API is running')
        .uponReceiving('a health check request')
        .withRequest('GET', '/api/v1/health')
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            status: like('healthy'),
            version: like('1.21.0'),
            timestamp: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/health`);

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.status).toBe('healthy');
        });
    });
  });

  describe('GET /api/v1/me', () => {
    it('returns current user context', async () => {
      await provider
        .addInteraction()
        .given('a user is authenticated')
        .uponReceiving('a request for current user context')
        .withRequest('GET', '/api/v1/me', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            user_id: like('user-123'),
            client_account_id: like('1'),
            engagement_id: like('1'),
            session_id: like('session-abc'),
            active_flows: like([]),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/me`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.client_account_id).toBeDefined();
          expect(data.engagement_id).toBeDefined();
        });
    });
  });
});
