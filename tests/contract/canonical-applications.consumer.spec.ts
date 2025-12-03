/**
 * Canonical Applications API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the Canonical Applications API.
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

describe('Canonical Applications API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('GET /api/v1/canonical-applications', () => {
    it('returns list of canonical applications', async () => {
      await provider
        .addInteraction()
        .given('canonical applications exist')
        .uponReceiving('a request to list canonical applications')
        .withRequest('GET', '/api/v1/canonical-applications', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            applications: eachLike({
              id: uuid(),
              name: like('Customer Portal'),
              description: like('Main customer-facing web application'),
              business_criticality: regex('low|medium|high|critical', 'high'),
              owner: like('Engineering Team'),
              assets_count: like(15),
              migration_status: regex('not_started|in_progress|completed', 'not_started'),
              created_at: like('2025-01-01T00:00:00Z'),
            }),
            total: like(10),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/canonical-applications`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.applications)).toBe(true);
        });
    });
  });

  describe('POST /api/v1/canonical-applications/map-asset', () => {
    it('maps an asset to a canonical application', async () => {
      const appId = '550e8400-e29b-41d4-a716-446655440000';
      const assetId = '650e8400-e29b-41d4-a716-446655440001';

      await provider
        .addInteraction()
        .given('a canonical application and asset exist', { app_id: appId, asset_id: assetId })
        .uponReceiving('a request to map an asset to a canonical application')
        .withRequest('POST', '/api/v1/canonical-applications/map-asset', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            canonical_application_id: uuid(appId),
            asset_id: uuid(assetId),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            success: like(true),
            mapping_id: uuid(),
            canonical_application_id: uuid(appId),
            asset_id: uuid(assetId),
            message: like('Asset mapped successfully'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/canonical-applications/map-asset`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
            body: JSON.stringify({
              canonical_application_id: appId,
              asset_id: assetId,
            }),
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.success).toBe(true);
        });
    });
  });

  describe('POST /api/v1/canonical-applications/bulk-map-assets', () => {
    it('bulk maps assets to a canonical application', async () => {
      const appId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a canonical application and multiple assets exist', { app_id: appId })
        .uponReceiving('a request to bulk map assets')
        .withRequest('POST', '/api/v1/canonical-applications/bulk-map-assets', (builder) => {
          builder.headers({
            'Content-Type': 'application/json',
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
          builder.jsonBody({
            canonical_application_id: uuid(appId),
            asset_ids: eachLike('650e8400-e29b-41d4-a716-446655440001'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            success: like(true),
            mapped_count: like(5),
            failed_count: like(0),
            canonical_application_id: uuid(appId),
            message: like('Bulk mapping completed'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/canonical-applications/bulk-map-assets`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
              body: JSON.stringify({
                canonical_application_id: appId,
                asset_ids: [
                  '650e8400-e29b-41d4-a716-446655440001',
                  '650e8400-e29b-41d4-a716-446655440002',
                ],
              }),
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.success).toBe(true);
          expect(data.mapped_count).toBeGreaterThan(0);
        });
    });
  });

  describe('GET /api/v1/canonical-applications/{canonical_application_id}/readiness-gaps', () => {
    it('returns readiness gaps for a canonical application', async () => {
      const appId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a canonical application with assessed assets', { app_id: appId })
        .uponReceiving('a request for application readiness gaps')
        .withRequest(
          'GET',
          `/api/v1/canonical-applications/${appId}/readiness-gaps`,
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
            canonical_application_id: uuid(appId),
            overall_readiness_score: like(0.75),
            gaps: eachLike({
              id: uuid(),
              category: regex(
                'technical_debt|security|compliance|documentation',
                'technical_debt'
              ),
              severity: regex('low|medium|high|critical', 'medium'),
              description: like('Legacy authentication mechanism needs update'),
              affected_assets: like(3),
              remediation_effort: regex('low|medium|high', 'medium'),
            }),
            total_gaps: like(8),
            critical_gaps: like(2),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/canonical-applications/${appId}/readiness-gaps`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.canonical_application_id).toBe(appId);
          expect(data.overall_readiness_score).toBeDefined();
        });
    });
  });
});
