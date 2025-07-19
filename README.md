# offlet

🔒 Offline Digital Cash System with Dual Signatures

Concept:
Enable secure offline peer-to-peer transactions using pre-signed digital tokens that can be transferred and redeemed without constant internet access.

🧠 How It Works

1. Token Generation (Online)
- Users request tokens (₹1, ₹2, ₹5...) from the server.
- Tokens include: amount, sender_id, expiry, transaction_id
- Server signs with a private HMAC key
- Tokens are stored encrypted on device

2. Offline Transfer
- Sender scans receiver's QR (containing receiver_id, HSN)
- Token is embedded with receiver info
- Signed locally using sender’s device key (HSN)
- Shared via QR/Bluetooth/NFC

3. Online Redemption
- Receiver uploads token to server
- Server verifies both signatures (server + sender)
- Checks expiry, uniqueness, and binds it to receiver
- Token is marked as redeemed
- Amount is credited

🔐 Security Highlights
- 🔑 Dual Signature: Server + Local HSN binding
- 🧾 Tamper-proof and one-time redeemable
- 🕹️ Works offline for transfer; only receiver needs to be online for redemption
- 🔍 Tokens traceable but anonymous in transit

💰 Why It’s Like Cash
Just like handing over a signed banknote:
- ✅ Fixed denomination
- ✅ Physically transferable
- ✅ One-time use
- ✅ Tamper-proof
