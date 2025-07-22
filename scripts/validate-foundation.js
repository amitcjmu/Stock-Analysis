#!/usr/bin/env node

/**
 * Foundation Validation Script
 * 
 * Validates that the foundation setup is complete and ready for agent deployment
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const VALIDATION_CHECKS = [
  'Shared type definitions exist',
  'TypeScript compilation passes',
  'ESLint configuration enhanced',
  'Progress tracking operational',
  'Package scripts available',
  'Auto-fix improvements verified'
];

function validateSharedTypes() {
  const sharedTypesPath = 'src/types/shared';
  const requiredFiles = [
    'index.ts',
    'metadata-types.ts', 
    'api-types.ts',
    'config-types.ts',
    'analysis-types.ts',
    'form-types.ts'
  ];
  
  console.log('🔍 Validating shared type definitions...');
  
  for (const file of requiredFiles) {
    const filePath = path.join(sharedTypesPath, file);
    if (!fs.existsSync(filePath)) {
      throw new Error(`Missing shared type file: ${filePath}`);
    }
  }
  
  console.log('✅ All shared type definitions present');
  return true;
}

function validateTypeScript() {
  console.log('🔍 Validating TypeScript compilation...');
  
  try {
    execSync('npm run types:validate', { stdio: 'pipe' });
    console.log('✅ TypeScript compilation passes');
    return true;
  } catch (error) {
    throw new Error('TypeScript compilation failed');
  }
}

function validateESLintConfig() {
  console.log('🔍 Validating ESLint configuration...');
  
  const configPath = 'eslint.config.js';
  if (!fs.existsSync(configPath)) {
    throw new Error('ESLint config file missing');
  }
  
  const configContent = fs.readFileSync(configPath, 'utf8');
  const requiredRules = [
    '@typescript-eslint/consistent-type-imports'
    // Note: consistent-type-exports requires parserOptions.project, deferred to Phase 4
  ];
  
  for (const rule of requiredRules) {
    if (!configContent.includes(rule)) {
      throw new Error(`Missing ESLint rule: ${rule}`);
    }
  }
  
  console.log('✅ ESLint configuration enhanced');
  return true;
}

function validateProgressTracking() {
  console.log('🔍 Validating progress tracking...');
  
  try {
    const result = execSync('npm run lint:progress', { encoding: 'utf8' });
    if (!result.includes('ESLint Error Analysis')) {
      throw new Error('Progress tracker not working correctly');
    }
    console.log('✅ Progress tracking operational');
    return true;
  } catch (error) {
    throw new Error('Progress tracking validation failed');
  }
}

function validatePackageScripts() {
  console.log('🔍 Validating package scripts...');
  
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredScripts = [
    'lint:progress',
    'lint:tolerant', 
    'lint:agent-ready',
    'types:validate'
  ];
  
  for (const script of requiredScripts) {
    if (!packageJson.scripts[script]) {
      throw new Error(`Missing package script: ${script}`);
    }
  }
  
  console.log('✅ All required package scripts available');
  return true;
}

function validateAutoFixImprovements() {
  console.log('🔍 Validating auto-fix improvements...');
  
  try {
    const result = execSync('npm run lint:progress', { encoding: 'utf8' });
    const match = result.match(/Total Errors: (\d+)/);
    if (!match) {
      throw new Error('Could not parse error count');
    }
    
    const errorCount = parseInt(match[1]);
    if (errorCount >= 2357) { // Original count before auto-fix
      throw new Error('Auto-fix did not reduce error count');
    }
    
    console.log(`✅ Auto-fix reduced errors (now ${errorCount})`);
    return true;
  } catch (error) {
    throw new Error('Auto-fix validation failed');
  }
}

function generateValidationReport() {
  const report = {
    timestamp: new Date().toISOString(),
    foundationReady: true,
    checksCompleted: VALIDATION_CHECKS.length,
    readyForAgentDeployment: true
  };
  
  fs.writeFileSync('foundation-validation-report.json', JSON.stringify(report, null, 2));
  console.log('📄 Validation report saved to foundation-validation-report.json');
}

async function runValidation() {
  console.log('🚀 Starting Foundation Validation...\n');
  
  const validators = [
    validateSharedTypes,
    validateTypeScript,
    validateESLintConfig,
    validateProgressTracking,
    validatePackageScripts,
    validateAutoFixImprovements
  ];
  
  try {
    for (let i = 0; i < validators.length; i++) {
      console.log(`\n[${i + 1}/${validators.length}] ${VALIDATION_CHECKS[i]}`);
      await validators[i]();
    }
    
    console.log('\n🎉 Foundation Validation Complete!');
    console.log('✅ All systems ready for AI agent deployment');
    
    generateValidationReport();
    
    console.log('\n📊 Current Baseline:');
    execSync('npm run lint:progress', { stdio: 'inherit' });
    
  } catch (error) {
    console.error(`\n❌ Foundation validation failed: ${error.message}`);
    process.exit(1);
  }
}

runValidation();