#!/bin/bash
# External Onboarding Script
# This script can be downloaded from the API for easy onboarding.

read -p "Enter the API base URL (e.g., http://localhost:9103): " API_URL
API_URL=${API_URL%/}
read -p "Enter your project name: " PROJECT_NAME
read -p "Enter onboarding path (e.g., external_project): " ONBOARDING_PATH

# Step 1: Generate user token
echo "\nGenerating user token..."
TOKEN_RESP=$(curl -s -X POST "$API_URL/admin/generate-token" \
  -H 'Content-Type: application/json' \
  -d '{"description": "Token for '$PROJECT_NAME'", "role": "user"}')
TOKEN=$(echo "$TOKEN_RESP" | grep -o '"token"[ ]*:[ ]*"[^"]*"' | head -1 | cut -d '"' -f4)
if [ -z "$TOKEN" ]; then
  echo "Error generating token: $TOKEN_RESP"
  exit 1
fi
echo "$TOKEN" > .apitoken
echo "Token generated: ${TOKEN:0:6}... (saved to .apitoken)"

# Step 2: Register project and onboarding path
echo "Registering project and onboarding path..."
INIT_RESP=$(curl -s -X POST "$API_URL/onboarding/init" \
  -H 'Content-Type: application/json' \
  -d '{"project_name": "'$PROJECT_NAME'", "path": "'$ONBOARDING_PATH'"}')
echo "$INIT_RESP" | grep -q 'error' && { echo "Error initializing onboarding: $INIT_RESP"; exit 1; }
echo "Onboarding initialized!"

echo "\nNext steps:"
echo "- Your API token is saved in .apitoken. Use it as 'Authorization: Bearer <token>' in requests."
echo "- Explore the API docs at $API_URL/docs"
echo "- Follow the onboarding steps for '$ONBOARDING_PATH' in the docs or via the API." 