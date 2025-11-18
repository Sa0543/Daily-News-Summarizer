const API_BASE_URL = 'http://localhost:8000';

// Categories with emoji icons
const categories = [
    { name: 'General', icon: '📰' },
    { name: 'Politics', icon: '🏛️' },
    { name: 'Sports', icon: '⚽' },
    { name: 'Business', icon: '💼' },
    { name: 'Technology', icon: '💻' },
    { name: 'Education', icon: '📚' },
    { name: 'Entertainment', icon: '🎬' },
    { name: 'International', icon: '🌍' },
    { name: 'Health', icon: '🏥' }
];

// DOM Elements
const categoryGrid = document.getElementById('category-grid');
const maxArticlesInput = document.getElementById('max-articles');
const articleCountSpan = document.getElementById('article-count');
const fetchBtn = document.getElementById('fetch-btn');
const newsGrid = document.getElementById('news-grid');
const searchBtn = document.getElementById('search-btn');
const searchQuery = document.getElementById('search-query');
const searchResultsCount = document.getElementById('search-results-count');
const searchCountSpan = document.getElementById('search-count');
const searchResults = document.getElementById('search-results');
const summarizeBtn = document.getElementById('summarize-btn');
const textInput = document.getElementById('text-input');
const summaryResult = document.getElementById('summary-result');
const summaryText = document.getElementById('summary-text');

// Initialize categories with icons
function initCategories() {
    categories.forEach(cat => {
        const div = document.createElement('div');
        div.className = 'category-item';
        div.innerHTML = `
            <input type="checkbox" id="cat-${cat.name}" value="${cat.name}" checked>
            <label for="cat-${cat.name}">
                <span class="category-icon">${cat.icon}</span>
                <span class="category-name">${cat.name}</span>
            </label>
        `;
        categoryGrid.appendChild(div);
    });
}

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
    });
});

// Article count slider
maxArticlesInput.addEventListener('input', (e) => {
    articleCountSpan.textContent = e.target.value;
});

// Search count slider
searchResultsCount.addEventListener('input', (e) => {
    searchCountSpan.textContent = e.target.value;
});

// Fetch News
fetchBtn.addEventListener('click', async () => {
    const selectedCategories = Array.from(document.querySelectorAll('#category-grid input:checked')).map(cb => cb.value);
    const maxArticles = parseInt(maxArticlesInput.value);

    if (selectedCategories.length === 0) {
        alert('Please select at least one category');
        return;
    }

    setLoading(fetchBtn, true);
    newsGrid.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE_URL}/fetch-news`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                categories: selectedCategories,
                max_articles: maxArticles
            })
        });

        const data = await response.json();
        displayNews(data.articles);
    } catch (error) {
        console.error('Error:', error);
        newsGrid.innerHTML = '<div class="empty-state">Failed to fetch news. Please try again.</div>';
    } finally {
        setLoading(fetchBtn, false);
    }
});

// Display News
function displayNews(articles) {
    if (articles.length === 0) {
        newsGrid.innerHTML = '<div class="empty-state">No articles found</div>';
        return;
    }

    newsGrid.innerHTML = articles.map(article => {
        const categoryInfo = categories.find(c => c.name === article.category);
        const categoryIcon = categoryInfo ? categoryInfo.icon : '📰';
        
        return `
        <div class="news-card">
            ${article.image ? `<img src="${article.image}" alt="${article.title}" class="news-card-image" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23667eea33%22 width=%22100%22 height=%22100%22/%3E%3C/svg%3E'">` : '<div class="news-card-image"></div>'}
            <div class="news-card-content">
                <span class="news-card-category">${categoryIcon} ${article.category}</span>
                <h3 class="news-card-title">${article.title}</h3>
                <div class="news-card-meta">
                    <span>📰 ${article.source}</span>
                    <span>📅 ${new Date(article.published).toLocaleDateString()}</span>
                </div>
                <p class="news-card-description">${truncate(article.description || article.content, 150)}</p>
                <a href="${article.url}" target="_blank" class="news-card-link">Read More →</a>
            </div>
        </div>
    `}).join('');
}

// Search Articles
searchBtn.addEventListener('click', async () => {
    const query = searchQuery.value.trim();
    const k = parseInt(searchResultsCount.value);

    if (!query) {
        alert('Please enter a search query');
        return;
    }

    setLoading(searchBtn, true);
    searchResults.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, k })
        });

        const data = await response.json();
        displaySearchResults(data.results);
    } catch (error) {
        console.error('Error:', error);
        searchResults.innerHTML = '<div class="empty-state">Search failed. Please try again.</div>';
    } finally {
        setLoading(searchBtn, false);
    }
});

// Display Search Results
function displaySearchResults(results) {
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="empty-state">No results found</div>';
        return;
    }

    searchResults.innerHTML = results.map(result => `
        <div class="search-result-card">
            <h3 class="search-result-title">${result.title}</h3>
            <p class="search-result-snippet">${result.snippet}</p>
            <div class="search-result-meta">
                <span>📰 ${result.source}</span>
                ${result.url ? `<a href="${result.url}" target="_blank" class="news-card-link">Read Full Article →</a>` : ''}
            </div>
        </div>
    `).join('');
}

// Summarize Text
summarizeBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    const summaryLength = document.querySelector('input[name="summary-length"]:checked').value;

    if (!text) {
        alert('Please enter text to summarize');
        return;
    }

    setLoading(summarizeBtn, true);
    summaryResult.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, summary_length: summaryLength })
        });

        const data = await response.json();
        summaryText.textContent = data.summary;
        summaryResult.style.display = 'block';
    } catch (error) {
        console.error('Error:', error);
        alert('Summarization failed. Please try again.');
    } finally {
        setLoading(summarizeBtn, false);
    }
});

// Helper Functions
function setLoading(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const loader = button.querySelector('.loader');
    
    if (isLoading) {
        button.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'inline-block';
    } else {
        button.disabled = false;
        btnText.style.display = 'inline';
        loader.style.display = 'none';
    }
}

function truncate(text, length) {
    return text.length > length ? text.substring(0, length) + '...' : text;
}

// Initialize
initCategories();
