document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchResultsContainer = document.getElementById('search-results-container');

    // Function to create a document preview card
    function createDocumentCard(document) {
        const card = document.createElement('div');
        card.className = 'document-card';

        // Create preview image container
        const previewContainer = document.createElement('div');
        previewContainer.className = 'document-preview';

        // Create preview image
        const previewImage = document.createElement('img');
        previewImage.src = document.previewUrl || 'assets/images/document-placeholder.png';
        previewImage.alt = document.title;
        previewImage.className = 'document-preview-image';

        // Create document info container
        const infoContainer = document.createElement('div');
        infoContainer.className = 'document-info';

        // Create document title
        const title = document.createElement('h3');
        title.className = 'document-title';
        title.textContent = document.title;

        // Create document description
        const description = document.createElement('p');
        description.className = 'document-description';
        description.textContent = document.description;

        // Create download button
        const downloadButton = document.createElement('a');
        downloadButton.href = document.downloadUrl;
        downloadButton.className = 'btn btn-download';
        downloadButton.textContent = 'Download';

        // Assemble the card
        previewContainer.appendChild(previewImage);
        infoContainer.appendChild(title);
        infoContainer.appendChild(description);
        infoContainer.appendChild(downloadButton);

        card.appendChild(previewContainer);
        card.appendChild(infoContainer);

        return card;
    }

    // Function to display search results
    function displaySearchResults(results) {
        if (!searchResultsContainer) return;

        // Clear previous results
        searchResultsContainer.innerHTML = '';

        if (results.length === 0) {
            searchResultsContainer.innerHTML = '<p class="no-results">No documents found matching your search.</p>';
            return;
        }

        // Create results grid
        const resultsGrid = document.createElement('div');
        resultsGrid.className = 'search-results-grid';

        // Add each document card to the grid
        results.forEach(document => {
            const card = createDocumentCard(document);
            resultsGrid.appendChild(card);
        });

        searchResultsContainer.appendChild(resultsGrid);
    }

    // Function to handle search
    async function handleSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        try {
            // Show loading state
            searchResultsContainer.innerHTML = '<div class="loading">Searching...</div>';

            // Make API call to backend
            const response = await fetch('http://localhost:5000/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });

            if (!response.ok) {
                throw new Error('Search request failed');
            }

            const data = await response.json();
            displaySearchResults(data.results);

        } catch (error) {
            console.error('Search error:', error);
            searchResultsContainer.innerHTML = '<p class="error">An error occurred while searching. Please try again.</p>';
        }
    }

    // Add event listeners
    if (searchButton) {
        searchButton.addEventListener('click', handleSearch);
    }

    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
    }
}); 