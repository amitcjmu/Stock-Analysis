/**
 * CSV Parsing and Cleansing Utility
 *
 * Handles CSV file parsing with data cleansing to fix common issues like:
 * - Commas in unquoted text fields causing column misalignment
 * - Column count mismatches
 *
 * Uses papaparse for proper CSV parsing (handles quoted fields, newlines, etc.)
 * then applies cleansing logic for malformed CSVs with unquoted commas.
 *
 * Designed to be expandable for future edge cases:
 * - Different delimiters
 * - Encoding issues
 */

import Papa from 'papaparse';

export interface CsvRecord {
  [key: string]: string | number;
}

export interface CsvParseResult {
  headers: string[];
  records: CsvRecord[];
  cleansingStats?: CleansingStats;
}

export interface CleansingStats {
  totalRows: number;
  rowsCleansed: number;
  rowsSkipped: number;
}

/**
 * Configuration constants for CSV cleansing
 * All replaceable values are centralized here for easy management
 */
export const CSV_CLEANSING_CONFIG = {
  /**
   * Character to replace commas with when cleansing text fields
   * Options: ' ' (space), ', ' (comma+space), '' (remove)
   */
  COMMA_REPLACEMENT: ' ' as string,

  /**
   * Maximum ratio of text fields to columns before considering a field as likely text
   * Used to identify which fields are likely text descriptions vs structured data
   */
  TEXT_FIELD_THRESHOLD: 0.5 as number,

  /**
   * Minimum field length to be considered for cleansing
   * Very short fields are less likely to be text descriptions
   */
  MIN_TEXT_FIELD_LENGTH: 5 as number,
} as const;

/**
 * Cleanses a CSV row by merging excess columns into text fields when column count mismatch is detected
 *
 * Strategy: When we have more columns than expected, we find the longest field(s)
 * before the mismatch point and merge the excess columns into them.
 *
 * Example: If we expect 3 columns but have 4 parts: ["A", "Long text", "more", "B"]
 * We merge "more" into "Long text" to get: ["A", "Long text more", "B"]
 *
 * @param row - The CSV row as a string
 * @param expectedColumnCount - Expected number of columns from header
 * @returns Cleansed row string with excess columns merged into text fields
 */
function cleanseMisalignedRow(row: string, expectedColumnCount: number): string {
  // Split row to check for mismatch
  const parts = row.split(',').map(p => p.trim());
  const actualColumnCount = parts.length;

  // If no mismatch, return as-is
  if (actualColumnCount <= expectedColumnCount) {
    return row;
  }

  // Calculate excess columns (these are likely from commas in text fields)
  const excessColumns = actualColumnCount - expectedColumnCount;

  // Strategy: Find which field(s) likely contain the text with commas
  // We look at fields in positions where text descriptions are common (usually middle fields)
  // and find the longest ones as they're most likely to contain the commas

  // Identify candidate fields for merging (usually not the first or last column)
  // For simplicity, we'll check fields from position 1 to expectedColumnCount-2
  const candidateStart = Math.max(1, 0);
  const candidateEnd = Math.min(expectedColumnCount - 1, actualColumnCount - excessColumns - 1);

  // Find the longest field among candidates (likely the text field with commas)
  let mergeTargetIndex = candidateStart;
  let maxLength = parts[candidateStart]?.length || 0;

  for (let i = candidateStart; i <= candidateEnd; i++) {
    if (parts[i] && parts[i].length > maxLength && parts[i].length >= CSV_CLEANSING_CONFIG.MIN_TEXT_FIELD_LENGTH) {
      maxLength = parts[i].length;
      mergeTargetIndex = i;
    }
  }

  // Build cleansed row by merging excess columns into the target field
  const cleansedParts: string[] = [];

  // Iterate through expected columns and merge excess where needed
  for (let i = 0; i < expectedColumnCount; i++) {
    if (i === mergeTargetIndex) {
      // Merge this field with the excess columns that follow it
      const excessStartIndex = i + 1;
      const excessEndIndex = Math.min(excessStartIndex + excessColumns, actualColumnCount);
      const excessParts = parts.slice(excessStartIndex, excessEndIndex);

      // Merge target field with excess columns
      const mergedValue = [
        parts[i],
        ...excessParts
      ].join(CSV_CLEANSING_CONFIG.COMMA_REPLACEMENT);

      cleansedParts.push(mergedValue);

      // Skip past the merged excess columns when continuing
      // We'll handle remaining parts after this loop
      break;
    } else {
      // Normal field before merge target
      cleansedParts.push(parts[i]);
    }
  }

  // After merging, add remaining parts that should be separate columns
  const lastMergedIndex = mergeTargetIndex + excessColumns;
  for (let i = lastMergedIndex + 1; i < actualColumnCount && cleansedParts.length < expectedColumnCount; i++) {
    cleansedParts.push(parts[i]);
  }

  // Ensure we have exactly expectedColumnCount fields
  while (cleansedParts.length < expectedColumnCount) {
    cleansedParts.push('');
  }
  while (cleansedParts.length > expectedColumnCount) {
    cleansedParts.pop();
  }

  return cleansedParts.join(',');
}

/**
 * Parses and cleanses CSV file content
 *
 * Uses papaparse for proper CSV parsing, then applies cleansing if column mismatches are detected.
 *
 * @param fileContent - Raw CSV file content as string
 * @returns Parsed CSV data with headers and records
 */
export function parseAndCleanseCSV(fileContent: string): CsvParseResult {
  if (!fileContent || fileContent.trim().length === 0) {
    return {
      headers: [],
      records: [],
      cleansingStats: {
        totalRows: 0,
        rowsCleansed: 0,
        rowsSkipped: 0,
      },
    };
  }

  // Use papaparse to parse CSV (handles quoted fields, newlines, etc. correctly)
  const parsed = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => header.trim().replace(/"/g, ''),
    transform: (value) => value.trim(),
  });

  const headers = parsed.meta.fields || [];
  const expectedColumnCount = headers.length;

  if (headers.length === 0) {
    return {
      headers: [],
      records: [],
      cleansingStats: {
        totalRows: 0,
        rowsCleansed: 0,
        rowsSkipped: 0,
      },
    };
  }

  // Track cleansing statistics
  const stats: CleansingStats = {
    totalRows: parsed.data.length,
    rowsCleansed: 0,
    rowsSkipped: 0,
  };

  // Check each parsed row for column count mismatches
  // If papaparse parsed correctly, all rows should have same column count
  // If not, we need to detect and cleanse malformed rows
  const records: CsvRecord[] = [];
  const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line.length > 0);

  for (let i = 0; i < parsed.data.length; i++) {
    const parsedRow = parsed.data[i] as Record<string, unknown>;

    // Get original line for this row (skip header line)
    const originalLine = lines[i + 1]; // +1 because first line is header

    if (!originalLine) {
      // Skip if no corresponding line
      continue;
    }

    // Check if row has column mismatch by comparing original split count
    const parts = originalLine.split(',');
    const actualColumnCount = parts.length;
    const needsCleansing = actualColumnCount > expectedColumnCount;

    if (needsCleansing) {
      // Apply cleansing to the original line
      const cleansedLine = cleanseMisalignedRow(originalLine, expectedColumnCount);

      // Parse cleansed line with papaparse
      const cleansedParsed = Papa.parse(cleansedLine, {
        header: false,
        skipEmptyLines: false,
        transform: (value) => value.trim(),
      });

      // Build record from cleansed data
      const cleansedValues = cleansedParsed.data[0] as string[];
      const record: CsvRecord = {};
      headers.forEach((header, headerIndex) => {
        record[header] = (cleansedValues[headerIndex] || '').toString();
      });

      records.push(record);
      stats.rowsCleansed++;
    } else {
      // Row parsed correctly, use papaparse result
      const record: CsvRecord = {};
      headers.forEach((header) => {
        record[header] = parsedRow[header] || '';
      });
      records.push(record);
      stats.rowsSkipped++;
    }
  }

  return {
    headers,
    records,
    cleansingStats: stats,
  };
}

/**
 * Async wrapper to parse CSV from File object
 *
 * @param file - File object containing CSV data
 * @returns Promise resolving to parsed CSV data
 */
export async function parseCsvFile(file: File): Promise<CsvParseResult> {
  // Use FileReader for compatibility in test environments
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const result = parseAndCleanseCSV(text);
        resolve(result);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

/**
 * Parse CSV file and return only records (backward compatibility)
 *
 * @param file - File object containing CSV data
 * @returns Promise resolving to array of records
 */
export async function parseCsvData(file: File): Promise<CsvRecord[]> {
  const result = await parseCsvFile(file);
  return result.records;
}

/**
 * Parse CSV file and return headers and sample data (for discovery flow)
 *
 * @param file - File object containing CSV data
 * @param maxSampleRows - Maximum number of sample rows to return (default: 10)
 * @returns Promise resolving to headers and sample data
 */
export async function parseCsvFileForDiscovery(
  file: File,
  maxSampleRows: number = 10
): Promise<{ headers: string[]; sample_data: Array<Record<string, unknown>> }> {
  const result = await parseCsvFile(file);

  return {
    headers: result.headers,
    sample_data: result.records.slice(0, maxSampleRows) as Array<Record<string, unknown>>,
  };
}
