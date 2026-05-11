// Demo monitor — wires the index.html panels to the real backend when it's
// reachable, and falls back to a clearly-labelled preview mode when it isn't
// (e.g. when this page is hosted on Vercel without a backend behind it).

const FOCUS_SKU = 'LAPTOP-001';
const FOCUS_WAREHOUSE = 'WAREHOUSE-001';

const FLOW_STEPS = [
    { label: 'Source',    name: 'Inventory Service',  desc: 'Spring Boot · Postgres · transactional writes' },
    { label: 'Transport', name: 'Kafka',              desc: 'Topic: inventory-events' },
    { label: 'ETL',       name: 'Data Pipeline',      desc: 'Python consumer · feature engineering' },
    { label: 'Storage',   name: 'Postgres + Redis',   desc: 'analytics.current_metrics · cache' },
    { label: 'Serving',   name: 'Analytics Service',  desc: 'FastAPI · /velocity endpoint' }
];

const ENDPOINTS = [
    { method: 'GET',  url: '/api/v1/inventory/LAPTOP-001/WAREHOUSE-001',                                    note: 'Inventory state for the focus SKU' },
    { method: 'POST', url: '/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=1',    note: 'Records one sale (Basic Auth: demo_user / demo_pass)' },
    { method: 'GET',  url: '/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30',            note: 'Velocity metrics derived from the pipeline' },
    { method: 'GET',  url: '/api/v1/analytics/trend/LAPTOP-001/WAREHOUSE-001',                              note: 'Trend forecast (analytics service)' },
    { method: 'GET',  url: '/health/',                                                                     note: 'Analytics liveness' },
    { method: 'GET',  url: '/health/detailed',                                                             note: 'Analytics dependencies + version' }
];

const STACK = [
    { layer: 'Inventory service',  tech: 'Spring Boot, Java 17',         port: '8080', surface: '/swagger-ui/index.html' },
    { layer: 'Analytics service',  tech: 'FastAPI, Python 3.11',         port: '8000', surface: '/api/docs' },
    { layer: 'Data pipeline',      tech: 'Python, Kafka consumer',       port: '—',    surface: 'Background worker' },
    { layer: 'Database',           tech: 'PostgreSQL 14',                port: '5432', surface: 'Schemas: public, analytics' },
    { layer: 'Cache',              tech: 'Redis 7',                      port: '6379', surface: 'metrics:{sku}:{warehouseId}' },
    { layer: 'Streaming',          tech: 'Kafka + Zookeeper',            port: '9093', surface: 'Topic: inventory-events' },
    { layer: 'Frontend',           tech: 'Static HTML/JS via Nginx',     port: '3000', surface: 'This page' },
    { layer: 'Monitoring',         tech: 'Prometheus + Grafana',         port: '9090 / 3001', surface: '/api/health' }
];

const PREVIEW_DATA = {
    inventory: {
        sku: FOCUS_SKU,
        warehouseId: FOCUS_WAREHOUSE,
        availableQuantity: 41,
        reservedQuantity: 4,
        totalQuantity: 45,
        reorderPoint: 25,
        updatedAt: new Date(Date.now() - 1000 * 60 * 6).toISOString()
    },
    velocity: {
        sku: FOCUS_SKU,
        warehouse_id: FOCUS_WAREHOUSE,
        velocity_7d: 3.2,
        velocity_30d: 2.8,
        total_sales: 84,
        average_daily_sales: 2.8,
        period_days: 30
    }
};

const state = {
    isPreviewMode: false,
    backendReachable: false,
    inventoryHealthy: false,
    analyticsHealthy: false
};

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('triggerDemoSale').addEventListener('click', triggerDemoSale);
    document.getElementById('refreshDemo').addEventListener('click', refreshDemo);

    renderFlow();
    renderEndpoints();
    renderStack();

    await refreshDemo({ silent: true });
});

function renderFlow() {
    const el = document.getElementById('flowPanel');
    if (!el) return;
    el.innerHTML = FLOW_STEPS.map(step => `
        <div class="flow-step">
            <span class="flow-label">${escapeHtml(step.label)}</span>
            <span class="flow-name">${escapeHtml(step.name)}</span>
            <span class="flow-desc">${escapeHtml(step.desc)}</span>
        </div>
    `).join('');
}

function renderEndpoints() {
    const el = document.getElementById('endpointsPanel');
    if (!el) return;
    el.innerHTML = `
        <table class="data">
            <thead>
                <tr><th>Method</th><th>URL</th><th>Description</th></tr>
            </thead>
            <tbody>
                ${ENDPOINTS.map(e => `
                    <tr>
                        <td><span class="pill ${e.method === 'POST' ? 'pill-warn' : 'pill-info'}">${e.method}</span></td>
                        <td class="mono">${escapeHtml(e.url)}</td>
                        <td>${escapeHtml(e.note)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function renderStack() {
    const el = document.getElementById('stackPanel');
    if (!el) return;
    el.innerHTML = `
        <table class="data">
            <thead>
                <tr><th>Layer</th><th>Tech</th><th>Port</th><th>Surface</th></tr>
            </thead>
            <tbody>
                ${STACK.map(s => `
                    <tr>
                        <td>${escapeHtml(s.layer)}</td>
                        <td>${escapeHtml(s.tech)}</td>
                        <td class="mono">${escapeHtml(s.port)}</td>
                        <td>${escapeHtml(s.surface)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function refreshDemo({ silent = false } = {}) {
    if (!silent) showToast('Refreshing…', 'info', 1200);
    setLoading('focusInventoryPanel', true);
    setLoading('focusVelocityPanel', true);

    const [invResult, velResult] = await Promise.allSettled([
        api.getInventory(FOCUS_SKU, FOCUS_WAREHOUSE),
        api.getVelocity(FOCUS_SKU, FOCUS_WAREHOUSE, 30)
    ]);

    const inv = invResult.status === 'fulfilled' ? invResult.value : null;
    const vel = velResult.status === 'fulfilled' ? velResult.value : null;

    state.inventoryHealthy = !!inv;
    state.analyticsHealthy = !!vel;
    state.backendReachable = state.inventoryHealthy || state.analyticsHealthy;
    state.isPreviewMode = !state.backendReachable;

    updateModeBanner();
    updateSummary(inv, vel);
    renderFocusInventory(inv);
    renderFocusVelocity(vel);

    if (!silent) {
        if (state.backendReachable) {
            showToast('Refreshed from live backend', 'success');
        } else {
            showToast('Backend unreachable — showing preview data', 'info');
        }
    }
}

async function triggerDemoSale() {
    const button = document.getElementById('triggerDemoSale');
    button.disabled = true;
    const originalLabel = button.textContent;
    button.textContent = 'Recording sale…';

    try {
        if (state.isPreviewMode) {
            await sleep(700);
            PREVIEW_DATA.inventory.availableQuantity = Math.max(0, PREVIEW_DATA.inventory.availableQuantity - 1);
            PREVIEW_DATA.inventory.totalQuantity = Math.max(0, PREVIEW_DATA.inventory.totalQuantity - 1);
            PREVIEW_DATA.inventory.updatedAt = new Date().toISOString();
            PREVIEW_DATA.velocity.total_sales += 1;
            await refreshDemo({ silent: true });
            showToast('Preview mode: simulated a sale (no backend)', 'info');
            return;
        }

        await api.recordSale(FOCUS_SKU, FOCUS_WAREHOUSE, 1);
        showToast('Sale recorded · waiting for the pipeline…', 'success');

        // Give the consumer a moment to process the new event before we re-fetch.
        await sleep(2500);
        await refreshDemo({ silent: true });
        showToast('Refreshed after live sale', 'success');
    } catch (err) {
        console.error('triggerDemoSale failed:', err);
        showToast(err.message || 'Could not record sale', 'error', 4500);
    } finally {
        button.disabled = false;
        button.textContent = originalLabel;
    }
}

function updateModeBanner() {
    const banner = document.getElementById('modeBanner');
    const text = document.getElementById('modeBannerText');
    if (!banner || !text) return;

    if (state.isPreviewMode) {
        banner.hidden = false;
        banner.classList.remove('banner-info');
        text.textContent = 'No backend reachable at this URL. Numbers below are illustrative — run `make demo` locally for live data.';
    } else if (state.inventoryHealthy && !state.analyticsHealthy) {
        banner.hidden = false;
        banner.classList.add('banner-info');
        text.textContent = 'Inventory service reachable but analytics service is not. Velocity panel will show preview data.';
    } else if (!state.inventoryHealthy && state.analyticsHealthy) {
        banner.hidden = false;
        banner.classList.add('banner-info');
        text.textContent = 'Analytics service reachable but inventory service is not. Inventory panel will show preview data.';
    } else {
        banner.hidden = true;
    }
}

function updateSummary(inv, vel) {
    const invStatus = document.getElementById('invStatus');
    const invStatusDetail = document.getElementById('invStatusDetail');
    const anaStatus = document.getElementById('anaStatus');
    const anaStatusDetail = document.getElementById('anaStatusDetail');

    invStatus.innerHTML = state.inventoryHealthy
        ? '<span class="pill pill-success">Healthy</span>'
        : (state.isPreviewMode ? '<span class="pill pill-info">Preview</span>' : '<span class="pill pill-danger">Unreachable</span>');
    invStatusDetail.textContent = state.inventoryHealthy
        ? `Connected to inventory service`
        : (state.isPreviewMode ? 'Static fallback data' : 'No response from inventory-service');

    anaStatus.innerHTML = state.analyticsHealthy
        ? '<span class="pill pill-success">Healthy</span>'
        : (state.isPreviewMode ? '<span class="pill pill-info">Preview</span>' : '<span class="pill pill-danger">Unreachable</span>');
    anaStatusDetail.textContent = state.analyticsHealthy
        ? `Connected to analytics service`
        : (state.isPreviewMode ? 'Static fallback data' : 'No response from analytics-service');

    const effectiveInv = inv || PREVIEW_DATA.inventory;
    const effectiveVel = vel || PREVIEW_DATA.velocity;

    document.getElementById('invQty').textContent = formatNumber(effectiveInv.availableQuantity);
    document.getElementById('focusSkuLabel').textContent = effectiveInv.sku || FOCUS_SKU;
    document.getElementById('velocity7d').textContent = formatNumber(effectiveVel.velocity_7d, 2);
    document.getElementById('velocity30d').textContent = formatNumber(effectiveVel.velocity_30d, 2);
    document.getElementById('lastRefresh').textContent = formatDate(new Date().toISOString());
    document.getElementById('lastRefreshDetail').textContent = state.backendReachable ? 'Live data' : 'Preview data';
}

function renderFocusInventory(inv) {
    const el = document.getElementById('focusInventoryPanel');
    if (!el) return;

    const data = inv || PREVIEW_DATA.inventory;
    if (!data) {
        el.innerHTML = '<div class="empty-state">No inventory data available.</div>';
        return;
    }

    const isPreview = !inv;
    el.innerHTML = `
        ${isPreview ? '<div class="banner" style="margin-bottom:14px;">Showing preview data.</div>' : ''}
        <dl class="dlist">
            <dt>SKU</dt><dd>${escapeHtml(data.sku || FOCUS_SKU)}</dd>
            <dt>Warehouse</dt><dd>${escapeHtml(data.warehouseId || FOCUS_WAREHOUSE)}</dd>
            <dt>Available</dt><dd>${formatNumber(data.availableQuantity)}</dd>
            <dt>Reserved</dt><dd>${formatNumber(data.reservedQuantity)}</dd>
            <dt>Total</dt><dd>${formatNumber(data.totalQuantity)}</dd>
            ${data.reorderPoint != null ? `<dt>Reorder pt.</dt><dd>${formatNumber(data.reorderPoint)}</dd>` : ''}
            ${data.updatedAt ? `<dt>Updated</dt><dd>${escapeHtml(formatDate(data.updatedAt))} <span style="color:var(--text-muted)">(${escapeHtml(formatRelativeTime(data.updatedAt))})</span></dd>` : ''}
        </dl>
    `;
}

function renderFocusVelocity(vel) {
    const el = document.getElementById('focusVelocityPanel');
    if (!el) return;

    const data = vel || PREVIEW_DATA.velocity;
    const isPreview = !vel;
    el.innerHTML = `
        ${isPreview ? '<div class="banner" style="margin-bottom:14px;">Showing preview data.</div>' : ''}
        <dl class="dlist">
            <dt>SKU</dt><dd>${escapeHtml(data.sku || FOCUS_SKU)}</dd>
            <dt>Warehouse</dt><dd>${escapeHtml(data.warehouse_id || FOCUS_WAREHOUSE)}</dd>
            <dt>Velocity 7d</dt><dd>${formatNumber(data.velocity_7d, 2)}</dd>
            <dt>Velocity 30d</dt><dd>${formatNumber(data.velocity_30d, 2)}</dd>
            <dt>Total sales</dt><dd>${formatNumber(data.total_sales)}</dd>
            <dt>Avg daily</dt><dd>${formatNumber(data.average_daily_sales, 2)}</dd>
            <dt>Period (d)</dt><dd>${formatNumber(data.period_days)}</dd>
        </dl>
    `;
}

function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

window.triggerDemoSale = triggerDemoSale;
window.refreshDemo = refreshDemo;
