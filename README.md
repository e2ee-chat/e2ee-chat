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

Then open http://127.0.0.1:5000 in your browser.

## Cryptographic algorithms

- Key exchange: X448
- Key derivation: HKDF
- Message encryption: AES-256-GCM
