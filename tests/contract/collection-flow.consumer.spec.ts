/**
 * Collection Flow API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the Collection Flow API.
 * The generated pact file is used to verify the backend provider.
 *
 * Run: npx vitest tests/contract/
 * Pacts output: tests/contract/pacts/
 */

import { describe, it, expect } from 'vitest';
import { PactV4, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';

const { like, eachLike, uuid, regex } = MatchersV3;

const CONSUMER = 'migrate-ui-frontend';
const PROVIDER = 'migrate-api-backend';

describe('Collection Flow API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('POST /api/v1/collection/flows/from-discovery', () => {
    it('creates a collection flow from discovery', async () => {
      const discoveryFlowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a discovery flow exists', { discovery_flow_id: discoveryFlowId })
        .uponReceiving('a request to create collection flow from discovery')
        .withRequest('POST', '/api/v1/collection/flows/from-discovery', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            discovery_flow_id: uuid(discoveryFlowId),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            id: uuid(),
            discovery_flow_id: uuid(discoveryFlowId),
            status: regex('created|active|pending', 'created'),
            message: like('Collection flow created successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/collection/flows/from-discovery`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
            body: JSON.stringify({
              discovery_flow_id: discoveryFlowId,
            }),
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.id).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/collection/status', () => {
    it('returns collection flow status', async () => {
      await provider
        .addInteraction()
        .given('an active collection flow exists')
        .uponReceiving('a request for collection flow status')
        .withRequest('GET', '/api/v1/collection/status', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            has_active_flow: like(true),
            flow_id: uuid(),
            status: regex('active|pending|completed', 'active'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/collection/status`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.has_active_flow).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/collection/flows', () => {
    it('lists collection flows', async () => {
      await provider
        .addInteraction()
        .given('collection flows exist')
        .uponReceiving('a request to list collection flows')
        .withRequest('GET', '/api/v1/collection/flows', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flows: eachLike({
              id: uuid(),
              status: regex('active|pending|completed', 'active'),
              created_at: like('2025-01-01T00:00:00Z'),
            }),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/collection/flows`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.flows)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/collection/collection/flows/{flow_id}/status', () => {
    it('returns detailed collection flow status', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a collection flow exists', { flow_id: flowId })
        .uponReceiving('a request for detailed collection flow status')
        .withRequest('GET', `/api/v1/collection/collection/flows/${flowId}/status`, (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(flowId),
            status: regex('active|pending|completed|error', 'active'),
            completeness_percentage: like(75.5),
            total_questions: like(100),
            answered_questions: like(75),
            pending_questions: like(25),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/collection/collection/flows/${flowId}/status`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.flow_id).toBe(flowId);
        });
    });
  });

  describe('POST /api/v1/collection/flows/{flow_id}/scan-gaps', () => {
    it('initiates gap scanning for a collection flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a collection flow ready for gap analysis', { flow_id: flowId })
        .uponReceiving('a request to scan gaps')
        .withRequest('POST', `/api/v1/collection/flows/${flowId}/scan-gaps`, (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(202, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            task_id: uuid(),
            status: like('scanning'),
            message: like('Gap scanning initiated'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/collection/flows/${flowId}/scan-gaps`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(202);
          const data = await response.json();
          expect(data.task_id).toBeDefined();
        });
    });
  });

  describe('POST /api/v1/collection/collection/flows/{flow_id}/transition-to-assessment', () => {
    it('transitions collection flow to assessment', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a completed collection flow', { flow_id: flowId })
        .uponReceiving('a request to transition to assessment')
        .withRequest(
          'POST',
          `/api/v1/collection/collection/flows/${flowId}/transition-to-assessment`,
          (builder) => {
            builder.headers({
              'Content-Type': 'application/json',
              'X-Client-Account-ID': like('1'),
              'X-Engagement-ID': like('1'),
            });
          }
        )
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            success: like(true),
            assessment_flow_id: uuid(),
            message: like('Successfully transitioned to assessment'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/collection/collection/flows/${flowId}/transition-to-assessment`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.success).toBe(true);
          expect(data.assessment_flow_id).toBeDefined();
        });
    });
  });
});
