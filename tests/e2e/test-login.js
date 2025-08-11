// Quick test to find working credentials
const credentials = [
  { email: 'demo@demo-corp.com', password: 'demo123' },
  { email: 'demo@demo-corp.com', password: 'Demo123!' },
  { email: 'demo@demo-corp.com', password: 'Password123!' },
  { email: 'admin@demo.com', password: 'Admin123!' },
  { email: 'user@demo.com', password: 'User123!' },
  { email: 'chocka@gmail.com', password: 'Password123!' }
];

async function testLogin(cred) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cred)
    });

    const data = await response.json();

    if (response.ok && data.access_token) {
      console.log(`✅ SUCCESS: ${cred.email} with password: ${cred.password}`);
      return true;
    } else {
      console.log(`❌ Failed: ${cred.email} - ${data.error?.details?.original_message || 'Unknown error'}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Error testing ${cred.email}: ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('Testing login credentials...\n');

  for (const cred of credentials) {
    const success = await testLogin(cred);
    if (success) {
      console.log('\n✅ Found working credentials!');
      process.exit(0);
    }
  }

  console.log('\n❌ No working credentials found');
  process.exit(1);
}

main();
