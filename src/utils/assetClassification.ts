/**
 * Asset Classification Utility
 * Bug #971 Fix: Centralized asset type classification for consistency across the app.
 *
 * This utility provides a single source of truth for asset type classification,
 * used by both useApplicationData (Collection) and useInventoryProgress (Discovery).
 */

/**
 * Standard asset categories used across the application
 */
export type AssetCategory =
  | 'SERVER'
  | 'APPLICATION'
  | 'DATABASE'
  | 'NETWORK'
  | 'STORAGE'
  | 'SECURITY'
  | 'VIRTUALIZATION'
  | 'OTHER'
  | 'UNKNOWN';

/**
 * Keywords that indicate each asset category
 * Used for classification when no explicit type mapping exists
 */
const CATEGORY_KEYWORDS: Record<AssetCategory, readonly string[]> = {
  SERVER: ['server', 'srv', 'host', 'vm', 'virtual_machine', 'virtual machine', 'node'],
  APPLICATION: ['application', 'app', 'service', 'api', 'web', 'portal', 'system', 'platform', 'software'],
  DATABASE: ['database', 'db', 'sql', 'mysql', 'postgres', 'postgresql', 'oracle', 'mongo', 'mongodb', 'redis', 'cassandra'],
  NETWORK: ['network', 'switch', 'router', 'firewall', 'gateway', 'loadbalancer', 'lb', 'proxy', 'vpn'],
  STORAGE: ['storage', 'san', 'nas', 'disk', 'volume'],
  SECURITY: ['security', 'firewall', 'ids', 'ips', 'waf'],
  VIRTUALIZATION: ['virtualization', 'hypervisor', 'vmware', 'hyper-v', 'kvm'],
  OTHER: ['other', 'unknown', 'misc', 'miscellaneous'],
  UNKNOWN: [],
};

/**
 * Classify an asset type string into a standard category.
 *
 * @param assetType - The raw asset type string from the backend
 * @returns The normalized asset category
 */
export function classifyAssetType(assetType: string | null | undefined): AssetCategory {
  if (!assetType) return 'UNKNOWN';

  const type = assetType.toLowerCase().trim();

  // Check each category's keywords
  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    if (category === 'UNKNOWN') continue; // Skip UNKNOWN, it's the fallback

    for (const keyword of keywords) {
      if (type.includes(keyword)) {
        return category as AssetCategory;
      }
    }
  }

  // Default fallback
  return 'UNKNOWN';
}

/**
 * Check if an asset type belongs to a specific category.
 *
 * @param assetType - The raw asset type string
 * @param category - The category to check against
 * @returns True if the asset belongs to the category
 */
export function isAssetCategory(
  assetType: string | null | undefined,
  category: AssetCategory
): boolean {
  return classifyAssetType(assetType) === category;
}

/**
 * Check if an asset should be counted as "devices" (network + other/unknown).
 * This is used by the Discovery Inventory Progress component.
 *
 * @param assetType - The raw asset type string
 * @returns True if the asset should be counted as a device
 */
export function isDeviceAsset(assetType: string | null | undefined): boolean {
  const category = classifyAssetType(assetType);
  return category === 'NETWORK' || category === 'OTHER' || category === 'UNKNOWN';
}

/**
 * Get all standard asset categories
 */
export function getAllCategories(): readonly AssetCategory[] {
  return Object.keys(CATEGORY_KEYWORDS) as AssetCategory[];
}
