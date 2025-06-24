// Clear React Query cache and localStorage to fix stale flow ID issue
console.log('🧹 Clearing browser cache and storage...');

// Clear localStorage
Object.keys(localStorage).forEach(key => {
  if (key.includes('flow') || key.includes('discovery') || key.includes('react-query')) {
    console.log(`Removing localStorage key: ${key}`);
    localStorage.removeItem(key);
  }
});

// Clear sessionStorage
Object.keys(sessionStorage).forEach(key => {
  if (key.includes('flow') || key.includes('discovery') || key.includes('react-query')) {
    console.log(`Removing sessionStorage key: ${key}`);
    sessionStorage.removeItem(key);
  }
});

// Clear React Query cache if available
if (window.queryClient) {
  console.log('Clearing React Query cache...');
  window.queryClient.clear();
}

// Clear any polling intervals
if (window.pollingManager) {
  console.log('Emergency stopping all polling...');
  window.pollingManager.emergencyStop();
}

console.log('✅ Cache cleared! Please refresh the page.');
