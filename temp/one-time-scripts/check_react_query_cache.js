console.log('🔍 Checking React Query cache for flow IDs...');
if (window.queryClient) {
  const cache = window.queryClient.getQueryCache();
  const queries = cache.getAll();
  console.log('Total queries in cache:', queries.length);

  queries.forEach(query => {
    if (query.queryKey.includes('discoveryFlowV2') || query.queryKey.includes('flow')) {
      console.log('Flow-related query:', query.queryKey, query.state);
    }
  });

  // Check for the specific problematic flow ID
  const problemFlowId = '11055bdf-5e39-4e0d-913e-0c7080f82e2c';
  queries.forEach(query => {
    if (JSON.stringify(query.queryKey).includes(problemFlowId)) {
      console.log('🚨 FOUND PROBLEMATIC FLOW ID IN CACHE:', query.queryKey);
      console.log('Query state:', query.state);
      console.log('Removing from cache...');
      window.queryClient.removeQueries(query.queryKey);
    }
  });
} else {
  console.log('❌ React Query client not found on window');
}
