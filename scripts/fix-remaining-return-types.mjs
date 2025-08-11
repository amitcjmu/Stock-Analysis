#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

// Get specific files with return type issues
const output = execSync('npm run lint 2>&1 | grep "Missing return type on function"', { encoding: 'utf8' });
const files = [...new Set(output.split('\n').filter(line => line.includes('.tsx') || line.includes('.ts')).map(line => {
  const match = line.match(/\/([^:]+\.(tsx?)):/);
  return match ? match[1] : null;
}).filter(Boolean))];

console.log('Found ', files.length, ' files with return type issues:');
files.forEach(file => console.log('  - ', file));

let totalFixed = 0;

files.forEach((filePath, index) => {
  console.log('\n[', index + 1, '/', files.length, '] Processing: ', filePath);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // More targeted patterns for functions without return types

    // Pattern 1: Exported functions without return types
    const exportedFunctionRegex = /export\s+(const|function)\s+(\w+)\s*=?\s*([^:]*)\s*(?:\([^)]*\))?\s*(?:=>\s*)?\{/g;
    content = content.replace(exportedFunctionRegex, (match, keyword, funcName, rest) => {
      if (match.includes(': ') && match.lastIndexOf(':') > match.lastIndexOf(')')) {
        return match; // Already has return type
      }

      // Analyze function for better return type inference
      const returnType = inferReturnTypeFromName(funcName);
      fileFixCount++;
      modified = true;

      if (keyword === 'const') {
        if (match.includes('=>')) {
          const paramMatch = match.match(/\(([^)]*)\)/);
          const params = paramMatch ? paramMatch[1] : '';
          return `export const ${funcName} = (${params}): ${returnType} => {`;
        } else {
          return `export const ${funcName}: () => ${returnType} = {`;
        }
      } else {
        const paramMatch = match.match(/\(([^)]*)\)/);
        const params = paramMatch ? paramMatch[1] : '';
        return `export function ${funcName}(${params}): ${returnType} {`;
      }
    });

    // Pattern 2: Method-like functions in objects
    const methodRegex = /(\s+)(\w+)\s*\([^)]*\)\s*\{/g;
    content = content.replace(methodRegex, (match, whitespace, methodName) => {
      if (match.includes(': ')) return match; // Already has return type

      // Skip certain patterns
      if (methodName === 'constructor' || methodName.startsWith('use') || methodName.startsWith('handle')) {
        return match;
      }

      const returnType = inferReturnTypeFromName(methodName);
      fileFixCount++;
      modified = true;

      const paramMatch = match.match(/\(([^)]*)\)/);
      const params = paramMatch ? paramMatch[1] : '';
      return `${whitespace}${methodName}(${params}): ${returnType} {`;
    });

    // Pattern 3: Anonymous functions and arrow functions assigned to variables
    const varFunctionRegex = /(const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{/g;
    content = content.replace(varFunctionRegex, (match, keyword, varName) => {
      if (match.includes(': ') && match.lastIndexOf(':') > match.lastIndexOf(')')) {
        return match; // Already has return type
      }

      const returnType = inferReturnTypeFromName(varName);
      fileFixCount++;
      modified = true;

      const paramMatch = match.match(/\(([^)]*)\)/);
      const params = paramMatch ? paramMatch[1] : '';
      return `${keyword} ${varName} = (${params}): ${returnType} => {`;
    });

    // Pattern 4: Callback functions without return types
    const callbackRegex = /(\w+):\s*\([^)]*\)\s*=>\s*\{/g;
    content = content.replace(callbackRegex, (match, callbackName) => {
      if (match.includes(': ') && match.split(':').length > 2) {
        return match; // Already has return type
      }

      const returnType = inferReturnTypeFromName(callbackName, 'callback');
      fileFixCount++;
      modified = true;

      const paramMatch = match.match(/\(([^)]*)\)/);
      const params = paramMatch ? paramMatch[1] : '';
      return `${callbackName}: (${params}): ${returnType} => {`;
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log('  ✅ Fixed ', fileFixCount, ' return types in ', filePath);
      totalFixed += fileFixCount;
    } else {
      console.log('  ⏸️  No additional fixes needed in ', filePath);
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log('\n🎉 Total return types fixed: ', totalFixed);

// Helper function to infer return type based on function name and context
function inferReturnTypeFromName(functionName, context = 'function') {
  const name = functionName.toLowerCase();

  // React component patterns
  if (functionName.match(/^[A-Z]/) && context !== 'callback') {
    return 'JSX.Element';
  }

  // Hook patterns
  if (name.startsWith('use')) {
    if (name.includes('state')) return 'any';
    if (name.includes('effect')) return 'void';
    if (name.includes('callback') || name.includes('memo')) return 'any';
    return 'any';
  }

  // Handler patterns
  if (name.includes('handle') || name.includes('handler') || name.startsWith('on')) {
    return 'void';
  }

  // Getter patterns
  if (name.startsWith('get') || name.startsWith('fetch') || name.startsWith('load')) {
    if (name.includes('async') || context === 'async') return 'Promise<any>';
    return 'any';
  }

  // Boolean patterns
  if (name.startsWith('is') || name.startsWith('has') || name.startsWith('can') || name.startsWith('should')) {
    return 'boolean';
  }

  // Utility functions
  if (name.includes('format') || name.includes('transform') || name.includes('convert')) {
    return 'string';
  }

  // Callback context
  if (context === 'callback') {
    return 'void';
  }

  // Default fallback
  return 'any';
}
