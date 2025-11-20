let selectedCategories = [];

// Load categories on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadCategories();
    setupEventListeners();
});

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();
        
        const container = document.getElementById('categoriesContainer');
        container.innerHTML = '';
        
        data.categories.forEach(category => {
            const div = document.createElement('div');
            div.className = 'category-item';
            div.innerHTML = `
                <input type="checkbox" id="cat-${category.name}" value="${category.name}">
                <span class="icon">${category.icon}</span>
                <span class="name">${category.name}</span>
            `;
            
            div.addEventListener('click', (e) => {
                if (e.target.tagName !== 'INPUT') {
                    const checkbox = div.querySelector('input');
                    checkbox.checked = !checkbox.checked;
                }
                toggleCategory(category.name, div);
            });
            
            container.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
        showError('Failed to load categories. Please refresh the page.');
    }
}

function toggleCategory(categoryName, element) {
    const checkbox = element.querySelector('input');
    
    if (checkbox.checked) {
        element.classList.add('selected');
        if (!selectedCategories.includes(categoryName)) {
            selectedCategories.push(categoryName);
        }
    } else {
        element.classList.remove('selected');
        selectedCategories = selectedCategories.filter(c => c !== categoryName);
    }
}

function setupEventListeners() {
    const fetchBtn = document.getElementById('fetchBtn');
    fetchBtn.addEventListener('click', fetchAndSummarize);
}

async function fetchAndSummarize() {
    const articleCount = parseInt(document.getElementById('articleCount').value);
    const fetchBtn = document.getElementById('fetchBtn');
    const btnText = fetchBtn.querySelector('.btn-text');
    const spinner = fetchBtn.querySelector('.spinner');
    
    // Validation
    if (selectedCategories.length === 0) {
        showError('Please select at least one category.');
        return;
    }
    
    if (articleCount < 1 || articleCount > 50) {
        showError('Please enter a number between 1 and 50.');
        return;
    }
    
    // Show loading state
    fetchBtn.disabled = true;
    btnText.textContent = 'Fetching...';
    spinner.style.display = 'inline-block';
    
    try {
        const response = await fetch('/api/fetch-and-summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                categories: selectedCategories,
                max_articles: articleCount
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch articles');
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to fetch and summarize articles. Please try again.');
    } finally {
        // Reset button state
        fetchBtn.disabled = false;
        btnText.textContent = 'Fetch & Summarize';
        spinner.style.display = 'none';
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const articlesContainer = document.getElementById('articlesContainer');
    const countDisplay = document.getElementById('articleCountDisplay');
    
    resultsSection.style.display = 'block';
    countDisplay.textContent = data.count;
    articlesContainer.innerHTML = '';
    
    if (data.results && data.results.length > 0) {
        data.results.forEach(article => {
            const articleCard = createArticleCard(article);
            articlesContainer.appendChild(articleCard);
        });
        
        // Smooth scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        articlesContainer.innerHTML = '<p style="text-align: center; color: #666;">No articles found for the selected categories.</p>';
    }
}

function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = 'article-card';
    
    const publishedDate = article.published ? new Date(article.published).toLocaleDateString() : 'N/A';
    
    card.innerHTML = `
        <div class="article-header">
            <h3 class="article-title">${article.title}</h3>
            <span class="article-category">${article.category || 'General'}</span>
        </div>
        <div class="article-meta">
            <span class="article-source">📡 ${article.source}</span>
            <span class="article-date">📅 ${publishedDate}</span>
        </div>
        <p class="article-summary">${article.summary}</p>
        <a href="${article.url}" target="_blank" class="article-link">Read full article →</a>
    `;
    
    return card;
}

function showError(message) {
    const resultsSection = document.getElementById('resultsSection');
    const articlesContainer = document.getElementById('articlesContainer');
    
    resultsSection.style.display = 'block';
    articlesContainer.innerHTML = `<div class="error-message">${message}</div>`;
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}
