// Fix Frontend Authentication Token
// Run this script in the browser console to manually set authentication

console.log('=== Frontend Authentication Fix ===');

// Clear any corrupted tokens first
localStorage.removeItem('auth_token');
localStorage.removeItem('user_data');

// Set the admin authentication token (matches backend hardcoded admin)
const adminToken = 'db-token-55555555-5555-5555-5555-555555555555-admin123';
localStorage.setItem('auth_token', adminToken);

// Set the admin user data (matches backend user)
const adminUser = {
  id: '55555555-5555-5555-5555-555555555555',
  email: 'admin@democorp.com',
  role: 'admin',
  full_name: 'Admin User',
  username: 'admin',
  status: 'active',
  organization: 'Democorp',
  role_description: 'Platform Administrator'
};

localStorage.setItem('user_data', JSON.stringify(adminUser));

console.log('✅ Authentication token set:', localStorage.getItem('auth_token'));
console.log('✅ User data set:', JSON.parse(localStorage.getItem('user_data')));

// Test API call with the token
console.log('🔄 Testing API call...');
fetch('/api/v1/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('📡 API Response Status:', response.status);
  return response.json();
})
.then(data => {
  console.log('📡 API Response Data:', data);
  console.log('🔄 Refreshing page to apply changes...');
  setTimeout(() => location.reload(), 1000);
})
.catch(error => {
  console.error('❌ API Test Failed:', error);
  console.log('🔄 Refreshing page anyway...');
  setTimeout(() => location.reload(), 1000);
});
