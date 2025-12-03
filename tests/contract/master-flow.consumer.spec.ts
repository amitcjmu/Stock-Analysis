/**
 * Master Flow API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * Tests for the Master Flow Orchestrator (MFO) endpoints.
 * These are critical endpoints for flow lifecycle management.
 *
 * Run: npx vitest tests/contract/
 * Pacts output: tests/contract/pacts/
 */

import { describe, it, expect } from 'vitest';
import { PactV4, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';

// Import types from generated OpenAPI schema
import type { ApiSchemas } from '@/types/generated';

const { like, eachLike, regex, uuid } = MatchersV3;

const CONSUMER = 'migrate-ui-frontend';
const PROVIDER = 'migrate-api-backend';

describe('Master Flow API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('GET /api/v1/master-flows/{flow_id}', () => {
    it('returns master flow details when flow exists', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a master flow exists', { flow_id: flowId })
        .uponReceiving('a request for master flow details')
        .withRequest('GET', `/api/v1/master-flows/${flowId}`, (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(flowId),
            flow_type: regex('discovery|assessment|collection|decommission', 'assessment'),
            flow_name: like('Q4 Assessment'),
            flow_status: regex('pending|active|in_progress|completed|paused|failed|cancelled', 'in_progress'),
            client_account_id: like('1'),
            engagement_id: like('1'),
            user_id: like('user-123'),
            flow_configuration: like({}),
            created_at: like('2025-01-01T00:00:00Z'),
            updated_at: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/master-flows/${flowId}`, {
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data: ApiSchemas['MasterFlowResponse'] = await response.json();
          expect(data.flow_id).toBe(flowId);
          expect(data.flow_type).toBeDefined();
          expect(data.flow_status).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/master-flows', () => {
    it('returns list of master flows for engagement', async () => {
      await provider
        .addInteraction()
        .given('multiple master flows exist')
        .uponReceiving('a request for all master flows')
        .withRequest('GET', '/api/v1/master-flows', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flows: eachLike({
              flow_id: uuid(),
              flow_type: regex('discovery|assessment|collection|decommission', 'assessment'),
              flow_status: regex('pending|active|in_progress|completed|paused|failed|cancelled', 'completed'),
              created_at: like('2025-01-01T00:00:00Z'),
            }),
            total: like(3),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/master-flows`, {
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.flows).toBeDefined();
          expect(Array.isArray(data.flows)).toBe(true);
        });
    });
  });

  describe('POST /api/v1/master-flows/{flow_id}/pause', () => {
    it('pauses an active flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('an active master flow exists', { flow_id: flowId })
        .uponReceiving('a request to pause the flow')
        .withRequest('POST', `/api/v1/master-flows/${flowId}/pause`, (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            success: like(true),
            flow_id: uuid(flowId),
            new_status: like('paused'),
            message: like('Flow paused successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/master-flows/${flowId}/pause`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.success).toBe(true);
          expect(data.new_status).toBe('paused');
        });
    });
  });

  describe('POST /api/v1/master-flows/{flow_id}/resume', () => {
    it('resumes a paused flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a paused master flow exists', { flow_id: flowId })
        .uponReceiving('a request to resume the flow')
        .withRequest('POST', `/api/v1/master-flows/${flowId}/resume`, (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            success: like(true),
            flow_id: uuid(flowId),
            new_status: like('in_progress'),
            message: like('Flow resumed successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/master-flows/${flowId}/resume`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.success).toBe(true);
          expect(data.new_status).toBe('in_progress');
        });
    });
  });
});
