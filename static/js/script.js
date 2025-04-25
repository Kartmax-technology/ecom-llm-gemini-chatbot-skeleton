// Fix for NaN values in JSON
function fixNaNInJson(jsonString) {
    // Replace NaN with null in the JSON string
    return jsonString.replace(/:\s*NaN\b/g, ': null');
}

// Constants
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const productsGrid = document.getElementById('productsGrid');
const typingIndicator = document.getElementById('typingIndicator');
const filterBtn = document.getElementById('filterBtn');
const filterPanel = document.getElementById('filterPanel');
const closeFilter = document.getElementById('closeFilter');
const applyFilters = document.getElementById('applyFilters');
const productCount = document.getElementById('productCount');
const colorFilters = document.getElementById('colorFilters');
const brandFilters = document.getElementById('brandFilters');
const minPrice = document.getElementById('minPrice');
const maxPrice = document.getElementById('maxPrice');

// Generate a random user ID for this session
const userId = 'user_' + Math.random().toString(36).substring(2, 15);

// WebSocket Connection
let socket = null;
let isConnected = false;

// Products data
let allProducts = [];
let filteredProducts = [];
let currentFilters = {
    gender: null,
    color: null,
    minPrice: null,
    maxPrice: null,
    brand: null
};

// Helper Functions
function formatPrice(priceString) {
    if (!priceString) return "Price not available";
    return priceString;
}

function getImageUrl(product) {
    if (product.image_link) return product.image_link;
    return "https://placehold.co/400x300?text=No+Image";
}

function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    typingIndicator.style.display = 'inline-flex';
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// WebSocket connection with NaN handling
function connectWebSocket() {
    try {
        console.log("Attempting to connect to WebSocket...");
        // Create WebSocket connection
        socket = new WebSocket(`${WS_BASE_URL}/ws/chat/${userId}`);

        socket.onopen = function(e) {
            console.log('WebSocket connection established');
            isConnected = true;
        };

        socket.onclose = function(event) {
            console.log('WebSocket connection closed with code:', event.code);
            isConnected = false;

            // Try to reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            isConnected = false;
        };

        socket.onmessage = function(event) {
            try {
                // Fix NaN values in the JSON string
                const fixedData = fixNaNInJson(event.data);
                const data = JSON.parse(fixedData);
                handleResponse(data);
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
                hideTypingIndicator();

                // Try to extract just the response text
                try {
                    const responseMatch = event.data.match(/"response":"([^"]+)"/);
                    if (responseMatch && responseMatch[1]) {
                        addMessage(responseMatch[1], 'assistant');
                    }
                } catch (err) {
                    addMessage("I received your message but had trouble processing the response.", 'assistant');
                }
            }
        };
    } catch (err) {
        console.error('Error creating WebSocket connection:', err);
        isConnected = false;
    }
}

async function sendMessage(message) {
    if (message.trim() === '') return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    userInput.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Try to use WebSocket if connected
    if (isConnected && socket.readyState === WebSocket.OPEN) {
        try {
            socket.send(JSON.stringify({
                message: message
            }));
        } catch (err) {
            console.error("Error sending via WebSocket:", err);
            fallbackToREST(message);
        }
    } else {
        fallbackToREST(message);
    }
}

async function fallbackToREST(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });

        if (response.ok) {
            const rawText = await response.text();

            // Fix NaN values in the response
            const fixedText = fixNaNInJson(rawText);

            // Parse the fixed JSON
            const data = JSON.parse(fixedText);
            handleResponse(data);
        } else {
            throw new Error('Failed to get response: ' + response.status);
        }
    } catch (error) {
        console.error('Error sending message via REST:', error);
        hideTypingIndicator();
        addMessage('Sorry, I had trouble connecting to the server. Please try again.', 'assistant');
    }
}

function handleResponse(data) {
    // Hide typing indicator
    hideTypingIndicator();

    // Add assistant message to chat
    if (data.response) {
        addMessage(data.response, 'assistant');
    }

    // Update product list
    if (data.products) {
        displayProducts(data.products);
    }
}

function displayProducts(products) {
    // Store all products globally
    allProducts = products || [];
    filteredProducts = [...allProducts];

    // Update the product count
    productCount.textContent = filteredProducts.length;

    // Clear products grid
    productsGrid.innerHTML = '';

    // If no products, show empty state
    if (!filteredProducts || filteredProducts.length === 0) {
        productsGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <h3>No Products Found</h3>
                <p>Try a different search or adjust your filters</p>
                <div class="suggestion-chips<div class="suggestion-chips">
                    <div class="suggestion-chip" onclick="suggestQuery('Show men\'s shoes')">
                        <i class="fas fa-male"></i> Men's Shoes
                    </div>
                    <div class="suggestion-chip" onclick="suggestQuery('Show women\'s sandals')">
                        <i class="fas fa-female"></i> Women's Sandals
                    </div>
                </div>
            </div>
        `;
        return;
    }

    // Populate color and brand filters
    populateFilters();

    // Add each product (limiting to max 20)
    const productsToShow = filteredProducts.slice(0, 20);

    productsToShow.forEach(product => {
        const productCard = document.createElement('div');
        productCard.classList.add('product-card');

        // Extract price for discount calculation
        let currentPrice = "";
        let originalPrice = "";
        let discountBadge = "";

        if (product.price) {
            const priceMatch = product.price.match(/(\d+)/);
            if (priceMatch) {
                const priceValue = parseInt(priceMatch[0]);
                currentPrice = product.price;

                // For demo, randomly add discounts to some products
                if (Math.random() > 0.7) {
                    const discountPercent = Math.floor(Math.random() * 20) + 5;
                    const originalValue = Math.floor(priceValue * (100 / (100 - discountPercent)));
                    originalPrice = `${originalValue} INR`;
                    discountBadge = `<div class="discount-badge">${discountPercent}% OFF</div>`;
                }
            }
        }

        // Format gender display
        let genderText = "";
        if (product.gender === "male") {
            genderText = "Men's";
        } else if (product.gender === "female") {
            genderText = "Women's";
        }

        // Get availability status
        const inStock = product.availability === "In stock";
        const stockClass = inStock ? "in-stock" : "out-of-stock";
        const stockText = inStock ? "In Stock" : "Out of Stock";

        // Extract size information
        let sizeChips = "";
        if (product.size) {
            const sizeText = product.size;
            sizeChips = `<div class="size-chips">
                <span class="size-chip">${sizeText}</span>
            </div>`;
        }

        productCard.innerHTML = `
            <div class="product-image">
                <img src="${getImageUrl(product)}" alt="${product.title}" 
                     onerror="this.src='https://placehold.co/400x300?text=No+Image'">
                ${genderText ? `<div class="gender-badge">${genderText}</div>` : ''}
                ${discountBadge}
            </div>
            <div class="product-info">
                <div class="product-brand">${product.brand || 'Brand'}</div>
                <div class="product-name">${product.title || product.description || 'Product Name'}</div>
                <div class="product-price">
                    <span class="current-price">${currentPrice}</span>
                    ${originalPrice ? `<span class="original-price">${originalPrice}</span>` : ''}
                </div>
                ${sizeChips}
                <div class="availability">
                    <div class="stock-status ${stockClass}">
                        <i class="fas fa-${inStock ? 'circle-check' : 'circle-xmark'}"></i>
                        <span>${stockText}</span>
                    </div>
                </div>
                <div class="product-action">
                    <a href="${product.link || '#'}" target="_blank" class="view-button">
                        <i class="fas fa-external-link-alt"></i> View Details
                    </a>
                    <button class="cart-button">
                        <i class="fas fa-shopping-cart"></i>
                    </button>
                </div>
            </div>
        `;

        // Add click event to expand product info
        productCard.addEventListener('click', (e) => {
            // Don't trigger if they clicked a button or link
            if (e.target.closest('.view-button') || e.target.closest('.cart-button')) return;

            suggestQuery(`Tell me more about ${product.title || 'this product'}`);
        });

        productsGrid.appendChild(productCard);
    });
}

function populateFilters() {
    // Get unique colors
    const colors = [...new Set(allProducts.map(p => p.colour).filter(Boolean))];
    colorFilters.innerHTML = '';
    colors.slice(0, 10).forEach(color => {
        const colorOption = document.createElement('div');
        colorOption.classList.add('filter-option');
        colorOption.setAttribute('data-filter', 'color');
        colorOption.setAttribute('data-value', color);
        if (currentFilters.color === color) {
            colorOption.classList.add('active');
        }
        colorOption.textContent = color;
        colorOption.addEventListener('click', toggleFilter);
        colorFilters.appendChild(colorOption);
    });

    // Get unique brands
    const brands = [...new Set(allProducts.map(p => p.brand).filter(Boolean))];
    brandFilters.innerHTML = '';
    brands.slice(0, 10).forEach(brand => {
        const brandOption = document.createElement('div');
        brandOption.classList.add('filter-option');
        brandOption.setAttribute('data-filter', 'brand');
        brandOption.setAttribute('data-value', brand);
        if (currentFilters.brand === brand) {
            brandOption.classList.add('active');
        }
        brandOption.textContent = brand;
        brandOption.addEventListener('click', toggleFilter);
        brandFilters.appendChild(brandOption);
    });
}

function toggleFilter(e) {
    const filter = e.target.getAttribute('data-filter');
    const value = e.target.getAttribute('data-value');

    // Toggle active state visually
    if (filter === 'gender' || filter === 'color' || filter === 'brand') {
        // Remove active class from all options in this filter group
        document.querySelectorAll(`.filter-option[data-filter="${filter}"]`).forEach(opt => {
            opt.classList.remove('active');
        });

        // Toggle the current filter
        if (currentFilters[filter] === value) {
            currentFilters[filter] = null; // Deselect if already selected
        } else {
            e.target.classList.add('active');
            currentFilters[filter] = value; // Select new value
        }
    }
}

function applyProductFilters() {
    // Start with all products
    filteredProducts = [...allProducts];

    // Apply gender filter
    if (currentFilters.gender) {
        filteredProducts = filteredProducts.filter(p => p.gender === currentFilters.gender);
    }

    // Apply color filter
    if (currentFilters.color) {
        filteredProducts = filteredProducts.filter(p => p.colour === currentFilters.color);
    }

    // Apply brand filter
    if (currentFilters.brand) {
        filteredProducts = filteredProducts.filter(p => p.brand === currentFilters.brand);
    }

    // Apply price filter
    if (currentFilters.minPrice) {
        filteredProducts = filteredProducts.filter(p => {
            const priceMatch = p.price?.match(/(\d+)/);
            if (priceMatch) {
                return parseInt(priceMatch[0]) >= currentFilters.minPrice;
            }
            return true;
        });
    }
    if (currentFilters.maxPrice) {
        filteredProducts = filteredProducts.filter(p => {
            const priceMatch = p.price?.match(/(\d+)/);
            if (priceMatch) {
                return parseInt(priceMatch[0]) <= currentFilters.maxPrice;
            }
            return true;
        });
    }

    // Update display
    displayProducts(filteredProducts);
}

function suggestQuery(query) {
    userInput.value = query;
    sendMessage(query);
}

// Initialize
function initialize() {
    // Try to establish WebSocket connection
    connectWebSocket();

    // Add event listeners for chat input
    sendButton.addEventListener('click', function() {
        const message = userInput.value;
        if (message && message.trim()) {
            sendMessage(message);
        }
    });

    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const message = userInput.value;
            if (message && message.trim()) {
                sendMessage(message);
            }
            e.preventDefault();
        }
    });

    // Filter panel events
    filterBtn.addEventListener('click', function() {
        filterPanel.classList.add('show');
    });

    closeFilter.addEventListener('click', function() {
        filterPanel.classList.remove('show');
    });

    applyFilters.addEventListener('click', function() {
        // Get price values
        currentFilters.minPrice = minPrice.value ? parseInt(minPrice.value) : null;
        currentFilters.maxPrice = maxPrice.value ? parseInt(maxPrice.value) : null;

        applyProductFilters();
        filterPanel.classList.remove('show');
    });

    // Close filter panel when clicking outside
    document.addEventListener('click', (e) => {
        if (!filterPanel.contains(e.target) && e.target !== filterBtn && filterPanel.classList.contains('show')) {
            filterPanel.classList.remove('show');
        }
    });
}

// Expose suggestQuery to global scope for onclick handlers
window.suggestQuery = suggestQuery;

// Start the application
document.addEventListener('DOMContentLoaded', initialize);