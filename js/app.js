// API Configuration
const API_BASE_URL = 'http://localhost:9000/api/v1';

// API Client
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `HTTP error! status: ${response.status}`);
            }

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Products
    async getProducts(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/products${queryString ? '?' + queryString : ''}`);
    }

    async getProduct(id) {
        return this.request(`/products/${id}`);
    }

    async getProductBySku(sku) {
        return this.request(`/products/sku/${sku}`);
    }

    async createProduct(data) {
        return this.request('/products', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProduct(id, data) {
        return this.request(`/products/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteProduct(id) {
        return this.request(`/products/${id}`, {
            method: 'DELETE'
        });
    }

    async searchProducts(searchTerm, params = {}) {
        const queryString = new URLSearchParams({ searchTerm, ...params }).toString();
        return this.request(`/products/search?${queryString}`);
    }

    // Inventory
    async getInventory(sku, warehouseId) {
        return this.request(`/inventory/${sku}/${warehouseId}`);
    }

    async adjustInventory(data) {
        return this.request('/inventory/adjust', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async recordSale(sku, warehouseId, quantity) {
        return this.request(`/inventory/sale?sku=${sku}&warehouseId=${warehouseId}&quantity=${quantity}`, {
            method: 'POST'
        });
    }

    async recordReceipt(sku, warehouseId, quantity) {
        return this.request(`/inventory/receipt?sku=${sku}&warehouseId=${warehouseId}&quantity=${quantity}`, {
            method: 'POST'
        });
    }

    async getLowStockItems(threshold = 10) {
        return this.request(`/inventory/low-stock?threshold=${threshold}`);
    }

    // Categories
    async getCategories() {
        return this.request('/categories');
    }

    async createCategory(data) {
        return this.request('/categories', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Warehouses
    async getWarehouses() {
        return this.request('/warehouses');
    }

    async createWarehouse(data) {
        return this.request('/warehouses', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Analytics
    async getInventoryVelocity(sku, warehouseId, periodDays = 30) {
        return this.request(`/analytics/velocity/${sku}/${warehouseId}?period_days=${periodDays}`);
    }

    async getWarehouseSummary(warehouseId) {
        return this.request(`/analytics/warehouse-summary/${warehouseId}`);
    }
}

// Initialize API client
const api = new APIClient(API_BASE_URL);

// Toast Notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Format Currency
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format Number
function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return new Intl.NumberFormat('en-US').format(num);
}

// Format Date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Error Handler
function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showToast(error.message || 'An error occurred', 'error');
}

// Loading State
function setLoading(elementId, isLoading) {
    const element = document.getElementById(elementId);
    if (!element) return;

    if (isLoading) {
        element.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    }
}

// Export for use in other scripts
window.api = api;
window.showToast = showToast;
window.formatCurrency = formatCurrency;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.handleError = handleError;
window.setLoading = setLoading;
