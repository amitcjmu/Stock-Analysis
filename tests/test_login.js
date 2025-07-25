import axios from 'axios';

async function testLogin() {
  try {
    console.log('Testing login to backend...');

    const response = await axios.post('http://localhost:8000/api/v1/auth/login', {
      email: 'chocka@gmail.com',
      password: 'Password123!'
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    console.log('Login successful!');
    console.log('Response:', response.data);
    console.log('Token:', response.data.token.access_token);

    // Test with the token
    if (response.data.token && response.data.token.access_token) {
      console.log('\nTesting authenticated request...');
      const userResponse = await axios.get('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${response.data.token.access_token}`
        }
      });
      console.log('User info:', userResponse.data);
    }

  } catch (error) {
    console.error('Login failed:', error.response ? error.response.data : error.message);
  }
}

testLogin();
