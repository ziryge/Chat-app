// JavaScript for real-time chat functionality

// WebSocket connection for real-time updates
const socket = new WebSocket('ws://localhost:8000');

socket.onopen = () => {
    console.log('WebSocket connection established');
};

socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    displayMessage(message);
};

function sendMessage(content) {
    const message = {
        user: 'current_user', // Replace with dynamic user data
        content: content,
        timestamp: new Date().toISOString()
    };
    socket.send(JSON.stringify(message));
    displayMessage(message);
}

function displayMessage(message) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('div');
    messageElement.className = 'chat-message';
    messageElement.innerHTML = `<strong>${message.user}:</strong> ${message.content} <span class='timestamp'>${message.timestamp}</span>`;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Event listener for sending messages
document.getElementById('send-button').addEventListener('click', () => {
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value;
    if (content) {
        sendMessage(content);
        messageInput.value = '';
    }
});