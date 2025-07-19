#!/bin/bash

set -e  # error

# clearing.. output
rm -f master_token.json signed_token.json

# reg users (if not already present)
echo "📝 Registering users..."
curl -s -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "alicepass"}' | tee alice_register.json

curl -s -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "bobpass"}' | tee bob_register.json

# embedded IDs
ALICE_EMBEDDED=$(jq -r .embedded_id alice_register.json)
BOB_EMBEDDED=$(jq -r .embedded_id bob_register.json)

echo "📌 Alice embedded_id: $ALICE_EMBEDDED"
echo "📌 Bob embedded_id: $BOB_EMBEDDED"

# money for poor Alice
echo "💸 Adding balance to Alice..."
curl -s -X POST http://127.0.0.1:5000/add_money \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "amount": 1000}' | jq .

# tokens 
echo "🔐 Logging in..."
ALICE_TOKEN=$(curl -s -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "alicepass"}' | jq -r .access_token)

BOB_TOKEN=$(curl -s -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "bobpass"}' | jq -r .access_token)

# master token
echo "🎟️ Generating master token..."
curl -s -X POST http://127.0.0.1:5000/generate_master \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500}' > master_token.json
jq . master_token.json

# locally sign hoga
echo "✍️ Signing locally..."
echo "$BOB_EMBEDDED" | python3 scripts/sign_local.py master_token.json $ALICE_EMBEDDED > signed_token.json
jq . signed_token.json

# redeem
echo "💳 Redeeming token as Bob..."
curl -s -X POST http://127.0.0.1:5000/redeem_token \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -H "Content-Type: application/json" \
  -d @signed_token.json | jq .

echo "✅ Flow complete!"
