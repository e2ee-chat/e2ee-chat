import base64
import json
import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    send_from_directory,
    url_for,
    abort,
)


def generate_exchange_keys() -> tuple[str, str]:
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_b = private_key.private_bytes_raw()
    public_b = public_key.public_bytes_raw()
    private_key_b64 = base64.b64encode(private_b).decode()
    public_key_b64 = base64.b64encode(public_b).decode()
    return private_key_b64, public_key_b64


def derive_key(
    private_key_b64: str,
    peer_public_key_b64: str,
) -> bytes | None:
    try:
        private_b = base64.b64decode(private_key_b64)
        public_b = base64.b64decode(peer_public_key_b64)
        private_key = X25519PrivateKey.from_private_bytes(private_b)
        peer_public_key = X25519PublicKey.from_public_bytes(public_b)
        shared_key = private_key.exchange(peer_public_key)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'E2EE Chat | X25519 | AES-256',
        )
        derived_key = hkdf.derive(shared_key)
        return derived_key
    except (ValueError, TypeError):
        return None


def encrypt_text(plaintext: str, key: bytes) -> str:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES256(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES256.block_size).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    iv_b64 = base64.b64encode(iv).decode()
    ciphertext_b64 = base64.b64encode(ciphertext).decode()
    encrypted_text = '|'.join((iv_b64, ciphertext_b64))
    return encrypted_text


def decrypt_text(encrypted_text: str, key: bytes) -> str | None:
    try:
        iv_b64 = encrypted_text.split('|')[0]
        ciphertext_b64 = encrypted_text.split('|')[1]
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        cipher = Cipher(algorithms.AES256(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES256.block_size).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext.decode()
    except (ValueError, IndexError):
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


def create_storage_folder() -> None:
    os.makedirs(os.path.join(app.root_path, 'storage'), exist_ok=True)


def generate_chat_name() -> str:
    create_storage_folder()
    while True:
        name = os.urandom(5).hex()
        path = os.path.join(app.root_path, 'storage', f'{name}.json')
        if not os.path.exists(path):
            return name


def get_chat(name: str) -> dict | None:
    path = os.path.join(app.root_path, 'storage', f'{name}.json')
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_chat(name: str, data: dict) -> None:
    path = os.path.join(app.root_path, 'storage', f'{name}.json')
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)


app = Flask(__name__)


@app.route('/')
def home():
    create_storage_folder()
    chat_files = os.listdir(os.path.join(app.root_path, 'storage'))
    chats = []
    for file in chat_files:
        if file.endswith('.json'):
            name = os.path.splitext(file)[0]
            data = get_chat(name)
            chats.append((name, len(data['messages'])))
    chats = sorted(chats, key=lambda x: x[1], reverse=True)
    context = {'chats': chats}
    return render_template('home.html', **context)


@app.route('/create_chat', methods=['GET', 'POST'])
def create_chat():
    if request.method == 'POST':
        name = request.form['chat_name']
        public_key = request.form['public_key']
        data = {
            'chat_name': name,
            'public_key': public_key,
            'peer_public_key': '',
            'messages': [],
        }
        save_chat(name, data)
        return redirect(url_for('set_peer_public_key', name=name))
    name = generate_chat_name()
    private_key, public_key = generate_exchange_keys()
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
        peer_public_key = request.form['peer_public_key']
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
        private_key_b64 = request.form['private_key'].strip()
        peer_public_key_b64 = data['peer_public_key']
        derived_key = derive_key(private_key_b64, peer_public_key_b64)
        if derived_key is None:
            return redirect(url_for('chat', name=name))
        new_message = request.form['message'].strip()
        if new_message:
            operation = request.form['operation']
            messages = []
            messages.extend(data['messages'])
            if operation == 'encrypt':
                e_new_message = encrypt_text(new_message, derived_key)
                created_at = get_utc_now()
                e_created_at = encrypt_text(created_at, derived_key)
                messages.append({
                    'text': e_new_message,
                    'created_at': e_created_at,
                    'is_my_message': True,
                })
                data['messages'] = messages
                save_chat(name, data)
                context['encrypted'] = e_new_message
            elif operation == 'decrypt':
                d_new_message = decrypt_text(new_message, derived_key)
                if d_new_message:
                    created_at = get_utc_now()
                    e_created_at = encrypt_text(created_at, derived_key)
                    messages.append({
                        'text': new_message,
                        'created_at': e_created_at,
                        'is_my_message': False,
                    })
                    data['messages'] = messages
                    save_chat(name, data)
                    context['decrypted'] = d_new_message
        data = get_chat(name)
        percent = int(request.form['percent'])
        number_to_decrypt = len(data['messages']) * percent // 100
        number_encrypted = len(data['messages']) - number_to_decrypt
        messages = []
        messages.extend(data['messages'][:number_encrypted])
        for msg in data['messages'][number_encrypted:]:
            d_message = decrypt_text(msg['text'], derived_key)
            d_created_at = decrypt_text(msg['created_at'], derived_key)
            if d_message and d_created_at:
                msg['text'] = d_message
                msg['created_at'] = d_created_at
                msg['decrypted'] = True
            messages.append(msg)
        context['messages'] = messages
        context['percent'] = percent
        return render_template('chat.html', **context)
    context['messages'] = data['messages']
    return render_template('chat.html', **context)


@app.post('/chat/<name>/delete_chat')
def delete_chat(name):
    path = os.path.join(app.root_path, 'storage', f'{name}.json')
    if not os.path.isfile(path):
        return redirect(url_for('chat', name=name))
    os.remove(path)
    return redirect(url_for('home'))


@app.route('/storage/<name>.json')
def chat_file(name):
    return send_from_directory(
        os.path.join(app.root_path, 'storage'),
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
