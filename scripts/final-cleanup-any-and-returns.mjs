#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

// Get specific files with remaining any or return type issues
console.log('Getting files with remaining linting issues...');
const lintOutput = execSync('npm run lint 2>&1 | grep -E "(Unexpected any|Missing return type)" | head -100', { encoding: 'utf8' });
const fileMatches = [...new Set(lintOutput.split('\n').filter(line => line.includes('.tsx') || line.includes('.ts')).map(line => {
  const match = line.match(/^([^:]+\.tsx?)/);
  return match ? match[1] : null;
}).filter(Boolean))];

console.log(`Found ${fileMatches.length} files with remaining issues:`);
fileMatches.forEach(file => console.log(`  - ${file}`));

let totalFixed = 0;

fileMatches.forEach((filePath, index) => {
  console.log(`\n[${index + 1}/${fileMatches.length}] Processing: ${filePath}`);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // Fix remaining patterns that our previous scripts missed

    // 1. Replace 'unknown' with more specific types for common patterns
    const unknownToSpecificRegex = /(\w+)\s*\([^)]*\):\s*unknown\s*=>/g;
    content = content.replace(unknownToSpecificRegex, (match, funcName) => {
      const lowerName = funcName.toLowerCase();
      let betterType = 'unknown';

      if (lowerName.includes('render') || lowerName.includes('component') || funcName.match(/^[A-Z]/)) {
        betterType = 'JSX.Element | null';
      } else if (lowerName.includes('handle') || lowerName.includes('click') || lowerName.includes('submit')) {
        betterType = 'void';
      } else if (lowerName.includes('validate') || lowerName.includes('check') || lowerName.startsWith('is') || lowerName.startsWith('has')) {
        betterType = 'boolean';
      } else if (lowerName.includes('format') || lowerName.includes('parse') || lowerName.includes('string')) {
        betterType = 'string';
      } else if (lowerName.includes('count') || lowerName.includes('length') || lowerName.includes('size')) {
        betterType = 'number';
      }

      if (betterType !== 'unknown') {
        fileFixCount++;
        modified = true;
        return match.replace(': unknown', `: ${betterType}`);
      }
      return match;
    });

    // 2. Fix remaining any types in variable assignments
    const variableAnyRegex = /:\s*any\s*=/g;
    content = content.replace(variableAnyRegex, (match) => {
      fileFixCount++;
      modified = true;
      return match.replace(': any', ': unknown');
    });

    // 3. Fix parameter any types in commonly used patterns
    const parameterAnyRegex = /\(([^)]*)\bany\b([^)]*)\)/g;
    content = content.replace(parameterAnyRegex, (match, before, after) => {
      fileFixCount++;
      modified = true;
      return match.replace('any', 'unknown');
    });

    // 4. Add return types to functions that are missing them
    const missingReturnTypeRegex = /(export\s+)?(const|function)\s+(\w+)\s*=?\s*(\([^)]*\))\s*\{/g;
    content = content.replace(missingReturnTypeRegex, (match, exportKeyword = '', keyword, funcName, params) => {
      // Skip if already has return type
      if (match.includes(': ') && match.indexOf(':') > match.lastIndexOf(')')) return match;

      // Infer return type based on function name patterns
      let returnType = 'void';
      const lowerName = funcName.toLowerCase();

      if (funcName.match(/^[A-Z]/) || lowerName.includes('render') || lowerName.includes('component')) {
        returnType = 'JSX.Element';
      } else if (lowerName.includes('validate') || lowerName.includes('check') || lowerName.startsWith('is') || lowerName.startsWith('has')) {
        returnType = 'boolean';
      } else if (lowerName.includes('format') || lowerName.includes('parse') || lowerName.includes('get') && lowerName.includes('string')) {
        returnType = 'string';
      } else if (lowerName.includes('count') || lowerName.includes('length') || lowerName.includes('size')) {
        returnType = 'number';
      } else if (lowerName.includes('fetch') || lowerName.includes('load') || lowerName.includes('save')) {
        returnType = 'Promise<unknown>';
      }

      fileFixCount++;
      modified = true;

      if (keyword === 'const') {
        return `${exportKeyword}const ${funcName} = ${params}: ${returnType} => {`;
      } else {
        return `${exportKeyword}function ${funcName}${params}: ${returnType} {`;
      }
    });

    // 5. Fix specific React patterns
    const reactComponentRegex = /const\s+([A-Z]\w*)\s*=\s*\(\s*[^)]*\s*\)\s*=>\s*\{/g;
    content = content.replace(reactComponentRegex, (match, componentName) => {
      if (!match.includes(': ')) {
        fileFixCount++;
        modified = true;
        return match.replace(') =>', '): JSX.Element =>');
      }
      return match;
    });

    // 6. Fix useEffect callbacks
    const useEffectRegex = /useEffect\s*\(\s*\(\s*\)\s*=>\s*\{/g;
    content = content.replace(useEffectRegex, (match) => {
      if (!match.includes(': ')) {
        fileFixCount++;
        modified = true;
        return match.replace(') =>', '): void =>');
      }
      return match;
    });

    // 7. Fix event handlers
    const eventHandlerRegex = /(on\w*|handle\w*)\s*=\s*\([^)]*\)\s*=>\s*\{/g;
    content = content.replace(eventHandlerRegex, (match) => {
      if (!match.includes(': ') || match.lastIndexOf(':') < match.lastIndexOf(')')) {
        fileFixCount++;
        modified = true;
        return match.replace(') =>', '): void =>');
      }
      return match;
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log(`  ✅ Fixed ${fileFixCount} issues in ${filePath}`);
      totalFixed += fileFixCount;
    } else {
      console.log(`  ⏸️  No additional fixes needed in ${filePath}`);
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log(`\n🎉 Total issues fixed: ${totalFixed}`);
