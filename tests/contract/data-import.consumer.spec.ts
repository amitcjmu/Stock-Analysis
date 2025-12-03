/**
 * Data Import API Consumer Contract Tests
 *
 * Issue #592: API Contract Testing Implementation
 *
 * These tests define the consumer expectations for the Data Import API.
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

describe('Data Import API Consumer Contract', () => {
  const provider = new PactV4({
    consumer: CONSUMER,
    provider: PROVIDER,
    dir: path.resolve(process.cwd(), 'tests/contract/pacts'),
    logLevel: 'warn',
  });

  describe('GET /api/v1/data-import/imports', () => {
    it('returns list of data imports', async () => {
      await provider
        .addInteraction()
        .given('data imports exist')
        .uponReceiving('a request to list data imports')
        .withRequest('GET', '/api/v1/data-import/imports', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            imports: eachLike({
              id: uuid(),
              filename: like('cmdb_export.csv'),
              status: regex('pending|processing|completed|failed', 'completed'),
              records_total: like(1000),
              records_processed: like(1000),
              created_at: like('2025-01-01T00:00:00Z'),
            }),
            total: like(5),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/data-import/imports`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.imports)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/data-import/latest', () => {
    it('returns the latest data import', async () => {
      await provider
        .addInteraction()
        .given('at least one data import exists')
        .uponReceiving('a request for the latest import')
        .withRequest('GET', '/api/v1/data-import/latest', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            id: uuid(),
            filename: like('cmdb_export_latest.csv'),
            status: regex('pending|processing|completed|failed', 'completed'),
            records_total: like(500),
            records_processed: like(500),
            created_at: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/data-import/latest`, {
            headers: {
              'X-Client-Account-ID': '1',
              'X-Engagement-ID': '1',
            },
          });

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.id).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/data-import/imports/{import_id}', () => {
    it('returns a specific data import', async () => {
      const importId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('a data import exists', { import_id: importId })
        .uponReceiving('a request for a specific import')
        .withRequest('GET', `/api/v1/data-import/imports/${importId}`, (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            id: uuid(importId),
            filename: like('cmdb_export.csv'),
            status: regex('pending|processing|completed|failed', 'completed'),
            records_total: like(1000),
            records_processed: like(1000),
            field_mappings_count: like(25),
            created_at: like('2025-01-01T00:00:00Z'),
            updated_at: like('2025-01-01T00:00:00Z'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/imports/${importId}`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.id).toBe(importId);
        });
    });
  });

  describe('GET /api/v1/data-import/available-target-fields', () => {
    it('returns available target fields for mapping', async () => {
      await provider
        .addInteraction()
        .given('target fields are configured')
        .uponReceiving('a request for available target fields')
        .withRequest('GET', '/api/v1/data-import/available-target-fields', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            fields: eachLike({
              name: like('server_name'),
              display_name: like('Server Name'),
              category: like('identity'),
              required: like(true),
              data_type: regex('string|number|boolean|date', 'string'),
            }),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/available-target-fields`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.fields)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/data-import/target-field-categories', () => {
    it('returns field categories', async () => {
      await provider
        .addInteraction()
        .given('field categories are configured')
        .uponReceiving('a request for target field categories')
        .withRequest('GET', '/api/v1/data-import/target-field-categories', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            categories: eachLike({
              name: like('identity'),
              display_name: like('Identity'),
              fields_count: like(5),
            }),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/target-field-categories`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(Array.isArray(data.categories)).toBe(true);
        });
    });
  });

  describe('GET /api/v1/data-import/field-mappings/imports/{import_id}/mappings', () => {
    it('returns field mappings for an import', async () => {
      const importId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('an import with field mappings exists', { import_id: importId })
        .uponReceiving('a request for import field mappings')
        .withRequest(
          'GET',
          `/api/v1/data-import/field-mappings/imports/${importId}/mappings`,
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
              status: regex('approved|pending|rejected|ai_suggested', 'pending'),
              mapping_type: regex('ai|manual|learned', 'ai'),
            }),
            unmapped_fields: eachLike(like('custom_field_1')),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/field-mappings/imports/${importId}/mappings`,
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

  describe('POST /api/v1/data-import/field-mappings/imports/{import_id}/generate', () => {
    it('generates AI field mappings for an import', async () => {
      const importId = '550e8400-e29b-41d4-a716-446655440000';

      await provider
        .addInteraction()
        .given('an import ready for mapping generation', { import_id: importId })
        .uponReceiving('a request to generate field mappings')
        .withRequest(
          'POST',
          `/api/v1/data-import/field-mappings/imports/${importId}/generate`,
          (builder) => {
            builder.headers({
              'Content-Type': 'application/json',
              'X-Client-Account-ID': like('1'),
              'X-Engagement-ID': like('1'),
            });
          }
        )
        .willRespondWith(202, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            task_id: uuid(),
            status: like('processing'),
            message: like('Field mapping generation started'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/field-mappings/imports/${importId}/generate`,
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

  describe('GET /api/v1/data-import/critical-attributes-status', () => {
    it('returns critical attributes mapping status', async () => {
      await provider
        .addInteraction()
        .given('imports with critical attributes exist')
        .uponReceiving('a request for critical attributes status')
        .withRequest('GET', '/api/v1/data-import/critical-attributes-status', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            critical_fields_total: like(10),
            critical_fields_mapped: like(8),
            completion_percentage: like(80.0),
            missing_fields: eachLike(like('business_criticality')),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/critical-attributes-status`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.critical_fields_total).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/data-import/learning-statistics', () => {
    it('returns learning statistics', async () => {
      await provider
        .addInteraction()
        .given('learning data exists')
        .uponReceiving('a request for learning statistics')
        .withRequest('GET', '/api/v1/data-import/learning-statistics', (builder) => {
          builder.headers({
            'X-Client-Account-ID': like('1'),
            'X-Engagement-ID': like('1'),
          });
        })
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            total_learned_mappings: like(150),
            accuracy_rate: like(0.92),
            mappings_by_type: like({
              ai_suggested: 100,
              manually_approved: 30,
              manually_created: 20,
            }),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(
            `${mockServer.url}/api/v1/data-import/learning-statistics`,
            {
              headers: {
                'X-Client-Account-ID': '1',
                'X-Engagement-ID': '1',
              },
            }
          );

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.total_learned_mappings).toBeDefined();
        });
    });
  });

  describe('GET /api/v1/data-import/health', () => {
    it('returns data import service health', async () => {
      await provider
        .addInteraction()
        .given('data import service is running')
        .uponReceiving('a health check request for data import service')
        .withRequest('GET', '/api/v1/data-import/health')
        .willRespondWith(200, (builder) => {
          builder.headers({ 'Content-Type': 'application/json' });
          builder.jsonBody({
            status: regex('healthy|degraded|unhealthy', 'healthy'),
            service: like('data-import'),
          });
        })
        .executeTest(async (mockServer) => {
          const response = await fetch(`${mockServer.url}/api/v1/data-import/health`);

          expect(response.status).toBe(200);
          const data = await response.json();
          expect(data.status).toBeDefined();
        });
    });
  });
});
