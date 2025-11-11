import { Client } from 'pg';

/**
 * Seeds test assets for gap analysis E2E tests
 * Run this before gap analysis tests to ensure assets exist
 */

const DB_CONFIG = {
  host: 'localhost',
  port: 5432,
  database: 'migration_db',
  user: 'postgres',
  password: 'postgres',
};

// Demo user context (from demo credentials)
const DEMO_CLIENT_ID = '11111111-1111-1111-1111-111111111111';
const DEMO_ENGAGEMENT_ID = '22222222-2222-2222-2222-222222222222';

const TEST_ASSETS = [
  {
    name: 'test-web-server-01',
    asset_type: 'server',
    hostname: 'web01.test.local',
    ip_address: '192.168.1.101',
    environment: 'production',
    operating_system: 'Ubuntu 22.04',
    cpu_cores: 4,
    memory_gb: 16,
    storage_gb: 500,
    application_name: 'Web Application',
    criticality: 'high',
    status: 'active',
  },
  {
    name: 'test-db-server-01',
    asset_type: 'server',
    hostname: 'db01.test.local',
    ip_address: '192.168.1.102',
    environment: 'production',
    operating_system: 'Red Hat Enterprise Linux 8',
    cpu_cores: 8,
    memory_gb: 64,
    storage_gb: 2000,
    application_name: 'Database Server',
    criticality: 'critical',
    status: 'active',
  },
  {
    name: 'test-app-server-01',
    asset_type: 'server',
    hostname: 'app01.test.local',
    ip_address: '192.168.1.103',
    environment: 'staging',
    operating_system: 'CentOS 7',
    cpu_cores: 4,
    memory_gb: 32,
    storage_gb: 1000,
    application_name: 'Application Server',
    criticality: 'medium',
    status: 'active',
  },
];

async function seedTestAssets() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('✅ Connected to database');

    // Check if test assets already exist
    const checkResult = await client.query(
      `SELECT COUNT(*) as count FROM migration.assets 
       WHERE client_account_id = $1 AND engagement_id = $2 
       AND name LIKE 'test-%'`,
      [DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID]
    );

    const existingCount = parseInt(checkResult.rows[0].count);
    
    if (existingCount >= 3) {
      console.log(`✅ Test assets already exist (${existingCount} found)`);
      return;
    }

    // Delete old test assets
    await client.query(
      `DELETE FROM migration.assets 
       WHERE client_account_id = $1 AND engagement_id = $2 
       AND name LIKE 'test-%'`,
      [DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID]
    );
    console.log('🧹 Cleaned up old test assets');

    // Insert new test assets
    for (const asset of TEST_ASSETS) {
      await client.query(
        `INSERT INTO migration.assets (
          id, client_account_id, engagement_id, 
          name, asset_type, hostname, ip_address, 
          environment, operating_system, cpu_cores, 
          memory_gb, storage_gb, application_name, 
          criticality, status, created_at, updated_at
        ) VALUES (
          gen_random_uuid(), $1, $2, 
          $3, $4, $5, $6, 
          $7, $8, $9, 
          $10, $11, $12, 
          $13, $14, NOW(), NOW()
        )`,
        [
          DEMO_CLIENT_ID,
          DEMO_ENGAGEMENT_ID,
          asset.name,
          asset.asset_type,
          asset.hostname,
          asset.ip_address,
          asset.environment,
          asset.operating_system,
          asset.cpu_cores,
          asset.memory_gb,
          asset.storage_gb,
          asset.application_name,
          asset.criticality,
          asset.status,
        ]
      );
      console.log(`✅ Created asset: ${asset.name}`);
    }

    console.log(`\n🎉 Successfully seeded ${TEST_ASSETS.length} test assets`);
  } catch (error) {
    console.error('❌ Error seeding test assets:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// Run if called directly
if (require.main === module) {
  seedTestAssets()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

export { seedTestAssets, TEST_ASSETS };
