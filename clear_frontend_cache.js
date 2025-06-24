// Enhanced Frontend Cache Clearing Script
console.log('🧹 Starting comprehensive frontend cache clearing...');

// 1. Clear all storage
try {
  localStorage.clear();
  sessionStorage.clear();
  console.log('✅ Storage cleared');
} catch (e) {
  console.error('❌ Storage clear failed:', e);
}

// 2. Clear React Query cache if available
if (window.__REACT_QUERY_CLIENT__) {
  try {
    window.__REACT_QUERY_CLIENT__.clear();
    console.log('✅ React Query cache cleared');
  } catch (e) {
    console.error('❌ React Query clear failed:', e);
  }
}

// 3. Clear any module cache (for development)
if (import.meta.hot) {
  try {
    import.meta.hot.invalidate();
    console.log('✅ HMR cache invalidated');
  } catch (e) {
    console.error('❌ HMR invalidation failed:', e);
  }
}

// 4. Clear browser caches
try {
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => {
        caches.delete(name);
        console.log(`✅ Cache deleted: ${name}`);
      });
    });
  }
} catch (e) {
  console.error('❌ Browser cache clear failed:', e);
}

// 5. Clear any intervals/timeouts
try {
  // Clear high interval IDs (common range)
  for (let i = 1; i < 1000; i++) {
    clearInterval(i);
    clearTimeout(i);
  }
  console.log('✅ Intervals/timeouts cleared');
} catch (e) {
  console.error('❌ Interval/timeout clear failed:', e);
}

// 6. Force page reload
console.log('🔄 Forcing page reload in 2 seconds...');
setTimeout(() => {
  window.location.reload(true);
}, 2000);
