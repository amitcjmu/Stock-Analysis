#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

console.log('Adding return types for boundary type issues...');

// Get files with explicit-module-boundary-types issues
let lintOutput;
try {
  lintOutput = execSync('npm run lint 2>&1', { encoding: 'utf8' });
} catch (error) {
  lintOutput = error.output.join('');
}

const lines = lintOutput.split('\n');
const boundaryIssues = [];
let currentFile = null;

lines.forEach(line => {
  const fileMatch = line.match(/^([^:]+\.tsx?)$/);
  if (fileMatch) {
    currentFile = fileMatch[1];
    return;
  }

  const issueMatch = line.match(/^\s*(\d+):(\d+)\s+(warning|error)\s+.*explicit-module-boundary-types/);
  if (issueMatch && currentFile) {
    boundaryIssues.push({
      file: currentFile,
      line: parseInt(issueMatch[1]),
      column: parseInt(issueMatch[2])
    });
  }
});

console.log(`Found ${boundaryIssues.length} boundary type issues`);

// Group by file
const fileGroups = {};
boundaryIssues.forEach(issue => {
  if (!fileGroups[issue.file]) {
    fileGroups[issue.file] = [];
  }
  fileGroups[issue.file].push(issue);
});

let totalFixed = 0;

Object.keys(fileGroups).forEach((filePath, index) => {
  console.log(`\n[${index + 1}/${Object.keys(fileGroups).length}] Processing: ${filePath}`);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // Pattern 1: Simple function expressions without return types
    const simpleFunctionRegex = /(\w+)\s*:\s*\([^)]*\)\s*=>\s*\{/g;
    content = content.replace(simpleFunctionRegex, (match, funcName) => {
      if (!match.includes(': ') || match.lastIndexOf(':') < match.lastIndexOf(')')) {
        fileFixCount++;
        modified = true;
        return match.replace(') =>', '): void =>');
      }
      return match;
    });

    // Pattern 2: Function declarations without return types
    const functionDeclRegex = /function\s+(\w+)\s*\([^)]*\)\s*\{/g;
    content = content.replace(functionDeclRegex, (match, funcName) => {
      if (!match.includes(': ')) {
        fileFixCount++;
        modified = true;
        return match.replace(') {', '): void {');
      }
      return match;
    });

    // Pattern 3: Arrow functions assigned to variables
    const arrowFunctionRegex = /const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{/g;
    content = content.replace(arrowFunctionRegex, (match, funcName) => {
      if (!match.includes(': ') || match.lastIndexOf(':') < match.lastIndexOf(')')) {
        // Infer return type based on function name
        let returnType = 'void';
        const lowerName = funcName.toLowerCase();

        if (funcName.match(/^[A-Z]/) || lowerName.includes('render') || lowerName.includes('component')) {
          returnType = 'JSX.Element';
        } else if (lowerName.includes('get') || lowerName.includes('fetch')) {
          returnType = 'unknown';
        } else if (lowerName.includes('validate') || lowerName.includes('check') || lowerName.startsWith('is')) {
          returnType = 'boolean';
        }

        fileFixCount++;
        modified = true;
        return match.replace(') =>', `): ${returnType} =>`);
      }
      return match;
    });

    // Pattern 4: Object method definitions
    const methodRegex = /(\s+)(\w+)\s*\([^)]*\)\s*\{/g;
    content = content.replace(methodRegex, (match, whitespace, methodName) => {
      // Skip constructor and already typed methods
      if (methodName === 'constructor' || match.includes(': ')) {
        return match;
      }

      // Only apply to method-like patterns (indented)
      if (whitespace.length >= 2) {
        fileFixCount++;
        modified = true;
        return match.replace(') {', '): void {');
      }
      return match;
    });

    // Pattern 5: Export function declarations
    const exportFunctionRegex = /export\s+function\s+(\w+)\s*\([^)]*\)\s*\{/g;
    content = content.replace(exportFunctionRegex, (match, funcName) => {
      if (!match.includes(': ')) {
        let returnType = 'void';
        const lowerName = funcName.toLowerCase();

        if (funcName.match(/^[A-Z]/) || lowerName.includes('render') || lowerName.includes('component')) {
          returnType = 'JSX.Element';
        } else if (lowerName.includes('get') || lowerName.includes('fetch')) {
          returnType = 'unknown';
        }

        fileFixCount++;
        modified = true;
        return match.replace(') {', `): ${returnType} {`);
      }
      return match;
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log(`  ✅ Added ${fileFixCount} return types in ${filePath}`);
      totalFixed += fileFixCount;
    } else {
      console.log(`  ⏸️  No return types added in ${filePath}`);
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log(`\n🎉 Total return types added: ${totalFixed}`);
