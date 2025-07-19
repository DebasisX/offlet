import sys, json, hmac, hashlib

if len(sys.argv) != 3:
    print('Usage: sign_local.py <token.json> <sender_embedded_id>')
    sys.exit(1)

token_file, sender_embedded_id = sys.argv[1], sys.argv[2]
data = json.load(open(token_file))

receiver_embedded_id = input().strip()
data['receiver_embedded_id'] = receiver_embedded_id

# idhar strict order: transaction_id, amount, expiry, sender_username, sender_embedded_id
msg = "|".join([
    data['transaction_id'],
    str(data['amount']),
    data['expiry'],
    data['sender_username'],
    data['sender_embedded_id'],
    data['receiver_embedded_id']
])

data['local_signature'] = hmac.new(
    sender_embedded_id.encode(), msg.encode(), hashlib.sha256
).hexdigest()

print(json.dumps(data, indent=2))
