/**
 * Discovery Flow API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the Unified Discovery Flow API.
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

describe('Discovery Flow API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('POST /api/v1/unified-discovery/flows/initialize', () => {
    it('initializes a new discovery flow', async () => {
      await provider
        .addInteraction()
        .given('ready to create discovery flow')
        .uponReceiving('a request to initialize discovery flow')
        .withRequest('POST', '/api/v1/unified-discovery/flows/initialize', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            flow_name: like('Discovery Flow Q4 2025'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(),
            status: regex('initialized|created|active', 'initialized'),
            message: like('Discovery flow initialized successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/unified-discovery/flows/initialize`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
              body: JSON.stringify({
                flow_name: 'Discovery Flow Q4 2025',
              }),
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.flow_id).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/unified-discovery/flows/{flow_id}/status', () => {
    it('returns discovery flow status', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a discovery flow exists', { flow_id: flowId })
        .uponReceiving('a request for discovery flow status')
        .withRequest('GET', `/api/v1/unified-discovery/flows/${flowId}/status`, (builder) => {
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
            current_phase: like('data_import'),
            progress_percentage: like(45.0),
            created_at: like('2025-01-01T00:00:00Z'),
            updated_at: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/unified-discovery/flows/${flowId}/status`,
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

  describe('GET /api/v1/unified-discovery/flows/active', () => {
    it('returns active discovery flow', async () => {
      await provider
        .addInteraction()
        .given('an active discovery flow exists')
        .uponReceiving('a request for active discovery flow')
        .withRequest('GET', '/api/v1/unified-discovery/flows/active', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(),
            status: regex('active|running', 'active'),
            current_phase: like('field_mapping'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/unified-discovery/flows/active`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.flow_id).toBeDefined();
        });
    });
  });

  describe('POST /api/v1/unified-discovery/flows/{flow_id}/execute', () => {
    it('executes a discovery flow phase', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a discovery flow ready for execution', { flow_id: flowId })
        .uponReceiving('a request to execute discovery flow')
        .withRequest('POST', `/api/v1/unified-discovery/flows/${flowId}/execute`, (builder) => {
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
            status: regex('running|processing|executing', 'running'),
            message: like('Flow execution started'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/unified-discovery/flows/${flowId}/execute`,
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

  describe('POST /api/v1/unified-discovery/flows/{flow_id}/pause', () => {
    it('pauses a running discovery flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a running discovery flow', { flow_id: flowId })
        .uponReceiving('a request to pause discovery flow')
        .withRequest('POST', `/api/v1/unified-discovery/flows/${flowId}/pause`, (builder) => {
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
            message: like('Flow paused successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/unified-discovery/flows/${flowId}/pause`,
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

  describe('POST /api/v1/unified-discovery/flows/{flow_id}/resume', () => {
    it('resumes a paused discovery flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a paused discovery flow', { flow_id: flowId })
        .uponReceiving('a request to resume discovery flow')
        .withRequest('POST', `/api/v1/unified-discovery/flows/${flowId}/resume`, (builder) => {
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
            message: like('Flow resumed successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/unified-discovery/flows/${flowId}/resume`,
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

  describe('GET /api/v1/unified-discovery/assets', () => {
    it('returns discovered assets', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('discovery flow has assets', { flow_id: flowId })
        .uponReceiving('a request for discovered assets')
        .withRequest('GET', '/api/v1/unified-discovery/assets', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
            'X-Flow-ID': like(flowId),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            assets: eachLike({
              id: uuid(),
              name: like('Server-001'),
              asset_type: regex('server|database|application', 'server'),
              status: like('discovered'),
            }),
            total: like(10),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/unified-discovery/assets`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
              'X-Flow-ID': flowId,
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.assets)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/unified-discovery/flows/{flow_id}/field-mappings', () => {
    it('returns field mappings for a discovery flow', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('discovery flow has field mappings', { flow_id: flowId })
        .uponReceiving('a request for field mappings')
        .withRequest(
          'GET',
          `/api/v1/unified-discovery/flows/${flowId}/field-mappings`,
          (builder) => {
            builder.headers({
              'X-Client-Account-ID': like('1'),
              'X-Engagement-ID': like('1'),
            });
          }
        )
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            mappings: eachLike({
              id: uuid(),
              source_field: like('hostname'),
              target_field: like('server_name'),
              confidence: like(0.95),
              status: regex('approved|pending|rejected', 'pending'),
            }),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/unified-discovery/flows/${flowId}/field-mappings`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.mappings)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/unified-discovery/health', () => {
    it('returns discovery service health', async () => {
      await provider
        .addInteraction()
        .given('discovery service is running')
        .uponReceiving('a health check request for discovery service')
        .withRequest('GET', '/api/v1/unified-discovery/health')
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            status: regex('healthy|degraded|unhealthy', 'healthy'),
            service: like('discovery'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/unified-discovery/health`);

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.status).toBeDefined();
        });
    });
  });
});
