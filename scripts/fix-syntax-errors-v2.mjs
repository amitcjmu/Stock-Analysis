#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';

// Get all TypeScript/React files
const files = glob.sync('src/**/*.{ts,tsx}');
let totalFixed = 0;

console.log(`Processing ${files.length} files for syntax error fixes...`);

files.forEach((filePath, index) => {
  console.log(`[${index + 1}/${files.length}] Processing: ${filePath}`);

  try {
    let content = readFileSync(filePath, 'utf8');
    let modified = false;
    let fileFixCount = 0;

    // Fix malformed if statements: if (condition): void {
    const ifStatementRegex = /if\s*\([^)]+\)\s*:\s*void\s*\{/g;
    content = content.replace(ifStatementRegex, (match) => {
      const conditionMatch = match.match(/if\s*\(([^)]+)\)\s*:\s*void\s*\{/);
      if (conditionMatch) {
        const condition = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `if (${condition}) {`;
      }
      return match;
    });

    // Fix malformed else if statements: else if (condition): void {
    const elseIfStatementRegex = /else\s+if\s*\([^)]+\)\s*:\s*void\s*\{/g;
    content = content.replace(elseIfStatementRegex, (match) => {
      const conditionMatch = match.match(/else\s+if\s*\(([^)]+)\)\s*:\s*void\s*\{/);
      if (conditionMatch) {
        const condition = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `else if (${condition}) {`;
      }
      return match;
    });

    // Fix malformed while loops: while (condition): void {
    const whileLoopRegex = /while\s*\([^)]+\)\s*:\s*void\s*\{/g;
    content = content.replace(whileLoopRegex, (match) => {
      const conditionMatch = match.match(/while\s*\(([^)]+)\)\s*:\s*void\s*\{/);
      if (conditionMatch) {
        const condition = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `while (${condition}) {`;
      }
      return match;
    });

    // Fix malformed for loops: for (expr): void {
    const forLoopRegex = /for\s*\([^)]+\)\s*:\s*void\s*\{/g;
    content = content.replace(forLoopRegex, (match) => {
      const conditionMatch = match.match(/for\s*\(([^)]+)\)\s*:\s*void\s*\{/);
      if (conditionMatch) {
        const expression = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `for (${expression}) {`;
      }
      return match;
    });

    // Fix malformed switch statements: switch (expr): void {
    const switchStatementRegex = /switch\s*\([^)]+\)\s*:\s*void\s*\{/g;
    content = content.replace(switchStatementRegex, (match) => {
      const conditionMatch = match.match(/switch\s*\(([^)]+)\)\s*:\s*void\s*\{/);
      if (conditionMatch) {
        const expression = conditionMatch[1];
        fileFixCount++;
        modified = true;
        return `switch (${expression}) {`;
      }
      return match;
    });

    // Fix malformed catch blocks: } catch (err): void {
    const catchBlockRegex = /\}\s*catch\s*\([^)]*\)\s*:\s*void\s*\{/g;
    content = content.replace(catchBlockRegex, (match) => {
      const catchMatch = match.match(/\}\s*catch\s*\(([^)]*)\)\s*:\s*void\s*\{/);
      if (catchMatch) {
        const errorParam = catchMatch[1];
        fileFixCount++;
        modified = true;
        return `} catch (${errorParam}) {`;
      }
      return match;
    });

    // Fix malformed try blocks: try: void {
    const tryBlockRegex = /try\s*:\s*void\s*\{/g;
    content = content.replace(tryBlockRegex, () => {
      fileFixCount++;
      modified = true;
      return 'try {';
    });

    // Fix incorrect return type syntax in conditions that shouldn't have return types
    // Pattern: condition): void { should be condition) {
    const conditionReturnTypeRegex = /\)\s*:\s*(void|unknown|any|boolean|string|number)\s*\{/g;
    content = content.replace(conditionReturnTypeRegex, (match, returnType) => {
      // Only fix if this looks like a condition rather than a function declaration
      const beforeMatch = content.slice(Math.max(0, content.indexOf(match) - 50), content.indexOf(match));
      if (beforeMatch.includes('if (') || beforeMatch.includes('while (') || beforeMatch.includes('for (') ||
          beforeMatch.includes('switch (') || beforeMatch.includes('} catch (')) {
        fileFixCount++;
        modified = true;
        return ') {';
      }
      return match;
    });

    if (modified) {
      writeFileSync(filePath, content);
      console.log(`  ✅ Fixed ${fileFixCount} syntax errors in ${filePath}`);
      totalFixed += fileFixCount;
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
  }
});

console.log(`\n🎉 Total syntax errors fixed: ${totalFixed}`);
