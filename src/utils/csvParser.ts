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
  cleansing_stats?: CleansingStats;
}

export interface CleansingStats {
  total_rows: number;
  rows_cleansed: number;
  rows_skipped: number;
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

  /**
   * Maximum file size in bytes to prevent DoS attacks
   * Default: 10MB
   */
  MAX_FILE_SIZE: 10 * 1024 * 1024 as number,

  /**
   * Maximum number of rows to prevent resource exhaustion
   * Default: 100,000 rows
   */
  MAX_ROWS: 100000 as number,

  /**
   * Maximum field length in characters to prevent large field DoS
   * Default: 100KB per field
   */
  MAX_FIELD_LENGTH: 100 * 1024 as number,

  /**
   * Maximum number of columns to prevent column explosion attacks
   * Default: 1000 columns
   */
  MAX_COLUMNS: 1000 as number,
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

  // Identify candidate fields for merging - consider all fields as potential candidates
  const candidateStart = 0;
  const candidateEnd = Math.min(expectedColumnCount - 1, actualColumnCount - excessColumns - 1);

  // Find the longest field among candidates (likely the text field with commas)
  let mergeTargetIndex = -1;
  let maxLength = -1;

  for (let i = candidateStart; i <= candidateEnd; i++) {
    if (parts[i] && parts[i].length > maxLength && parts[i].length >= CSV_CLEANSING_CONFIG.MIN_TEXT_FIELD_LENGTH) {
      maxLength = parts[i].length;
      mergeTargetIndex = i;
    }
  }

  // If no suitable target found, default to the first field to avoid errors
  if (mergeTargetIndex === -1) {
    mergeTargetIndex = 0;
  }

  // Build cleansed row by merging excess columns into the target field
  // Simplified single-loop approach
  const cleansedParts: string[] = [];
  let partIndex = 0;

  while (cleansedParts.length < expectedColumnCount && partIndex < parts.length) {
    if (cleansedParts.length === mergeTargetIndex) {
      // This is the target column - merge it with the excess parts
      const partsToMerge = parts.slice(partIndex, partIndex + excessColumns + 1);
      const mergedValue = partsToMerge.join(CSV_CLEANSING_CONFIG.COMMA_REPLACEMENT);
      cleansedParts.push(mergedValue);
      partIndex += excessColumns + 1;
    } else {
      // This is a regular column
      cleansedParts.push(parts[partIndex]);
      partIndex++;
    }
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
 * Uses papaparse for proper CSV parsing, then applies cleansing only for rows that papaparse
 * identifies as malformed (via error reporting), preventing corruption of valid quoted CSV files.
 *
 * @param fileContent - Raw CSV file content as string
 * @returns Parsed CSV data with headers and records
 * @throws Error if file size exceeds limits or validation fails
 */
export function parseAndCleanseCSV(fileContent: string): CsvParseResult {
  // Validate input size to prevent DoS attacks
  if (fileContent.length > CSV_CLEANSING_CONFIG.MAX_FILE_SIZE) {
    throw new Error(
      `CSV file size (${fileContent.length} bytes) exceeds maximum allowed size (${CSV_CLEANSING_CONFIG.MAX_FILE_SIZE} bytes)`
    );
  }

  if (!fileContent || fileContent.trim().length === 0) {
      return {
        headers: [],
        records: [],
        cleansing_stats: {
          total_rows: 0,
          rows_cleansed: 0,
          rows_skipped: 0,
        },
      };
  }

  // Use papaparse to parse CSV (handles quoted fields, newlines, etc. correctly)
  const parsed = Papa.parse(fileContent, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => header.trim().replace(/"/g, ''),
    transform: (value) => {
      const trimmed = value.trim();
      // Validate field length to prevent large field DoS
      if (trimmed.length > CSV_CLEANSING_CONFIG.MAX_FIELD_LENGTH) {
        throw new Error(
          `Field length (${trimmed.length}) exceeds maximum allowed length (${CSV_CLEANSING_CONFIG.MAX_FIELD_LENGTH})`
        );
      }
      return trimmed;
    },
  });

  const headers = parsed.meta.fields || [];

  // Validate header count
  if (headers.length > CSV_CLEANSING_CONFIG.MAX_COLUMNS) {
    throw new Error(
      `Number of columns (${headers.length}) exceeds maximum allowed (${CSV_CLEANSING_CONFIG.MAX_COLUMNS})`
    );
  }

  // Validate and sanitize header names
  const sanitizedHeaders = headers.map((header, index) => {
    if (!header || typeof header !== 'string') {
      return `column_${index + 1}`;
    }
    // Remove potentially dangerous characters, limit length
    const sanitized = header.replace(/[^\w\s-]/g, '_').substring(0, 100);
    return sanitized || `column_${index + 1}`;
  });

  const expectedColumnCount = sanitizedHeaders.length;

  if (sanitizedHeaders.length === 0) {
      return {
        headers: [],
        records: [],
        cleansing_stats: {
          total_rows: 0,
          rows_cleansed: 0,
          rows_skipped: 0,
        },
      };
  }

  // Validate row count
  if (parsed.data.length > CSV_CLEANSING_CONFIG.MAX_ROWS) {
    throw new Error(
      `Number of rows (${parsed.data.length}) exceeds maximum allowed (${CSV_CLEANSING_CONFIG.MAX_ROWS})`
    );
  }

  // Track cleansing statistics and audit info
  const stats: CleansingStats = {
    total_rows: parsed.data.length,
    rows_cleansed: 0,
    rows_skipped: 0,
  };

  // Use papaparse's error reporting AND column count checking to identify malformed rows
  // This prevents corrupting valid quoted CSV files, but also catches column misalignment
  const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line.length > 0);
  const linesWithoutHeader = lines.slice(1);

  // Create a set of row indexes that have errors (malformed rows) from papaparse
  const errorRowIndexesFromParser = new Set<number>(
    parsed.errors
      .filter((e) => e.code === 'TooManyFields' || e.code === 'Quotes')
      .map((e) => e.row || 0)
  );

  // Additionally check for column count mismatches by parsing without headers
  // This catches unquoted commas that papaparse might parse incorrectly
  const errorRowIndexes = new Set<number>(errorRowIndexesFromParser);

  // Parse first line as header to get expected column count
  const headerLine = lines[0];
  const headerParsed = Papa.parse(headerLine, {
    header: false,
    skipEmptyLines: false,
  });
  const expectedColumnCountFromHeader = (headerParsed.data[0] as string[])?.length || expectedColumnCount;

  // Check each data row for column count mismatches
  console.info(
    `[CSV Detection] Checking ${linesWithoutHeader.length} rows for column mismatches. Expected columns: ${expectedColumnCountFromHeader}`
  );

  for (let i = 0; i < linesWithoutHeader.length; i++) {
    const rowLine = linesWithoutHeader[i];
    if (!rowLine) continue;

    // Parse this row without header to get actual column count
    const rowParsed = Papa.parse(rowLine, {
      header: false,
      skipEmptyLines: false,
    });
    const actualColumnCount = (rowParsed.data[0] as string[])?.length || 0;
    const rowValues = (rowParsed.data[0] as string[]) || [];

    // If column count doesn't match, this row likely has unquoted commas causing misalignment
    if (actualColumnCount > expectedColumnCountFromHeader) {
      errorRowIndexes.add(i);
      console.warn(
        `[CSV Detection] ⚠️ Row ${i + 1} has column mismatch: expected ${expectedColumnCountFromHeader}, got ${actualColumnCount} - likely unquoted commas`
      );
      console.warn(`[CSV Detection] Row ${i + 1} content preview: ${rowLine.substring(0, 150)}...`);
      console.warn(`[CSV Detection] Row ${i + 1} parsed values:`, rowValues);
    } else if (actualColumnCount < expectedColumnCountFromHeader) {
      // Log but don't cleanse - missing columns might be intentional
      console.warn(
        `[CSV Detection] Row ${i + 1} has fewer columns: expected ${expectedColumnCountFromHeader}, got ${actualColumnCount}`
      );
    }
  }

  // Audit log (can be enhanced to send to logging service)
  if (errorRowIndexes.size > 0) {
    console.info(
      `[CSV Parsing] Detected ${errorRowIndexes.size} malformed rows out of ${parsed.data.length} total rows (${errorRowIndexesFromParser.size} from papaparse errors, ${errorRowIndexes.size - errorRowIndexesFromParser.size} from column count checks)`
    );
  }

  const records: CsvRecord[] = [];

  for (let i = 0; i < parsed.data.length; i++) {
    const originalLine = linesWithoutHeader[i];
    const needsCleansing = errorRowIndexes.has(i);

    if (needsCleansing && originalLine) {
      // Only cleanse rows that papaparse identified as malformed OR column count mismatch detected
      // Apply cleansing to the original line using the detected expected column count
      const cleansedLine = cleanseMisalignedRow(originalLine, expectedColumnCountFromHeader || expectedColumnCount);

      // Parse cleansed line with papaparse
      const cleansedParsed = Papa.parse(cleansedLine, {
        header: false,
        skipEmptyLines: false,
        transform: (value) => {
          const trimmed = value.trim();
          if (trimmed.length > CSV_CLEANSING_CONFIG.MAX_FIELD_LENGTH) {
            return trimmed.substring(0, CSV_CLEANSING_CONFIG.MAX_FIELD_LENGTH);
          }
          return trimmed;
        },
      });

      // Build record from cleansed data
      const cleansedValues = cleansedParsed.data[0] as string[];
      const record: CsvRecord = {};
      sanitizedHeaders.forEach((header, headerIndex) => {
        const value = cleansedValues[headerIndex] || '';
        record[header] = value.toString();
      });

      records.push(record);
      stats.rows_cleansed++;

      // Audit log for cleansing action
      console.info(`[CSV Cleansing] Row ${i + 1} cleansed: merged excess columns (unquoted commas replaced with spaces)`);
    } else {
      // Row parsed correctly by papaparse, use its result directly
      const parsedRow = parsed.data[i] as Record<string, unknown>;
      const record: CsvRecord = {};
      sanitizedHeaders.forEach((header, originalHeaderIndex) => {
        // Use original header name for lookup (before sanitization)
        const originalHeader = headers[originalHeaderIndex];
        const value = parsedRow[originalHeader] || '';
        record[header] = value.toString();
      });
      records.push(record);
      stats.rows_skipped++;
    }
  }

  // Final audit log
  console.info(
    `[CSV Parsing Complete] Parsed ${records.length} records, ${stats.rows_cleansed} cleansed, ${stats.rows_skipped} skipped`
  );

  if (stats.rows_cleansed > 0) {
    console.warn(
      `[CSV Parsing] ⚠️ DATA CLEANSING WAS APPLIED: ${stats.rows_cleansed} row(s) had unquoted commas replaced with spaces`
    );
  } else {
    console.info(
      `[CSV Parsing] ✅ No cleansing needed - all CSV data is properly formatted (commas are correctly quoted)`
    );
  }

  return {
    headers: sanitizedHeaders,
    records,
    cleansing_stats: stats,
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
        if (!text) {
          reject(
            new Error(
              'Failed to read CSV file: File appears to be empty or could not be read. ' +
                'Please ensure the file contains valid CSV data and try again.'
            )
          );
          return;
        }
        const result = parseAndCleanseCSV(text);
        resolve(result);
      } catch (error) {
        // Provide actionable error messages for parsing failures
        if (error instanceof Error) {
          // Check for specific error types from parseAndCleanseCSV
          if (error.message.includes('exceeds maximum')) {
            reject(
              new Error(
                `CSV file validation failed: ${error.message}. ` +
                  'Please reduce the file size or split it into smaller files. ' +
                  'Maximum allowed: 10MB file size, 100,000 rows, 1000 columns.'
              )
            );
          } else if (error.message.includes('Invalid CSV')) {
            reject(
              new Error(
                `CSV parsing failed: ${error.message}. ` +
                  'Please ensure the file is a valid CSV format with proper column headers. ' +
                  'Try opening the file in a spreadsheet application to verify the format.'
              )
            );
          } else {
            reject(
              new Error(
                `Failed to parse CSV file: ${error.message}. ` +
                  'Please ensure the file is a valid CSV file with UTF-8 encoding. ' +
                  'Try opening the file in a text editor and re-saving as UTF-8 if needed.'
              )
            );
          }
        } else {
          reject(
            new Error(
              'Failed to parse CSV file: Unknown error occurred. ' +
                'Please ensure the file is a valid CSV file and try again.'
            )
          );
        }
      }
    };
    reader.onerror = (e) => {
      const error = (e.target as FileReader).error;
      const errorMsg = error?.message || 'Unknown error';
      reject(
        new Error(
          `Failed to read CSV file: ${errorMsg}. ` +
            'Please ensure the file is a valid text file with UTF-8 encoding. ' +
            'Try opening the file in a text editor and re-saving as UTF-8 if needed.'
        )
      );
    };
    reader.readAsText(file);
  });
}

/**
 * Parse CSV file and return records (backward compatibility)
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
