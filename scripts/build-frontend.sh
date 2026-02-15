#!/bin/bash
# Render build script: injects API_URL into config.js
# Set API_URL in Render dashboard to your backend URL (e.g. https://activity-planner-1-jvw3.onrender.com)
cd "$(dirname "$0")/.."
API_URL="${API_URL:-http://localhost:5001}"
echo "window.API_BASE = '${API_URL}/v1';" > frontend/config.js
echo "Built config.js with API_BASE=${API_URL}/v1"
