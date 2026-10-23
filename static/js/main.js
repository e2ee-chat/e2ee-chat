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
    .catch((error) => console.error(error));
}

document.querySelectorAll('button[data-copy-target]').forEach((button) => {
  button.addEventListener('click', () => {
    copyToClipboard(button);
  });
});

const messageField = document.getElementById('message');
const operationField = document.getElementById('operation');
const messages = document.getElementById('messages');

if (messageField) {
  window.scrollTo(0, document.body.scrollHeight);
  document.querySelectorAll('.created-at').forEach((element) => {
    const date = new Date(element.textContent.trim());
    const formattedTime = date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    element.textContent = formattedTime;
    element.setAttribute('data-tip', date.toLocaleString());
  });
  messageField.addEventListener('input', () => {
    messageField.style.height = 'auto';
    messageField.style.height = `${messageField.scrollHeight}px`;
    if (messageField.scrollHeight >= 220) {
      messages.style.paddingBottom = `${220}px`;
    } else {
      messages.style.paddingBottom = `${messageField.scrollHeight + 12}px`;
    }
    if (!operationField) {
      return;
    }
    const message = messageField.value.trim();
    if (message) {
      operationField.disabled = false;
      const parts = message.split('|');
      if (parts.length === 2 && parts[0].length === 16) {
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
    const message = messageField.value.trim();
    if (message) {
      messageForFormField.value = message;
    }
    navigator.clipboard.writeText('')
      .catch((error) => console.error(error));
  });
}

document.querySelectorAll('form[data-clear-clipboard]').forEach((form) => {
  form.addEventListener('submit', () => {
    navigator.clipboard.writeText('')
      .catch((error) => console.error(error));
  });
});