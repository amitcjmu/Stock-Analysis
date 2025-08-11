import fs from 'fs';
import path from 'path';
import { glob } from 'glob';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const config = {
  srcDir: path.join(__dirname, '..', 'src'),
  extensions: ['.tsx', '.ts'],
  dryRun: true, // Set to true to see what would be changed without actually changing
};

// Statistics
const stats = {
  filesProcessed: 0,
  componentsFixed: 0,
  voidFunctionsFixed: 0,
  skipped: 0,
  errors: 0,
};

// Patterns for React components
const componentPatterns = [
  // const Component = () => {
  /^(\s*)(export\s+)?(const|let)\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
  // const Component = (props) => {
  /^(\s*)(export\s+)?(const|let)\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\([^)]+\)\s*=>\s*\{/gm,
  // export default function Component() {
  /^(\s*)(export\s+default\s+)?function\s+([A-Z][a-zA-Z0-9]*)\s*\([^)]*\)\s*\{/gm,
];

// Patterns for void functions (event handlers, callbacks)
const voidFunctionPatterns = [
  // handleClick = () => {
  /^(\s*)(handle[A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
  // onSomething = () => {
  /^(\s*)(on[A-Z][a-zA-Z0-9]*)\s*=\s*\(\s*\)\s*=>\s*\{/gm,
  // handleClick = (event) => {
  /^(\s*)(handle[A-Z][a-zA-Z0-9]*)\s*=\s*\([^)]+\)\s*=>\s*\{/gm,
  // onSomething = (event) => {
  /^(\s*)(on[A-Z][a-zA-Z0-9]*)\s*=\s*\([^)]+\)\s*=>\s*\{/gm,
];

// Check if a function returns JSX
function returnsJSX(content, functionStartIndex) {
  // Find the function body
  let braceCount = 0;
  let inFunction = false;
  let functionBody = '';

  for (let i = functionStartIndex; i < content.length; i++) {
    if (content[i] === '{') {
      braceCount++;
      inFunction = true;
    } else if (content[i] === '}') {
      braceCount--;
      if (braceCount === 0 && inFunction) {
        functionBody = content.substring(functionStartIndex, i + 1);
        break;
      }
    }
  }

  // Check if the function returns JSX
  return /return\s*\(?\s*</.test(functionBody) ||
         /return\s+</.test(functionBody) ||
         /=>\s*\(?\s*</.test(functionBody);
}

// Check if a function returns nothing (void)
function returnsVoid(content, functionStartIndex) {
  // Find the function body
  let braceCount = 0;
  let inFunction = false;
  let functionBody = '';

  for (let i = functionStartIndex; i < content.length; i++) {
    if (content[i] === '{') {
      braceCount++;
      inFunction = true;
    } else if (content[i] === '}') {
      braceCount--;
      if (braceCount === 0 && inFunction) {
        functionBody = content.substring(functionStartIndex, i + 1);
        break;
      }
    }
  }

  // Check if the function has no return statement or only empty returns
  const hasReturn = /return\s+[^;}]/.test(functionBody);
  return !hasReturn;
}

// Process a single file
function processFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    let modified = content;
    let changesMade = false;

    // Skip if file already has many return types (likely already processed)
    if (content.includes('): JSX.Element') || content.includes('): void')) {
      stats.skipped++;
      return;
    }

    // Process React components
    componentPatterns.forEach(pattern => {
      const matches = [...content.matchAll(pattern)];
      matches.forEach(match => {
        const fullMatch = match[0];
        const indent = match[1] || '';
        const exportKeyword = match[2] || '';
        const constOrFunction = match[3] || 'const';
        const componentName = match[4] || match[3];

        // Check if this is likely a React component
        if (componentName && componentName[0] === componentName[0].toUpperCase()) {
          const matchIndex = match.index;

          // Check if it returns JSX
          if (returnsJSX(content, matchIndex)) {
            // Check if it already has a return type
            if (!content.substring(matchIndex, matchIndex + 200).includes('): ')) {
              // Add return type
              const newDeclaration = fullMatch.replace(
                /\)\s*=>\s*\{/,
                '): JSX.Element => {'
              ).replace(
                /\)\s*\{/,
                '): JSX.Element {'
              );

              if (newDeclaration !== fullMatch) {
                modified = modified.replace(fullMatch, newDeclaration);
                stats.componentsFixed++;
                changesMade = true;
                console.log('  ✓ Added JSX.Element return type to ', componentName);
              }
            }
          }
        }
      });
    });

    // Process void functions
    voidFunctionPatterns.forEach(pattern => {
      const matches = [...modified.matchAll(pattern)];
      matches.forEach(match => {
        const fullMatch = match[0];
        const indent = match[1] || '';
        const functionName = match[2];

        const matchIndex = match.index;

        // Check if it returns void
        if (returnsVoid(modified, matchIndex)) {
          // Check if it already has a return type
          if (!modified.substring(matchIndex, matchIndex + 200).includes('): ')) {
            // Add return type
            const newDeclaration = fullMatch.replace(
              /\)\s*=>\s*\{/,
              '): void => {'
            );

            if (newDeclaration !== fullMatch) {
              modified = modified.replace(fullMatch, newDeclaration);
              stats.voidFunctionsFixed++;
              changesMade = true;
              console.log('  ✓ Added void return type to ', functionName);
            }
          }
        }
      });
    });

    // Write the file if changes were made
    if (changesMade && !config.dryRun) {
      fs.writeFileSync(filePath, modified, 'utf8');
    }

    if (changesMade) {
      stats.filesProcessed++;
    }

  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    stats.errors++;
  }
}

// Main function
async function main() {
  console.log('🔧 Adding return types to TypeScript files...\n');

  if (config.dryRun) {
    console.log('🔍 DRY RUN MODE - No files will be modified\n');
  }

  // Find all TypeScript files
  const pattern = `${config.srcDir}/**/*.{ts,tsx}`;
  const files = await glob(pattern, {
    ignore: [
      '**/node_modules/**',
      '**/*.test.{ts,tsx}',
      '**/*.spec.{ts,tsx}',
      '**/*.d.ts',
    ],
  });

  console.log('Found ', files.length, ' TypeScript files to process\n');

  // Process each file
  files.forEach((file, index) => {
    if (index % 10 === 0) {
      console.log('Processing file ', index + 1, '/', files.length, '...');
    }
    console.log('\nProcessing: ', path.relative(config.srcDir, file));
    processFile(file);
  });

  // Print statistics
  console.log('\n📊 Summary:');
  console.log('Files processed: ', stats.filesProcessed);
  console.log('React components fixed: ', stats.componentsFixed);
  console.log('Void functions fixed: ', stats.voidFunctionsFixed);
  console.log('Files skipped: ', stats.skipped);
  console.log('Errors: ', stats.errors);
  console.log('Total fixes: ', stats.componentsFixed + stats.voidFunctionsFixed);

  if (config.dryRun) {
    console.log('\n🔍 This was a dry run. Set dryRun to false to apply changes.');
  }
}

// Run the script
main().catch(console.error);
