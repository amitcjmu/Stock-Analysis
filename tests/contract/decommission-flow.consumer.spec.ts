/**
 * Decommission Flow API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the Decommission Flow API.
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

describe('Decommission Flow API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('POST /api/v1/decommission-flow/initialize', () => {
    it('initializes a new decommission flow', async () => {
      await provider
        .addInteraction()
        .given('systems eligible for decommission exist')
        .uponReceiving('a request to initialize decommission flow')
        .withRequest('POST', '/api/v1/decommission-flow/initialize', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            selected_system_ids: eachLike('550e8400-e29b-41d4-a716-446655440001'),
            flow_name: like('Decommission Q4 2025'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(),
            status: regex('initialized|created|active', 'initialized'),
            message: like('Decommission flow initialized successfully'),
            systems_count: like(5),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/initialize`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
              body: JSON.stringify({
                selected_system_ids: ['550e8400-e29b-41d4-a716-446655440001'],
                flow_name: 'Decommission Q4 2025',
              }),
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.flow_id).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/decommission-flow/{flow_id}/status', () => {
    it('returns decommission flow status', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a decommission flow exists', { flow_id: flowId })
        .uponReceiving('a request for decommission flow status')
        .withRequest('GET', `/api/v1/decommission-flow/${flowId}/status`, (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(flowId),
            status: regex('initialized|running|paused|completed|error', 'running'),
            current_phase: like('data_backup'),
            progress_percentage: like(30.0),
            systems_remaining: like(3),
            systems_completed: like(2),
            created_at: like('2025-01-01T00:00:00Z'),
            updated_at: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/${flowId}/status`,
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

  describe('POST /api/v1/decommission-flow/{flow_id}/resume', () => {
    it('resumes a paused decommission flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a paused decommission flow', { flow_id: flowId })
        .uponReceiving('a request to resume decommission flow')
        .withRequest('POST', `/api/v1/decommission-flow/${flowId}/resume`, (builder) => {
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
            status: regex('running|active|resumed', 'running'),
            message: like('Decommission flow resumed successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/${flowId}/resume`,
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
          expect(data.flow_id).toBe(flowId);
        });
    });
  });

  describe('POST /api/v1/decommission-flow/{flow_id}/pause', () => {
    it('pauses a running decommission flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a running decommission flow', { flow_id: flowId })
        .uponReceiving('a request to pause decommission flow')
        .withRequest('POST', `/api/v1/decommission-flow/${flowId}/pause`, (builder) => {
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
            status: like('paused'),
            message: like('Decommission flow paused successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/${flowId}/pause`,
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
          expect(data.status).toBe('paused');
        });
    });
  });

  describe('POST /api/v1/decommission-flow/{flow_id}/cancel', () => {
    it('cancels a decommission flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('an active decommission flow', { flow_id: flowId })
        .uponReceiving('a request to cancel decommission flow')
        .withRequest('POST', `/api/v1/decommission-flow/${flowId}/cancel`, (builder) => {
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
            status: like('cancelled'),
            message: like('Decommission flow cancelled'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/${flowId}/cancel`,
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
          expect(data.status).toBe('cancelled');
        });
    });
  });

  describe('GET /api/v1/decommission-flow/', () => {
    it('lists decommission flows', async () => {
      await provider
        .addInteraction()
        .given('decommission flows exist')
        .uponReceiving('a request to list decommission flows')
        .withRequest('GET', '/api/v1/decommission-flow/', (builder) => {
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
              status: regex('initialized|running|completed|cancelled', 'running'),
              systems_count: like(5),
              created_at: like('2025-01-01T00:00:00Z'),
            }),
            total: like(3),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/decommission-flow/`, {
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

  describe('GET /api/v1/decommission-flow/eligible-systems', () => {
    it('returns systems eligible for decommission', async () => {
      await provider
        .addInteraction()
        .given('systems exist that can be decommissioned')
        .uponReceiving('a request for eligible systems')
        .withRequest('GET', '/api/v1/decommission-flow/eligible-systems', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            systems: eachLike({
              id: uuid(),
              name: like('Legacy Server 001'),
              type: regex('server|database|application', 'server'),
              recommendation: like('retire'),
              risk_level: regex('low|medium|high', 'low'),
            }),
            total: like(10),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/eligible-systems`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.systems)).toBe(true);
        });
    });
  });

  describe('POST /api/v1/decommission-flow/{flow_id}/phases/{phase_name}', () => {
    it('executes a specific decommission phase', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';
      const phaseName = 'data_backup';

      await provider
        .addInteraction()
        .given('a decommission flow ready for phase execution', { flow_id: flowId })
        .uponReceiving('a request to execute a decommission phase')
        .withRequest(
          'POST',
          `/api/v1/decommission-flow/${flowId}/phases/${phaseName}`,
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
            flow_id: uuid(flowId),
            phase: like(phaseName),
            status: regex('running|completed|pending', 'running'),
            message: like('Phase execution started'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/decommission-flow/${flowId}/phases/${phaseName}`,
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
          expect(data.phase).toBe(phaseName);
        });
    });
  });

  describe('GET /api/v1/decommission/data-retention', () => {
    it('returns data retention policies', async () => {
      await provider
        .addInteraction()
        .given('data retention policies exist')
        .uponReceiving('a request for data retention policies')
        .withRequest('GET', '/api/v1/decommission/data-retention', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            policies: eachLike({
              id: uuid(),
              name: like('Standard Retention'),
              retention_days: like(90),
              data_types: eachLike('logs'),
            }),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/decommission/data-retention`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.policies)).toBe(true);
        });
    });
  });
});
