import fs from 'fs';
import path from 'path';
import { glob } from 'glob';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const config = {
  srcDir: path.join(__dirname, '..', 'src'),
  dryRun: false, // Set to true for dry run
  targetFixes: 400, // Stop after fixing this many to stay under warning limit
};

// Statistics
const stats = {
  filesProcessed: 0,
  totalFixes: 0,
  componentsFixed: 0,
  voidFunctionsFixed: 0,
  hookReturnsFixed: 0,
  utilFunctionsFixed: 0,
};

// Quick patterns that are most common
const patterns = [
  // React Components: const Component = () => {
  {
    pattern: /^(\s*)(export\s+)?(const)\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
    replacement: '$1$2$3 $4 = (): JSX.Element => {',
    type: 'component',
    check: (content, match) => {
      const name = match[4];
      return name && name[0] === name[0].toUpperCase() &&
             !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // React Components with props: const Component = (props) => {
  {
    pattern: /^(\s*)(export\s+)?(const)\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(([^)]+)\)\s*=>\s*\{/gm,
    replacement: '$1$2$3 $4 = ($5): JSX.Element => {',
    type: 'component',
    check: (content, match) => {
      const name = match[4];
      return name && name[0] === name[0].toUpperCase() &&
             !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // Pages/Views: export default function Component() {
  {
    pattern: /^(\s*)(export\s+default\s+)?function\s+([A-Z][a-zA-Z0-9]*)\s*\(\s*\)\s*\{/gm,
    replacement: '$1$2function $3(): JSX.Element {',
    type: 'component',
    check: (content, match) => {
      return !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // Event handlers: handleSomething = () => {
  {
    pattern: /^(\s*)(handle[A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
    replacement: '$1$2 = (): void => {',
    type: 'void',
    check: (content, match) => {
      return !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // Event handlers with params: handleSomething = (event) => {
  {
    pattern: /^(\s*)(handle[A-Z][a-zA-Z0-9]*)\s*=\s*\(([^)]+)\)\s*=>\s*\{/gm,
    replacement: '$1$2 = ($3): void => {',
    type: 'void',
    check: (content, match) => {
      return !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // onClick handlers: onClick = () => {
  {
    pattern: /^(\s*)(on[A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
    replacement: '$1$2 = (): void => {',
    type: 'void',
    check: (content, match) => {
      return !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // Hooks: export const useXXX = () => {
  {
    pattern: /^(\s*)(export\s+)?(const)\s+(use[A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
    replacement: null, // Will be handled specially
    type: 'hook',
    check: (content, match) => {
      return !content.substring(match.index, match.index + 200).includes('): ');
    }
  },

  // Utility functions that are clearly void
  {
    pattern: /^(\s*)(export\s+)?(const)\s+(log[A-Z][a-zA-Z0-9]*|show[A-Z][a-zA-Z0-9]*|set[A-Z][a-zA-Z0-9]*)\s*=\s*\([^)]*\)\s*=>\s*\{/gm,
    replacement: null, // Will be determined by content
    type: 'util',
    check: (content, match) => {
      return !content.substring(match.index, match.index + 200).includes('): ');
    }
  },
];

// Process file quickly
function processFile(filePath) {
  if (stats.totalFixes >= config.targetFixes) {
    return; // Stop if we've fixed enough
  }

  try {
    const content = fs.readFileSync(filePath, 'utf8');
    let modified = content;
    let fileFixCount = 0;

    // Quick skip for already processed files
    if (content.includes('): JSX.Element') || content.includes('): void')) {
      return;
    }

    // Apply patterns
    for (const patternDef of patterns) {
      const matches = [...content.matchAll(patternDef.pattern)];

      for (const match of matches) {
        if (stats.totalFixes >= config.targetFixes) {
          break;
        }

        if (patternDef.check(content, match)) {
          let replacement = patternDef.replacement;

          // Special handling for hooks and utils
          if (patternDef.type === 'hook') {
            // For hooks, we'll just add a generic return type
            replacement = match[0].replace('=> {', '=> /* TODO: Add proper return type */ {');
          } else if (patternDef.type === 'util') {
            // Check if function returns void
            const functionBody = content.substring(match.index, match.index + 1000);
            const hasReturn = /return\s+[^;}]/.test(functionBody);
            if (!hasReturn) {
              replacement = match[0].replace('=> {', '): void => {');
            }
          }

          if (replacement) {
            modified = modified.replace(match[0], replacement);
            fileFixCount++;
            stats.totalFixes++;

            switch(patternDef.type) {
              case 'component': stats.componentsFixed++; break;
              case 'void': stats.voidFunctionsFixed++; break;
              case 'hook': stats.hookReturnsFixed++; break;
              case 'util': stats.utilFunctionsFixed++; break;
            }
          }
        }
      }
    }

    // Write file if changed
    if (fileFixCount > 0 && !config.dryRun) {
      fs.writeFileSync(filePath, modified, 'utf8');
      stats.filesProcessed++;
      console.log(`✓ Fixed ${fileFixCount} in ${path.basename(filePath)}`);
    } else if (fileFixCount > 0) {
      console.log(`Would fix ${fileFixCount} in ${path.basename(filePath)}`);
    }

  } catch (error) {
    console.error(`Error in ${filePath}: ${error.message}`);
  }
}

// Main
async function main() {
  console.log('🚀 Fast Return Type Fixer\n');

  if (config.dryRun) {
    console.log('🔍 DRY RUN MODE\n');
  }

  // Get files sorted by most likely to have issues
  const patterns = [
    'src/components/**/*.tsx',
    'src/pages/**/*.tsx',
    'src/hooks/**/*.ts',
    'src/components/**/*.ts',
    'src/utils/**/*.ts',
    'src/services/**/*.ts',
  ];

  let allFiles = [];
  for (const pattern of patterns) {
    const files = await glob(path.join(__dirname, '..', pattern), {
      ignore: ['**/*.test.*', '**/*.spec.*', '**/*.d.ts'],
    });
    allFiles = allFiles.concat(files);
  }

  // Remove duplicates
  allFiles = [...new Set(allFiles)];

  console.log(`Processing ${allFiles.length} files...\n`);

  // Process files
  for (const file of allFiles) {
    if (stats.totalFixes >= config.targetFixes) {
      console.log(`\n⚡ Reached target of ${config.targetFixes} fixes, stopping.`);
      break;
    }
    processFile(file);
  }

  // Summary
  console.log('\n📊 Summary:');
  console.log(`Files modified: ${stats.filesProcessed}`);
  console.log(`React components: ${stats.componentsFixed}`);
  console.log(`Void functions: ${stats.voidFunctionsFixed}`);
  console.log(`Hooks marked: ${stats.hookReturnsFixed}`);
  console.log(`Util functions: ${stats.utilFunctionsFixed}`);
  console.log(`Total fixes: ${stats.totalFixes}`);

  if (config.dryRun) {
    console.log('\n💡 Run with dryRun: false to apply changes');
  }
}

main().catch(console.error);
