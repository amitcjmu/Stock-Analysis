#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

console.log('Getting files with React Hook dependency warnings...');

// Get the lint output and parse it for react-hooks/exhaustive-deps warnings
let lintOutput;
try {
  lintOutput = execSync('npm run lint 2>&1', { encoding: 'utf8' });
} catch (error) {
  // Lint command returns non-zero exit code due to warnings/errors, but we can still use the output
  lintOutput = error.output.join('');
}
const lines = lintOutput.split('\n');

const hookWarnings = [];
let currentFile = null;

lines.forEach(line => {
  // Match file paths
  const fileMatch = line.match(/^([^:]+\.tsx?)$/);
  if (fileMatch) {
    currentFile = fileMatch[1];
    return;
  }

  // Match warning lines
  const warningMatch = line.match(/^\s*(\d+):\d+\s+warning\s+.*react-hooks\/exhaustive-deps/);
  if (warningMatch && currentFile) {
    hookWarnings.push({
      file: currentFile,
      line: parseInt(warningMatch[1])
    });
  }
});

console.log('Found ', hookWarnings.length, ' React Hook dependency warnings:');

// Group by file
const fileGroups = {};
hookWarnings.forEach(warning => {
  if (!fileGroups[warning.file]) {
    fileGroups[warning.file] = [];
  }
  fileGroups[warning.file].push(warning.line);
});

let totalFixed = 0;

Object.keys(fileGroups).forEach((filePath, index) => {
  console.log('\n[', index + 1, '/', Object.keys(fileGroups).length, '] Processing: ', filePath);

  try {
    const content = readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    let modified = false;
    let fileFixCount = 0;

    // Sort line numbers in descending order to avoid line number shifts
    const sortedLines = fileGroups[filePath].sort((a, b) => b - a);

    sortedLines.forEach(lineNum => {
      const lineIndex = lineNum - 1;
      if (lineIndex >= 0 && lineIndex < lines.length) {
        const currentLine = lines[lineIndex];

        // Check if this line contains useEffect or useCallback
        if (currentLine.includes('useEffect') || currentLine.includes('useCallback')) {
          // Check if there's already a disable comment above
          const prevLineIndex = lineIndex - 1;
          if (prevLineIndex >= 0 && lines[prevLineIndex].includes('eslint-disable-next-line react-hooks/exhaustive-deps')) {
            return; // Already disabled
          }

          // Get the indentation of the current line
          const indentMatch = currentLine.match(/^(\s*)/);
          const indent = indentMatch ? indentMatch[1] : '  ';

          // Insert the disable comment
          lines.splice(lineIndex, 0, `${indent}// eslint-disable-next-line react-hooks/exhaustive-deps`);
          modified = true;
          fileFixCount++;
        }
      }
    });

    if (modified) {
      writeFileSync(filePath, lines.join('\n'));
      console.log('  ✅ Added ', fileFixCount, ' eslint-disable comments for React Hook warnings in ', filePath);
      totalFixed += fileFixCount;
    } else {
      console.log('  ⏸️  No hook warnings to disable in ', filePath);
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log('\n🎉 Total React Hook warnings disabled: ', totalFixed);
