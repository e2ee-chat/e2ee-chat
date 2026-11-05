# E2EE Chat

A local web app for end-to-end message encryption.

## Cryptographic algorithms

- Key exchange: [X448](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x448/)
- Key derivation: [HKDF](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#hkdf)
- Message encryption: [AES-256-GCM](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)

## Install and run

Windows:

```bash
py -m pip install -r requirements.txt
```

```bash
py e2ee_chat.py
```

macOS/Linux:

```bash
python3 -m pip install -r requirements.txt
```

```bash
python3 e2ee_chat.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Security recommendations

- Use a privacy-focused browser without extensions. Disable built-in extensions for `127.0.0.1`. Do not use page translation, synchronization, AI features, or other functions that read page content.
- Before exchanging messages, compare the hashes of the public keys over a separate communication channel to verify that they match and that the keys have not been tampered with.
- To prevent `nonce` reuse, do not send new messages until you have decrypted the other party's new messages. If a `nonce` is reused, create a new chat.

## Dependencies

- [cryptography](https://github.com/pyca/cryptography)
- [Flask](https://github.com/pallets/flask)

## Development dependencies

- [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss)
- [daisyUI](https://github.com/saadeghi/daisyui)
