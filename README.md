# E2EE Chat

End-to-end encrypted chat app for desktop.

## Install and run

Windows:

```bash
py -m pip install -r requirements.txt
py e2ee_chat.py
```

macOS/Linux:

```bash
pip install -r requirements.txt
python3 e2ee_chat.py
```

Open 127.0.0.1:5000

## Algorithm

1. X25519
2. HKDF
3. AES256
