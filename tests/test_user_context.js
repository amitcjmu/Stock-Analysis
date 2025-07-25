import axios from 'axios';

async function testUserContext() {
  try {
    console.log('Testing login to backend...');

    // First login
    const loginResponse = await axios.post('http://localhost:8000/api/v1/auth/login', {
      email: 'chocka@gmail.com',
      password: 'Password123!'
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    console.log('Login successful!');
    const token = loginResponse.data.token.access_token;
    console.log('Token:', token);

    // Test get current user (the one that's failing in get_current_user_context)
    console.log('\nTesting get_current_user dependency...');
    try {
      const meResponse = await axios.get('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
          'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
        }
      });
      console.log('User from /me endpoint:', meResponse.data);
    } catch (error) {
      console.error('Failed to get user:', error.response ? error.response.data : error.message);
    }

    // Test master flow endpoint to trigger get_current_user_context
    console.log('\nTesting master flow endpoint that uses get_current_user_context...');
    try {
      const masterFlowResponse = await axios.get('http://localhost:8000/api/v1/master-flows/coordination/summary', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
          'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
        }
      });
      console.log('Master flow response:', masterFlowResponse.data);
    } catch (error) {
      console.error('Master flow request failed:', error.response ? error.response.data : error.message);
    }

  } catch (error) {
    console.error('Login failed:', error.response ? error.response.data : error.message);
  }
}

testUserContext();
