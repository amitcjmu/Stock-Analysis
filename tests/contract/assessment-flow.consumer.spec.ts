/**
 * Assessment Flow API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the Assessment Flow API.
 * The generated pact file is used to verify the backend provider.
 *
 * Run: npx vitest tests/contract/
 * Pacts output: tests/contract/pacts/
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { PactV4, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';

// Import types from generated OpenAPI schema
import type { ApiSchemas } from '@/types/generated';

const { like, eachLike, regex, uuid } = MatchersV3;

// Provider and consumer names for Pact
const CONSUMER = 'migrate-ui-frontend';
const PROVIDER = 'migrate-api-backend';

describe('Assessment Flow API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('GET /api/v1/assessment-flow/{flow_id}/status', () => {
    it('returns assessment flow status when flow exists', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('an assessment flow exists', { flow_id: flowId })
        .uponReceiving('a request for assessment flow status')
        .withRequest('GET', `/api/v1/assessment-flow/${flowId}/status`, (builder) => {
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
            status: regex('initialized|processing|paused_for_user_input|completed|error', 'processing'),
            progress_percentage: like(45.5),
            current_phase: like('tech_debt_assessment'),
            next_phase: like('dependency_analysis'),
            pause_points: eachLike('dependency_analysis'),
            user_inputs_captured: like(false),
            selected_applications: like(5),
            assessment_complete: like(false),
            created_at: like('2025-01-01T00:00:00Z'),
            updated_at: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          // Make request to mock server
          const response = await fetch(`${mockServer.url}/api/v1/assessment-flow/${flowId}/status`, {
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data: ApiSchemas['AssessmentFlowStatusResponse'] = await response.json();
          expect(data.flow_id).toBe(flowId);
          expect(data.status).toBeDefined();
          expect(data.progress_percentage).toBeGreaterThanOrEqual(0);
        });
    });

    it('returns 404 when flow does not exist', async () => {
      const flowId = '00000000-0000-0000-0000-000000000000';

      await provider
        .addInteraction()
        .given('no assessment flow exists')
        .uponReceiving('a request for non-existent assessment flow status')
        .withRequest('GET', `/api/v1/assessment-flow/${flowId}/status`, (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(404, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            detail: like('Flow not found'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/assessment-flow/${flowId}/status`, {
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(404);
        });
    });
  });

  describe('POST /api/v1/assessment-flow/initialize', () => {
    it('creates a new assessment flow', async () => {
      await provider
        .addInteraction()
        .given('applications ready for assessment')
        .uponReceiving('a request to create assessment flow')
        .withRequest('POST', '/api/v1/assessment-flow/initialize', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            selected_application_ids: eachLike('550e8400-e29b-41d4-a716-446655440001'),
            flow_name: like('Q4 2025 Assessment'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            flow_id: uuid(),
            status: regex('initialized|processing', 'initialized'),
            current_phase: like('initialization'),
            next_phase: like('architecture_standards'),
            selected_applications: like(1),
            message: like('Assessment flow created successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/assessment-flow/initialize`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
            body: JSON.stringify({
              selected_application_ids: ['550e8400-e29b-41d4-a716-446655440001'],
              flow_name: 'Q4 2025 Assessment',
            }),
          });

          expect(response.status).toBe(200);
          const data: ApiSchemas['AssessmentFlowResponse'] = await response.json();
          expect(data.flow_id).toBeDefined();
          expect(data.message).toBeDefined();
        });
    });
  });

  describe('PUT /api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id}', () => {
    it('accepts a 6R recommendation', async () => {
      const flowId = '550e8400-e29b-41d4-a716-446655440000';
      const appId = '650e8400-e29b-41d4-a716-446655440001';

      await provider
        .addInteraction()
        .given('assessment flow with 6R decisions', { flow_id: flowId, app_id: appId })
        .uponReceiving('a request to accept 6R recommendation')
        .withRequest('PUT', `/api/v1/assessment-flow/${flowId}/sixr-decisions/${appId}`, (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            strategy: like('rehost'),
            reasoning: like('Low complexity, suitable for lift-and-shift'),
            confidence_level: like(0.95),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            success: like(true),
            flow_id: uuid(flowId),
            app_id: uuid(appId),
            strategy: like('rehost'),
            message: like('Recommendation accepted'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/assessment-flow/${flowId}/sixr-decisions/${appId}`,
            {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
              body: JSON.stringify({
                strategy: 'rehost',
                reasoning: 'Low complexity, suitable for lift-and-shift',
                confidence_level: 0.95,
              }),
            }
          );

          expect(response.status).toBe(200);
          const data: ApiSchemas['AcceptRecommendationResponse'] = await response.json();
          expect(data.success).toBe(true);
        });
    });
  });
});
