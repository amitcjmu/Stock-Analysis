import type { Asset } from '../../../types/asset';

export const exportAssets = (assets: Asset[], selectedColumns: string[]): void => {
  try {
    console.log('🔄 Starting CSV export...', { assetCount: assets.length, columns: selectedColumns });

    // Validate inputs
    if (!assets || assets.length === 0) {
      console.warn('⚠️ No assets to export');
      alert('No assets available to export');
      return;
    }

    if (!selectedColumns || selectedColumns.length === 0) {
      console.warn('⚠️ No columns selected for export');
      alert('Please select at least one column to export');
      return;
    }

    const csvHeaders = selectedColumns.join(',');
    const csvRows = assets.map(asset =>
      selectedColumns.map(col => {
        const value = asset[col as keyof Asset];
        let stringValue = value !== null && value !== undefined ? String(value) : '';

        // Security: Prevent CSV formula injection by prepending single quote to dangerous characters
        // Excel/LibreOffice interpret cells starting with =, +, -, @, or | as formulas
        if (stringValue.length > 0 && /^[=+\-@|]/.test(stringValue)) {
          stringValue = `'${stringValue}`;
        }

        // Escape commas and quotes in CSV
        if (stringValue.includes(',') || stringValue.includes('"')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    );

    const csvContent = [csvHeaders, ...csvRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);

    // Create and trigger download
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `asset-inventory-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up
    window.URL.revokeObjectURL(url);

    console.log('✅ CSV export completed successfully');
  } catch (error) {
    console.error('❌ Error exporting CSV:', error);
    alert('Failed to export CSV. Please try again.');
  }
};
