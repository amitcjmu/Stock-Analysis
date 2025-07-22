#!/usr/bin/env node

/**
 * Simple Progress Tracker for ESLint Compliance
 * 
 * Quick script to count ESLint errors by type and provide baseline metrics.
 */

import { execSync } from 'child_process';

function runSimpleAnalysis() {
  try {
    console.log('🚀 Running Simple ESLint Analysis...');
    
    // Run ESLint and count errors
    const result = execSync('npx eslint . --ext ts,tsx', { 
      encoding: 'utf8',
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    console.log('✅ No ESLint errors found!');
    return { totalErrors: 0, anyTypeErrors: 0 };
    
  } catch (error) {
    // ESLint exits with non-zero when errors found
    if (error.stdout) {
      const output = error.stdout;
      const lines = output.split('\n');
      
      let totalErrors = 0;
      let anyTypeErrors = 0;
      
      for (const line of lines) {
        if (line.includes('error')) {
          totalErrors++;
          if (line.includes('@typescript-eslint/no-explicit-any')) {
            anyTypeErrors++;
          }
        }
      }
      
      console.log('\n📊 ESLint Error Analysis:');
      console.log(`Total Errors: ${totalErrors}`);
      console.log(`Any-Type Errors: ${anyTypeErrors}`);
      console.log(`Other Errors: ${totalErrors - anyTypeErrors}`);
      console.log(`Any-Type Percentage: ${Math.round((anyTypeErrors / totalErrors) * 100)}%`);
      
      return { totalErrors, anyTypeErrors };
    } else {
      console.error('❌ ESLint execution failed:', error.message);
      return null;
    }
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runSimpleAnalysis();
}

export { runSimpleAnalysis };