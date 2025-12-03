/**
 * FinOps API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the FinOps API.
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

describe('FinOps API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('GET /api/v1/finops/metrics', () => {
    it('returns FinOps metrics', async () => {
      await provider
        .addInteraction()
        .given('FinOps metrics are available')
        .uponReceiving('a request for FinOps metrics')
        .withRequest('GET', '/api/v1/finops/metrics', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            total_cost: like(15000.0),
            cost_trend: regex('increasing|decreasing|stable', 'stable'),
            cost_by_category: like({
              compute: 8000.0,
              storage: 4000.0,
              network: 3000.0,
            }),
            period: like('monthly'),
            start_date: like('2025-01-01'),
            end_date: like('2025-01-31'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/finops/metrics`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.total_cost).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/finops/resources', () => {
    it('returns resource cost breakdown', async () => {
      await provider
        .addInteraction()
        .given('resources with costs exist')
        .uponReceiving('a request for resource costs')
        .withRequest('GET', '/api/v1/finops/resources', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            resources: eachLike({
              id: uuid(),
              name: like('Production Web Server'),
              type: regex('compute|storage|database|network', 'compute'),
              monthly_cost: like(500.0),
              utilization: like(0.75),
              recommendation: like('right-size'),
            }),
            total: like(25),
            total_monthly_cost: like(12500.0),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/finops/resources`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.resources)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/finops/opportunities', () => {
    it('returns cost optimization opportunities', async () => {
      await provider
        .addInteraction()
        .given('cost optimization opportunities exist')
        .uponReceiving('a request for optimization opportunities')
        .withRequest('GET', '/api/v1/finops/opportunities', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            opportunities: eachLike({
              id: uuid(),
              title: like('Right-size oversized instances'),
              category: regex('rightsizing|scheduling|reserved|spot', 'rightsizing'),
              potential_savings: like(2500.0),
              effort: regex('low|medium|high', 'low'),
              priority: regex('low|medium|high|critical', 'high'),
              affected_resources: like(5),
            }),
            total_potential_savings: like(10000.0),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/finops/opportunities`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.opportunities)).toBe(true);
          expect(data.total_potential_savings).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/finops/alerts', () => {
    it('returns cost alerts', async () => {
      await provider
        .addInteraction()
        .given('cost alerts are configured')
        .uponReceiving('a request for cost alerts')
        .withRequest('GET', '/api/v1/finops/alerts', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            alerts: eachLike({
              id: uuid(),
              type: regex('budget|anomaly|threshold', 'budget'),
              severity: regex('info|warning|critical', 'warning'),
              message: like('Budget threshold exceeded'),
              resource_id: uuid(),
              created_at: like('2025-01-01T00:00:00Z'),
              acknowledged: like(false),
            }),
            unacknowledged_count: like(3),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/finops/alerts`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.alerts)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/finops/llm-costs', () => {
    it('returns LLM usage costs', async () => {
      await provider
        .addInteraction()
        .given('LLM usage data exists')
        .uponReceiving('a request for LLM costs')
        .withRequest('GET', '/api/v1/finops/llm-costs', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            total_cost: like(250.0),
            total_tokens: like(5000000),
            cost_by_model: like({
              'gpt-4': 150.0,
              'gpt-3.5-turbo': 50.0,
              'claude-3-opus': 50.0,
            }),
            cost_by_flow_type: like({
              discovery: 100.0,
              assessment: 100.0,
              collection: 50.0,
            }),
            period: like('monthly'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/finops/llm-costs`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.total_cost).toBeDefined();
          expect(data.total_tokens).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/finops/health', () => {
    it('returns FinOps service health', async () => {
      await provider
        .addInteraction()
        .given('FinOps service is running')
        .uponReceiving('a health check request for FinOps service')
        .withRequest('GET', '/api/v1/finops/health')
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            status: regex('healthy|degraded|unhealthy', 'healthy'),
            service: like('finops'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/finops/health`);

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.status).toBeDefined();
        });
    });
  });
});
