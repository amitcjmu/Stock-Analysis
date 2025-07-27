#!/usr/bin/env node
import fs from 'fs/promises';
import path from 'path';
import { glob } from 'glob';
import ts from 'typescript';

async function fixReturnTypes() {
  const files = await glob('src/**/*.{ts,tsx}', {
    ignore: ['**/*.d.ts', '**/node_modules/**', '**/*.test.*', '**/*.spec.*']
  });

  console.log(`Found ${files.length} TypeScript files to check`);
  let totalFixed = 0;

  for (const file of files) {
    const content = await fs.readFile(file, 'utf-8');
    const updated = addReturnTypes(content, file);

    if (content !== updated) {
      await fs.writeFile(file, updated);
      console.log(`✅ Fixed ${file}`);
      totalFixed++;
    }
  }

  console.log(`\n✨ Fixed return types in ${totalFixed} files`);
}

function addReturnTypes(content, filePath) {
  // Parse common patterns and add return types
  let updated = content;

  // Pattern 1: Export functions without return type
  updated = updated.replace(
    /export\s+(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*{/g,
    (match, async, name, params) => {
      // Skip if already has return type
      if (match.includes(':')) return match;

      // Infer return type based on function name and content
      const returnType = inferReturnType(name, content, !!async);
      return `export ${async || ''}function ${name}(${params})${returnType} {`;
    }
  );

  // Pattern 2: Arrow functions in hooks
  updated = updated.replace(
    /export\s+const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>\s*{/g,
    (match, name, params) => {
      // Skip if already has return type
      if (match.includes(':')) return match;

      // Check if it's a hook
      if (name.startsWith('use')) {
        const returnType = inferHookReturnType(name, content);
        return `export const ${name} = (${params})${returnType} => {`;
      }
      return match;
    }
  );

  // Pattern 3: Component functions
  updated = updated.replace(
    /const\s+(\w+):\s*React\.FC(?:<[^>]+>)?\s*=\s*\(([^)]*)\)\s*=>\s*{/g,
    (match) => match // Already typed as React.FC
  );

  // Pattern 4: Regular const functions
  updated = updated.replace(
    /export\s+const\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)\s*=>\s*{/g,
    (match, name, async, params) => {
      // Skip if already has return type or is a component
      if (match.includes(':') || name[0] === name[0].toUpperCase()) return match;

      const returnType = inferReturnType(name, content, !!async);
      return `export const ${name} = ${async || ''}(${params})${returnType} => {`;
    }
  );

  return updated;
}

function inferReturnType(functionName, content, isAsync) {
  // Common patterns
  if (functionName.includes('validate') || functionName.startsWith('is')) {
    return isAsync ? ': Promise<boolean>' : ': boolean';
  }

  if (functionName.includes('get') || functionName.includes('fetch')) {
    return isAsync ? ': Promise<any>' : ': any';
  }

  if (functionName.includes('handle') || functionName.startsWith('on')) {
    return isAsync ? ': Promise<void>' : ': void';
  }

  if (functionName.includes('create') || functionName.includes('build')) {
    return isAsync ? ': Promise<any>' : ': any';
  }

  // Check for explicit returns in function body
  const functionBody = content.substring(content.indexOf(functionName));
  const returnMatch = functionBody.match(/return\s+([^;]+);/);

  if (returnMatch) {
    const returnValue = returnMatch[1].trim();

    if (returnValue === 'true' || returnValue === 'false') {
      return isAsync ? ': Promise<boolean>' : ': boolean';
    }

    if (returnValue === 'null' || returnValue === 'undefined') {
      return isAsync ? ': Promise<void>' : ': void';
    }

    if (returnValue.startsWith('{') || returnValue.startsWith('[')) {
      return isAsync ? ': Promise<any>' : ': any';
    }
  }

  // Default return types
  return isAsync ? ': Promise<any>' : ': any';
}

function inferHookReturnType(hookName, content) {
  // Common hook patterns
  if (hookName === 'useState') return '';
  if (hookName === 'useEffect' || hookName === 'useLayoutEffect') return '';

  // Custom hooks
  if (hookName.includes('Query') || hookName.includes('Mutation')) {
    return ': any'; // Could be more specific with react-query types
  }

  // Check for object return
  const functionBody = content.substring(content.indexOf(hookName));
  if (functionBody.includes('return {')) {
    return ': any'; // Could analyze the object structure
  }

  // Default for custom hooks
  return ': any';
}

// Run the script
fixReturnTypes().catch(console.error);
