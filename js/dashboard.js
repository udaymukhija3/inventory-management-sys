// Dashboard Logic
let dashboardData = {
    products: [],
    lowStockItems: [],
    warehouses: []
};

// Initialize Dashboard
async function initDashboard() {
    await Promise.all([
        loadStats(),
        loadRecentProducts(),
        loadLowStockAlerts()
    ]);
}

// Load Statistics
async function loadStats() {
    try {
        // Get products
        const productsResponse = await api.getProducts({ pageSize: 1000 });
        const products = productsResponse.content || [];
        dashboardData.products = products;

        // Get warehouses
        const warehouses = await api.getWarehouses();
        dashboardData.warehouses = warehouses || [];

        // Get low stock items
        const lowStock = await api.getLowStockItems(20);
        dashboardData.lowStockItems = lowStock || [];

        // Calculate total value
        let totalValue = 0;
        for (const product of products) {
            if (product.price) {
                // This is simplified - in real app would get actual inventory quantities
                totalValue += parseFloat(product.price) * 10; // Assuming avg 10 units per product
            }
        }

        // Update UI
        document.getElementById('totalProducts').textContent = formatNumber(products.length);
        document.getElementById('totalValue').textContent = formatCurrency(totalValue);
        document.getElementById('lowStockItems').textContent = formatNumber(lowStock.length);
        document.getElementById('totalWarehouses').textContent = formatNumber(warehouses.length);

    } catch (error) {
        handleError(error, 'loadStats');
        // Set default values on error
        document.getElementById('totalProducts').textContent = '0';
        document.getElementById('totalValue').textContent = '$0.00';
        document.getElementById('lowStockItems').textContent = '0';
        document.getElementById('totalWarehouses').textContent = '0';
    }
}

// Load Recent Products
async function loadRecentProducts() {
    const container = document.getElementById('recentProducts');
    setLoading('recentProducts', true);

    try {
        const response = await api.getProducts({ pageSize: 5, sortBy: 'createdAt', direction: 'DESC' });
        const products = response.content || [];

        if (products.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">No products found. <a href="products.html" class="link">Add your first product</a></p>';
            return;
        }

        const tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Price</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${products.map(product => `
                        <tr>
                            <td><strong>${product.sku}</strong></td>
                            <td>${product.name}</td>
                            <td>${product.categoryName || 'Uncategorized'}</td>
                            <td>${formatCurrency(product.price)}</td>
                            <td>
                                <span class="badge ${product.isActive ? 'badge-success' : 'badge-danger'}">
                                    ${product.isActive ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = tableHTML;

    } catch (error) {
        handleError(error, 'loadRecentProducts');
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">Failed to load products</p>';
    }
}

// Load Low Stock Alerts
async function loadLowStockAlerts() {
    const container = document.getElementById('lowStockList');
    setLoading('lowStockList', true);

    try {
        const items = await api.getLowStockItems(20);

        if (!items || items.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;"><i class="fas fa-check-circle"></i> All items are well stocked!</p>';
            return;
        }

        const alertsHTML = items.slice(0, 5).map(item => `
            <div class="alert-item">
                <div class="alert-item-content">
                    <h4>${item.sku}</h4>
                    <p>Warehouse: ${item.warehouseId} • Available: ${item.availableQuantity} units</p>
                </div>
                <span class="badge ${item.availableQuantity === 0 ? 'badge-danger' : 'badge-warning'}">
                    ${item.availableQuantity === 0 ? 'Out of Stock' : 'Low Stock'}
                </span>
            </div>
        `).join('');

        container.innerHTML = alertsHTML;

    } catch (error) {
        handleError(error, 'loadLowStockAlerts');
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">Failed to load alerts</p>';
    }
}

// Refresh Dashboard
async function refreshDashboard() {
    showToast('Refreshing dashboard...', 'info');
    await initDashboard();
    showToast('Dashboard refreshed!', 'success');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

// Export for use in HTML
window.refreshDashboard = refreshDashboard;
