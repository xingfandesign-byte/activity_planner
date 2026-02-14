#!/bin/bash
echo "Testing Activity Planner Backend..."
echo ""

echo "1. Testing health endpoint..."
curl -s http://localhost:5001/health || echo "❌ Backend not running!"
echo ""
echo ""

echo "2. Testing digest endpoint..."
curl -s http://localhost:5001/v1/digest | python3 -m json.tool | head -20 || echo "❌ Digest endpoint failed!"
echo ""

echo "3. Testing preferences endpoint..."
curl -s http://localhost:5001/v1/preferences | python3 -m json.tool | head -15 || echo "❌ Preferences endpoint failed!"
echo ""

echo "✅ Test complete!"
