// frontend/js/script.js
document.addEventListener('DOMContentLoaded', () => {

    // Select the main grid container and chat interface container
    const issueGridContainer = document.getElementById('issue-grid'); // ID of the category button grid div
    const issueButtons = document.querySelectorAll('#issue-grid .issue-card'); // Buttons inside the grid
    const chatInterfaceContainer = document.getElementById('chat-interface'); // ID of the chat container div

    // Select chat interface elements
    const chatCategoryTitle = document.getElementById('chat-category-title'); // Span for category title
    const chatBox = document.getElementById('chat-box'); // Div where messages appear
    const userInput = document.getElementById('user-input'); // Input field
    const sendButton = document.getElementById('send-button'); // Send button
    const backButton = document.getElementById('back-to-categories'); // Back button

    let currentCategory = null; // Variable to store the selected category


    // --- Initial State ---
    // Ensure chat is hidden on page load
    // This needs to override any CSS default or previous state
    if (chatInterfaceContainer) {
        chatInterfaceContainer.style.display = 'none';
    }

    // --- Event Listeners ---

    // Event listener for clicking the category buttons
    if (issueButtons && issueGridContainer && chatInterfaceContainer && chatCategoryTitle) {
        issueButtons.forEach(button => {
            button.addEventListener('click', () => {
                currentCategory = button.dataset.category; // Get category from data-category attribute
                console.log("Category selected:", currentCategory);

                // Hide the issue grid and show the chat interface
                issueGridContainer.style.display = 'none'; // Hide the category grid
                chatCategoryTitle.textContent = currentCategory; // Set chat title based on category
                // Use 'block' or display property matching your CSS for .chat-container
                chatInterfaceContainer.style.display = 'block'; // Show the chat container

                // Add initial AI welcome message (using general knowledge for now)
                addMessageToChat("AI", `Hello! You've selected ${currentCategory}. Ask me a general question about this topic in Algeria. Remember, I cannot give legal advice.`);

                // Focus the input field for immediate typing
                if (userInput) userInput.focus();
            });
        });
    } else {
        console.error("One or more UI elements for category selection or chat not found! Check IDs in HTML.");
    }

    // Event listener for Send button click
    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }

    // Event listener for pressing Enter key in the input field
    if (userInput) {
        userInput.addEventListener('keypress', function (e) {
            // Check for Enter key (key code 13) and ensure send button is not disabled
            if (e.key === 'Enter' && sendButton && !sendButton.disabled) {
                e.preventDefault(); // Prevent default form submission if input is inside a form
                handleSendMessage(); // Call the function to send message
            }
        });
    }

    // Event listener for the Back button click
    if (backButton) {
        backButton.addEventListener('click', () => {
            // Clear chat box content
            if (chatBox) {
                chatBox.innerHTML = ''; // Removes all child message elements (messages)
            }
            currentCategory = null; // Reset the selected category

            // Hide chat interface and show the issue grid
            if (chatInterfaceContainer) chatInterfaceContainer.style.display = 'none';
            // Ensure display property matches your CSS for .issue-grid
            if (issueGridContainer) issueGridContainer.style.display = 'grid'; // Show the category grid again

            // Optional: Scroll back to the top of the section
            // window.scrollTo({ top: 0, behavior: 'smooth' }); // Or scroll to the section element
        });
    }


    // --- Helper Functions ---

    // Function to handle sending a message (triggered by button click or Enter key)
    function handleSendMessage() {
        // Check if essential elements and category are available
        if (!userInput || !currentCategory || !sendButton) {
            console.error("Cannot send message: UI elements or category missing.");
            return; // Exit if not ready
        }

        const message = userInput.value.trim(); // Get message text, remove leading/trailing whitespace
        if (!message) {
            // Optionally alert user they can't send empty message
            console.log("Attempted to send empty message.");
            return; // Don't send empty messages
        }

        console.log(`User message: "${message}" (Category: ${currentCategory})`); // Log the message

        // Add user message to the chat UI immediately
        addMessageToChat("User", message);

        // Clear the input field
        userInput.value = '';

        // Call the function to send the message to the backend API
        sendMessageToBackend(message, currentCategory);
    }

    // Function to add a message (from User or AI) to the chat box UI
    function addMessageToChat(sender, text) {
        if (!chatBox) {
            console.error("Chat box element not found! Cannot add message.");
            return; // Exit if chat box isn't found
        }

        const messageElement = document.createElement('div'); // Create a new div for the message
        messageElement.classList.add('chat-message'); // Add base message class

        // Add sender-specific class for styling (user-message or ai-message)
        if (sender === "User") {
            messageElement.classList.add('user-message');
        } else { // Assume sender is "AI" for simplicity
            messageElement.classList.add('ai-message');
        }

        // Set the text content of the message element
        // Use textContent to prevent potential XSS issues if AI response contains HTML
        messageElement.textContent = text;

        // Append the new message element to the chat box
        chatBox.appendChild(messageElement);

        // Scroll to the bottom of the chat box to show the latest message
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Function to show a typing indicator message
    function addTypingIndicator() {
        if (!chatBox) return; // Exit if chat box not found

        // Remove any existing typing indicator before adding a new one
        removeTypingIndicator();

        const typingElement = document.createElement('div'); // Create element for indicator
        // Add classes for styling (matches AI message bubble look)
        typingElement.classList.add('chat-message', 'ai-message', 'typing-indicator');
        // Add elements for the bouncing dots (styled in CSS)
        typingElement.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        typingElement.id = 'typing-indicator'; // Add a unique ID for easy removal

        // Append the indicator to the chat box
        chatBox.appendChild(typingElement);

        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Function to remove the typing indicator message
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator'); // Find the indicator by its ID
        if (indicator) {
            indicator.remove(); // Remove the element from the DOM
        }
    }

    // --- Function to send message to the backend API ---
    // This function makes the network request to your Flask server
    async function sendMessageToBackend(message, category) {
        // Check if sendButton exists before trying to access its 'disabled' property
        if (!sendButton) {
            console.error("Send button element not found! Cannot send API request.");
            removeTypingIndicator(); // Ensure indicator is removed if we exit early
            return;
        }

        // Show typing indicator and disable send button while waiting for response
        addTypingIndicator();
        sendButton.disabled = true;

        try {
            // *** IMPORTANT: Ensure this URL matches your running Flask backend ***
            // Flask development server typically runs on http://localhost:5000
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST', // Use POST method as defined in Flask route
                headers: {
                    'Content-Type': 'application/json', // Specify that the request body is JSON
                },
                // Convert the message and category data into a JSON string for the request body
                body: JSON.stringify({ message: message, category: category }),
            });

            // Remove typing indicator after the fetch call completes (whether success or error)
            removeTypingIndicator();

            // Check if the HTTP response status indicates success (2xx range)
            if (!response.ok) {
                // Handle HTTP errors (e.g., 400 Bad Request, 500 Internal Server Error)
                let errorMsg = `Sorry, there was an issue communicating with the server (Status: ${response.status}). Please try again later.`;
                console.error(`Error from backend: ${response.status} ${response.statusText}`);
                try {
                    // Attempt to read a more specific error message from the backend response if it's JSON
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMsg = `Error: ${errorData.error}`; // Use the error message provided by the backend
                    }
                } catch (e) {
                    // If parsing the error response fails (e.g., backend didn't return JSON error),
                    // just use the generic error message.
                    console.error("Failed to parse backend error response as JSON:", e);
                }
                // Add the error message to the chat box (formatted like an AI message)
                addMessageToChat("AI", errorMsg);
                return; // Stop processing here after handling the error
            }

            // If the response was OK (status 2xx), parse the JSON response body
            const data = await response.json();

            // Check if the expected 'reply' key is in the JSON data
            if (data && data.reply) {
                // Add the AI's actual reply to the chat box
                addMessageToChat("AI", data.reply);
            } else {
                // Handle cases where the backend returned OK but the expected data structure is missing
                console.error("Backend returned OK but missing 'reply' key in JSON:", data);
                addMessageToChat("AI", "Sorry, I received an unexpected response format from the server.");
            }

        } catch (error) { // Catch network errors or other issues with the fetch operation itself
            // Ensure typing indicator is removed on network errors
            removeTypingIndicator();
            console.error("Error sending message to backend:", error);
            // Display a user-friendly error message for network issues
            addMessageToChat("AI", "Sorry, I couldn't connect to the server. Please ensure it's running and check your network connection.");
        } finally {
            // This block always runs after try/catch, regardless of success or failure
            // Ensure send button is re-enabled
            if (sendButton) sendButton.disabled = false;
        }
    }
}); // End of DOMContentLoaded listener