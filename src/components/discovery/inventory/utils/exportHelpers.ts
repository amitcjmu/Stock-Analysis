import type { AssetInventory } from '../types/inventory.types';

export const exportAssets = (assets: AssetInventory[], selectedColumns: string[]) => {
  const csvHeaders = selectedColumns.join(',');
  const csvRows = assets.map(asset =>
    selectedColumns.map(col => {
      const value = asset[col];
      // Escape commas and quotes in CSV
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value || '';
    }).join(',')
  );

  const csvContent = [csvHeaders, ...csvRows].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `asset-inventory-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
};
