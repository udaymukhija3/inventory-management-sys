// Lightweight HTTP layer for the demo monitor.
//
// Endpoints are grouped by what's actually exposed today by the supported
// services in docker-compose.dev.yml. When the page is hosted statically
// (e.g. on Vercel) without a backend, every call here will fail; demo.js
// catches those failures and renders the page in preview mode instead.

const API_BASE_URL = (window.__APP_CONFIG__ && window.__APP_CONFIG__.API_BASE_URL) || '/api/v1';
const DEMO_USERNAME = (window.__APP_CONFIG__ && window.__APP_CONFIG__.INVENTORY_USERNAME) || 'demo_user';
const DEMO_PASSWORD = (window.__APP_CONFIG__ && window.__APP_CONFIG__.INVENTORY_PASSWORD) || 'demo_pass';

function buildAuthHeader(user, pass) {
    try {
        return `Basic ${btoa(`${user}:${pass}`)}`;
    } catch (e) {
        return '';
    }
}

const INVENTORY_AUTH_HEADER = buildAuthHeader(DEMO_USERNAME, DEMO_PASSWORD);

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, { method = 'GET', headers = {}, body, withAuth = false, timeoutMs = 5000 } = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const finalHeaders = { 'Accept': 'application/json', ...headers };
        if (withAuth && INVENTORY_AUTH_HEADER) {
            finalHeaders['Authorization'] = INVENTORY_AUTH_HEADER;
        }
        if (body !== undefined && !finalHeaders['Content-Type']) {
            finalHeaders['Content-Type'] = 'application/json';
        }

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
            const response = await fetch(url, {
                method,
                headers: finalHeaders,
                body: body !== undefined ? JSON.stringify(body) : undefined,
                signal: controller.signal,
                credentials: 'omit'
            });
            if (!response.ok) {
                const detail = await response.text().catch(() => '');
                const err = new Error(`HTTP ${response.status}${detail ? `: ${detail.slice(0, 200)}` : ''}`);
                err.status = response.status;
                throw err;
            }
            if (response.status === 204) return null;
            const text = await response.text();
            if (!text) return null;
            try { return JSON.parse(text); } catch { return text; }
        } finally {
            clearTimeout(timer);
        }
    }

    // --- Inventory service (Spring Boot) ---
    async getInventory(sku, warehouseId) {
        return this.request(`/inventory/${encodeURIComponent(sku)}/${encodeURIComponent(warehouseId)}`, { withAuth: true });
    }

    async recordSale(sku, warehouseId, quantity = 1) {
        const params = new URLSearchParams({ sku, warehouseId, quantity: String(quantity) });
        return this.request(`/inventory/sale?${params.toString()}`, { method: 'POST', withAuth: true });
    }

    // --- Analytics service (FastAPI) ---
    async getVelocity(sku, warehouseId, periodDays = 30) {
        const params = new URLSearchParams({ period_days: String(periodDays) });
        return this.request(`/analytics/velocity/${encodeURIComponent(sku)}/${encodeURIComponent(warehouseId)}?${params.toString()}`);
    }

    async getTrend(sku, warehouseId) {
        return this.request(`/analytics/trend/${encodeURIComponent(sku)}/${encodeURIComponent(warehouseId)}`);
    }
}

const api = new APIClient(API_BASE_URL);

// --- Generic UI helpers used by demo.js ---

function showToast(message, type = 'info', durationMs = 2800) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('show'), durationMs);
}

function formatNumber(num, fractionDigits = 0) {
    if (num === null || num === undefined || Number.isNaN(num)) return '—';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: fractionDigits,
        maximumFractionDigits: fractionDigits
    }).format(num);
}

function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    }).format(date);
}

function formatRelativeTime(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return '—';
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

function setLoading(elementId, isLoading) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (isLoading) {
        el.innerHTML = '<div class="loading-state">Loading…</div>';
    }
}

window.api = api;
window.showToast = showToast;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.formatRelativeTime = formatRelativeTime;
window.setLoading = setLoading;
