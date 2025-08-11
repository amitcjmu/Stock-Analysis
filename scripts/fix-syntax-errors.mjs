#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';

// Get all TypeScript/React files
const files = glob.sync('src/**/*.{ts,tsx}');
let totalFixed = 0;

console.log('Processing ', files.length, ' files for syntax error fixes...');

files.forEach((filePath, index) => {
  console.log('[', index + 1, '/', files.length, '] Processing: ', filePath);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // Fix the malformed if statements created by the bulk script
    // Pattern: if(condition): any {
    const ifStatementRegex = /if\s*\([^)]+\)\s*:\s*any\s*\{/g;
    content = content.replace(ifStatementRegex, (match) => {
      // Extract the condition part
      const conditionMatch = match.match(/if\s*\(([^)]+)\)\s*:\s*any\s*\{/);
      if (conditionMatch) {
        const condition = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `if (${condition}) {`;
      }
      return match;
    });

    // Fix malformed switch statement cases
    // Pattern: switch(expr): any {
    const switchStatementRegex = /switch\s*\([^)]+\)\s*:\s*any\s*\{/g;
    content = content.replace(switchStatementRegex, (match) => {
      const conditionMatch = match.match(/switch\s*\(([^)]+)\)\s*:\s*any\s*\{/);
      if (conditionMatch) {
        const expression = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `switch (${expression}) {`;
      }
      return match;
    });

    // Fix malformed case statements
    // Pattern: case 'value': any {
    const caseStatementRegex = /case\s+([^:]+)\s*:\s*any\s*\{/g;
    content = content.replace(caseStatementRegex, (match) => {
      const caseMatch = match.match(/case\s+([^:]+)\s*:\s*any\s*\{/);
      if (caseMatch) {
        const caseValue = caseMatch[1].trim();
        fileFixCount++;
        modified = true;
        return `case ${caseValue}: {`;
      }
      return match;
    });

    // Fix malformed for loops
    // Pattern: for(expr): any {
    const forLoopRegex = /for\s*\([^)]+\)\s*:\s*any\s*\{/g;
    content = content.replace(forLoopRegex, (match) => {
      const conditionMatch = match.match(/for\s*\(([^)]+)\)\s*:\s*any\s*\{/);
      if (conditionMatch) {
        const expression = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `for (${expression}) {`;
      }
      return match;
    });

    // Fix malformed while loops
    // Pattern: while(expr): any {
    const whileLoopRegex = /while\s*\([^)]+\)\s*:\s*any\s*\{/g;
    content = content.replace(whileLoopRegex, (match) => {
      const conditionMatch = match.match(/while\s*\(([^)]+)\)\s*:\s*any\s*\{/);
      if (conditionMatch) {
        const condition = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `while (${condition}) {`;
      }
      return match;
    });

    // Fix malformed catch blocks
    // Pattern: } catch(err): any {
    const catchBlockRegex = /\}\s*catch\s*\([^)]*\)\s*:\s*any\s*\{/g;
    content = content.replace(catchBlockRegex, (match) => {
      const catchMatch = match.match(/\}\s*catch\s*\(([^)]*)\)\s*:\s*any\s*\{/);
      if (catchMatch) {
        const errorParam = catchMatch[1];
        fileFixCount++;
        modified = true;
        return `} catch (${errorParam}) {`;
      }
      return match;
    });

    // Fix malformed try-catch without parameters
    // Pattern: try: any {
    const tryBlockRegex = /try\s*:\s*any\s*\{/g;
    content = content.replace(tryBlockRegex, () => {
      fileFixCount++;
      modified = true;
      return 'try {';
    });

    // Fix function expressions that were incorrectly processed
    // Pattern: function(...): any => { becomes function(...) => {
    const arrowFunctionRegex = /(\w+\s*\([^)]*\))\s*:\s*any\s*=>/g;
    content = content.replace(arrowFunctionRegex, (match, params) => {
      fileFixCount++;
      modified = true;
      return `${params} => `;
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log('  ✅ Fixed ', fileFixCount, ' syntax errors in ', filePath);
      totalFixed += fileFixCount;
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log('\n🎉 Total syntax errors fixed: ', totalFixed);
