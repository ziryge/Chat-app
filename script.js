document.getElementById('send-button').addEventListener('click', function() {
    const messageInput = document.getElementById('message');
    const message = messageInput.value.trim();

    if (message) {
        addMessage(message, 'sent');
        messageInput.value = '';

        // Simulate receiving a reply
        setTimeout(() => {
            addMessage('This is a reply!', 'received');
        }, 1000);
    }
});

function addMessage(message, type) {
    const chatDisplay = document.getElementById('chat-display');
    const messageElement = document.createElement('div');
    messageElement.textContent = message;
    messageElement.className = `chat-message ${type}`;

    const timestamp = document.createElement('span');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    messageElement.appendChild(timestamp);

    chatDisplay.appendChild(messageElement);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}