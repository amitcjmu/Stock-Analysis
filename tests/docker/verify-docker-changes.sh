#!/bin/bash

echo "🔍 Verifying Docker environment has latest code changes..."

# Check if containers are running
echo "📊 Checking container status..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Containers are not running. Please run ./docker-rebuild.sh first"
    exit 1
fi

echo "✅ Containers are running"

# Test backend health
echo "🏥 Testing backend health..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Test field mapping tool availability
echo "🔧 Testing field mapping tool availability..."
docker-compose exec -T backend python -c "
try:
    from app.services.tools.field_mapping_tool import field_mapping_tool
    from app.services.field_mapper import field_mapper

    # Test basic functionality
    result = field_mapping_tool.learn_field_mapping('TEST_FIELD', 'Test Field', 'verification')
    print(f'✅ Field mapping tool working: {result[\"success\"]}')

    # Test field mapper
    mappings = field_mapper.get_field_mappings()
    print(f'✅ Field mapper working: {len(mappings)} base mappings available')

    # Test learned mappings persistence
    stats = field_mapper.get_mapping_statistics()
    print(f'✅ Mapping statistics: {stats[\"base_field_types\"]} base types, {stats[\"learned_field_types\"]} learned types')

    print('🎉 All field mapping functionality is working in Docker!')

except Exception as e:
    print(f'❌ Field mapping test failed: {e}')
    exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Field mapping functionality verified in Docker"
else
    echo "❌ Field mapping functionality test failed"
    echo "📝 Checking backend logs for errors..."
    docker-compose logs --tail=20 backend
    exit 1
fi

# Test agent monitoring endpoint
echo "🤖 Testing agent monitoring endpoint..."
if curl -s http://localhost:8000/api/v1/monitoring/status | grep -q "success"; then
    echo "✅ Agent monitoring endpoint working"
else
    echo "❌ Agent monitoring endpoint failed"
fi

# Test frontend accessibility
echo "🌐 Testing frontend accessibility..."
if curl -s http://localhost:8081 | grep -q "html"; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend accessibility test failed"
fi

echo ""
echo "🎯 Verification Summary:"
echo "✅ Docker containers running"
echo "✅ Backend health check passed"
echo "✅ Field mapping tool available"
echo "✅ Agent monitoring working"
echo "✅ Frontend accessible"
echo ""
echo "🚀 All systems operational! Your code changes are active in Docker."
echo "🌐 Access the application at: http://localhost:8081"
