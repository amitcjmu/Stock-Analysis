#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';

// Get all TypeScript/React files
const files = glob.sync('src/**/*.{ts,tsx}');
let totalFixed = 0;

console.log(`Processing ${files.length} files to fix explicit 'any' types...`);

files.forEach((filePath, index) => {
  console.log(`[${index + 1}/${files.length}] Processing: ${filePath}`);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // Fix function return types that are 'any' based on function analysis

    // Pattern 1: Functions returning JSX.Element instead of any
    const jsxFunctionRegex = /(\w+)\s*\([^)]*\):\s*any\s*=>\s*\{[^}]*return\s*\(/g;
    content = content.replace(jsxFunctionRegex, (match) => {
      if (match.includes('return (') || match.includes('jsx') || match.includes('<')) {
        fileFixCount++;
        modified = true;
        return match.replace(': any', ': JSX.Element');
      }
      return match;
    });

    // Pattern 2: Functions with React component patterns
    const componentFunctionRegex = /([A-Z]\w*)\s*\([^)]*\):\s*any\s*=>\s*\{/g;
    content = content.replace(componentFunctionRegex, (match, funcName) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': JSX.Element');
    });

    // Pattern 3: Event handlers that return void
    const handlerFunctionRegex = /(handle\w*|on\w*)\s*\([^)]*\):\s*any\s*=>\s*\{/g;
    content = content.replace(handlerFunctionRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': void');
    });

    // Pattern 4: Boolean functions
    const booleanFunctionRegex = /(is\w*|has\w*|can\w*|should\w*)\s*\([^)]*\):\s*any\s*=>\s*\{/g;
    content = content.replace(booleanFunctionRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': boolean');
    });

    // Pattern 5: String formatting/transformation functions
    const stringFunctionRegex = /(format\w*|transform\w*|convert\w*|render\w*)\s*\([^)]*\):\s*any\s*=>\s*\{/g;
    content = content.replace(stringFunctionRegex, (match, funcName) => {
      // Skip render functions that might return JSX
      if (funcName.toLowerCase().includes('render')) {
        fileFixCount++;
        modified = true;
        return match.replace(': any', ': JSX.Element | null');
      } else {
        fileFixCount++;
        modified = true;
        return match.replace(': any', ': string');
      }
    });

    // Pattern 6: Getter functions that return specific types
    const getterFunctionRegex = /(get\w*)\s*\([^)]*\):\s*any\s*=>\s*\{/g;
    content = content.replace(getterFunctionRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': unknown');
    });

    // Pattern 7: Filter/map/reduce callback functions
    const arrayCallbackRegex = /\.(filter|map|reduce|forEach|some|every)\s*\(\s*\([^)]*\):\s*any\s*=>/g;
    content = content.replace(arrayCallbackRegex, (match) => {
      if (match.includes('.filter') || match.includes('.some') || match.includes('.every')) {
        fileFixCount++;
        modified = true;
        return match.replace(': any', ': boolean');
      } else if (match.includes('.forEach')) {
        fileFixCount++;
        modified = true;
        return match.replace(': any', ': void');
      } else {
        fileFixCount++;
        modified = true;
        return match.replace(': any', ': unknown');
      }
    });

    // Pattern 8: useEffect return functions (cleanup functions)
    const useEffectCleanupRegex = /useEffect\s*\(\s*\(\s*\)\s*:\s*any\s*=>/g;
    content = content.replace(useEffectCleanupRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': void | (() => void)');
    });

    // Pattern 9: Promise functions
    const promiseFunctionRegex = /(async\s+\w+)\s*\([^)]*\):\s*any\s*=>/g;
    content = content.replace(promiseFunctionRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': Promise<unknown>');
    });

    // Pattern 10: Replace remaining isolated 'any' return types with 'unknown' (safer)
    const isolatedAnyRegex = /\):\s*any\s*=>/g;
    content = content.replace(isolatedAnyRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': unknown');
    });

    // Pattern 11: Function declarations with 'any' return type
    const functionDeclarationAnyRegex = /function\s+\w+\s*\([^)]*\):\s*any\s*\{/g;
    content = content.replace(functionDeclarationAnyRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': unknown');
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log(`  ✅ Fixed ${fileFixCount} explicit 'any' types in ${filePath}`);
      totalFixed += fileFixCount;
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log(`\n🎉 Total explicit 'any' types fixed: ${totalFixed}`);
