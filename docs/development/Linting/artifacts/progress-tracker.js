#!/usr/bin/env node

/**
 * Automated Progress Tracker for ESLint Compliance AI Swarm
 * 
 * This script automatically tracks ESLint error reduction progress across
 * agent domains and updates the progress tracker markdown file.
 * 
 * Usage: node progress-tracker.js [--update-markdown]
 * 
 * @version 1.0
 * @date 2025-01-21
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  projectRoot: path.resolve(__dirname, '../../../..'),
  trackerPath: path.resolve(__dirname, '../tracking/PROGRESS-TRACKER.md'),
  eslintCommand: 'npm run lint -- --format json',
  
  // Agent file mappings
  agentDomains: {
    'Agent A': {
      name: 'Forward Declarations',
      patterns: [
        'src/types/api/planning/timeline/core-types.ts',
        'src/types/api/planning/strategy/core-types.ts', 
        'src/types/api/finops/flow-management.ts'
      ],
      targetErrors: 111,
      priority: 'Critical'
    },
    'Agent B': {
      name: 'Metadata Standardization',
      patterns: [
        'src/types/api/**/*',
        'src/components/admin/**/*'
      ],
      targetErrors: 80,
      priority: 'High'
    },
    'Agent C': {
      name: 'Configuration Values',
      patterns: [
        'src/types/api/planning/**/*',
        'src/types/api/finops/**/*'
      ],
      targetErrors: 60,
      priority: 'High'
    },
    'Agent D': {
      name: 'Form Hook Typing',
      patterns: [
        'src/types/hooks/shared/form-hooks.ts',
        'src/hooks/useUnifiedDiscoveryFlow.ts',
        'src/hooks/discovery/**/*'
      ],
      targetErrors: 50,
      priority: 'Medium'
    },
    'Agent E': {
      name: 'API Response Typing',
      patterns: [
        'src/utils/api/apiTypes.ts',
        'src/utils/api/**/*'
      ],
      targetErrors: 40,
      priority: 'Medium'
    },
    'Agent F': {
      name: 'Component Props',
      patterns: [
        'src/components/discovery/**/*',
        'src/types/components/**/*'
      ],
      targetErrors: 35,
      priority: 'Medium'
    },
    'Agent G': {
      name: 'Hook Patterns',
      patterns: [
        'src/types/hooks/shared/ui-state.ts',
        'src/types/hooks/shared/base-patterns.ts'
      ],
      targetErrors: 30,
      priority: 'Low'
    },
    'Agent H': {
      name: 'Edge Cases',
      patterns: ['**/*.ts', '**/*.tsx'],
      targetErrors: 25,
      priority: 'Low'
    }
  }
};

/**
 * Execute ESLint and return parsed results
 */
function runESLint() {
  try {
    console.log('🔍 Running ESLint analysis...');
    process.chdir(CONFIG.projectRoot);
    
    const eslintOutput = execSync(CONFIG.eslintCommand, { 
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    return JSON.parse(eslintOutput);
  } catch (error) {
    // ESLint exits with non-zero when errors found, but still produces JSON
    if (error.stdout) {
      try {
        return JSON.parse(error.stdout);
      } catch (parseError) {
        console.error('❌ Failed to parse ESLint output:', parseError.message);
        return null;
      }
    }
    console.error('❌ ESLint execution failed:', error.message);
    return null;
  }
}

/**
 * Analyze ESLint results and categorize by agent domains
 */
function analyzeResults(eslintResults) {
  if (!eslintResults) return null;

  const analysis = {
    totalFiles: eslintResults.length,
    totalErrors: 0,
    anyTypeErrors: 0,
    otherErrors: 0,
    agentProgress: {},
    errorsByFile: {},
    errorPatterns: {}
  };

  // Initialize agent progress
  Object.keys(CONFIG.agentDomains).forEach(agentId => {
    analysis.agentProgress[agentId] = {
      ...CONFIG.agentDomains[agentId],
      currentErrors: 0,
      filesAffected: [],
      errorReduction: 0,
      status: 'Pending'
    };
  });

  // Analyze each file
  eslintResults.forEach(fileResult => {
    const { filePath, messages } = fileResult;
    const relativePath = path.relative(CONFIG.projectRoot, filePath);
    
    analysis.errorsByFile[relativePath] = {
      totalErrors: messages.length,
      anyTypeErrors: 0,
      otherErrors: 0,
      agents: []
    };

    messages.forEach(message => {
      analysis.totalErrors++;
      
      if (message.ruleId === '@typescript-eslint/no-explicit-any') {
        analysis.anyTypeErrors++;
        analysis.errorsByFile[relativePath].anyTypeErrors++;
        
        // Track error patterns
        const pattern = `${message.ruleId}:${message.line}`;
        analysis.errorPatterns[pattern] = (analysis.errorPatterns[pattern] || 0) + 1;
        
        // Assign to appropriate agent
        Object.entries(CONFIG.agentDomains).forEach(([agentId, domain]) => {
          const matchesPattern = domain.patterns.some(pattern => {
            if (pattern.includes('**')) {
              // Simple glob matching
              const regex = new RegExp(pattern.replace('**', '.*').replace('*', '[^/]*'));
              return regex.test(relativePath);
            } else {
              return relativePath === pattern;
            }
          });

          if (matchesPattern) {
            analysis.agentProgress[agentId].currentErrors++;
            if (!analysis.agentProgress[agentId].filesAffected.includes(relativePath)) {
              analysis.agentProgress[agentId].filesAffected.push(relativePath);
            }
            if (!analysis.errorsByFile[relativePath].agents.includes(agentId)) {
              analysis.errorsByFile[relativePath].agents.push(agentId);
            }
          }
        });
      } else {
        analysis.otherErrors++;
        analysis.errorsByFile[relativePath].otherErrors++;
      }
    });
  });

  // Calculate progress for each agent
  Object.entries(analysis.agentProgress).forEach(([agentId, progress]) => {
    progress.errorReduction = Math.max(0, progress.targetErrors - progress.currentErrors);
    progress.progressPercent = Math.round((progress.errorReduction / progress.targetErrors) * 100);
    
    if (progress.currentErrors === 0) {
      progress.status = 'Complete';
    } else if (progress.errorReduction > 0) {
      progress.status = 'In Progress';
    } else {
      progress.status = 'Pending';
    }
  });

  return analysis;
}

/**
 * Generate progress summary report
 */
function generateReport(analysis) {
  if (!analysis) return null;

  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalErrors: analysis.totalErrors,
      anyTypeErrors: analysis.anyTypeErrors,
      otherErrors: analysis.otherErrors,
      overallProgress: Math.round(((2173 - analysis.anyTypeErrors) / 2173) * 100)
    },
    phases: {
      'Phase 1': { status: 'Pending', progress: 0 },
      'Phase 2': { status: 'Pending', progress: 0 },
      'Phase 3': { status: 'Pending', progress: 0 }
    },
    agents: analysis.agentProgress,
    topIssueFiles: Object.entries(analysis.errorsByFile)
      .sort(([,a], [,b]) => b.anyTypeErrors - a.anyTypeErrors)
      .slice(0, 10)
      .map(([file, data]) => ({ file, ...data }))
  };

  return report;
}

/**
 * Update the progress tracker markdown file
 */
function updateProgressTracker(analysis) {
  if (!analysis) return false;

  try {
    let trackerContent = fs.readFileSync(CONFIG.trackerPath, 'utf8');
    const timestamp = new Date().toISOString().split('T')[0];
    
    // Update overall progress summary
    const overallProgress = Math.round(((2173 - analysis.anyTypeErrors) / 2173) * 100);
    trackerContent = trackerContent.replace(
      /- \*\*Total Errors Addressed\*\*: \d+\/2,173 \(\d+%\)/,
      `- **Total Errors Addressed**: ${2173 - analysis.anyTypeErrors}/2,173 (${overallProgress}%)`
    );
    
    trackerContent = trackerContent.replace(
      /- \*\*Estimated Remaining\*\*: \d+/,
      `- **Estimated Remaining**: ${analysis.anyTypeErrors}`
    );

    // Update agent progress table
    Object.entries(analysis.agentProgress).forEach(([agentId, progress]) => {
      const agentLetter = agentId.split(' ')[1]; // Extract letter from "Agent A"
      const statusIcon = {
        'Complete': '✅',
        'In Progress': '⏳',
        'Pending': '⭕'
      }[progress.status] || '⭕';

      // Update agent row in Wave tables
      const progressText = `${progress.errorReduction}/${progress.targetErrors}`;
      const agentRowPattern = new RegExp(
        `(\\| \\*\\*${agentId}\\*\\* \\| .+ \\| \\d+ \\| )([⭕⏳✅] .+ \\| )\\d+/\\d+`,
        'g'
      );
      
      trackerContent = trackerContent.replace(
        agentRowPattern,
        `$1${statusIcon} ${progress.status} | ${progressText}`
      );
    });

    // Add timestamp to last updated
    trackerContent = trackerContent.replace(
      /\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}/,
      `**Last Updated**: ${timestamp}`
    );

    // Write updated content
    fs.writeFileSync(CONFIG.trackerPath, trackerContent);
    console.log('✅ Progress tracker updated successfully');
    return true;
    
  } catch (error) {
    console.error('❌ Failed to update progress tracker:', error.message);
    return false;
  }
}

/**
 * Display console report
 */
function displayReport(analysis) {
  if (!analysis) return;

  console.log('\n📊 ESLint Progress Report');
  console.log('========================');
  console.log(`Timestamp: ${new Date().toLocaleString()}`);
  console.log(`Total Errors: ${analysis.totalErrors}`);
  console.log(`Any-Type Errors: ${analysis.anyTypeErrors}`);
  console.log(`Other Errors: ${analysis.otherErrors}`);
  console.log(`Overall Progress: ${Math.round(((2173 - analysis.anyTypeErrors) / 2173) * 100)}%`);
  
  console.log('\n🤖 Agent Progress:');
  Object.entries(analysis.agentProgress).forEach(([agentId, progress]) => {
    const status = {
      'Complete': '✅',
      'In Progress': '⏳', 
      'Pending': '⭕'
    }[progress.status] || '⭕';
    
    console.log(`${status} ${agentId}: ${progress.errorReduction}/${progress.targetErrors} (${progress.progressPercent}%)`);
  });

  console.log('\n📁 Top Issue Files:');
  Object.entries(analysis.errorsByFile)
    .sort(([,a], [,b]) => b.anyTypeErrors - a.anyTypeErrors)
    .slice(0, 5)
    .forEach(([file, data]) => {
      console.log(`  ${data.anyTypeErrors} errors: ${file}`);
    });

  console.log('\n');
}

/**
 * Save detailed analysis to JSON file for other tools
 */
function saveAnalysisData(analysis) {
  const analysisPath = path.resolve(__dirname, '../tracking/latest-analysis.json');
  try {
    fs.writeFileSync(analysisPath, JSON.stringify(analysis, null, 2));
    console.log('📄 Detailed analysis saved to latest-analysis.json');
  } catch (error) {
    console.error('❌ Failed to save analysis data:', error.message);
  }
}

/**
 * Main execution function
 */
function main() {
  const updateMarkdown = process.argv.includes('--update-markdown');
  
  console.log('🚀 Starting ESLint Progress Analysis...');
  
  // Run ESLint analysis
  const eslintResults = runESLint();
  if (!eslintResults) {
    process.exit(1);
  }
  
  // Analyze results
  const analysis = analyzeResults(eslintResults);
  if (!analysis) {
    console.error('❌ Failed to analyze ESLint results');
    process.exit(1);
  }
  
  // Display report
  displayReport(analysis);
  
  // Save analysis data
  saveAnalysisData(analysis);
  
  // Update markdown if requested
  if (updateMarkdown) {
    updateProgressTracker(analysis);
  } else {
    console.log('ℹ️  Use --update-markdown flag to update the progress tracker file');
  }
  
  console.log('✅ Analysis complete!');
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  runESLint,
  analyzeResults,
  generateReport,
  updateProgressTracker,
  CONFIG
};