# E2EE Chat

Desktop app for end-to-end message encryption.

## Install and run

Windows:

```bash
py -m pip install -r requirements.txt
py e2ee_chat.py
```

macOS/Linux:

```bash
python3 -m pip install -r requirements.txt
python3 e2ee_chat.py
```

Then open <http://127.0.0.1:5000> in your browser.

## Cryptographic algorithms

- Key exchange: [X448](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x448/)
- Key derivation: [HKDF](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#hkdf)
- Message encryption: [AES-256-GCM](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)

## Dependencies

- [cryptography](https://github.com/pyca/cryptography)
- [Flask](https://github.com/pallets/flask)

## Development dependencies

- [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss)
- [daisyUI](https://github.com/saadeghi/daisyui)
