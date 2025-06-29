#!/usr/bin/env node

import http from 'http';
import https from 'https';

async function testEndpoint(url, description) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https:') ? https : http;
    
    console.log(`🔍 Testing: ${description}`);
    console.log(`📍 URL: ${url}`);
    
    client.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log(`✅ Status: ${res.statusCode}`);
        console.log(`📊 Content Length: ${data.length} chars`);
        
        if (res.statusCode === 200) {
          resolve({ status: res.statusCode, data, headers: res.headers });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    }).on('error', (err) => {
      console.log(`❌ Error: ${err.message}`);
      reject(err);
    });
  });
}

async function testFieldMappingAPI() {
  const baseURL = 'http://localhost:8000/api/v1';
  const headers = {
    'X-Client-Account-Id': 'dfea7406-1575-4348-a0b2-2770cbe2d9f9',
    'X-Engagement-Id': 'ce27e7b1-2ac6-4b74-8dd5-b52d542a1669'
  };
  
  console.log('🚀 Testing Field Mapping APIs...\n');
  
  try {
    // Test available target fields
    console.log('1️⃣ Testing Available Target Fields API');
    const fieldsResponse = await makeAPICall(`${baseURL}/data-import/available-target-fields`, headers);
    const fieldsData = JSON.parse(fieldsResponse.data);
    console.log(`   📋 Found ${fieldsData.fields?.length || 0} available fields`);
    console.log(`   🏷️ Categories: ${Object.keys(fieldsData.categories || {}).length}`);
    
    // Test context field mappings
    console.log('\n2️⃣ Testing Context Field Mappings API');
    const mappingsResponse = await makeAPICall(`${baseURL}/data-import/context-field-mappings`, headers);
    const mappingsData = JSON.parse(mappingsResponse.data);
    console.log(`   📊 Success: ${mappingsData.success}`);
    console.log(`   🔗 Mappings: ${mappingsData.mappings?.length || 0}`);
    
    if (mappingsData.mappings && mappingsData.mappings.length > 0) {
      const sampleMapping = mappingsData.mappings[0];
      console.log(`   📝 Sample mapping: ${sampleMapping.sourceField} → ${sampleMapping.targetAttribute}`);
      console.log(`   📈 Status: ${sampleMapping.status}`);
      console.log(`   🎯 Confidence: ${sampleMapping.confidence}`);
    }
    
    console.log('\n✅ All API tests passed!');
    return true;
    
  } catch (error) {
    console.log(`\n❌ API test failed: ${error.message}`);
    return false;
  }
}

function makeAPICall(url, headers) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: headers
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve({ status: res.statusCode, data, headers: res.headers });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

async function testFrontendPages() {
  console.log('🌐 Testing Frontend Pages...\n');
  
  try {
    // Test main page
    console.log('1️⃣ Testing Main Page');
    const mainPage = await testEndpoint('http://localhost:8081/', 'Main frontend page');
    const hasReactRoot = mainPage.data.includes('<div id="root">');
    console.log(`   ⚛️ React root found: ${hasReactRoot}`);
    
    // Test attribute mapping page
    console.log('\n2️⃣ Testing Attribute Mapping Page');
    const attributePage = await testEndpoint('http://localhost:8081/discovery/attribute-mapping', 'Attribute mapping page');
    const hasReactApp = attributePage.data.includes('src="/src/main.tsx');
    console.log(`   📱 React app script: ${hasReactApp}`);
    
    // Test if main.tsx is accessible
    console.log('\n3️⃣ Testing React Main Script');
    const mainScript = await testEndpoint('http://localhost:8081/src/main.tsx', 'React main script');
    const hasReactDOM = mainScript.data.includes('ReactDOM');
    console.log(`   🔧 ReactDOM found: ${hasReactDOM}`);
    
    console.log('\n✅ All frontend tests passed!');
    return true;
    
  } catch (error) {
    console.log(`\n❌ Frontend test failed: ${error.message}`);
    return false;
  }
}

async function runAllTests() {
  console.log('🧪 Starting Comprehensive Frontend & API Tests\n');
  console.log('=' .repeat(60));
  
  const frontendPassed = await testFrontendPages();
  console.log('\n' + '=' .repeat(60));
  
  const apiPassed = await testFieldMappingAPI();
  console.log('\n' + '=' .repeat(60));
  
  console.log('\n📊 Test Summary:');
  console.log(`   🌐 Frontend Tests: ${frontendPassed ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`   🔗 API Tests: ${apiPassed ? '✅ PASSED' : '❌ FAILED'}`);
  
  if (frontendPassed && apiPassed) {
    console.log('\n🎉 ALL TESTS PASSED! Field mapping functionality should be working.');
    console.log('\n💡 Next Steps:');
    console.log('   1. Open browser to http://localhost:8081/discovery/attribute-mapping');
    console.log('   2. Click on "Field Mapping" tab');
    console.log('   3. Verify dropdowns are interactive');
    console.log('   4. Test approve/reject buttons');
  } else {
    console.log('\n⚠️  Some tests failed. Check the output above for details.');
  }
  
  process.exit(frontendPassed && apiPassed ? 0 : 1);
}

// Run the tests
runAllTests().catch(console.error);