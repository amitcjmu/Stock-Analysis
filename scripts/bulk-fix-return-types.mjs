#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';
import { execSync } from 'child_process';
import path from 'path';

// Get all TypeScript/React files
const files = glob.sync('src/**/*.{ts,tsx}');
let totalFixed = 0;

console.log('Processing ', files.length, ' files for return type fixes...');

files.forEach((filePath, index) => {
  console.log('[', index + 1, '/', files.length, '] Processing: ', filePath);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // Pattern 1: Function declarations without return types
    const functionDeclarationRegex = /(export\s+)?(async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{/g;
    content = content.replace(functionDeclarationRegex, (match, exportKeyword = '', asyncKeyword = '', functionName, offset) => {
      // Skip if already has return type
      if (match.includes(': ')) return match;

      // Analyze function content to determine return type
      const remainingContent = content.slice(offset);
      const functionEnd = findFunctionEnd(remainingContent);
      const functionBody = remainingContent.slice(0, functionEnd);

      const returnType = inferReturnType(functionBody, functionName);
      fileFixCount++;
      modified = true;

      return `${exportKeyword}${asyncKeyword}function ${functionName}(${match.match(/\(([^)]*)\)/)[1]}): ${returnType} {`;
    });

    // Pattern 2: Arrow functions without return types
    const arrowFunctionRegex = /(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>\s*\{/g;
    content = content.replace(arrowFunctionRegex, (match, exportKeyword = '', declarationKeyword, functionName, asyncKeyword = '') => {
      // Skip if already has return type
      if (match.includes(': ') && match.lastIndexOf(':') > match.lastIndexOf(')')) return match;

      // Find the function body
      const functionStart = match.lastIndexOf('=>');
      const remainingContent = content.slice(content.indexOf(match) + functionStart);
      const functionEnd = findFunctionEnd(remainingContent);
      const functionBody = remainingContent.slice(0, functionEnd);

      const returnType = inferReturnType(functionBody, functionName);
      fileFixCount++;
      modified = true;

      const params = match.match(/\(([^)]*)\)/)[1];
      return `${exportKeyword}${declarationKeyword} ${functionName} = ${asyncKeyword}(${params}): ${returnType} => {`;
    });

    // Pattern 3: Method definitions without return types
    const methodRegex = /(\s+)(async\s+)?(\w+)\s*\([^)]*\)\s*\{/g;
    content = content.replace(methodRegex, (match, whitespace, asyncKeyword = '', methodName) => {
      // Skip constructors and special methods
      if (methodName === 'constructor' || methodName.startsWith('use') || methodName.startsWith('handle')) return match;
      // Skip if already has return type
      if (match.includes(': ')) return match;

      const returnType = inferReturnType('', methodName);
      fileFixCount++;
      modified = true;

      const params = match.match(/\(([^)]*)\)/)[1];
      return `${whitespace}${asyncKeyword}${methodName}(${params}): ${returnType} {`;
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log('  ✅ Fixed ', fileFixCount, ' return types in ', filePath);
      totalFixed += fileFixCount;
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log('\n🎉 Total return types fixed: ', totalFixed);

// Helper function to find the end of a function body
function findFunctionEnd(content) {
  let braceCount = 0;
  let inString = false;
  let inComment = false;
  let i = 0;

  while (i < content.length) {
    const char = content[i];
    const nextChar = content[i + 1];

    // Handle string literals
    if ((char === '"' || char === "'" || char === '`') && !inComment) {
      inString = !inString;
    }
    // Handle comments
    else if (char === '/' && nextChar === '/' && !inString) {
      inComment = true;
    }
    else if (char === '\n' && inComment) {
      inComment = false;
    }
    // Handle braces
    else if (!inString && !inComment) {
      if (char === '{') braceCount++;
      if (char === '}') braceCount--;
      if (braceCount === 0 && char === '}') {
        return i + 1;
      }
    }
    i++;
  }
  return content.length;
}

// Helper function to infer return type based on function content and name
function inferReturnType(functionBody, functionName) {
  // React component patterns
  if (functionName.match(/^[A-Z]/) || functionBody.includes('jsx') || functionBody.includes('JSX') || functionBody.includes('<')) {
    return 'JSX.Element';
  }

  // Hook patterns
  if (functionName.startsWith('use')) {
    if (functionBody.includes('useState')) return 'any'; // More specific typing would need analysis
    if (functionBody.includes('useEffect')) return 'void';
    if (functionBody.includes('useMemo') || functionBody.includes('useCallback')) return 'any';
    return 'any';
  }

  // Handler patterns
  if (functionName.includes('Handler') || functionName.includes('handle') || functionName.startsWith('on')) {
    return 'void';
  }

  // Async function patterns
  if (functionBody.includes('await') || functionBody.includes('Promise') || functionBody.includes('async')) {
    return 'Promise<any>';
  }

  // Return statement analysis
  if (functionBody.includes('return true') || functionBody.includes('return false')) {
    return 'boolean';
  }
  if (functionBody.includes('return null')) {
    return 'null';
  }
  if (functionBody.includes('return undefined') || functionBody.includes('return;')) {
    return 'void';
  }
  if (functionBody.includes('return []')) {
    return 'any[]';
  }
  if (functionBody.includes('return {}')) {
    return 'any';
  }

  // Default fallback
  return 'any';
}
