const API_BASE_URL = (window.__APP_CONFIG__ && window.__APP_CONFIG__.API_BASE_URL) || '/api/v1';
const DEMO_CREDENTIALS = 'demo_user:demo_pass';

function buildAuthHeader(credentials) {
    try {
        return `Basic ${btoa(credentials)}`;
    } catch (error) {
        console.error('Failed to encode demo credentials:', error);
        return '';
    }
}

const DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': buildAuthHeader(DEMO_CREDENTIALS)
};

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                ...DEFAULT_HEADERS,
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

    async recordSale(sku, warehouseId, quantity) {
        return this.request(`/inventory/sale?sku=${sku}&warehouseId=${warehouseId}&quantity=${quantity}`, {
            method: 'POST'
        });
    }
    async getInventoryVelocity(sku, warehouseId, periodDays = 30) {
        return this.request(`/analytics/velocity/${sku}/${warehouseId}?period_days=${periodDays}`);
    }

    async getDemoOverview(sku = 'LAPTOP-001', warehouseId = 'WAREHOUSE-001', runsLimit = 5, metricsLimit = 8) {
        const queryString = new URLSearchParams({
            sku,
            warehouse_id: warehouseId,
            runs_limit: runsLimit,
            metrics_limit: metricsLimit
        }).toString();
        return this.request(`/analytics/demo/overview?${queryString}`);
    }

    async getDemoRuns(limit = 10) {
        return this.request(`/analytics/demo/runs?limit=${limit}`);
    }

    async getDemoCurrentMetrics(limit = 10) {
        return this.request(`/analytics/demo/current-metrics?limit=${limit}`);
    }

    async getLatestBacktest() {
        return this.request('/analytics/backtest/latest');
    }
}

const api = new APIClient(API_BASE_URL);

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return new Intl.NumberFormat('en-US').format(num);
}

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

function formatRelativeTime(dateString) {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    const seconds = Math.round((date.getTime() - Date.now()) / 1000);
    const formatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    const ranges = [
        { limit: 60, unit: 'second' },
        { limit: 3600, unit: 'minute', divisor: 60 },
        { limit: 86400, unit: 'hour', divisor: 3600 },
        { limit: 604800, unit: 'day', divisor: 86400 }
    ];

    for (const range of ranges) {
        if (Math.abs(seconds) < range.limit) {
            const value = range.divisor ? Math.round(seconds / range.divisor) : seconds;
            return formatter.format(value, range.unit);
        }
    }

    return formatDate(dateString);
}

function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showToast(error.message || 'An error occurred', 'error');
}

window.api = api;
window.showToast = showToast;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.formatRelativeTime = formatRelativeTime;
window.handleError = handleError;
window.setLoading = setLoading;
