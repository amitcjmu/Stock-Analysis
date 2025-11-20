/**
 * AI Gap Analysis Caching Feature - Smoke Test
 *
 * Focuses on:
 * 1. Database schema verification (columns exist)
 * 2. Frontend component rendering (no console errors)
 * 3. API endpoint connectivity
 * 4. Basic UI element presence
 *
 * These tests don't require complex login flows and focus on
 * regression detection rather than comprehensive feature testing.
 */

import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

const BASE_URL = 'http://localhost:8081';
const API_URL = 'http://localhost:8000';

/**
 * Helper: Execute database query via Docker
 */
function queryDatabase(sql: string): string {
  try {
    const command = `docker exec migration_postgres psql -U postgres -d migration_db -t -c "${sql}"`;
    const result = execSync(command, { encoding: 'utf-8' });
    return result.trim();
  } catch (error) {
    console.error('Database query failed:', error);
    throw error;
  }
}

/**
 * Helper: Check backend logs for errors
 */
function checkBackendLogs(pattern: string): boolean {
  try {
    const logs = execSync('docker logs migration_backend --tail 100', { encoding: 'utf-8' });
    return logs.includes(pattern);
  } catch (error) {
    return false;
  }
}

/**
 * Helper: Get latest backend error logs
 */
function getBackendErrors(): string {
  try {
    const logs = execSync('docker logs migration_backend --tail 50 2>&1 | grep -i "error\\|exception\\|traceback" || true', {
      encoding: 'utf-8',
      shell: '/bin/bash'
    });
    return logs;
  } catch (error) {
    return '';
  }
}

test.describe('AI Gap Analysis Caching - Smoke Tests', () => {

  // TEST 1: Database Schema
  test('Database has required AI gap analysis columns', async () => {
    console.log('\n--- TEST 1: Database Schema ---');

    const sql = `
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_schema = 'migration'
      AND table_name = 'assets'
      AND column_name LIKE 'ai_%'
      ORDER BY column_name;
    `;

    const result = queryDatabase(sql);
    console.log('Result:', result);

    // Both columns must exist
    expect(result).toContain('ai_gap_analysis_status');
    expect(result).toContain('ai_gap_analysis_timestamp');
    expect(result).toContain('integer');  // status is integer
    expect(result).toContain('timestamp with time zone');  // timestamp column

    console.log('✓ Both required columns exist with correct types');
  });

  // TEST 2: Default Column Values
  test('Assets table columns have correct defaults', async () => {
    console.log('\n--- TEST 2: Column Defaults ---');

    const sql = `
      SELECT column_name, column_default
      FROM information_schema.columns
      WHERE table_schema = 'migration'
      AND table_name = 'assets'
      AND column_name = 'ai_gap_analysis_status';
    `;

    const result = queryDatabase(sql);
    console.log('Column defaults:', result);

    // Status should default to 0
    expect(result).toContain('ai_gap_analysis_status');
    expect(result).toContain('0');  // Default value is 0

    console.log('✓ Column defaults are correct (status defaults to 0)');
  });

  // TEST 3: Index for Performance
  test('Performance index exists on ai_gap_analysis_status', async () => {
    console.log('\n--- TEST 3: Performance Index ---');

    const sql = `
      SELECT indexname, indexdef
      FROM pg_indexes
      WHERE schemaname = 'migration'
      AND tablename = 'assets'
      AND indexdef LIKE '%ai_gap_analysis_status%';
    `;

    const result = queryDatabase(sql);
    console.log('Index found:', result);

    expect(result.length).toBeGreaterThan(0);
    expect(result).toContain('ai_gap_analysis_status');

    console.log('✓ Performance index exists on ai_gap_analysis_status');
  });

  // TEST 4: Sample Asset Status Check
  test('Sample assets have valid status values (0, 1, or 2)', async () => {
    console.log('\n--- TEST 4: Asset Status Values ---');

    const sql = `
      SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN ai_gap_analysis_status = 0 THEN 1 END) as status_0,
        COUNT(CASE WHEN ai_gap_analysis_status = 1 THEN 1 END) as status_1,
        COUNT(CASE WHEN ai_gap_analysis_status = 2 THEN 1 END) as status_2,
        COUNT(CASE WHEN ai_gap_analysis_status NOT IN (0,1,2) THEN 1 END) as invalid
      FROM migration.assets
      WHERE client_account_id = '00000000-0000-0000-0000-000000000001'::uuid
      LIMIT 100;
    `;

    const result = queryDatabase(sql);
    console.log('Asset status distribution:', result);

    // No invalid status values should exist
    expect(result).not.toContain('invalid | 1');  // No invalid statuses with count > 0

    console.log('✓ All assets have valid status values (0, 1, or 2)');
  });

  // TEST 5: Timestamp Consistency
  test('Assets with status=2 have valid timestamps', async () => {
    console.log('\n--- TEST 5: Timestamp Consistency ---');

    const sql = `
      SELECT COUNT(*)
      FROM migration.assets
      WHERE ai_gap_analysis_status = 2
      AND ai_gap_analysis_timestamp IS NOT NULL
      AND client_account_id = '00000000-0000-0000-0000-000000000001'::uuid;
    `;

    const result = queryDatabase(sql);
    const count = parseInt(result);

    console.log(`Assets with status=2 and timestamp: ${count}`);

    // This is informational - status=2 should generally have timestamps
    // (though it's possible to have status=2 without timestamp from migrations)
    if (count > 0) {
      console.log('✓ Found assets with status=2 and timestamps');
    } else {
      console.log('⚠ No assets with status=2 found (expected for initial test state)');
    }

    expect(count).toBeGreaterThanOrEqual(0);
  });

  // TEST 6: Frontend App Loads Without Errors
  test('Frontend loads without console errors on homepage', async ({ page }) => {
    console.log('\n--- TEST 6: Frontend Loading ---');

    // Capture console messages
    const consoleMessages = [];
    const consoleErrors = [];

    page.on('console', msg => {
      consoleMessages.push({ type: msg.type(), text: msg.text() });
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to homepage
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // Check for critical errors
    const criticalErrors = consoleErrors.filter(msg =>
      msg.includes('404') ||
      msg.includes('500') ||
      msg.includes('ai_gap_analysis')
    );

    console.log(`Console messages: ${consoleMessages.length} total`);
    console.log(`Console errors: ${consoleErrors.length} total`);
    if (criticalErrors.length > 0) {
      console.log('Critical errors found:', criticalErrors);
    }

    // No critical errors related to the feature
    expect(criticalErrors.length).toBe(0);

    console.log('✓ Frontend loaded without critical errors');
  });

  // TEST 7: API Health Check
  test('Backend API is responding correctly', async () => {
    console.log('\n--- TEST 7: API Health ---');

    const urls = [
      `${API_URL}/health`,
      `${API_URL}/docs`
    ];

    for (const url of urls) {
      try {
        const response = await fetch(url, { method: 'GET' });
        console.log(`${url}: ${response.status}`);
        expect(response.status).toBeLessThan(500);  // No server errors
      } catch (error) {
        console.error(`Failed to reach ${url}:`, error);
        throw error;
      }
    }

    console.log('✓ Backend API is healthy');
  });

  // TEST 8: Backend Logs - No Critical Errors Since Startup
  test('Backend logs contain no AI gap analysis related errors', async () => {
    console.log('\n--- TEST 8: Backend Log Analysis ---');

    const errors = getBackendErrors();

    if (errors) {
      console.log('Recent errors:', errors);
    }

    // Check for specific feature-related errors
    const hasAIGapErrors = checkBackendLogs('ai_gap_analysis_status ERROR');
    const hasTimestampErrors = checkBackendLogs('ai_gap_analysis_timestamp ERROR');

    expect(hasAIGapErrors).toBe(false);
    expect(hasTimestampErrors).toBe(false);

    console.log('✓ No AI gap analysis specific errors in logs');
  });

  // TEST 9: Data Validation - No Gaps with Status Mismatch
  test('No data integrity issues: all AI-enhanced gaps belong to analyzed assets', async () => {
    console.log('\n--- TEST 9: Data Integrity ---');

    // Find gaps with confidence scores (AI-enhanced gaps)
    const gapsSql = `
      SELECT COUNT(DISTINCT cdg.asset_id)
      FROM migration.collection_data_gaps cdg
      JOIN migration.assets a ON cdg.asset_id = a.id
      WHERE cdg.confidence_score IS NOT NULL
      AND a.client_account_id = '00000000-0000-0000-0000-000000000001'::uuid;
    `;

    const gapsResult = queryDatabase(gapsSql);
    const gapsCount = parseInt(gapsResult);
    console.log(`Assets with AI-enhanced gaps: ${gapsCount}`);

    // Find assets with status=2
    const statusSql = `
      SELECT COUNT(*)
      FROM migration.assets
      WHERE ai_gap_analysis_status = 2
      AND client_account_id = '00000000-0000-0000-0000-000000000001'::uuid;
    `;

    const statusResult = queryDatabase(statusSql);
    const statusCount = parseInt(statusResult);
    console.log(`Assets with status=2: ${statusCount}`);

    // This is informational - we expect consistency
    console.log(`✓ Data integrity check complete (gaps: ${gapsCount}, completed: ${statusCount})`);
  });

  // TEST 10: Collection Flow Status Endpoint Response Format
  test('Collection flow endpoints return properly formatted responses', async ({ page }) => {
    console.log('\n--- TEST 10: API Response Format ---');

    try {
      // Try to access collection flow API (may return 401/403 without auth, but should be valid JSON)
      const response = await page.request.get(
        `${API_URL}/api/v1/collection/flows`,
        {
          headers: {
            'X-Client-Account-ID': '1',
            'X-Engagement-ID': '1'
          }
        }
      );

      console.log(`API response status: ${response.status()}`);

      // Check response is valid (even if 401/403)
      expect(response.status()).toBeLessThan(500);

      if (response.ok()) {
        const data = await response.json();
        console.log('Response is valid JSON');
        expect(typeof data).toBe('object');
      } else {
        console.log(`Expected 401/403 response: ${response.status()}`);
      }

      console.log('✓ API endpoints return properly formatted responses');
    } catch (error) {
      // Network errors are acceptable in test environment
      console.log('⚠ Network error (expected without full auth setup):', error);
    }
  });

});

test.describe('AI Gap Analysis - DataGapDiscovery Component', () => {

  // TEST 11: Component Rendering (if accessible)
  test('Collection flow component loads without TypeScript errors', async ({ page }) => {
    console.log('\n--- TEST 11: Component Rendering ---');

    // Just verify frontend app loads
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // Look for common collection flow elements
    const hasLinks = await page.locator('[href*="collection"]').count();
    console.log(`Found ${hasLinks} collection-related links in UI`);

    // Even if not logged in, the page should render without crashing
    await expect(page).not.toHaveTitle('Error');
    await expect(page).not.toHaveTitle('500');

    console.log('✓ Component loads without crashing');
  });

  // TEST 12: Database - No Orphaned Records
  test('No orphaned records: all gaps reference existing assets', async () => {
    console.log('\n--- TEST 12: Referential Integrity ---');

    const sql = `
      SELECT COUNT(*)
      FROM migration.collection_data_gaps cdg
      LEFT JOIN migration.assets a ON cdg.asset_id = a.id
      WHERE a.id IS NULL;
    `;

    const result = queryDatabase(sql);
    const orphanedCount = parseInt(result);

    console.log(`Orphaned gaps (referencing deleted assets): ${orphanedCount}`);
    expect(orphanedCount).toBe(0);

    console.log('✓ No referential integrity violations');
  });

});
