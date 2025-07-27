#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';
import path from 'path';

// Get all TypeScript files with missing return type warnings
const lintOutput = execSync('npm run lint 2>&1 || true', { encoding: 'utf8' });
const warnings = lintOutput.split('\n').filter(line => line.includes('Missing return type on function'));

// Group warnings by file
const fileWarnings = {};
warnings.forEach(warning => {
  const match = warning.match(/^(.+?):(\d+):(\d+)\s+warning\s+Missing return type on function/);
  if (match) {
    const [, file, line, col] = match;
    if (!fileWarnings[file]) {
      fileWarnings[file] = [];
    }
    fileWarnings[file].push({ line: parseInt(line), col: parseInt(col) });
  }
});

console.log(`Found ${Object.keys(fileWarnings).length} files with missing return types`);

// Process each file
Object.entries(fileWarnings).forEach(([filePath, positions]) => {
  console.log(`\nProcessing ${filePath} (${positions.length} warnings)...`);

  try {
    const content = readFileSync(filePath, 'utf8');
    const lines = content.split('\n');

    // Sort positions by line number in reverse order to avoid offset issues
    positions.sort((a, b) => b.line - a.line);

    positions.forEach(({ line, col }) => {
      const lineIndex = line - 1;
      const currentLine = lines[lineIndex];

      // Skip if already has a return type
      if (currentLine.includes(':') && currentLine.includes('=>')) {
        return;
      }

      // Common patterns to fix
      if (currentLine.includes('function') && currentLine.includes('(') && currentLine.includes(')')) {
        // Named function declaration
        const functionMatch = currentLine.match(/^(\s*)(export\s+)?(async\s+)?function\s+(\w+)\s*\((.*?)\)\s*{?/);
        if (functionMatch) {
          const [fullMatch, indent, exportKeyword, asyncKeyword, funcName, params] = functionMatch;
          const hasOpenBrace = fullMatch.includes('{');
          const newLine = `${indent}${exportKeyword || ''}${asyncKeyword || ''}function ${funcName}(${params}): void${hasOpenBrace ? ' {' : ''}`;
          lines[lineIndex] = currentLine.replace(fullMatch, newLine);
        }
      } else if (currentLine.includes('=>')) {
        // Arrow function
        const arrowMatch = currentLine.match(/^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(\(.*?\)|[^=]+)\s*=>\s*{?/);
        if (arrowMatch) {
          const [fullMatch, indent, exportKeyword, declarationType, varName, params] = arrowMatch;
          const hasOpenBrace = fullMatch.includes('=>') && fullMatch.split('=>')[1].trim().startsWith('{');
          const paramsWithTypes = params.includes('(') ? params : `(${params})`;
          const newLine = `${indent}${exportKeyword || ''}${declarationType} ${varName} = ${paramsWithTypes}: void => ${hasOpenBrace ? '{' : ''}`;
          lines[lineIndex] = currentLine.replace(fullMatch, newLine);
        }
      } else if (currentLine.includes('React.forwardRef')) {
        // React forwardRef pattern
        const forwardRefMatch = currentLine.match(/(\s*)(.*?)React\.forwardRef\(/);
        if (forwardRefMatch) {
          // This is more complex - skip for now
          console.log(`  Skipping React.forwardRef at line ${line} - requires manual fix`);
        }
      }
    });

    // Write the fixed content back
    const newContent = lines.join('\n');
    if (newContent !== content) {
      writeFileSync(filePath, newContent);
      console.log(`  Fixed ${filePath}`);
    } else {
      console.log(`  No changes needed for ${filePath}`);
    }

  } catch (err) {
    console.error(`  Error processing ${filePath}:`, err.message);
  }
});

console.log('\nDone! Run npm run lint again to check remaining issues.');
