import base64
import json
import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x448 import (
    X448PrivateKey,
    X448PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
    abort,
)

app = Flask(__name__)

CHATS_DIR = os.path.join(app.root_path, 'chats')


def generate_keys() -> tuple[str, str]:
    private_key = X448PrivateKey.generate()
    public_key = private_key.public_key()
    private_b = private_key.private_bytes_raw()
    public_b = public_key.public_bytes_raw()
    private_key_b64 = base64.b64encode(private_b).decode()
    public_key_b64 = base64.b64encode(public_b).decode()
    return private_key_b64, public_key_b64


def derive_key(
    private_key_b64: str,
    peer_public_key_b64: str,
    verification_hash: str,
) -> bytes | None:
    try:
        private_b = base64.b64decode(private_key_b64)
        public_b = base64.b64decode(peer_public_key_b64)
        private_key = X448PrivateKey.from_private_bytes(private_b)
        peer_public_key = X448PublicKey.from_public_bytes(public_b)
        shared_key = private_key.exchange(peer_public_key)
        salt = base64.b64decode(verification_hash)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'E2EE Chat | X448 | AES-256-GCM',
        )
        derived_key = hkdf.derive(shared_key)
        return derived_key
    except (ValueError, TypeError):
        return None


def get_nonces(messages: list) -> list:
    nonces = []
    for msg in messages:
        nonce_b64 = msg['text'].split('|')[0]
        nonces.append(nonce_b64)
    return nonces


def generate_nonce(messages: list) -> bytes:
    nonces = get_nonces(messages)
    while True:
        nonce = os.urandom(12)
        nonce_b64 = base64.b64encode(nonce).decode()
        if nonce_b64 not in nonces:
            return nonce


def nonce_exists(message: str, messages: list) -> bool:
    nonces = get_nonces(messages)
    nonce_b64 = message.split('|')[0]
    if nonce_b64 in nonces:
        return True
    else:
        return False


def encrypt_text(plaintext: str, key: bytes, nonce: bytes) -> str:
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    nonce_b64 = base64.b64encode(nonce).decode()
    ciphertext_b64 = base64.b64encode(ciphertext).decode()
    encrypted_text = '|'.join((nonce_b64, ciphertext_b64))
    return encrypted_text


def decrypt_text(encrypted_text: str, key: bytes) -> str | None:
    try:
        nonce_b64 = encrypted_text.split('|')[0]
        ciphertext_b64 = encrypted_text.split('|')[1]
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except (ValueError, TypeError, IndexError):
        return None


def get_verification_hash(
    public_key_b64: str,
    peer_public_key_b64: str,
) -> str:
    public_key = base64.b64decode(public_key_b64)
    peer_public_key = base64.b64decode(peer_public_key_b64)
    first, second = sorted((public_key, peer_public_key))
    digest = hashes.Hash(hashes.SHA256())
    digest.update(first)
    digest.update(second)
    hash = digest.finalize()
    hash_b64 = base64.b64encode(hash).decode()
    return hash_b64


def get_utc_now() -> str:
    utc_now = datetime.now(timezone.utc)
    utc_now_iso = utc_now.isoformat(timespec='seconds')
    return utc_now_iso


def create_chats_folder() -> None:
    os.makedirs(CHATS_DIR, exist_ok=True)


def generate_chat_name() -> str:
    create_chats_folder()
    while True:
        name = os.urandom(5).hex()
        path = os.path.join(CHATS_DIR, f'{name}.json')
        if not os.path.exists(path):
            return name


def get_chat(name: str) -> dict | None:
    path = os.path.join(CHATS_DIR, f'{name}.json')
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_chat(name: str, data: dict) -> None:
    path = os.path.join(CHATS_DIR, f'{name}.json')
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)


@app.route('/')
def home():
    create_chats_folder()
    chat_files = os.listdir(CHATS_DIR)
    chats = []
    for file in chat_files:
        if file.endswith('.json'):
            name = os.path.splitext(file)[0]
            data = get_chat(name)
            chats.append((name, len(data['messages'])))
    chats = sorted(chats, key=lambda x: x[1], reverse=True)
    return render_template('home.html', chats=chats)


@app.route('/create_chat', methods=['GET', 'POST'])
def create_chat():
    if request.method == 'POST':
        name = request.form['name']
        public_key = request.form['public_key']
        data = {
            'public_key': public_key,
            'peer_public_key': '',
            'messages': [],
        }
        save_chat(name, data)
        return redirect(url_for('set_peer_public_key', name=name))
    name = generate_chat_name()
    private_key, public_key = generate_keys()
    context = {
        'name': name,
        'private_key': private_key,
        'public_key': public_key,
    }
    return render_template('create_chat.html', **context)


@app.route('/chat/<name>/set_peer_public_key', methods=['GET', 'POST'])
def set_peer_public_key(name):
    data = get_chat(name)
    if data is None:
        abort(404)
    if data['peer_public_key'] != '':
        return redirect(url_for('chat', name=name))
    if request.method == 'POST':
        peer_public_key = request.form['peer_public_key'].strip()
        data['peer_public_key'] = peer_public_key
        save_chat(name, data)
        return redirect(url_for('chat', name=name))
    context = {
        'name': name,
        'public_key': data['public_key'],
    }
    return render_template('set_peer_public_key.html', **context)


@app.route('/chat/<name>', methods=['GET', 'POST'])
def chat(name):
    data = get_chat(name)
    if data is None:
        abort(404)
    if data['peer_public_key'] == '':
        return redirect(url_for('set_peer_public_key', name=name))
    hash = get_verification_hash(data['public_key'], data['peer_public_key'])
    context = {
        'name': name,
        'hash': hash,
    }
    if request.method == 'POST':
        private_key = request.form['private_key'].strip()
        derived_key = derive_key(private_key, data['peer_public_key'], hash)
        if derived_key is None:
            return redirect(url_for('chat', name=name))
        message = request.form['message'].strip()
        if message:
            operation = request.form['operation']
            messages = []
            messages.extend(data['messages'])
            if operation == 'Encrypt':
                nonce = generate_nonce(messages)
                e_message = encrypt_text(message, derived_key, nonce)
                messages.append({
                    'text': e_message,
                    'created_at': get_utc_now(),
                    'is_my_message': True,
                })
                data['messages'] = messages
                save_chat(name, data)
                context['encrypted'] = e_message
            elif operation == 'Decrypt':
                d_message = decrypt_text(message, derived_key)
                n_exists = nonce_exists(message, messages)
                if d_message is not None and not n_exists:
                    messages.append({
                        'text': message,
                        'created_at': get_utc_now(),
                        'is_my_message': False,
                    })
                    data['messages'] = messages
                    save_chat(name, data)
                    context['decrypted'] = d_message
        data = get_chat(name)
        percent = int(request.form['percent'])
        number_to_decrypt = len(data['messages']) * percent // 100
        number_encrypted = len(data['messages']) - number_to_decrypt
        messages = []
        messages.extend(data['messages'][:number_encrypted])
        for msg in data['messages'][number_encrypted:]:
            d_message = decrypt_text(msg['text'], derived_key)
            if d_message:
                msg['text'] = d_message
                msg['decrypted'] = True
            messages.append(msg)
        context['messages'] = messages
        context['percent'] = percent
        return render_template('chat.html', **context)
    context['messages'] = data['messages']
    return render_template('chat.html', **context)


@app.post('/chat/<name>/delete_chat')
def delete_chat(name):
    path = os.path.join(CHATS_DIR, f'{name}.json')
    if not os.path.isfile(path):
        return redirect(url_for('chat', name=name))
    os.remove(path)
    return redirect(url_for('home'))


@app.route('/chats/<name>.json')
def chat_file(name):
    return send_from_directory(
        os.path.join(CHATS_DIR),
        f'{name}.json',
        mimetype='application/json',
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )


if __name__ == '__main__':
    app.run()
