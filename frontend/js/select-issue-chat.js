function selectIssue(category) {
    document.querySelector('.select-issue-section').style.display = 'none';
    document.getElementById('chatSection').style.display = 'block';
    // Store the selected category
    window.selectedCategory = category;
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    const chatBox = document.getElementById('chatBox');

    if (message) {
        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'chat-message user-message';
        userMessage.textContent = message;
        chatBox.appendChild(userMessage);

        // Clear input
        input.value = '';

        // Add typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-message ai-message typing-indicator';
        typingIndicator.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            // Send message to backend
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    category: window.selectedCategory || 'General'
                })
            });

            // Remove typing indicator
            typingIndicator.remove();

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Add AI response
            const aiMessage = document.createElement('div');
            aiMessage.className = 'chat-message ai-message';
            aiMessage.textContent = data.reply;
            chatBox.appendChild(aiMessage);
        } catch (error) {
            console.error('Error:', error);
            // Remove typing indicator
            typingIndicator.remove();

            // Add error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'chat-message ai-message';
            errorMessage.textContent = 'Sorry, I encountered an error. Please try again later.';
            chatBox.appendChild(errorMessage);
        }

        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Add event listener for Enter key
document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}); 