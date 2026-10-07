function copyToClipboard(button) {
  const targetId = button.getAttribute('data-copy-target');
  const targetField = document.getElementById(targetId);
  if (!targetField || !targetField.value.trim()) {
    return;
  }
  const originalText = button.textContent;
  navigator.clipboard.writeText(targetField.value)
    .then(() => {
      button.textContent = 'Copied';
      button.disabled = true;
      setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
      }, 1500);
    })
    .catch((error) => {
      console.error('Failed to copy:', error);
    });
}

document.querySelectorAll('button[data-copy-target]').forEach((button) => {
  button.addEventListener('click', () => {
    copyToClipboard(button);
  });
});

const messageField = document.getElementById('message');
const operationField = document.getElementById('operation');

if (messageField) {
  window.scrollTo(0, document.body.scrollHeight);
  document.querySelectorAll('.created-at').forEach((element) => {
    const date = new Date(element.textContent.trim());
    const shortTime = date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    element.textContent = shortTime;
    element.setAttribute('data-tip', date.toLocaleString());
  });
  messageField.addEventListener('input', () => {
    messageField.style.height = 'auto';
    messageField.style.height = `${messageField.scrollHeight}px`;
    if (!operationField) {
      return;
    }
    if (messageField.value.trim() !== '') {
      operationField.disabled = false;
      if (messageField.value.includes('==|')) {
        operationField.value = 'decrypt';
      } else {
        operationField.value = 'encrypt';
      }
    } else {
      operationField.disabled = true;
    }
  });
}

const encryptDecryptForm = document.getElementById('encrypt-decrypt-form');
const messageForFormField = document.getElementById('message-for-form');

if (encryptDecryptForm && messageField && messageForFormField) {
  encryptDecryptForm.addEventListener('submit', () => {
    if (messageField.value.trim()) {
      messageForFormField.value = messageField.value.trim();
    }
  });
}