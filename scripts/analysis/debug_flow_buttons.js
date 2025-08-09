// Debug script to test flow button functionality
// Run this in the browser console on the /discovery/cmdb-import page

console.log('=== DEBUGGING FLOW BUTTONS ===');

// Check if the buttons exist
const continueButtons = document.querySelectorAll('button:contains("Continue Flow")');
const viewDetailsButtons = document.querySelectorAll('button:contains("View Details")');

console.log('Continue Flow buttons found:', continueButtons.length);
console.log('View Details buttons found:', viewDetailsButtons.length);

// Check for any React component errors
if (window.React) {
    console.log('React is available');
} else {
    console.log('React is not available');
}

// Check localStorage for flow IDs
console.log('localStorage currentFlowId:', localStorage.getItem('currentFlowId'));

// Check auth context
const authToken = localStorage.getItem('auth_token');
console.log('Auth token exists:', !!authToken);

// Check for any JavaScript errors
window.addEventListener('error', (e) => {
    console.error('JavaScript error:', e.error);
});

// Test if we can find the flow manager component
const flowManagerElements = document.querySelectorAll('[data-testid="incomplete-flow-manager"], .flow-manager, [class*="IncompleteFlowManager"]');
console.log('Flow manager elements found:', flowManagerElements.length);

// Test if buttons are disabled
const allButtons = document.querySelectorAll('button');
const disabledButtons = Array.from(allButtons).filter(btn => btn.disabled);
console.log('Total buttons:', allButtons.length);
console.log('Disabled buttons:', disabledButtons.length);

// Look for any error messages
const errorElements = document.querySelectorAll('[class*="error"], [class*="alert-destructive"], .text-red-500');
console.log('Error elements found:', errorElements.length);

// Check if the page is still loading
const loadingElements = document.querySelectorAll('[class*="loading"], [class*="spinner"], .animate-spin');
console.log('Loading elements found:', loadingElements.length);

console.log('=== END DEBUG ===');
