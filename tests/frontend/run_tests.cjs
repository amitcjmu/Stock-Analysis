#!/usr/bin/env node

const { TestUtils, FrontendTestRunner } = require('./test_ui_components.js');

async function runTests() {
    const runner = new FrontendTestRunner();
    
    // Add all tests
    runner.addTest('Responsive Breakpoints', TestUtils.testResponsiveBreakpoints);
    runner.addTest('Grid Responsiveness', TestUtils.testGridResponsiveness);
    runner.addTest('Button Responsiveness', TestUtils.testButtonResponsiveness);
    runner.addTest('Table Responsiveness', TestUtils.testTableResponsiveness);
    runner.addTest('Accessibility Features', TestUtils.testAccessibility);
    runner.addTest('Loading States', TestUtils.testLoadingStates);
    runner.addTest('Error Handling', TestUtils.testErrorHandling);
    runner.addTest('Form Validation', TestUtils.testFormValidation);
    runner.addTest('Navigation', TestUtils.testNavigation);
    runner.addTest('Data Visualization', TestUtils.testDataVisualization);
    
    const success = await runner.runAllTests();
    process.exit(success ? 0 : 1);
}

runTests().catch(console.error); 