const themeButton = document.getElementById('theme-button');
if (themeButton) {
  let theme = document.documentElement.getAttribute('data-theme');
  const themeIcon = themeButton.querySelector('.icon');
  if (theme === 'light') {
    themeIcon.classList.add('icon-sun');
  } else {
    themeIcon.classList.add('icon-moon');
  }
  themeButton.addEventListener('click', () => {
    if (theme === 'light') {
      theme = 'dark';
      themeIcon.classList.replace('icon-sun', 'icon-moon');
    } else {
      theme = 'light';
      themeIcon.classList.replace('icon-moon', 'icon-sun');
    }
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  });
}

function copyToClipboard(button) {
  const targetId = button.getAttribute('data-copy-target');
  const targetField = document.getElementById(targetId);
  const buttonIcon = button.querySelector('.icon');
  const buttonText = button.querySelectorAll('span')[1];
  const originalText = buttonText.textContent;
  navigator.clipboard.writeText(targetField.value.trim())
    .then(() => {
      buttonText.textContent = 'Copied';
      buttonIcon.classList.replace('icon-copy', 'icon-check');
      buttonIcon.classList.replace('icon-muted', 'icon-success');
      button.disabled = true;
      setTimeout(() => {
        buttonText.textContent = originalText;
        buttonIcon.classList.replace('icon-check', 'icon-copy');
        buttonIcon.classList.replace('icon-success', 'icon-muted');
        button.disabled = false;
      }, 2000);
    })
    .catch((error) => console.error(error));
}

document.querySelectorAll('button[data-copy-target]').forEach((button) => {
  button.addEventListener('click', () => {
    copyToClipboard(button);
  });
});

const createChatForm = document.getElementById('create-chat-form');
if (createChatForm) {
  let submittingForm = false;
  window.addEventListener('beforeunload', (event) => {
    if (submittingForm) {
      return;
    };
    event.preventDefault();
    event.returnValue = '';
  });
  createChatForm.addEventListener('submit', () => {
    submittingForm = true;
    navigator.clipboard.writeText('')
      .catch((error) => console.error(error));
  });
}

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
    const message = messageField.value.trim();
    if (message) {
      const parts = message.split('|');
      if (parts.length === 2 && parts[0].length === 16 && !/\s/.test(message)) {
        operationField.value = 'Decrypt';
      } else {
        operationField.value = 'Encrypt';
      }
    } else {
      operationField.value = '-';
    }
  });
}

const encryptDecryptForm = document.getElementById('encrypt-decrypt-form');
const messageForFormField = document.getElementById('message-for-form');
if (encryptDecryptForm) {
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
