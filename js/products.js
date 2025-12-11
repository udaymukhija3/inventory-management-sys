// Products Page Logic
let currentEditId = null;
let allProducts = [];
let categories = [];

// Initialize Products Page
async function initProductsPage() {
    await loadCategories();
    await loadProducts();
}

// Load Categories
async function loadCategories() {
    try {
        categories = await api.getCategories();
        const select = document.getElementById('categoryId');
        if (select) {
            select.innerHTML = '<option value="">Select category...</option>' +
                categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load Products
async function loadProducts() {
    const container = document.getElementById('productsTable');
    setLoading('productsTable', true);

    try {
        const response = await api.getProducts({ pageSize: 100, sortBy: 'name', direction: 'ASC' });
        allProducts = response.content || [];

        displayProducts(allProducts);
        updateProductCount(allProducts.length);

    } catch (error) {
        handleError(error, 'loadProducts');
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">Failed to load products</p>';
    }
}

// Display Products
function displayProducts(products) {
    const container = document.getElementById('productsTable');

    if (products.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">No products found</p>';
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
                    <th>Actions</th>
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
                        <td>
                            <button class="btn btn-secondary" style="padding: 0.5rem 1rem; margin-right: 0.5rem;" 
                                    onclick="editProduct(${product.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-secondary" style="padding: 0.5rem 1rem; background: var(--danger);" 
                                    onclick="deleteProduct(${product.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

// Update Product Count
function updateProductCount(count) {
    const countElement = document.getElementById('productCount');
    if (countElement) {
        countElement.textContent = `${count} product${count !== 1 ? 's' : ''}`;
    }
}

// Handle Search
let searchTimeout;
function handleSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();

        if (!searchTerm) {
            displayProducts(allProducts);
            updateProductCount(allProducts.length);
            return;
        }

        const filtered = allProducts.filter(product =>
            product.name.toLowerCase().includes(searchTerm) ||
            product.sku.toLowerCase().includes(searchTerm) ||
            (product.description && product.description.toLowerCase().includes(searchTerm))
        );

        displayProducts(filtered);
        updateProductCount(filtered.length);
    }, 300);
}

// Open Product Modal
function openProductModal(productId = null) {
    const modal = document.getElementById('productModal');
    const form = document.getElementById('productForm');
    const title = document.getElementById('modalTitle');

    form.reset();
    currentEditId = productId;

    if (productId) {
        title.textContent = 'Edit Product';
        const product = allProducts.find(p => p.id === productId);
        if (product) {
            document.getElementById('sku').value = product.sku;
            document.getElementById('name').value = product.name;
            document.getElementById('description').value = product.description || '';
            document.getElementById('price').value = product.price;
            document.getElementById('categoryId').value = product.categoryId || '';
            document.getElementById('isActive').checked = product.isActive;
        }
    } else {
        title.textContent = 'Add Product';
    }

    modal.classList.add('show');
}

// Close Product Modal
function closeProductModal() {
    const modal = document.getElementById('productModal');
    modal.classList.remove('show');
    currentEditId = null;
}

// Handle Product Submit
async function handleProductSubmit(event) {
    event.preventDefault();

    const productData = {
        sku: document.getElementById('sku').value,
        name: document.getElementById('name').value,
        description: document.getElementById('description').value,
        price: parseFloat(document.getElementById('price').value),
        categoryId: document.getElementById('categoryId').value ? parseInt(document.getElementById('categoryId').value) : null,
        isActive: document.getElementById('isActive').checked
    };

    try {
        if (currentEditId) {
            await api.updateProduct(currentEditId, productData);
            showToast('Product updated successfully!', 'success');
        } else {
            await api.createProduct(productData);
            showToast('Product created successfully!', 'success');
        }

        closeProductModal();
        await loadProducts();

    } catch (error) {
        handleError(error, 'handleProductSubmit');
    }
}

// Edit Product
function editProduct(productId) {
    openProductModal(productId);
}

// Delete Product
async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) {
        return;
    }

    try {
        await api.deleteProduct(productId);
        showToast('Product deleted successfully!', 'success');
        await loadProducts();
    } catch (error) {
        handleError(error, 'deleteProduct');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initProductsPage();
});

// Export functions
window.openProductModal = openProductModal;
window.closeProductModal = closeProductModal;
window.handleProductSubmit = handleProductSubmit;
window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.handleSearch = handleSearch;
window.loadProducts = loadProducts;
